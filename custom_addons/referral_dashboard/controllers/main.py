from odoo import http
from odoo.exceptions import ValidationError
from odoo.http import request


class ReferralTransactionSyncController(http.Controller):
    @http.route("/referral/pos/sync", type="json", auth="user", methods=["POST"])
    def sync_pos_transaction(self, **payload):
        try:
            return request.env["referral.transaction"].sudo().sync_pos_transaction(payload)
        except ValidationError as error:
            return {
                "state": "error",
                "message": error.args[0],
            }
