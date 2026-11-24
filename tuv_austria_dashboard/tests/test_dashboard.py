from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestTuvDashboard(HttpCase):
    def test_data_matches_contacts(self):
        """Every bar must open exactly the contacts it counted."""
        Partner = self.env["res.partner"]
        data = self.env["tuv.dashboard"].get_dashboard_data()
        base = data["client_domain"]

        self.assertEqual(data["totals"]["clients"], Partner.search_count(base))
        for row in data["countries"] + data["cities"]:
            self.assertEqual(
                Partner.search_count(base + row["domain"]),
                row["count"],
                "the %r bar does not open the contacts it counted" % row["name"],
            )
        # the shares add up (rounding aside)
        for group in ("countries", "cities"):
            self.assertAlmostEqual(sum(r["percent"] for r in data[group]), 100.0, delta=1.0)

    def test_city_spellings_are_folded(self):
        """LAHORE and Lahore are one city, not two."""
        country = self.env.ref("base.pk")
        self.env["res.partner"].create(
            [
                {"name": "TUV Test A", "is_company": True, "city": "Lahore", "country_id": country.id},
                {"name": "TUV Test B", "is_company": True, "city": "LAHORE", "country_id": country.id},
                {"name": "TUV Test C", "is_company": True, "city": " lahore ", "country_id": country.id},
            ]
        )
        cities = self.env["tuv.dashboard"].get_dashboard_data()["cities"]
        lahore = [row for row in cities if row["name"] == "Lahore"]
        self.assertEqual(len(lahore), 1, "Lahore was counted more than once")

    def test_dashboard_renders(self):
        """The client action mounts without a single console error."""
        action = self.env.ref("tuv_austria_dashboard.action_tuv_dashboard")
        self.browser_js(
            "/odoo/action-%s" % action.id,
            "console.log('test successful')",
            "!!document.querySelector('.o_tuv_dashboard .o_tuv_kpi_value')",
            login="admin",
            timeout=120,
        )

    def test_dashboard_auto_refreshes(self):
        """The figures reload on their own, without blanking the screen.

        The minute timer is driven forward by hand: the test cannot sit and wait
        a real minute, so browser.setInterval is patched to fire at once.
        """
        action = self.env.ref("tuv_austria_dashboard.action_tuv_dashboard").copy(
            {"context": "{'tuv_refresh_interval': 800}"}
        )
        code = """
            (async () => {
                const { rpcBus } = odoo.loader.modules.get("@web/core/network/rpc");
                let calls = 0;
                rpcBus.addEventListener("RPC:REQUEST", (ev) => {
                    if (ev.detail.data.params.model === "tuv.dashboard") {
                        calls++;
                    }
                });
                const shown = () => document.querySelector(".o_tuv_kpi_value").textContent;
                const before = shown();
                await new Promise((r) => setTimeout(r, 3000));
                if (calls < 2) {
                    console.error("the dashboard did not refresh itself, calls=" + calls);
                } else if (shown() !== before) {
                    console.error("the figures changed while nothing else did");
                } else if (!document.querySelector(".o_tuv_live")) {
                    console.error("no auto-refresh indicator on screen");
                } else {
                    console.log("test successful");
                }
            })();
        """
        self.browser_js(
            "/odoo/action-%s" % action.id,
            code,
            "!!document.querySelector('.o_tuv_dashboard .o_tuv_kpi_value')",
            login="admin",
            timeout=120,
        )
