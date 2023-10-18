# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

# Order Status Sync Operation

from odoo import models

class ConnectorSnippet(models.TransientModel):
    _inherit = "connector.snippet"

    def sync_order_status(self):
        success,failure, notinvoiceorship, alreadysynced, message = [],[],[],[],''
        ctx = dict(self._context or {})
        instance_id, channel, operation = ctx.get('instance_id', False), ctx.get('ecomm_channel',''), ctx.get('operation','')
        map_objs = self.env[ctx.get('active_model')].browse(ctx.get('active_ids',[]))
        if instance_id:
            connection = self.env['connector.instance'].with_context(ctx)._create_connection()
            if operation=='invoice':
                for map_obj in map_objs:
                    order_obj = map_obj.odoo_order_id
                    increment_id, invoice_objs = map_obj.name, order_obj.invoice_ids.filtered(lambda x: x.move_type=='out_invoice')
                    for obj in invoice_objs:
                        if obj.payment_state=='paid':
                            ecomm_invoice = obj.ecomm_invoice
                            if not ecomm_invoice:
                                success, failure = self.response_of_sync_order_station(channel, connection, 'invoice', 'OrderInvoice', increment_id, obj, order_obj, success, failure, instance_id)
                            else:
                                if order_obj.name not in alreadysynced:
                                    alreadysynced.append(order_obj.name)
                        else:
                            if order_obj.name not in notinvoiceorship:
                                notinvoiceorship.append(order_obj.name)
            else:
                for map_obj in map_objs:
                    order_obj = map_obj.odoo_order_id
                    increment_id, ship_objs = map_obj.name, order_obj.picking_ids.filtered(lambda x:x.picking_type_code=='outgoing')
                    for obj in ship_objs:
                        if obj.state=='done':
                            ecomm_shipment = obj.ecomm_shipment
                            if not ecomm_shipment:
                                itemData = {line.product_id.default_code:line.qty_done for line in obj.move_line_ids if line.product_id.default_code}
                                if itemData:
                                    itemData['send_email'] = map_obj.instance_id.notify
                                    ctx['itemData'] = itemData
                                tracking_data = obj.get_tracking_data()
                                if tracking_data:
                                    ctx['tracking_data'] = tracking_data
                                success, failure = self.response_of_sync_order_station(channel, connection, 'shipment', 'OrderShipment', increment_id, obj, order_obj, success, failure, instance_id)
                            else:
                                if order_obj.name not in alreadysynced:
                                    alreadysynced.append(order_obj.name)
                        else:
                            if order_obj.name not in notinvoiceorship:
                                notinvoiceorship.append(order_obj.name)
            channel2 = channel.capitalize()
            opr2 = operation.capitalize()
            if success:
                message+='{} for Odoo Order(s) {} has been created at {}\n'.format(opr2,success,channel2)
            if failure:
                message+='{} for odoo order(s) {} has not created at {}\n'.format(opr2,failure,channel2)
            if alreadysynced:
                message+='{} for odoo order(s) {} already synced at {}\n'.format(opr2,alreadysynced,channel2)
            if notinvoiceorship:
                message+='{} for odoo order(s) {} not created at odoo yet\n'.format(opr2,notinvoiceorship)
        return self.env['message.wizard'].genrated_message(message)

    def response_of_sync_order_station(self, channel, connection, odooopr, apiopr, increment_id, obj, order_obj, success, failure, instance_id):
        ctx = dict(self._context or {})
        if hasattr(self, '%s_order_status_sync_operation' % channel):
            resp = getattr(self.with_context(ctx), '%s_order_status_sync_operation' % channel)(
                        connection, odooopr, apiopr, increment_id)
            if resp.get('status')=='yes':
                obj.write({f'ecomm_{odooopr}':resp.get('ecomm_order_status_response','')})
                if order_obj.name not in success:
                    success.append(order_obj.name)
                self.create_history('yes', instance_id, resp)
            else:
                if order_obj.name not in failure:
                    failure.append(order_obj.name)
                self.create_history('no', instance_id, resp)
        return success, failure

    def create_history(self, status, instance_id, resp):
        self.env['connector.sync.history'].create({
            'status': status, 'instance_id': instance_id,
            'action_on': 'order', 'action': 'b', 'error_message': resp.get('text')
        })
        return True
