# Copyright 2025 Javier Antó Garcia <hola@javieranto.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3).

from odoo import api, fields, models


class ProductBookGenre(models.Model):
    _name = "product.book.genre"
    _description = "Book Genre"
    _parent_name = "parent_id"
    _parent_store = True
    _rec_name = "complete_name"
    _order = "complete_name"

    name = fields.Char(index=True, required=True)
    complete_name = fields.Char(
        compute="_compute_complete_name", recursive=True, store=True
    )
    parent_id = fields.Many2one(
        _name, ("Parent Category"), index=True, ondelete="cascade"
    )
    parent_path = fields.Char(index=True)
    book_ids = fields.Many2many("product.template")
    child_ids = fields.One2many(_name, "parent_id", ("Child Categories"))
    notes = fields.Text()
    color = fields.Integer()

    @api.depends("name", "parent_id.complete_name")
    def _compute_complete_name(self):
        for category in self:
            if category.parent_id:
                category.complete_name = (
                    f"{category.parent_id.complete_name} / {category.name}"
                )
            else:
                category.complete_name = category.name
