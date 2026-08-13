# Copyright 2025 Javier Antó Garcia <hola@javieranto.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # The config_parameter defines the key for the system parameter
    # that will store the value. Setting is available system-wide.
    blog_id = fields.Many2one(
        "blog.blog",
        string="Default Blog for Books",
        help="Select the blog where book posts will be published by default.",
        config_parameter="jag_library.default_blog_id",
    )
