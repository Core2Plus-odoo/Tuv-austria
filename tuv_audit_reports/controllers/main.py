from odoo import http
from odoo.http import content_disposition, request


class TuvDocxReportController(http.Controller):

    @http.route('/tuv_audit_reports/docx', type='http', auth='user', methods=['POST'])
    def download_docx_report(self, report_id, record_id, **kwargs):
        """Word (DOCX) report of the Print menu, filled for one record."""
        report = request.env['ir.actions.report'].browse(int(report_id)).exists()
        if not report or report.report_type != 'docx':
            raise request.not_found()
        content, filename = report._render_mdc_docx([int(record_id)])
        return request.make_response(content, headers=[
            ('Content-Type', 'application/vnd.openxmlformats-officedocument.'
                             'wordprocessingml.document'),
            ('Content-Length', len(content)),
            ('Content-Disposition', content_disposition(filename)),
        ])
