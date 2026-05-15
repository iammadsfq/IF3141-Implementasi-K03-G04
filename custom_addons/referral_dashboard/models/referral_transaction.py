from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ReferralTransaction(models.Model):
    _name = "referral.transaction"
    _description = "Transaksi Referral"
    _order = "transaction_date desc, id desc"

    order_ref = fields.Char(string="ID Order POS", required=True, copy=False, index=True)
    member_id = fields.Many2one("referral.member", string="Member Pembeli", required=True, ondelete="cascade")
    referrer_id = fields.Many2one(
        "referral.member",
        string="Referrer",
        related="member_id.referred_by_id",
        store=True,
        readonly=True,
    )
    amount = fields.Float(string="Nilai Transaksi", required=True)
    transaction_date = fields.Datetime(string="Tanggal Transaksi", default=fields.Datetime.now, required=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("rewarded", "Reward Diberikan"),
            ("non_referral", "Non Referral"),
            ("already_rewarded", "Referral Sudah Tervalidasi"),
            ("limit_reached", "Limit Bulanan Tercapai"),
            ("cancelled", "Dibatalkan"),
        ],
        default="draft",
        required=True,
        copy=False,
    )
    policy_id = fields.Many2one("referral.policy", string="Kebijakan Digunakan", readonly=True)
    points_awarded = fields.Integer(string="Poin Diberikan", readonly=True)
    reward_log_id = fields.Many2one("referral.reward.log", string="Log Reward", readonly=True, copy=False)
    note = fields.Text(string="Catatan")

    _sql_constraints = [
        ("referral_transaction_order_ref_unique", "unique(order_ref)", "ID order POS harus unik."),
    ]

    @api.constrains("amount")
    def _check_amount(self):
        for transaction in self:
            if transaction.amount < 0:
                raise ValidationError(_("Nilai transaksi tidak boleh negatif."))

    @api.model
    def _format_currency(self, amount):
        return "Rp {:,.0f}".format(amount or 0).replace(",", ".")

    @api.model
    def _get_period_bounds(self, period):
        now = datetime.now()
        period = period or "month"
        if period == "all":
            return False, False
        if period == "week":
            start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=7)
        elif period == "year":
            start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end = start + relativedelta(years=1)
        else:
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end = start + relativedelta(months=1)
        return fields.Datetime.to_string(start), fields.Datetime.to_string(end)

    def _get_monthly_reward_domain(self, referrer, transaction_date):
        month_start = transaction_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_end = month_start + relativedelta(months=1)
        return [
            ("member_id", "=", referrer.id),
            ("reward_date", ">=", fields.Datetime.to_string(month_start)),
            ("reward_date", "<", fields.Datetime.to_string(month_end)),
        ]

    def checkReferralEligibility(self):
        self.ensure_one()
        return bool(self.member_id and self.member_id.referred_by_id and self.state == "draft")

    def action_validate_referral_reward(self):
        reward_log_model = self.env["referral.reward.log"].sudo()
        policy = self.env["referral.policy"].sudo().getActivePolicy()

        for transaction in self:
            if transaction.state != "draft":
                continue

            if not transaction.member_id.referred_by_id:
                transaction.write(
                    {
                        "state": "non_referral",
                        "policy_id": policy.id,
                        "note": _("Transaksi tersimpan tanpa reward karena member tidak memiliki referrer."),
                    }
                )
                continue

            referrer = transaction.member_id.referred_by_id
            processed_transaction = self.search(
                [
                    ("member_id", "=", transaction.member_id.id),
                    ("id", "!=", transaction.id),
                    ("state", "in", ["rewarded", "limit_reached", "already_rewarded"]),
                ],
                limit=1,
            )
            if processed_transaction:
                transaction.write(
                    {
                        "state": "already_rewarded",
                        "policy_id": policy.id,
                        "points_awarded": 0,
                        "note": _("Reward tidak diberikan karena transaksi referral pertama member ini sudah pernah diproses."),
                    }
                )
                continue

            existing_reward = reward_log_model.search(
                [("referred_member_id", "=", transaction.member_id.id)],
                limit=1,
            )
            if existing_reward:
                transaction.write(
                    {
                        "state": "already_rewarded",
                        "policy_id": policy.id,
                        "points_awarded": 0,
                        "note": _("Reward tidak diberikan karena member ini sudah pernah memicu reward referral."),
                    }
                )
                continue

            monthly_domain = transaction._get_monthly_reward_domain(referrer, transaction.transaction_date)
            current_month_points = sum(reward_log_model.search(monthly_domain).mapped("points"))
            available_points = max(policy.max_point_monthly - current_month_points, 0)
            points_to_award = min(policy.point_per_referral, available_points)

            if points_to_award <= 0:
                transaction.write(
                    {
                        "state": "limit_reached",
                        "policy_id": policy.id,
                        "points_awarded": 0,
                        "note": _("Reward tidak diberikan karena limit poin bulanan referrer sudah tercapai."),
                    }
                )
                continue

            reward_log = reward_log_model.createReferralLog(
                {
                    "member_id": referrer.id,
                    "referred_member_id": transaction.member_id.id,
                    "transaction_id": transaction.id,
                    "policy_id": policy.id,
                    "points": points_to_award,
                    "amount": transaction.amount,
                    "reward_date": transaction.transaction_date,
                }
            )
            referrer.sudo().computePoints(points_to_award)
            transaction.write(
                {
                    "state": "rewarded",
                    "policy_id": policy.id,
                    "points_awarded": points_to_award,
                    "reward_log_id": reward_log.id,
                    "note": _("Reward referral berhasil diberikan."),
                }
            )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Validasi selesai"),
                "message": _("Transaksi referral telah diproses."),
                "type": "success",
                "sticky": False,
                "next": {
                    "type": "ir.actions.client",
                    "tag": "reload",
                },
            },
        }

    @api.model
    def sync_pos_transaction(self, values):
        values = values or {}
        order_ref = (values.get("order_ref") or "").strip()
        if not order_ref:
            raise ValidationError(_("ID order POS wajib diisi."))

        member = self.env["referral.member"].sudo().browse()
        if values.get("member_id"):
            member = self.env["referral.member"].sudo().browse(int(values["member_id"])).exists()
        elif values.get("member_phone"):
            member = self.env["referral.member"].sudo().search(
                [("phone_number", "=", str(values["member_phone"]).strip())],
                limit=1,
            )
        elif values.get("member_referral_code"):
            member = self.env["referral.member"].sudo().searchBasedOnReferral(values["member_referral_code"])

        if not member:
            raise ValidationError(_("Member pembeli tidak ditemukan."))
        
        raw_date = values.get("transaction_date")
        if isinstance(raw_date, str):
            transaction_date = fields.Datetime.from_string(raw_date)
        elif isinstance(raw_date, datetime):
            transaction_date = raw_date
        else:
            transaction_date = datetime.now()

        transaction = self.sudo().search([("order_ref", "=", order_ref)], limit=1)
        transaction_values = {
            "order_ref": order_ref,
            "member_id": member.id,
            "amount": float(values.get("amount") or values.get("total_price") or 0),
            "transaction_date": transaction_date,
        }
        if transaction:
            if transaction.state != "draft":
                return {
                    "id": transaction.id,
                    "state": transaction.state,
                    "points_awarded": transaction.points_awarded,
                    "message": _("Transaksi sudah pernah diproses."),
                }
            transaction.write(transaction_values)
        else:
            transaction = self.sudo().create(transaction_values)

        transaction.action_validate_referral_reward()
        return {
            "id": transaction.id,
            "state": transaction.state,
            "points_awarded": transaction.points_awarded,
            "message": transaction.note,
        }

    @api.model
    def getReferralTransactions(self, period="month"):
        start, end = self._get_period_bounds(period)
        domain = [("state", "=", "rewarded")]
        if start:
            domain.append(("transaction_date", ">=", start))
        if end:
            domain.append(("transaction_date", "<", end))
        transactions = self.search(domain)
        return transactions.read(["order_ref", "member_id", "amount",
                                "transaction_date", "points_awarded", "state"])

    @api.model
    def get_dashboard_metrics(self, period="month"):
        start, end = self._get_period_bounds(period)
        log_domain = []
        if start:
            log_domain.append(("reward_date", ">=", start))
        if end:
            log_domain.append(("reward_date", "<", end))

        logs = self.env["referral.reward.log"].sudo().search(log_domain)
        total_revenue = sum(logs.mapped("amount"))
        total_points = sum(logs.mapped("points"))
        ranking = {}

        for log in logs:
            member_id = log.member_id.id
            if member_id not in ranking:
                ranking[member_id] = {
                    "id": member_id,
                    "name": log.member_id.name,
                    "referrals": 0,
                    "points": 0,
                    "revenue": 0,
                }
            ranking[member_id]["referrals"] += 1
            ranking[member_id]["points"] += log.points
            ranking[member_id]["revenue"] += log.amount

        top_referrers = sorted(
            ranking.values(),
            key=lambda item: (item["points"], item["referrals"], item["revenue"]),
            reverse=True,
        )[:10]

        return {
            "period": period or "month",
            "startDate": start or "",
            "endDate": end or "",
            "kpiData": {
                "totalReferrals": len(logs),
                "totalRevenue": self._format_currency(total_revenue),
                "totalPoints": total_points,
            },
            "topReferrers": top_referrers,
        }

    def action_cancel(self):
        for transaction in self:
            if transaction.state == "draft":
                transaction.write({
                    "state": "cancelled",
                    "note": _("Transaksi dibatalkan secara manual.")
                })
        return True


class ReferralRewardLog(models.Model):
    _name = "referral.reward.log"
    _description = "Log Reward Referral"
    _order = "reward_date desc, id desc"

    member_id = fields.Many2one("referral.member", string="Referrer", required=True, ondelete="restrict")
    referred_member_id = fields.Many2one("referral.member", string="Member Referral", required=True, ondelete="restrict")
    transaction_id = fields.Many2one("referral.transaction", string="Transaksi", required=True, ondelete="cascade")
    policy_id = fields.Many2one("referral.policy", string="Kebijakan", required=True, ondelete="restrict")
    points = fields.Integer(string="Poin", required=True)
    amount = fields.Float(string="Nilai Transaksi", required=True)
    reward_date = fields.Datetime(string="Tanggal Reward", default=fields.Datetime.now, required=True)

    _sql_constraints = [
        ("referral_reward_log_transaction_unique", "unique(transaction_id)", "Satu transaksi hanya boleh memiliki satu log reward."),
    ]

    @api.constrains("points")
    def _check_points(self):
        for log in self:
            if log.points < 0:
                raise ValidationError(_("Poin reward tidak boleh negatif."))

    @api.model
    def createReferralLog(self, values):
        return self.create(values)

    @api.model
    def getLogReferral(self, period="month"):
        start, end = self.env["referral.transaction"]._get_period_bounds(period)
        domain = []
        if start:
            domain.append(("reward_date", ">=", start))
        if end:
            domain.append(("reward_date", "<", end))
        return self.search(domain)
