/** @odoo-module */

import { Component, onWillStart, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";

export class ReferralDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.state = useState({
            period: "month",
            isLoading: true,
            errorMessage: "",
            kpiData: {
                totalReferrals: 0,
                totalRevenue: "Rp 0",
                totalPoints: 0,
            },
            topReferrers: [],
        });

        onWillStart(async () => {
            await this.loadDashboard();
        });
    }

    async loadDashboard() {
        this.state.isLoading = true;
        try {
            const data = await this.orm.call(
                "referral.transaction",
                "get_dashboard_metrics",
                [this.state.period]
            );
            this.state.kpiData = data.kpiData;
            this.state.topReferrers = data.topReferrers;
            this.state.errorMessage = "";
        } catch (error) {
            this.state.errorMessage =
                "Dashboard gagal dimuat. Pastikan modul referral sudah diperbarui.";
        } finally {
            this.state.isLoading = false;
        }
    }

    async setPeriod(period) {
        this.state.period = period;
        await this.loadDashboard();
    }
}

ReferralDashboard.template = "referral_dashboard.DashboardTemplate";

registry.category("actions").add("referral_dashboard_client_action", ReferralDashboard);
