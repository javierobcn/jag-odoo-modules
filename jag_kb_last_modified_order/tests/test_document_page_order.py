# Copyright 2026 Javier Anto
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from lxml import etree

from odoo.tests.common import TransactionCase


class TestDocumentPageOrder(TransactionCase):
    def setUp(self):
        super().setUp()
        self.category = self.env["document.page"].create(
            {
                "name": "Category",
                "type": "category",
            }
        )

    def test_content_is_sorted_by_last_modification_desc(self):
        page_a = self.env["document.page"].create(
            {
                "name": "AAA older contribution",
                "type": "content",
                "parent_id": self.category.id,
                "content": "<p>A</p>",
            }
        )
        page_z = self.env["document.page"].create(
            {
                "name": "ZZZ newer contribution",
                "type": "content",
                "parent_id": self.category.id,
                "content": "<p>Z</p>",
            }
        )

        # Update through ORM to create a newer page revision.
        page_a.write({"content": "<p>A updated</p>"})

        ordered_pages = self.env["document.page"].search(
            [("id", "in", (page_a.id, page_z.id)), ("type", "=", "content")]
        )

        self.assertEqual(ordered_pages[0], page_a)

    def test_category_is_sorted_by_name_asc(self):
        category_z = self.env["document.page"].create(
            {
                "name": "Zeta",
                "type": "category",
            }
        )
        category_a = self.env["document.page"].create(
            {
                "name": "Alpha",
                "type": "category",
            }
        )

        ordered_categories = self.env["document.page"].search(
            [
                ("id", "in", (category_z.id, category_a.id)),
                ("type", "=", "category"),
            ]
        )

        self.assertEqual(ordered_categories[0], category_a)

    def test_kanban_shows_last_contribution_date(self):
        kanban_view_id = self.env.ref("document_page.view_browse_content_kanban").id
        view = self.env["document.page"].get_view(
            view_id=kanban_view_id,
            view_type="kanban",
        )
        arch = etree.XML(view["arch"])
        default_order = ",".join(
            [
                "is_category_sort desc",
                "category_name_sort asc",
                "content_date desc",
                "id desc",
            ]
        )

        self.assertTrue(arch.xpath("//kanban/field[@name='content_date']"))
        self.assertTrue(arch.xpath(f"//kanban[@default_order='{default_order}']"))
        self.assertTrue(arch.xpath("//t[@t-name='card']//field[@name='content_date']"))
        self.assertFalse(arch.xpath("//kanban/field[@name='write_date']"))
