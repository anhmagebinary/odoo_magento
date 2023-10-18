# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

from odoo import api, fields, models


class ConnectorCommonMapping(models.AbstractModel):
    _name = "connector.common.mapping"
    _description = "Common Mapping"

    odoo_id = fields.Integer(string='Odoo Id')
    ecomm_id = fields.Integer(string='Ecomm Id')
    need_sync = fields.Boolean(string='Update Required', default=False)
    instance_id = fields.Many2one(
        'connector.instance', string='Connector Instance')
    ecommerce_channel = fields.Selection(
        related="instance_id.ecomm_type", 
        string="eCommerce Channel", store=True)
    create_date = fields.Datetime(string='Created Date')
    write_date = fields.Datetime(string='Updated Date')
    created_by = fields.Char(string='Created By', default='odoo')

    @api.model
    def create(self, vals):
        vals = self.update_vals(vals)
        resp = self.check_mapping(vals)
        if resp:
            return resp
        else:
            return super(ConnectorCommonMapping, self).create(vals)

    def write(self, vals):
        vals = self.update_vals(vals)
        return super(ConnectorCommonMapping, self).write(vals)

    def update_vals(self, vals):
        ctx = dict(self._context or {})
        if ctx.get('instance_id'):
            vals['instance_id'] = ctx.get('instance_id')
        return vals

    def check_mapping(self, vals):
        obj = False
        if 'ecomm_id' in vals and 'odoo_id' in vals and 'instance_id' in vals:
            obj = self.search([('odoo_id', '=', vals.get('odoo_id')), ('ecomm_id', '=', vals.get('ecomm_id')), ('instance_id', '=', vals.get('instance_id'))], limit=1)
        return obj
