from odoo import http
from odoo.exceptions import ValidationError
from odoo.http import request
import logging; _logger = logging.getLogger(__name__)


class ReferralTransactionSyncController(http.Controller):
    @http.route("/referral/pos/sync", type="json", auth="public", methods=["POST"])
    def sync_pos_transaction(self, **payload):
        try:
            return request.env["referral.transaction"].sudo().sync_pos_transaction(payload)
        except ValidationError as error:
            return {"state": "error", "message": error.args[0]}
        except (ValueError, TypeError) as error:
            return {"state": "error", "message": _("Data tidak valid: %s") % str(error)}
        except Exception as error:
            _logger.exception("Unexpected error in sync_pos_transaction")
            return {"state": "error", "message": _("Terjadi kesalahan internal. Silakan coba lagi.")}
