/** @odoo-module */

import { Component, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";

export class ReferralPolicy extends Component {
    setup() {
        // State untuk menyimpan nilai input dan status notifikasi
        this.state = useState({
            pointPerReferral: 50,
            maxPointMonthly: 1000,
            showSuccess: false,
            showError: false,
            errorMessage: "",
        });
    }

    savePolicy() {
        if (this.state.pointPerReferral < 0 || this.state.maxPointMonthly < 0 || 
            this.state.pointPerReferral === "" || this.state.maxPointMonthly === "") {
            
            this.state.showError = true;
            this.state.showSuccess = false;
            this.state.errorMessage = "Format input tidak valid. Pastikan Anda memasukkan angka positif.";
            return;
        }
        
        // Simulasi Berhasil Simpan
        this.state.showError = false;
        this.state.showSuccess = true;
        
        setTimeout(() => {
            this.state.showSuccess = false;
        }, 4000);
    }
    
    cancel() {
        this.state.pointPerReferral = 50;
        this.state.maxPointMonthly = 1000;
        this.state.showSuccess = false;
        this.state.showError = false;
    }
}

ReferralPolicy.template = "referral_dashboard.PolicyTemplate";

registry.category("actions").add("referral_policy_client_action", ReferralPolicy);