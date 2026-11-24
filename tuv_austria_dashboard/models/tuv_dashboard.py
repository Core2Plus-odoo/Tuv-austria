from datetime import timedelta

from odoo import api, fields, models


class TuvDashboard(models.AbstractModel):
    """Read-only figures behind the Business Insurance dashboard."""

    _name = "tuv.dashboard"
    _description = "TUV Austria Dashboard"

    # A client is a company in Contacts. TUV certifies organisations, not people,
    # and customer_rank only counts the handful that already carry a sale order.
    CLIENT_DOMAIN = [("is_company", "=", True), ("user_ids", "=", False)]

    @api.model
    def _client_domain(self):
        domain = list(self.CLIENT_DOMAIN)
        own = self.env.companies.partner_id.ids
        if own:
            domain.append(("id", "not in", own))
        return domain

    @api.model
    def _percent(self, count, total):
        return round(count * 100.0 / total, 1) if total else 0.0

    @api.model
    def _group_by_country(self, domain, total):
        Partner = self.env["res.partner"]
        rows = []
        for country, count in Partner._read_group(domain, ["country_id"], ["__count"]):
            rows.append(
                {
                    "key": country.id or False,
                    "name": country.name or "Not set",
                    "code": country.code or "",
                    "count": count,
                    "percent": self._percent(count, total),
                    "domain": [("country_id", "=", country.id)] if country else [("country_id", "=", False)],
                }
            )
        return sorted(rows, key=lambda row: -row["count"])

    @api.model
    def _group_by_city(self, domain, total):
        """Group on the city name case-insensitively.

        The client base was imported over the years, so the same city arrives as
        "Lahore", "LAHORE" and "lahore". Counting those as three cities would make
        the dashboard lie, so they are folded together and shown title-cased.
        """
        Partner = self.env["res.partner"]
        merged = {}
        for city, count in Partner._read_group(domain, ["city"], ["__count"]):
            name = (city or "").strip()
            key = name.lower()
            entry = merged.setdefault(
                key, {"name": name.title() if name else "Not set", "count": 0, "spellings": []}
            )
            entry["count"] += count
            if name:
                entry["spellings"].append(name)
        rows = []
        for key, entry in merged.items():
            rows.append(
                {
                    "key": key or False,
                    "name": entry["name"],
                    "code": "",
                    "count": entry["count"],
                    "percent": self._percent(entry["count"], total),
                    "domain": [("city", "in", entry["spellings"])] if entry["spellings"] else [("city", "in", [False, ""])],
                }
            )
        return sorted(rows, key=lambda row: -row["count"])

    @api.model
    def get_dashboard_data(self):
        Partner = self.env["res.partner"]
        domain = self._client_domain()
        total = Partner.search_count(domain)

        countries = self._group_by_country(domain, total)
        cities = self._group_by_city(domain, total)
        month_ago = fields.Datetime.now() - timedelta(days=30)

        return {
            "company": self.env.company.name,
            "client_domain": domain,
            "totals": {
                "clients": total,
                "countries": len([row for row in countries if row["key"]]),
                "cities": len([row for row in cities if row["key"]]),
                "new_30_days": Partner.search_count(domain + [("create_date", ">=", month_ago)]),
            },
            "countries": countries,
            "cities": cities,
        }
