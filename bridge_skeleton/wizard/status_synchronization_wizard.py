# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

from odoo import fields, models

class SynchronizationWizard(models.TransientModel):
    _name = 'status.synchronization.wizard'
    _description = 'Status Synchronization Wizard'

    def _default_instance_name(self):
        return self.env['connector.instance'].search([], limit=1).id

    instance_id = fields.Many2one('connector.instance', string='Ecommerce Instance', default=lambda self: self._default_instance_name())
    operation = fields.Selection([('invoice','Sync Invoice'),('shipment','Sync Shipment')], string='Operation', default='invoice')

    def start_bulk_status_synchronization(self):
        partial = self.create({})
        ctx = dict(self._context or {})
        return {'name': "Synchronization Bulk Order Status",
                'view_mode': 'form',
                'view_id': False,
                'res_model': 'status.synchronization.wizard',
                'res_id': partial.id,
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'new',
                'context': ctx,
                'domain': '[]',
                }

    def start_status_synchronization(self):
        ctx = dict(self._context or {})
        ctx['instance_id'] = self.instance_id.id
        ctx['ecomm_channel'] = self.instance_id.ecomm_type
        ctx['operation'] = self.operation
        message = self.env['connector.snippet'].with_context(ctx).sync_order_status()
        return message
