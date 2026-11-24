import { Component, onWillStart, onWillUnmount, useState } from "@odoo/owl";
import { browser } from "@web/core/browser/browser";
import { formatDate, formatDateTime } from "@web/core/l10n/dates";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";

const REFRESH_INTERVAL = 60 * 1000;

/**
 * The opening screen of TUV Austria BIC: how many clients there are and where
 * they sit, city by city and country by country. Every bar is a link into the
 * matching Contacts list.
 *
 * The figures reload on their own once a minute, so a screen left open on the
 * wall stays current.
 */
export class TuvDashboard extends Component {
    static template = "tuv_austria_dashboard.Dashboard";
    static props = { ...standardActionServiceProps };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({
            data: null,
            loading: true,
            refreshing: false,
            cityLimit: 10,
            updatedAt: null,
        });
        onWillStart(() => this.load());

        // the cadence can be overridden from the action context, which is how the
        // client changes it without a code release
        const interval = this.props.action.context.tuv_refresh_interval || REFRESH_INTERVAL;
        this.timer = browser.setInterval(() => this.autoRefresh(), interval);
        onWillUnmount(() => browser.clearInterval(this.timer));
    }

    /**
     * @param {boolean} silent keep the figures on screen while they reload, so
     *  the minute tick does not blink the whole dashboard away
     */
    async load(silent = false) {
        this.state[silent ? "refreshing" : "loading"] = true;
        try {
            this.state.data = await this.orm.call("tuv.dashboard", "get_dashboard_data", []);
            this.state.updatedAt = formatDateTime(luxon.DateTime.now(), { format: "HH:mm" });
        } finally {
            this.state[silent ? "refreshing" : "loading"] = false;
        }
    }

    /** The minute tick. Skipped while the browser tab sits in the background. */
    autoRefresh() {
        if (this.state.loading || this.state.refreshing) {
            return;
        }
        if (document.hidden) {
            return;
        }
        this.load(true);
    }

    get today() {
        return formatDate(luxon.DateTime.now());
    }

    /** The widest bar fills the row, so small cities stay readable next to Lahore. */
    barWidth(row, rows) {
        const top = rows.length ? rows[0].count : 0;
        return top ? Math.max((row.count * 100) / top, 1.5) : 0;
    }

    /**
     * The share of the business the largest cities hold, as one stacked bar.
     * Concentration is the figure the management asks for: how much of the book
     * sits in a single place.
     */
    get concentration() {
        const palette = ["#e72929", "#b81d1d", "#0f1c2e", "#1b2b42", "#3d5a7f", "#8a99a8"];
        const rows = this.state.data.cities;
        const total = this.state.data.totals.clients;
        const segments = rows.slice(0, 5).map((row, index) => ({
            name: row.name,
            count: row.count,
            percent: row.percent,
            colour: palette[index],
            domain: row.domain,
        }));
        const rest = rows.slice(5).reduce((sum, row) => sum + row.count, 0);
        if (rest) {
            segments.push({
                name: _t("Other cities"),
                count: rest,
                percent: total ? Math.round((rest * 1000) / total) / 10 : 0,
                colour: palette[5],
                domain: null,
            });
        }
        return segments;
    }

    get cities() {
        const rows = this.state.data.cities;
        return this.state.cityLimit ? rows.slice(0, this.state.cityLimit) : rows;
    }

    toggleCities() {
        this.state.cityLimit = this.state.cityLimit ? 0 : 10;
    }

    openClients(title, extraDomain) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: title,
            res_model: "res.partner",
            domain: [...this.state.data.client_domain, ...(extraDomain || [])],
            views: [
                [false, "list"],
                [false, "kanban"],
                [false, "form"],
            ],
            target: "current",
            context: { create: false },
        });
    }

    openAllClients() {
        this.openClients(_t("Clients"), []);
    }
}

registry.category("actions").add("tuv_austria_dashboard.main", TuvDashboard);
