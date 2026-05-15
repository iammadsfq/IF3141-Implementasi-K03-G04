/** @odoo-module */

import { Component, onWillStart, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";

export class ReferralPolicy extends Component {
    setup() {
        this.orm = useService("orm");
        this.state = useState({
            policyId: false,
            pointPerReferral: 0,
            maxPointMonthly: 0,
            isLoading: true,
            isSaving: false,
            showSuccess: false,
            showError: false,
            errorMessage: "",
        });

        onWillStart(async () => {
            await this.loadPolicy();
        });
    }

    async loadPolicy() {
        try {
            const policy = await this.orm.call("referral.policy", "get_policy_payload", []);
            this.state.policyId = policy.id;
            this.state.pointPerReferral = policy.point_per_referral;
            this.state.maxPointMonthly = policy.max_point_monthly;
            this.state.showError = false;
        } catch (error) {
            this.state.showError = true;
            this.state.errorMessage = "Kebijakan aktif gagal dimuat.";
        } finally {
            this.state.isLoading = false;
        }
    }

    async savePolicy() {
        const pointPerReferral = Number.parseInt(this.state.pointPerReferral, 10);
        const maxPointMonthly = Number.parseInt(this.state.maxPointMonthly, 10);

        if (
            Number.isNaN(pointPerReferral) ||
            Number.isNaN(maxPointMonthly) ||
            pointPerReferral < 0 ||
            maxPointMonthly < 0
        ) {
            this.state.showError = true;
            this.state.showSuccess = false;
            this.state.errorMessage = "Format input tidak valid. Pastikan Anda memasukkan angka positif.";
            return;
        }

        this.state.isSaving = true;
        try {
            const policy = await this.orm.call("referral.policy", "save_policy_from_dashboard", [
                {
                    point_per_referral: pointPerReferral,
                    max_point_monthly: maxPointMonthly,
                },
            ]);
            this.state.policyId = policy.id;
            this.state.pointPerReferral = policy.point_per_referral;
            this.state.maxPointMonthly = policy.max_point_monthly;
            this.state.showError = false;
            this.state.showSuccess = true;

            setTimeout(() => {
                this.state.showSuccess = false;
            }, 4000);
        } catch (error) {
            this.state.showError = true;
            this.state.showSuccess = false;
            this.state.errorMessage = "Kebijakan gagal disimpan. Periksa kembali nilai yang dimasukkan.";
        } finally {
            this.state.isSaving = false;
        }
    }
    
    async cancel() {
        this.state.showSuccess = false;
        this.state.showError = false;
        this.state.isLoading = true;
        await this.loadPolicy();
    }
}

ReferralPolicy.template = "referral_dashboard.PolicyTemplate";

registry.category("actions").add("referral_policy_client_action", ReferralPolicy);
