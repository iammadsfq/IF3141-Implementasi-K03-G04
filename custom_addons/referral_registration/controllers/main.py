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
        }

    @http.route("/referral/register", type="http", auth="public", website=True, methods=["GET"])
    def referral_register_form(self, **kwargs):
        return request.render(
            "referral_registration.referral_registration_page",
            {
                "form_values": {},
                "error_message": False,
                "success_message": False,
                "created_member": False,
            },
        )

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
            return request.render(
                "referral_registration.referral_registration_page",
                {
                    "form_values": form_values,
                    "error_message": "Nama dan nomor telepon wajib diisi.",
                    "success_message": False,
                    "created_member": False,
                },
            )

        if not re.fullmatch(r"\d+", form_values["phone_number"]):
            return request.render(
                "referral_registration.referral_registration_page",
                {
                    "form_values": form_values,
                    "error_message": "Nomor telepon harus berupa angka.",
                    "success_message": False,
                    "created_member": False,
                },
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
            return request.render(
                "referral_registration.referral_registration_page",
                {
                    "form_values": form_values,
                    "error_message": error.args[0],
                    "success_message": False,
                    "created_member": False,
                },
            )
        except Exception:
            request.env.cr.rollback()
            return request.render(
                "referral_registration.referral_registration_page",
                {
                    "form_values": form_values,
                    "error_message": "Registrasi gagal diproses. Pastikan nomor telepon belum pernah terdaftar.",
                    "success_message": False,
                    "created_member": False,
                },
            )

        success_message = "Registrasi berhasil. Akun referral Anda telah dibuat."
        if form_values.get("referral_code"):
            success_message = "Registrasi berhasil dengan referral valid. Akun Anda sudah terhubung dengan referrer."

        return request.render(
            "referral_registration.referral_registration_page",
            {
                "form_values": {},
                "error_message": False,
                "success_message": success_message,
                "created_member": created_member,
            },
        )
