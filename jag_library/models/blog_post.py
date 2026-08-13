# Copyright 2025 Javier Antó Garcia <hola@javieranto.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
import re

from odoo import api, fields, models


class BlogPost(models.Model):
    """Extend blog.post for public book cover images and associations."""

    _inherit = "blog.post"

    # Field from upstream: associate books with blog posts
    product_ids = fields.One2many(
        "product.template",
        "blog_post_id",
        string="Associated Books",
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to convert cover_properties dict into JSON."""
        for vals in vals_list:
            self._ensure_cover_properties_json(vals)
        posts = super().create(vals_list)
        # Normalize cover image URLs for newly created posts
        for post in posts:
            post._update_cover_url()
        return posts

    def _ensure_cover_properties_json(self, vals):
        """Convert cover_properties dict to JSON string in vals dict if needed."""
        if "cover_properties" in vals and isinstance(vals["cover_properties"], dict):
            vals["cover_properties"] = json.dumps(vals["cover_properties"])

    @api.model
    def _fix_book_cover_urls(self):
        """
        Fix cover image URLs to use public controller.

        This method updates cover_properties of blog posts that reference
        product.template images to use the public controller instead.
        """
        posts = self.search([("cover_properties", "!=", False)])
        for post in posts:
            post._update_cover_url()

    @api.model
    def _get_public_cover_properties_json(self, cover_props_raw):
        """Return cover_properties JSON with public book URL, or None."""
        # cover_properties might be False, None, str, or dict
        if not cover_props_raw:
            return None

        # Parse JSON if it's a string
        if isinstance(cover_props_raw, str):
            try:
                cover_props = json.loads(cover_props_raw)
            except ValueError:
                return None
        elif isinstance(cover_props_raw, dict):
            cover_props = dict(cover_props_raw)
        else:
            return None

        if not isinstance(cover_props, dict):
            return None

        bg_image = cover_props.get("background-image", "")
        if "/web/image/product.template/" not in bg_image:
            return None

        # Format expected: url(/web/image/product.template/ID/field)
        # Capture both the product ID and the optional image field
        # (e.g. image_1920, image_1024).
        match = re.search(
            r"/web/image/product\.template/(\d+)(?:/([A-Za-z0-9_]+))?", bg_image
        )
        if not match:
            return None

        product_id = match.group(1)
        field_name = match.group(2)

        # Replace the exact matched /web/image/product.template/... segment
        old_url = match.group(0)
        if field_name:
            # Route with explicit field segment
            new_url = f"/library/book/image/{product_id}/{field_name}"
        else:
            # Route without field segment
            new_url = f"/library/book/image/{product_id}"
        new_bg_image = bg_image.replace(old_url, new_url)
        if new_bg_image == bg_image:
            return None

        cover_props["background-image"] = new_bg_image
        return json.dumps(cover_props)

    def _update_cover_url(self):
        """Update this post's cover URL to use public controller."""
        self.ensure_one()
        self._persist_cover_url_conversion()

    def write(self, vals):
        """Override write to fix cover URLs when cover_properties changes."""
        # Skip conversion if called from _persist_cover_url_conversion
        if self.env.context.get("skip_cover_conversion"):
            return super().write(vals)

        # Convert cover_properties dict to JSON string if needed
        # (base model expects a JSON string, not dict)
        vals = dict(vals)  # Make a copy to avoid modifying original
        self._ensure_cover_properties_json(vals)

        res = super().write(vals)
        if "cover_properties" in vals:
            for post in self:
                post._persist_cover_url_conversion()
        return res

    def _persist_cover_url_conversion(self):
        """Convert product.template URLs to public URLs and persist."""
        self.ensure_one()
        cover_props_json = self._get_public_cover_properties_json(self.cover_properties)
        if not cover_props_json:
            return

        # Use context to avoid recursion.
        self.with_context(skip_cover_conversion=True).write(
            {"cover_properties": cover_props_json}
        )
        # Ensure changes are flushed to database and cache is invalidated.
        self.flush_recordset()
        self.invalidate_recordset()
