# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

from odoo import fields, models


class ConnectorOptionMapping(models.Model):
    _name = "connector.option.mapping"
    _inherit = ['connector.common.mapping']
    _order = 'id desc'
    _description = "Ecomm Product Attribute Value"

    name = fields.Many2one(
        'product.attribute.value',
        string='Attribute Value',
        ondelete='cascade')
    odoo_attribute_id = fields.Integer('Odoo Attribute Id')
    ecomm_attribute_id = fields.Integer('Ecomm Attribute Id')
