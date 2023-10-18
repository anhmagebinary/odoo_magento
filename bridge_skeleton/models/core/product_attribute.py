# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

from odoo import api, models

class ProductAttribute(models.Model):
    _inherit = 'product.attribute'

    @api.model
    def get_duplicity_avoid_domain(self, vals):
        domain = []
        if vals.get("name"):
            domain += [("name", "=ilike", vals.get('name'))]
        return domain

    @api.model
    def check_duplicity(self, vals):
        domain = self.get_duplicity_avoid_domain(vals)
        return self.search(domain, limit=1) if domain else self.env['product.attribute']

    @api.model
    def create(self, vals):
        ctx = dict(self._context or {})
        ecomm_cannels = dict(self.env['connector.snippet']._get_ecomm_extensions()).keys()
        attribute_obj = False
        if any(key in ctx for key in ecomm_cannels):
            instance_id = ctx.get('instance_id')
            if self.env["connector.instance"].browse(instance_id).avoid_attribute_duplicity:
                attribute_obj = self.check_duplicity(vals)
        return attribute_obj or super(ProductAttribute, self).create(vals)

    def unlink(self):
        mappings = self.env['connector.attribute.mapping'].search([('name', 'in', self.ids)])
        self.env['connector.snippet'].delete_connector_mapping('connector.attribute.mapping', self, 'Attribute', mappings)
        return super(ProductAttribute, self).unlink()

class ProductAttributeValue(models.Model):
    _inherit = 'product.attribute.value'

    @api.model
    def get_duplicity_avoid_domain(self, vals):
        domain = []
        if vals.get("name"):
            domain += [("name", "=ilike", vals.get('name'))]
            domain = ["&"] + domain + [("attribute_id", "=", vals.get("attribute_id", False))]
        return domain

    @api.model
    def check_duplicity(self, vals):
        domain = self.get_duplicity_avoid_domain(vals)
        return self.search(domain, limit=1) if domain else self.env['product.attribute.value']

    @api.model
    def create(self, vals):
        ctx = dict(self._context or {})
        value_obj = False
        ecomm_cannels = dict(self.env['connector.snippet']._get_ecomm_extensions()).keys()
        if any(key in ctx for key in ecomm_cannels):
            instance_id = ctx.get('instance_id')
            if self.env["connector.instance"].browse(instance_id).avoid_attribute_duplicity:
                value_obj = self.check_duplicity(vals)
        return value_obj or super(ProductAttributeValue, self).create(vals)

    def unlink(self):
        mappings = self.env['connector.option.mapping'].search([('name', 'in', self.ids)])
        self.env['connector.snippet'].delete_connector_mapping('connector.option.mapping', self, 'Option', mappings)
        return super(ProductAttributeValue, self).unlink()
