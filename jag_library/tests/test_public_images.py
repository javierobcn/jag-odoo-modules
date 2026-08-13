# Copyright 2025 Javier Antó Garcia <hola@javieranto.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64

from odoo.tests.common import HttpCase


class TestPublicBookImages(HttpCase):
    """Test public access to book cover images via HTTP controller."""

    def setUp(self):
        super().setUp()
        # Create a test book with an image
        self.book = self.env["product.template"].create(
            {
                "name": "Test Book for Images",
                "is_book": True,
                "is_website_published": True,
                "isbn": "9780201633610",
                # Create a small test image (1x1 pixel red PNG)
                "image_1920": base64.b64encode(
                    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00"
                    b"\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00"
                    b"\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf"
                    b"\xc0\x00\x00\x00\x00\xff\xff\x03\x00\x00\x05"
                    b"\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
                ),
            }
        )
        self.book_back_cover = self.env["product.template"].create(
            {
                "name": "Test Book with Back Cover",
                "is_book": True,
                "is_website_published": True,
                "isbn": "9780132350884",
                "image_back_cover_1920": base64.b64encode(
                    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00"
                    b"\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00"
                    b"\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf"
                    b"\xc0\x00\x00\x00\x00\xff\xff\x03\x00\x00\x05"
                    b"\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
                ),
            }
        )
        self.non_book = self.env["product.template"].create(
            {
                "name": "Not a Book",
                "is_book": False,
            }
        )
        self.unpublished_book = self.env["product.template"].create(
            {
                "name": "Unpublished Book",
                "is_book": True,
                "is_website_published": False,
                "isbn": "9781492051367",
                "image_1920": base64.b64encode(
                    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00"
                    b"\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00"
                    b"\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf"
                    b"\xc0\x00\x00\x00\x00\xff\xff\x03\x00\x00\x05"
                    b"\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
                ),
            }
        )
        self.unpublished_back_cover_book = self.env["product.template"].create(
            {
                "name": "Unpublished Book with Back Cover",
                "is_book": True,
                "is_website_published": False,
                "isbn": "9781449331818",
                "image_back_cover_1920": base64.b64encode(
                    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00"
                    b"\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00"
                    b"\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf"
                    b"\xc0\x00\x00\x00\x00\xff\xff\x03\x00\x00\x05"
                    b"\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
                ),
            }
        )

    def test_public_access_book_cover_image(self):
        """Test that book cover images are accessible publicly."""
        url = f"/library/book/image/{self.book.id}"
        response = self.url_open(url)

        # Should return 200 OK
        self.assertEqual(
            response.status_code,
            200,
            "Book cover image should be accessible publicly",
        )

        # Test data is PNG, controller should return the real MIME type.
        self.assertEqual(
            response.headers.get("Content-Type", ""),
            "image/png",
            "Response should have PNG content type",
        )

        # Should have cache headers
        cache_control = response.headers.get("Cache-Control", "")
        self.assertIn(
            "public",
            cache_control,
            "Response should have public cache control",
        )

    def test_public_access_back_cover_image(self):
        """Test that back cover images are accessible publicly."""
        url = f"/library/book/back_cover/{self.book_back_cover.id}"
        response = self.url_open(url)

        # Should return 200 OK
        self.assertEqual(
            response.status_code,
            200,
            "Back cover image should be accessible publicly",
        )

        # Test data is PNG, controller should return the real MIME type.
        self.assertEqual(
            response.headers.get("Content-Type", ""),
            "image/png",
            "Response should have PNG content type",
        )

    def test_access_different_image_sizes(self):
        """Test access to different image sizes."""
        sizes = [
            "image_1920",
            "image_1024",
            "image_512",
            "image_256",
            "image_128",
        ]

        for size in sizes:
            url = f"/library/book/image/{self.book.id}/{size}"
            response = self.url_open(url)

            self.assertEqual(
                response.status_code,
                200,
                f"Should be able to access {size}",
            )

    def test_non_book_returns_404(self):
        """Test that non-book products return 404."""
        url = f"/library/book/image/{self.non_book.id}"
        response = self.url_open(url)

        # Should return 404 for non-book products
        self.assertEqual(
            response.status_code,
            404,
            "Non-book products should return 404",
        )

    def test_unpublished_book_returns_404(self):
        """Test that unpublished books do not expose cover images."""
        url = f"/library/book/image/{self.unpublished_book.id}"
        response = self.url_open(url)

        self.assertEqual(
            response.status_code,
            404,
            "Unpublished books should return 404",
        )

    def test_unpublished_back_cover_returns_404(self):
        """Test that unpublished books do not expose back cover images."""
        url = f"/library/book/back_cover/{self.unpublished_back_cover_book.id}"
        response = self.url_open(url)

        self.assertEqual(
            response.status_code,
            404,
            "Unpublished books back cover should return 404",
        )

    def test_non_existent_book_returns_404(self):
        """Test that non-existent book IDs return 404."""
        url = "/library/book/image/99999999"
        response = self.url_open(url)

        # Should return 404 for non-existent IDs
        self.assertEqual(
            response.status_code,
            404,
            "Non-existent book IDs should return 404",
        )

    def test_book_without_image_returns_404(self):
        """Test that books without images return 404."""
        book_no_image = self.env["product.template"].create(
            {
                "name": "Book without Image",
                "is_book": True,
                "isbn": "9780131103627",
            }
        )

        url = f"/library/book/image/{book_no_image.id}"
        response = self.url_open(url)

        # Should return 404 when no image is available
        self.assertEqual(
            response.status_code,
            404,
            "Books without images should return 404",
        )

    def test_invalid_field_uses_default(self):
        """Test that invalid field names default to image_1920."""
        # Try to access with an invalid field name
        url = f"/library/book/image/{self.book.id}/invalid_field"
        response = self.url_open(url)

        # Should still work, defaulting to image_1920
        self.assertEqual(
            response.status_code,
            200,
            "Invalid field should default to image_1920",
        )

    def test_unauthorized_access_works(self):
        """Test that images are accessible without authentication."""
        # Logout to ensure we're not authenticated
        self.authenticate(None, None)

        url = f"/library/book/image/{self.book.id}"
        response = self.url_open(url)

        # Should work without authentication
        self.assertEqual(
            response.status_code,
            200,
            "Images should be accessible without authentication",
        )
