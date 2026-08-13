# Copyright 2025 Javier Antó Garcia <hola@javieranto.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3).

import json
import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_book = fields.Boolean(string="Is a book")
    subtitle = fields.Char()
    isbn = fields.Char("ISBN")
    number_of_pages = fields.Integer()
    copies = fields.Integer(default=1)
    rating = fields.Selection(
        selection=[
            ("0", "Not Rated"),
            ("1", "Very Bad"),
            ("2", "Fair"),
            ("3", "Good"),
            ("4", "Very Good"),
            ("5", "Masterpiece"),
        ],
        default="0",
    )
    date_start_reading = fields.Date()
    date_end_reading = fields.Date()
    publication_year = fields.Integer(
        compute="_compute_publication_year",
        store=True,
    )
    publication_date = fields.Date()
    publisher_id = fields.Many2one(
        comodel_name="res.partner",
        domain=[("is_publisher", "=", True)],
    )
    author_ids = fields.Many2many(
        "res.partner",
        "res_partner_product_template_rel",
        "book_id",
        "partner_id",
        domain=[("is_author", "=", True)],
    )
    genre_ids = fields.Many2many(
        "product.book.genre",
        index=True,
    )
    language = fields.Many2one("res.lang", domain="[]")
    binding = fields.Selection(
        [
            ("hardcover", "Hard cover"),
            ("paperback", "paperback"),
            ("spiral", "Spiral"),
            ("ebook", "eBook"),
            ("other", "Other"),
        ],
    )
    edition = fields.Char()
    synopsis = fields.Html()
    reading_notes = fields.Html()
    image_back_cover_1920 = fields.Image("Back Cover", max_width=1920, max_height=1920)
    image_back_cover_1024 = fields.Image(
        "Back Cover 1024",
        related="image_back_cover_1920",
        max_width=1024,
        max_height=1024,
        store=True,
    )
    image_back_cover_512 = fields.Image(
        "Back Cover 512",
        related="image_back_cover_1920",
        max_width=512,
        max_height=512,
        store=True,
    )
    image_back_cover_256 = fields.Image(
        "Back Cover 256",
        related="image_back_cover_1920",
        max_width=256,
        max_height=256,
        store=True,
    )
    image_back_cover_128 = fields.Image(
        "Back Cover 128",
        related="image_back_cover_1920",
        max_width=128,
        max_height=128,
        store=True,
    )
    condition = fields.Selection(
        [
            ("new", "New"),
            ("good", "Good"),
            ("used", "Used"),
            ("damaged", "Damaged"),
        ],
        default="new",
    )
    location = fields.Char(
        string="Book Location",
        compute="_compute_location",
        store=True,
    )

    sequence = fields.Integer(
        default=10,
        help=(
            "Determines the order in the list view. "
            "The lowest number is displayed first."
        ),
    )

    is_website_published = fields.Boolean(
        readonly=False,
    )

    # Provide the exact field name expected by website helpers/controllers
    # so that /web/image can return the image publicly when this flag is set.
    website_published = fields.Boolean(
        string="Website Published",
        related="is_website_published",
        readonly=False,
        store=True,
    )

    blog_post_id = fields.Many2one("blog.post", copy=False)

    @api.depends("publication_date")
    def _compute_publication_year(self):
        for book in self:
            if book.publication_date:
                book.publication_year = book.publication_date.year
            else:
                book.publication_year = 0

    @api.depends(
        "product_variant_ids.stock_quant_ids.location_id",
        "product_variant_ids.stock_quant_ids.quantity",
        "qty_available",
    )
    def _compute_location(self):
        for book in self:
            # Filter quants to only include those in 'internal' locations
            # with a positive quantity.
            quants = book.product_variant_ids.mapped("stock_quant_ids")
            quants_in_internal_locs = quants.filtered(
                lambda q: q.location_id.usage == "internal" and q.quantity > 0
            )
            # Get the unique display names of these locations
            locations = quants_in_internal_locs.mapped("location_id.display_name")
            # Join the unique location names
            book.location = ", ".join(list(set(locations)))

    _sql_constraints = [
        (
            "library_book_name_date_uq",
            "UNIQUE (name, publication_date)",
            "Book title and publication date must be unique.",
        ),
        (
            "library_book_check_date",
            "CHECK (publication_date <= current_date)",
            "Publication date must not be in the future.",
        ),
        ("isbn_uniq", "UNIQUE (isbn)", "ISBN must be unique."),
    ]

    @api.constrains("isbn")
    def _constrain_isbn_valid(self):
        for book in self:
            if book.isbn and not book.check_isbn():
                raise ValidationError(
                    _("ISBN {} is invalid").format(book.isbn),
                )

    def check_isbn(self):
        self.ensure_one()
        digits = [int(x) for x in self.isbn if x.isdigit()]
        if len(digits) == 13:
            ponderations = [1, 3] * 6
            terms = [
                a * b
                for a, b in zip(
                    digits[:12],
                    ponderations,
                    strict=False,
                )
            ]
            remain = sum(terms) % 10
            check = 10 - remain if remain != 0 else 0
            return digits[-1] == check
        return False

    def button_check_isbn(self):
        """Check ISBN validity for all books in self."""
        for book in self:
            if not book.isbn:
                raise ValidationError(
                    _("Provide an ISBN for {}").format(book.name),
                )
            if not book.check_isbn():
                raise ValidationError(
                    _("ISBN {} is invalid").format(book.isbn),
                )
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "ISBN",
                "message": "ISBN OK!",
                "type": "info",
                "sticky": True,
                "next": {"type": "ir.actions.act_window_close"},
            },
        }

    publisher_country_id = fields.Many2one(
        "res.country",
        string="Publisher Country",
        related="publisher_id.country_id",
        readonly=False,
    )

    def _get_default_blog_id(self):
        """Get the default blog ID from config parameters."""
        config_params = self.env["ir.config_parameter"].sudo()
        blog_id_str = config_params.get_param("jag_library.default_blog_id")

        if not blog_id_str:
            raise UserError(
                _(
                    "No default blog is configured. Please set one in "
                    "Settings > Website > JAG Library."
                )
            )

        try:
            blog_id = int(blog_id_str)
        except (TypeError, ValueError):
            raise UserError(
                _(
                    "The configured default blog ID (%s) is invalid. "
                    "Please set a valid blog in Settings > Website > JAG Library."
                )
                % blog_id_str
            ) from None

        return blog_id

    def _get_blog_post_content(self):
        """
        Render QWeb template to generate blog post HTML content.

        Renders the content in the current language context.
        """
        self.ensure_one()
        return self.env["ir.qweb"]._render(
            "jag_library.blog_post_book_template",
            {"book": self, "book_id": self.id},
        )

    def _sync_blog_post_content_translations(self, post):
        """Save blog post content in all supported languages."""
        self.ensure_one()
        installed_langs = self.env["res.lang"].get_installed()
        for lang_code, _lang_name in installed_langs:
            translated_html = self.with_context(lang=lang_code)._get_blog_post_content()
            post.with_context(lang=lang_code).write({"content": translated_html})

    def _sync_product_image_attachment(self):
        """Create or update public attachment for product image.

        Ensures ir.attachment exists for image_1920 with public access,
        allowing /web/image to serve it to anonymous users.
        """
        self.ensure_one()
        if not self.image_1920:
            return

        try:
            attachment_model = self.env["ir.attachment"].sudo()
            domain = [
                ("res_model", "=", "product.template"),
                ("res_id", "=", self.id),
                ("res_field", "=", "image_1920"),
            ]
            attach = attachment_model.search(domain, limit=1)
            if attach:
                attach.write({"datas": self.image_1920, "public": True})
            else:
                attachment_model.create(
                    {
                        "name": f"{self.name}-image_1920",
                        "public": True,
                        "res_model": "product.template",
                        "res_id": self.id,
                        "res_field": "image_1920",
                        "datas": self.image_1920,
                    }
                )
        except Exception:
            _logger.exception(
                "Failed to create/update public attachment for product %s", self.id
            )

    def _unpublish_blog_post(self):
        """Unpublish the associated blog post if it exists."""
        self.ensure_one()
        if self.blog_post_id:
            self.blog_post_id.write({"is_published": False})

    def action_publish_to_blog(self):
        """Publish or update the book's blog post."""
        self.ensure_one()
        blog_default_id = self._get_default_blog_id()
        blog_id = self.env["blog.blog"].browse(blog_default_id)
        if not blog_id.exists():
            msg = _("The configured blog (ID: %s) no longer exists.") % blog_default_id
            raise UserError(msg)

        # Render content in English
        book_en = self.with_context(lang="en_US")
        post_content = book_en._get_blog_post_content()

        post_values = {
            "name": self.name,
            "blog_id": blog_id.id,
            "content": post_content,
            "is_published": False,
            "cover_properties": json.dumps(
                {
                    "background-image": f"url(/library/book/image/{self.id})",
                    "opacity": "0.6",
                    "resize_class": "o_half_screen_height",
                }
            ),
        }

        # Update or create blog post
        product_vals = {"is_website_published": True}
        if self.blog_post_id and self.blog_post_id.exists():
            self.blog_post_id.write(post_values)
            new_post = self.blog_post_id
        else:
            new_post = self.env["blog.post"].create(post_values)
            product_vals["blog_post_id"] = new_post.id

        # Sync translations
        self._sync_blog_post_content_translations(new_post)

        # Persist all product updates at once
        self.write(product_vals)

        # Ensure public attachment for product image
        self._sync_product_image_attachment()

        return {
            "name": _("Blog Post"),
            "type": "ir.actions.act_window",
            "res_model": "blog.post",
            "res_id": new_post.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_regenerate_blog_post_content(self):
        """Regenerate blog post content from template for all books.

        Used when template changes and existing posts need to be refreshed.
        """
        for book in self:
            if book.blog_post_id:
                book._sync_blog_post_content_translations(book.blog_post_id)
        return True


class ProductProduct(models.Model):
    _inherit = "product.product"

    def button_check_isbn(self):
        """
        Delegates the ISBN check to the product template.
        The button is on the product.product form, but the logic and fields
        (like ISBN) are on the product.template.
        """
        return self.product_tmpl_id.button_check_isbn()
