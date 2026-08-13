# Copyright 2025 Javier Antó Garcia <hola@javieranto.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import ast
import base64
import json

from odoo.tests.common import TransactionCase


class TestBlogPostImageURLs(TransactionCase):
    """Test blog post automatic URL conversion for public images."""

    def setUp(self):
        super().setUp()

        # Create a test book with an image
        self.book = self.env[
            "product.template"
        ].create(
            {
                "name": "Test Book for Blog",
                "is_book": True,
                "isbn": "9783161484100",  # Valid ISBN-13
                # Create a small test image (1x1 pixel red PNG)
                "image_1920": base64.b64encode(
                    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00"
                    b"\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00"
                    b"\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf"
                    b"\xc0\x00\x00\x00\x00\xff\xff\x03\x00\x00\x05"
                    b"\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
                ),
                "type": "consu",
                "is_storable": True,
            }
        )

        # Create a blog
        self.blog = self.env["blog.blog"].create(
            {
                "name": "Test Blog",
            }
        )

    def _get_cover_props(self, post):
        """Helper to get cover_properties as dict (handles string JSON/Python dict)."""
        props = post.cover_properties
        if isinstance(props, str):
            if not props:
                return {}
            try:
                # Try JSON first (double quotes)
                return json.loads(props)
            except json.JSONDecodeError:
                # Fall back to Python literal (single quotes)
                return ast.literal_eval(props)
        return props or {}

    def test_fix_book_cover_urls_method(self):
        """Test _fix_book_cover_urls method converts old URLs."""
        # Create a blog post with old-style image URL
        post = self.env["blog.post"].create(
            {
                "name": "Test Post",
                "blog_id": self.blog.id,
                "cover_properties": {
                    "background-image": (
                        f"url(/web/image/product.template/{self.book.id}"
                        f"/image_1920)"
                    ),
                    "opacity": "0.6",
                },
            }
        )

        # Run the fix method
        self.env["blog.post"]._fix_book_cover_urls()

        # Reload the post to get updated values
        post.invalidate_recordset()

        # Check that URL was converted
        bg_image = self._get_cover_props(post).get("background-image", "")
        self.assertIn(
            f"/library/book/image/{self.book.id}",
            bg_image,
            "URL should be converted to public controller",
        )
        self.assertNotIn(
            "/web/image/product.template/",
            bg_image,
            "Old URL pattern should be removed",
        )

    def test_write_auto_converts_urls(self):
        """Test that write() automatically converts URLs."""
        # Create a post
        post = self.env["blog.post"].create(
            {
                "name": "Test Post",
                "blog_id": self.blog.id,
            }
        )

        # Update with old-style image URL
        post.write(
            {
                "cover_properties": {
                    "background-image": (
                        f"url(/web/image/product.template/{self.book.id}"
                        f"/image_1920)"
                    ),
                }
            }
        )

        # Check that URL was auto-converted
        post.invalidate_recordset()
        bg_image = self._get_cover_props(post).get("background-image", "")
        self.assertIn(
            f"/library/book/image/{self.book.id}",
            bg_image,
            "URL should be auto-converted on write",
        )

    def test_update_cover_url_helper_method(self):
        """Test _update_cover_url helper method."""
        post = self.env["blog.post"].create(
            {
                "name": "Test Post",
                "blog_id": self.blog.id,
                "cover_properties": {
                    "background-image": (
                        f"url(/web/image/product.template/{self.book.id}"
                        f"/image_1920)"
                    ),
                },
            }
        )

        # Call the helper method directly
        post._update_cover_url()

        # Check conversion
        bg_image = self._get_cover_props(post).get("background-image", "")
        self.assertIn(
            "/library/book/image/",
            bg_image,
            "Helper method should convert URL",
        )

    def test_no_conversion_for_non_product_urls(self):
        """Test that non-product URLs are not modified."""
        original_url = "url(/web/image/some_other_model/123/image)"
        post = self.env["blog.post"].create(
            {
                "name": "Test Post",
                "blog_id": self.blog.id,
                "cover_properties": {
                    "background-image": original_url,
                },
            }
        )

        # Run fix method
        self.env["blog.post"]._fix_book_cover_urls()
        post.invalidate_recordset()

        # URL should remain unchanged
        bg_image = self._get_cover_props(post).get("background-image", "")
        self.assertEqual(
            bg_image,
            original_url,
            "Non-product URLs should not be modified",
        )

    def test_no_conversion_without_cover_properties(self):
        """Test that posts without cover_properties don't cause errors."""
        post = self.env["blog.post"].create(
            {
                "name": "Test Post Without Cover",
                "blog_id": self.blog.id,
            }
        )

        # Should not raise any error
        try:
            self.env["blog.post"]._fix_book_cover_urls()
            post.write({"name": "Updated Name"})
        except Exception as e:
            self.fail(f"Should not raise error: {e}")

    def test_multiple_posts_bulk_fix(self):
        """Test fixing URLs for multiple posts at once."""
        # Create multiple posts with old URLs
        posts = self.env["blog.post"]
        for i in range(3):
            post = self.env["blog.post"].create(
                {
                    "name": f"Test Post {i}",
                    "blog_id": self.blog.id,
                    "cover_properties": {
                        "background-image": (
                            f"url(/web/image/product.template/{self.book.id}"
                            f"/image_1920)"
                        ),
                    },
                }
            )
            posts |= post

        # Fix all URLs
        self.env["blog.post"]._fix_book_cover_urls()

        # Check all were converted
        for post in posts:
            post.invalidate_recordset()
            bg_image = self._get_cover_props(post).get("background-image", "")
            self.assertIn(
                "/library/book/image/",
                bg_image,
                f"Post {post.name} should have converted URL",
            )

    def test_product_ids_field_relationship(self):
        """Test product_ids One2many relationship."""
        # Create a blog post
        post = self.env["blog.post"].create(
            {
                "name": "Test Post with Book",
                "blog_id": self.blog.id,
            }
        )

        # Associate the book with the post
        self.book.blog_post_id = post.id

        # Check the relationship
        self.assertEqual(
            post.product_ids[0],
            self.book,
            "Book should be associated with post",
        )
        self.assertEqual(
            self.book.blog_post_id,
            post,
            "Post should be associated with book",
        )
