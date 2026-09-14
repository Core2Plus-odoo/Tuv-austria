# Copyright 2022 360 ERP (<https://www.360erp.nl>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    pdf_watermark = fields.Binary("Watermark")
    # Local addition (TUV Austria): rather than ticking a box on every report one by
    # one, the company names here the reports its letterhead belongs on. Anything not
    # listed prints without it - the Application Form and the Review Form carry their
    # own printed letterhead and must stay untouched.
    watermark_report_ids = fields.Many2many(
        "ir.actions.report",
        "res_company_watermark_report_rel",
        "company_id",
        "report_id",
        string="Reports With Letterhead",
        domain=[("report_type", "=", "qweb-pdf")],
        help="The watermark above is printed behind these reports only.",
    )

    watermark_margin_left = fields.Float(
        "Letterhead Left Margin (mm)",
        default=14.0,
        help="On the reports above, keep the printed text at least this far from "
        "the left edge so it does not run into the letterhead artwork.",
    )
    watermark_margin_right = fields.Float(
        "Letterhead Right Margin (mm)",
        default=36.0,
        help="On the reports above, keep the printed text at least this far from "
        "the right edge so it does not run into the letterhead address column.",
    )
