# Copyright 2026 Javier Anto
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class DocumentPage(models.Model):
    _inherit = "document.page"
    is_category_sort = fields.Boolean(
        compute="_compute_sort_fields",
        store=True,
        index=True,
    )
    category_name_sort = fields.Char(
        compute="_compute_sort_fields",
        store=True,
        index=True,
    )
    _order = (
        "is_category_sort desc, "
        "category_name_sort asc, "
        "content_date desc, "
        "history_head desc, "
        "id desc"
    )

    @api.depends("type", "name")
    def _compute_sort_fields(self):
        for page in self:
            is_category = page.type == "category"
            page.is_category_sort = is_category
            page.category_name_sort = page.name if is_category else ""
