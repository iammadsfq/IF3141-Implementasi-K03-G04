import re

from odoo import http
from odoo.exceptions import ValidationError
from odoo.http import request


class ReferralRegistrationController(http.Controller):
    def _sanitize_text(self, value):
        return re.sub(r"\s+", " ", (value or "").strip())

    def _get_form_values(self, post_values):
        return {
            "name": self._sanitize_text(post_values.get("name")),
            "phone_number": re.sub(r"\s+", "", (post_values.get("phone_number") or "").strip()),
            "referral_code": self._sanitize_text(post_values.get("referral_code")).upper(),
            "privacy_consent": bool(post_values.get("privacy_consent")),
        }

    def _render_registration_form(self, form_values=None, error_message=False, success_message=False, created_member=False):
        return request.render(
            "referral_registration.referral_registration_page",
            {
                "form_values": form_values or {},
                "error_message": error_message,
                "success_message": success_message,
                "created_member": created_member,
            },
        )

    def _render_points_form(self, lookup_values=None, error_message=False, member=False):
        return request.render(
            "referral_registration.referral_points_page",
            {
                "lookup_values": lookup_values or {},
                "error_message": error_message,
                "member": member,
            },
        )

    @http.route("/referral/register", type="http", auth="public", website=True, methods=["GET"])
    def referral_register_form(self, **kwargs):
        return self._render_registration_form()

    @http.route(
        "/referral/register",
        type="http",
        auth="public",
        website=True,
        methods=["POST"],
        csrf=True,
    )
    def referral_register_submit(self, **post):
        form_values = self._get_form_values(post)
        member_model = request.env["referral.member"].sudo()

        if not form_values.get("name") or not form_values.get("phone_number"):
            return self._render_registration_form(form_values, "Nama dan nomor telepon wajib diisi.")

        if not re.fullmatch(r"\d+", form_values["phone_number"]):
            return self._render_registration_form(form_values, "Nomor telepon harus berupa angka.")

        if not form_values.get("privacy_consent"):
            return self._render_registration_form(
                form_values,
                "Persetujuan penggunaan data pelanggan wajib dicentang sebelum registrasi.",
            )

        try:
            created_member = member_model.createNewMember(
                {
                    "name": form_values["name"],
                    "phone_number": form_values["phone_number"],
                },
                referral_code=form_values["referral_code"],
            )
        except ValidationError as error:
            return self._render_registration_form(form_values, error.args[0])
        except Exception:
            request.env.cr.rollback()
            return self._render_registration_form(
                form_values,
                "Registrasi gagal diproses. Pastikan nomor telepon belum pernah terdaftar.",
            )

        success_message = "Registrasi berhasil. Akun referral Anda telah dibuat."
        if form_values.get("referral_code"):
            success_message = "Registrasi berhasil dengan referral valid. Akun Anda sudah terhubung dengan referrer."

        return self._render_registration_form({}, False, success_message, created_member)

    @http.route("/referral/points", type="http", auth="public", website=True, methods=["GET"])
    def referral_points_form(self, **kwargs):
        return self._render_points_form()

    @http.route(
        "/referral/points",
        type="http",
        auth="public",
        website=True,
        methods=["POST"],
        csrf=True,
    )
    def referral_points_lookup(self, **post):
        lookup_values = {
            "phone_number": re.sub(r"\s+", "", (post.get("phone_number") or "").strip()),
            "referral_code": self._sanitize_text(post.get("referral_code")).upper(),
        }

        if not lookup_values["phone_number"] or not lookup_values["referral_code"]:
            return self._render_points_form(
                lookup_values,
                "Nomor telepon dan kode referral wajib diisi untuk melihat saldo poin.",
            )

        member = request.env["referral.member"].sudo().search(
            [
                ("phone_number", "=", lookup_values["phone_number"]),
                ("referral_code", "=", lookup_values["referral_code"]),
            ],
            limit=1,
        )
        if not member:
            return self._render_points_form(
                lookup_values,
                "Data member tidak ditemukan. Pastikan nomor telepon dan kode referral sesuai.",
            )

        return self._render_points_form({}, False, member)
