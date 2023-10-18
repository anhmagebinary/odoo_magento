# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

from odoo import fields, models

class AccountMove(models.Model):
    _inherit = "account.move"

    ecomm_invoice = fields.Char(
        string='Ecomm Invoice',
        help="Contains Ecomm Order Invoice Number (eg. 300000008)")


    def _invoice_paid_hook(self):
        self.skeleton_pre_payment_post()
        res = super()._invoice_paid_hook()
        self.skeleton_after_payment_post(res)
        return res

    def skeleton_pre_payment_post(self):
        return True

    def get_ecomm_orders(self, invoice_objs):
        origins = invoice_objs.mapped('invoice_origin')
        sales_order = self.env['sale.order'].search[('name', 'in', origins)]
        return sales_order

    def skeleton_after_payment_post(self, result):
        ctx = dict(self._context or {})
        snippet_obj = self.env['connector.snippet']
        ecomm_cannels = dict(snippet_obj._get_ecomm_extensions()).keys()
        if any(key in ctx for key in ecomm_cannels):
            return True
        for move in self:
            for sales_order in move.invoice_line_ids.mapped('sale_line_ids').mapped('order_id'):
                snippet_obj.manual_connector_order_operation('invoice', sales_order.ecommerce_channel, sales_order, move)
        return True
