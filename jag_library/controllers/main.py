# Copyright 2025 Javier Antó Garcia <hola@javieranto.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64

from odoo import http
from odoo.http import request


class LibraryController(http.Controller):
    """Controller to serve book images publicly."""

    @staticmethod
    def _guess_image_mimetype(image_binary):
        """Return MIME type inferred from image magic bytes."""
        if image_binary.startswith(b"\x89PNG\r\n\x1a\n"):
            return "image/png"
        if image_binary.startswith(b"\xff\xd8\xff"):
            return "image/jpeg"
        if image_binary.startswith((b"GIF87a", b"GIF89a")):
            return "image/gif"
        if (
            len(image_binary) >= 12
            and image_binary[:4] == b"RIFF"
            and image_binary[8:12] == b"WEBP"
        ):
            return "image/webp"
        return "application/octet-stream"

    def _serve_book_image(self, book_id, field, allowed_fields, default_field):
        """Serve book images publicly with security checks.

        Args:
            book_id: ID of the product.template record
            field: Requested image field name
            allowed_fields: List of allowed field names for security
            default_field: Default field to use if field not allowed

        Returns:
            HTTP response with image data or not_found()
        """
        # Security: Only allow specific fields
        if field not in allowed_fields:
            field = default_field

        # Get the product template (book)
        product = request.env["product.template"].sudo().browse(book_id)

        # Only expose images for books intentionally published on website.
        if (
            not product.exists()
            or not product.is_book
            or not product.is_website_published
        ):
            raise request.not_found()

        # Get the image data
        image_data = getattr(product, field, False)
        if not image_data:
            raise request.not_found()

        # Only decoding problems are expected user/data errors.
        try:
            image_binary = base64.b64decode(image_data, validate=True)
        except (TypeError, ValueError):
            raise request.not_found() from None

        content_type = self._guess_image_mimetype(image_binary)

        # Return image with appropriate headers
        return request.make_response(
            image_binary,
            headers=[
                ("Content-Type", content_type),
                ("Cache-Control", "public, max-age=604800"),  # Cache for 1 week
            ],
        )

    @http.route(
        [
            "/library/book/image/<int:book_id>",
            "/library/book/image/<int:book_id>/<string:field>",
        ],
        type="http",
        auth="public",
        website=True,
    )
    def book_image(self, book_id, field="image_1920", **kwargs):
        """Serve book cover images publicly."""
        allowed_fields = [
            "image_1920",
            "image_1024",
            "image_512",
            "image_256",
            "image_128",
        ]
        return self._serve_book_image(book_id, field, allowed_fields, "image_1920")

    @http.route(
        [
            "/library/book/back_cover/<int:book_id>",
            "/library/book/back_cover/<int:book_id>/<string:field>",
        ],
        type="http",
        auth="public",
        website=True,
    )
    def book_back_cover(self, book_id, field="image_back_cover_1920", **kwargs):
        """Serve book back cover images publicly."""
        allowed_fields = [
            "image_back_cover_1920",
            "image_back_cover_1024",
            "image_back_cover_512",
            "image_back_cover_256",
            "image_back_cover_128",
        ]
        return self._serve_book_image(
            book_id, field, allowed_fields, "image_back_cover_1920"
        )
