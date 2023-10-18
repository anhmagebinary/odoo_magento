# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

from odoo import api, fields, models
from ..core.res_partner import _unescape

class ProductCategory(models.Model):
    _inherit = "product.category"

    connector_mapping_ids = fields.One2many(
        string='Ecomm Channel Mappings',
        comodel_name='connector.category.mapping',
        inverse_name='name',
        copy=False
    )

    @api.model
    def get_duplicity_avoid_domain(self, vals):
        domain = []
        if vals.get("name"):
            domain += [("name", "=", vals.get('name'))]
            domain = ["&"] + domain + [("parent_id", "=", vals.get("parent_id", False))]
        return domain

    @api.model
    def check_duplicity(self, vals):
        domain = self.get_duplicity_avoid_domain(vals)
        return self.search(domain, limit=1) if domain else self.env['product.category']

    @api.model
    def create(self, vals):
        ctx = dict(self._context or {})
        category_obj = False
        ecomm_channels = dict(self.env['connector.snippet']._get_ecomm_extensions()).keys()
        if any(key in ctx for key in ecomm_channels):
            instance_id = ctx.get('instance_id')
            if vals.get('name'):
                vals['name'] = _unescape(vals['name'])
            if self.env["connector.instance"].browse(instance_id).avoid_category_duplicity:
                category_obj = self.check_duplicity(vals)
        return category_obj or super(ProductCategory, self).create(vals)

    def write(self, vals):
        ecomm_cannels = dict(self.env['connector.snippet']._get_ecomm_extensions()).keys()
        if any(key in dict(self._context or {}) for key in ecomm_cannels):
            if vals.get('name'):
                vals['name'] = _unescape(vals['name'])
        else:
            for cat_obj in self:
                cat_obj.connector_mapping_ids.need_sync = True
        return super(ProductCategory, self).write(vals)

    def unlink(self):
        mappings = self.env['connector.category.mapping']
        for categ in self:
            mappings += categ.connector_mapping_ids
        self.env['connector.snippet'].delete_connector_mapping('connector.category.mapping', self, 'Category', mappings)
        return super(ProductCategory, self).unlink()
