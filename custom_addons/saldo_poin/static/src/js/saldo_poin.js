/** @odoo-module */

import { Component, useState, onMounted, onWillUnmount } from "@odoo/owl";
import { registry } from "@web/core/registry";

export class ReferralSaldoPoin extends Component {
    setup() {
        this.member = {
            name: "Budi Santoso",
            initials: "BS",
            points: 1250,
            referrals: 3,
            code: "BUDI123",
        };

        this.state = useState({
            displayPoints: 0,
            copied: false,
            showToast: false,
            toastSuccess: true,
            toastMessage: "",
        });

        this._rafId = null;
        this._toastTimer = null;

        onMounted(() => this._startCountUp());
        onWillUnmount(() => {
            if (this._rafId) cancelAnimationFrame(this._rafId);
            if (this._toastTimer) clearTimeout(this._toastTimer);
        });
    }

    _startCountUp() {
        const target = this.member.points;
        const duration = 1400;
        const start = performance.now();

        const tick = (now) => {
            const p = Math.min(1, (now - start) / duration);
            const eased = 1 - Math.pow(1 - p, 3);
            this.state.displayPoints = Math.round(target * eased);
            if (p < 1) this._rafId = requestAnimationFrame(tick);
        };

        this._rafId = requestAnimationFrame(tick);
    }

    get formattedPoints() {
        return this.state.displayPoints.toLocaleString("id-ID");
    }

    async copyCode() {
        try {
            await navigator.clipboard.writeText(this.member.code);
            this.state.copied = true;
            this._showToast(true, "Tersalin!");
            setTimeout(() => { this.state.copied = false; }, 2000);
        } catch {
            this._showToast(false, "Gagal menyalin");
        }
    }

    _showToast(success, message) {
        if (this._toastTimer) clearTimeout(this._toastTimer);
        this.state.toastSuccess = success;
        this.state.toastMessage = message;
        this.state.showToast = true;
        this._toastTimer = setTimeout(() => { this.state.showToast = false; }, 2500);
    }
}

ReferralSaldoPoin.template = "referral_dashboard.SaldoPoin";
registry.category("actions").add("referral_saldo_poin_action", ReferralSaldoPoin);
