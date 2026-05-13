import re
import secrets
import string

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ReferralMember(models.Model):
    _name = "referral.member"
    _description = "Referral Member"
    _order = "create_date desc"
    _REFERRAL_CODE_PATTERN = re.compile(r"^[A-Z0-9]{6}$")

    name = fields.Char(required=True)
    phone_number = fields.Char(required=True)
    referral_code = fields.Char(readonly=True, copy=False, index=True)
    point = fields.Integer(default=0)
    referred_by_id = fields.Many2one("referral.member", string="Referred By", ondelete="set null")
    referred_member_ids = fields.One2many("referral.member", "referred_by_id", string="Referred Members")

    _sql_constraints = [
        ("referral_member_referral_code_unique", "unique(referral_code)", "Kode referral harus unik."),
        (
            "referral_member_phone_unique",
            "unique(phone_number)",
            "Nomor telepon sudah terdaftar. Gunakan nomor lain.",
        ),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records.filtered(lambda member: not member.referral_code).action_generate_referral_code()
        return records

    def action_generate_referral_code(self):
        for member in self:
            if not member.referral_code:
                member.referral_code = self._generate_unique_referral_code()
        return True

    @api.model
    def _generate_unique_referral_code(self):
        characters = string.ascii_uppercase + string.digits
        for _ in range(100):
            referral_code = "".join(secrets.choice(characters) for _ in range(6))
            if not self.search_count([("referral_code", "=", referral_code)]):
                return referral_code
        raise ValidationError(_("Gagal membuat kode referral unik. Silakan coba lagi."))

    def computePoints(self, points=0):
        for member in self:
            member.point += int(points or 0)
        return True

    @api.model
    def _sanitize_text(self, value):
        return re.sub(r"\s+", " ", (value or "").strip())

    @api.model
    def _sanitize_phone(self, value):
        return re.sub(r"\s+", "", (value or "").strip())

    @api.model
    def _is_phone_registered(self, phone_number):
        return bool(phone_number) and bool(self.search_count([("phone_number", "=", phone_number)]))

    @api.model
    def getMember(self, member_id=None, referral_code=None):
        if member_id:
            return self.browse(member_id).exists()
        if referral_code:
            return self.searchBasedOnReferral(referral_code)
        return self.browse()

    @api.model
    def searchBasedOnReferral(self, referral_code):
        normalized_referral_code = (referral_code or "").strip().upper()
        if not normalized_referral_code:
            return self.browse()
        if not self._REFERRAL_CODE_PATTERN.match(normalized_referral_code):
            return self.browse()
        return self.search([("referral_code", "=", normalized_referral_code)], limit=1)

    @api.model
    def createNewMember(self, member_values, referral_code=None):
        values = dict(member_values or {})
        values["name"] = self._sanitize_text(values.get("name"))
        values["phone_number"] = self._sanitize_phone(values.get("phone_number"))

        if not values.get("name") or not values.get("phone_number"):
            raise ValidationError(_("Nama dan nomor telepon wajib diisi."))
        if not re.fullmatch(r"\d+", values["phone_number"]):
            raise ValidationError(_("Nomor telepon harus berupa angka."))

        phone_exists = self._is_phone_registered(values["phone_number"])
        if phone_exists:
            raise ValidationError(_("Nomor telepon sudah terdaftar. Gunakan nomor lain."))

        normalized_referral_code = (referral_code or "").strip().upper()

        referrer = self.browse()
        if normalized_referral_code:
            if not self._REFERRAL_CODE_PATTERN.match(normalized_referral_code):
                raise ValidationError(_("Format kode referral tidak valid. Gunakan 6 karakter huruf kapital/angka."))
            referrer = self.searchBasedOnReferral(normalized_referral_code)
            if not referrer:
                raise ValidationError(_("Kode referral tidak ditemukan."))
            values["referred_by_id"] = referrer.id

        new_member = self.create(values)
        if referrer:
            referrer.computePoints(1)
        return new_member
