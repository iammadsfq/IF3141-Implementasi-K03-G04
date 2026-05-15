from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ReferralPolicy(models.Model):
    _name = "referral.policy"
    _description = "Kebijakan Referral"
    _order = "active desc, write_date desc, id desc"

    name = fields.Char(string="Nama Kebijakan", default="Kebijakan Referral Aktif", required=True)
    active = fields.Boolean(default=True)
    max_point_monthly = fields.Integer(
        string="Maksimal Poin per Bulan",
        default=1000,
        required=True,
        help="Batas maksimal poin yang bisa didapat member dalam 1 periode bulan berjalan.",
    )
    point_per_referral = fields.Integer(
        string="Poin per Referral",
        default=50,
        required=True,
        help="Jumlah poin yang didapat referrer setiap kali referral tervalidasi.",
    )

    @api.constrains("max_point_monthly", "point_per_referral")
    def _check_positive_policy_values(self):
        for policy in self:
            if policy.max_point_monthly <= 0 or policy.point_per_referral <= 0:
                raise ValidationError(_("Nilai poin dan batas bulanan harus lebih dari nol."))
    
    @api.constrains("active")
    def _check_single_active_policy(self):
        for policy in self:
            if policy.active:
                other_active = self.search([
                    ("active", "=", True),
                    ("id", "!=", policy.id),
                ])
                if other_active:
                    raise ValidationError(
                        _("Hanya boleh ada satu kebijakan referral yang aktif. "
                        "Nonaktifkan kebijakan lain terlebih dahulu.")
                    )

    @api.model
    def getActivePolicy(self):
        policy = self.search([("active", "=", True)], limit=1)
        if not policy:
            policy = self.create(
                {
                    "name": _("Kebijakan Referral Aktif"),
                    "point_per_referral": 50,
                    "max_point_monthly": 1000,
                    "active": True,
                }
            )
        return policy

    def setPointsPerReferral(self, value):
        self.write({"point_per_referral": int(value or 0)})
        return True

    def setMaxPointMonthly(self, value):
        self.write({"max_point_monthly": int(value or 0)})
        return True

    @api.model
    def get_policy_payload(self):
        policy = self.getActivePolicy()
        return {
            "id": policy.id,
            "name": policy.name,
            "point_per_referral": policy.point_per_referral,
            "max_point_monthly": policy.max_point_monthly,
        }

    @api.model
    def save_policy_from_dashboard(self, values):
        point_per_referral = int((values or {}).get("point_per_referral") or 0)
        max_point_monthly = int((values or {}).get("max_point_monthly") or 0)
        if point_per_referral <= 0 or max_point_monthly <= 0:  # Ubah dari < 0
            raise ValidationError(_("Nilai poin dan batas bulanan harus lebih dari nol."))

        policy = self.getActivePolicy()
        policy.write(
            {
                "point_per_referral": point_per_referral,
                "max_point_monthly": max_point_monthly,
            }
        )
        return policy.get_policy_payload()
