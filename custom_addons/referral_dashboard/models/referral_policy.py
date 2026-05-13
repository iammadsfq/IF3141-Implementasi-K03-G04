from odoo import models, fields

class ReferralPolicy(models.Model):
    _name = 'referral.policy'
    _description = 'Kebijakan Referral'

    name = fields.Char(string='Nama Kebijakan', default='Kebijakan Referral Aktif', required=True)
    
    # Field sesuai dengan sequence diagram
    max_point_monthly = fields.Integer(
        string='Maksimal Poin per Bulan', 
        help='Batas maksimal poin yang bisa didapat member dalam 1 periode bulan berjalan'
    )
    point_per_referral = fields.Integer(
        string='Poin per Referral', 
        help='Jumlah poin yang didapat setiap kali referral sukses'
    )