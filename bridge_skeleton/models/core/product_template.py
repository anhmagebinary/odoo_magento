# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

import binascii
import requests
from odoo import fields, api, models
from ..core.res_partner import _unescape


class ProductTemplate(models.Model):
    _inherit = "product.template"

    config_sku = fields.Char(string='SKU')
    connector_mapping_ids = fields.One2many(
        string='Ecomm Channel Mappings',
        comodel_name='connector.template.mapping',
        inverse_name='name',
        copy=False
    )
    connector_categ_ids = fields.One2many(
        string='Connector Extra Category',
        comodel_name='connector.extra.category',
        inverse_name='product_tmpl_id',
        copy=False
    )

    @api.model
    def get_duplicity_avoid_domain(self, vals):
        domain = []
        if vals.get("config_sku"):
            domain += [("config_sku", "=", vals.get('config_sku'))]
        if vals.get("barcode"):
            domain = ["|"] + domain + [("barcode", "=", vals.get("barcode"))]
        return domain

    @api.model
    def check_duplicity(self, vals):
        domain = self.get_duplicity_avoid_domain(vals)
        template_obj = False
        if domain:
            template_obj = self.search(domain, limit=1)
        return template_obj

    @api.model
    def create(self, vals):
        ctx = dict(self._context or {})
        ecomm_cannels = dict(self.env['connector.snippet']._get_ecomm_extensions()).keys()
        instance_id = ctx.get('instance_id')
        response = False
        if any(key in ctx for key in ecomm_cannels):
            ecomm_id = vals.pop('ecomm_id', 0)
            vals.pop('new_quantity', 0)
            vals = self.update_vals(vals, instance_id, True)
            if self.env["connector.instance"].browse(instance_id).avoid_product_duplicity:
                response = self.check_duplicity(vals)
        if not response:
            response = super(ProductTemplate, self).create(vals)
        if any(key in ctx for key in ecomm_cannels) and 'configurable' in ctx:
            channel = "".join(list(set(ctx.keys())&set(ecomm_cannels))) or 'Ecommerce' + str(instance_id)
            self.env['connector.snippet'].create_odoo_connector_mapping('connector.template.mapping', ecomm_id, response.id, instance_id, is_variants=True, created_by=channel)
        return response

    def write(self, vals):
        ctx = dict(self._context or {})
        instance_id = ctx.get('instance_id')
        ecomm_cannels = dict(self.env['connector.snippet']._get_ecomm_extensions()).keys()
        if any(key in ctx for key in ecomm_cannels):
            vals.pop('ecomm_id', 0)
            vals = self.update_vals(vals, instance_id)
        for tempObj in self:
            for tempMapObj in tempObj.connector_mapping_ids:
                tempMapObj.need_sync = False if instance_id and tempMapObj.instance_id.id == instance_id else True
        return super(ProductTemplate, self).write(vals)

    def unlink(self):
        mappings = self.env['connector.template.mapping']
        variants = self.env['product.product']
        for template in self:
            variants += template.product_variant_ids
            mappings += template.connector_mapping_ids.filtered(lambda obj: obj.is_variants == True)
        vrntMappings = self.env['connector.product.mapping']
        for vrnt in variants:
            vrntMappings += vrnt.connector_mapping_ids
        self.env['connector.snippet'].delete_connector_mapping('connector.template.mapping', self, 'Template', mappings)
        self.env['connector.snippet'].delete_connector_mapping('connector.product.mapping', variants, 'Product', vrntMappings)
        return super(ProductTemplate, self).unlink()

    def _create_variant_ids(self):
        ctx = dict(self._context or {})
        ecomm_cannels = dict(self.env['connector.snippet']._get_ecomm_extensions()).keys()
        if any(key in ctx for key in ecomm_cannels):
            return True
        else:
            return super(ProductTemplate, self)._create_variant_ids()

    def update_vals(self, vals, instance_id, create=False):
        if vals.get('default_code'):
            vals['config_sku'] = _unescape(vals.pop('default_code', ''))
        route = vals.pop('route', False)
        if route:
            vals['route_ids'] = [(6, 0, route)]
        if 'name' in vals:
            vals['name'] = _unescape(vals['name'])
        if 'description' in vals:
            vals['description'] = _unescape(vals['description'])
        if 'description_sale' in vals:
            vals['description_sale'] = _unescape(vals['description_sale'])
        category_ids = vals.pop('category_ids', None)
        if category_ids:
            categ_ids = list(set(category_ids))
            default_categ_obj = self.env["connector.instance"].browse(instance_id).category
            if default_categ_obj and create:
                vals['categ_id'] = default_categ_obj.id
            if create:
                extra_categ_objs = self.env['connector.extra.category'].create({
                    'instance_id':instance_id, 'categ_ids': [(6, 0, categ_ids)]
                })
                vals['connector_categ_ids'] = [(6, 0, [extra_categ_objs.id])]
            else:
                extra_categ_objs = self.connector_categ_ids.filtered(lambda obj: obj.instance_id.id == instance_id)
                if extra_categ_objs:
                    extra_categ_objs.write({'categ_ids': [(6, 0, categ_ids)]})
                else:
                    extra_categ_objs = self.env['connector.extra.category'].create({
                        'instance_id':instance_id, 'categ_ids': [(6, 0, categ_ids)]
                    })
                    vals['connector_categ_ids'] = [(6, 0, [extra_categ_objs.id])]
        image_url = vals.pop('image_url', False)
        if image_url:
            vals['image_1920'] = binascii.b2a_base64(requests.get(image_url, verify=False).content)
        vals.pop('attribute_list', None)
        return vals
