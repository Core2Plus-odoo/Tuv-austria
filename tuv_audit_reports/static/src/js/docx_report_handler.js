import { download } from "@web/core/network/download";
import { registry } from "@web/core/registry";

/**
 * Word (DOCX) reports of the Print menu (MDC / ATJF forms of the project):
 * download the filled .docx instead of a PDF.
 */
async function docxReportHandler(action, options, env) {
    if (action.report_type !== "docx") {
        return false;
    }
    const context = { ...(action.context || {}), ...(options.additionalContext || {}) };
    const ids = context.active_ids || (context.active_id ? [context.active_id] : []);
    for (const recordId of ids) {
        await download({
            url: "/tuv_audit_reports/docx",
            data: { report_id: action.id, record_id: recordId },
        });
    }
    return true;
}

registry.category("ir.actions.report handlers").add("tuv_docx_report", docxReportHandler);
