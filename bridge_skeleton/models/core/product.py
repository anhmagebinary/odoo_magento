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
import logging
_logger = logging.getLogger(__name__)

class ProductProduct(models.Model):
    _inherit = 'product.product'

    connector_mapping_ids = fields.One2many(
        string='Ecomm Channel Mappings',
        comodel_name='connector.product.mapping',
        inverse_name='name',
        copy=False
    )
    connector_categ_ids = fields.One2many(
        string='Connector Extra Category',
        comodel_name='connector.extra.category',
        inverse_name='product_id',
        copy=False
    )

    @api.model
    def get_duplicity_avoid_domain(self, vals):
        domain = []
        if vals.get("default_code"):
            domain += [("default_code", "=", vals.get('default_code'))]
        if vals.get("barcode"):
            domain = ["|"] + domain + [("barcode", "=", vals.get("barcode"))]
        return domain

    @api.model
    def check_duplicity(self, vals):
        domain = self.get_duplicity_avoid_domain(vals)
        product_obj = False
        if domain:
            product_obj = self.search(domain, limit=1)
        return product_obj

    @api.model
    def create(self, vals):
        ctx = dict(self._context or {})
        instance_id = ctx.get('instance_id')
        ecomm_channels = dict(self.env['connector.snippet']._get_ecomm_extensions()).keys()
        product_obj = False
        new_quantity = False
        if any(key in ctx for key in ecomm_channels):
            ecomm_id = int(vals.pop('ecomm_id', 0))
            new_quantity = int(vals.pop('new_quantity', 0))
            attr_val_ids = vals.get('value_ids', [])
            vals = self.update_vals(vals, instance_id, True)
            if self.env["connector.instance"].browse(instance_id).avoid_product_duplicity:
                product_obj = self.check_duplicity(vals)
        if not product_obj:
            product_obj = super(ProductProduct, self).create(vals)
        if product_obj and new_quantity:
            self.env['connector.snippet'].update_quantity({
                'product_id':product_obj.id, 'new_quantity':new_quantity
            })
        if any(key in ctx for key in ecomm_channels):
            template_obj = product_obj.product_tmpl_id
            template_id = template_obj.id
            channel = "".join(list(set(ctx.keys())&set(ecomm_channels))) or 'Ecommerce' + str(instance_id)
            try:
                if template_id:
                    extra_categ_objs = product_obj.connector_categ_ids.filtered(lambda obj: obj.instance_id.id == instance_id)
                    if extra_categ_objs and not extra_categ_objs.product_tmpl_id:
                        extra_categ_objs.product_tmpl_id = template_id
                    domain = [('product_tmpl_id', '=', template_id)]
                    for attr_val_id in attr_val_ids:
                        attr_val_id = int(attr_val_id)
                        attr_id = self.env['product.attribute.value'].browse(attr_val_id).attribute_id.id
                        search_domain = domain + [('attribute_id', '=', attr_id)]
                        attr_line_objs = self.env['product.template.attribute.line'].search(search_domain)
                        for attr_line_obj in attr_line_objs:
                            attr_line_obj.value_ids = [(4, attr_val_id)]
                    if ecomm_id:
                        mapp_dict = {
                            'instance_id' : instance_id,
                            'created_by' : channel,
                            'ecomm_id' : ecomm_id,
                        }
                        map_temp_objs = template_obj.connector_mapping_ids.filtered(lambda obj: obj.instance_id.id == instance_id)
                        if not map_temp_objs:
                            map_temp_dict = mapp_dict.copy()
                            map_temp_dict.update({
                                'name' : template_id,
                                'odoo_id' : template_id,
                            })
                            self.env['connector.template.mapping'].create(map_temp_dict)
                        else:
                            map_temp_objs.need_sync = False
                        self.env['connector.snippet'].create_odoo_connector_mapping(
                            'connector.product.mapping', ecomm_id, product_obj.id, 
                            instance_id, channel=channel
                        )
            except Exception as e:
                _logger.warning("Product create exception : %r", e)
        return product_obj

    def write(self, vals):
        ctx = dict(self._context or {})
        instance_id = ctx.get('instance_id', False)
        if any(key in ctx for key in dict(self.env['connector.snippet']._get_ecomm_extensions()).keys()):
            vals.pop('ecomm_id', None)
            vals = self.update_vals(vals, instance_id)
        for prod_obj in self:
            for mapped_obj in prod_obj.connector_mapping_ids:
                mapped_obj.need_sync = False if instance_id and mapped_obj.instance_id.id == instance_id else True
            for temp_map_obj in prod_obj.product_tmpl_id.connector_mapping_ids:
                temp_map_obj.need_sync = False if instance_id and temp_map_obj.instance_id.id == instance_id else True
        return super(ProductProduct, self).write(vals)

    def update_vals(self, vals, instance_id, create=False):
        if vals.get('default_code'):
            vals['default_code'] = _unescape(vals['default_code'])
        route = vals.pop('route', False)
        if route:
            vals['route_ids'] = [(6, 0, route)]
        if 'name' in vals:
            vals['name'] = _unescape(vals.get('name', ''))
        if 'description' in vals:
            vals['description'] = _unescape(vals.get('description', ''))
        if 'description_sale' in vals:
            vals['description_sale'] = _unescape(vals.get('description_sale', ''))
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
        attr_val_ids = vals.pop('value_ids', [])
        product_template_attribute_value_ids = []
        product_tmpl_id = vals.get('product_tmpl_id', 0)
        for attr_val_id in attr_val_ids:
            obj = self.env['product.template.attribute.value'].search([('product_tmpl_id', '=', product_tmpl_id), ('product_attribute_value_id', '=', attr_val_id)], limit=1)
            if obj:
                product_template_attribute_value_ids.append(obj.id)
        if product_template_attribute_value_ids:
            vals['product_template_attribute_value_ids'] = [(6, 0, product_template_attribute_value_ids)]
        image_url = vals.pop('image_url', False)
        if image_url:
            vals['image_1920'] = binascii.b2a_base64(requests.get(image_url, verify=False).content)
            # vals['image_variant'] = proImage
        return vals

    def unlink(self):
        mappings = self.env['connector.product.mapping']
        for prod in self:
            mappings += prod.connector_mapping_ids
        self.env['connector.snippet'].delete_connector_mapping('connector.product.mapping', self, 'Product', mappings)
        return super(ProductProduct, self).unlink()
