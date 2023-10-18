# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################
import logging
import base64
import csv
import io
import json
import operator
import zipfile
from datetime import date

from odoo import api, fields, models
from odoo.addons.web.controllers.main import GroupsTreeNode
from odoo.tools import pycompat
_logger = logging.getLogger(__name__)

class SynchronizationWizard(models.TransientModel):
    _name = 'synchronization.wizard'
    _description = "Synchronization Wizard"

    def _default_instance_name(self):
        return self.env['connector.instance'].search([], limit=1).id

    action = fields.Selection([('export', 'Export'), ('update', 'Update')], string='Action', default="export", required=True,
                              help="""Export: Export all Odoo Category/Products at other E-commerce. Update: Update all synced products/categories at other E-commerce, which requires to be update at other E-commerce""")
    instance_id = fields.Many2one('connector.instance', string='Ecommerce Instance', default=lambda self: self._default_instance_name())

    def start_attribute_synchronization(self):
        ctx = dict(self._context or {})
        ctx['instance_id'] = self.instance_id.id
        ctx['ecomm_channel'] = self.instance_id.ecomm_type
        message = self.env['connector.snippet'].with_context(
            ctx).export_attributes_and_their_values()
        return message

    def start_category_synchronization(self):
        ctx = dict(self._context or {})
        ctx['sync_opr'] = self.action
        ctx['instance_id'] = self.instance_id.id
        ctx['ecomm_channel'] = self.instance_id.ecomm_type
        message = self.env['connector.snippet'].with_context(
            ctx).sync_operations('product.category', 'connector.category.mapping', [], 'category')
        return message

    def start_category_synchronization_mapping(self):
        ctx = dict(self._context or {})
        mapped_ids = ctx.get('active_ids')
        map_objs = self.env['connector.category.mapping'].browse(mapped_ids)
        map_categ_ids = map_objs.mapped('name').ids
        ctx.update(
            sync_opr=self.action,
            instance_id=self.instance_id.id,
            ecomm_channel=self.instance_id.ecomm_type,
            active_model='product.category',
            active_ids=map_categ_ids,
        )
        message = self.env['connector.snippet'].with_context(
            ctx).sync_operations('product.category', 'connector.category.mapping', [], 'category')
        return message

    def start_bulk_category_synchronization_mapping(self):
        partial = self.create({'action': 'update'})
        ctx = dict(self._context or {})
        ctx['mapping_categ'] = False
        return {'name': "Synchronization Bulk Category",
                'view_mode': 'form',
                'view_id': False,
                'res_model': 'synchronization.wizard',
                'res_id': partial.id,
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'new',
                'context': ctx,
                'domain': '[]',
                }

    def start_product_synchronization(self):
        ctx = dict(self._context or {})
        ctx['sync_opr'] = self.action
        ctx['instance_id'] = self.instance_id.id
        ctx['ecomm_channel'] = self.instance_id.ecomm_type
        message = self.env['connector.snippet'].with_context(
            ctx).sync_operations('product.template', 'connector.template.mapping', [('type', '!=', 'service')], 'product')
        return message

    def start_product_synchronization_mapping(self):
        ctx = dict(self._context or {})
        mapped_ids = ctx.get('active_ids')
        map_objs = self.env['connector.template.mapping'].browse(mapped_ids)
        map_product_ids = map_objs.mapped('name').ids
        ctx.update(
            sync_opr=self.action,
            instance_id=self.instance_id.id,
            ecomm_channel=self.instance_id.ecomm_type,
            active_model='product.template',
            active_ids=map_product_ids,
        )
        message = self.env['connector.snippet'].with_context(
            ctx).sync_operations('product.template', 'connector.template.mapping', [('type', '!=', 'service')], 'product')
        return message

    def start_bulk_product_synchronization_mapping(self):
        partial = self.create({'action': 'update'})
        ctx = dict(self._context or {})
        ctx['mapping'] = False
        return {'name': "Synchronization Bulk Product",
                'view_mode': 'form',
                'view_id': False,
                'res_model': 'synchronization.wizard',
                'res_id': partial.id,
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'new',
                'context': ctx,
                'domain': '[]',
                }

    @api.model
    def start_bulk_product_synchronization(self):
        partial = self.create({})
        ctx = dict(self._context or {})
        ctx['check'] = False
        return {'name': "Synchronization Bulk Product",
                'view_mode': 'form',
                'view_id': False,
                'res_model': 'synchronization.wizard',
                'res_id': partial.id,
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'new',
                'context': ctx,
                'domain': '[]',
                }

    @api.model
    def start_bulk_category_synchronization(self):
        partial = self.create({})
        ctx = dict(self._context or {})
        ctx['All'] = True
        return {'name': "Synchronization Bulk Category",
                'view_mode': 'form',
                'view_id': False,
                'res_model': 'synchronization.wizard',
                'res_id': partial.id,
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'new',
                'context': ctx,
                'domain': '[]',
                }

    def reset_mapping(self):
        domain = [('instance_id', '=', self.instance_id.id)]
        channel = self.instance_id.ecomm_type
        models = ['connector.attribute.mapping', 'connector.category.mapping', 'connector.option.mapping','connector.order.mapping',
            'connector.partner.mapping', 'connector.product.mapping', 'connector.template.mapping', 'connector.sync.history']
        if hasattr(self, 'reset_%s_mapping' % channel):
            response = getattr(self, 'reset_%s_mapping' % channel)(domain)
            if response:
                models.extend(response or [])
        for model in models:
            self.unlink_tables(model, domain)
        return self.env['message.wizard'].genrated_message("<h4 class='text-success'><i class='fa fa-smile-o'></i> Mappings has been deleted successfully</h4>")

    def unlink_tables(self, model, domain=[]):
        record_objs = self.env[model].search(domain)
        if record_objs:
            record_objs.unlink()

    def from_data(self, fields, rows):
        fp = io.BytesIO()
        writer = pycompat.csv_writer(fp, quoting=1)

        writer.writerow(fields)

        for data in rows:
            row = []
            for d in data:
                # Spreadsheet apps tend to detect formulas on leading =, + and -
                if isinstance(d, str) and d.startswith(('=', '-', '+')):
                    d = "'" + d

                row.append(pycompat.to_text(d))
            writer.writerow(row)

        return fp.getvalue()

    def base(self, data):
        params = json.loads(data)
        model, fields, ids, domain, import_compat = \
            operator.itemgetter('model', 'fields', 'ids', 'domain', 'import_compat')(params)

        field_names = [f['name'] for f in fields]
        if import_compat:
            columns_headers = field_names
        else:
            columns_headers = [val['label'].strip() for val in fields]

        Model = self.env[model].with_context(**params.get('context', {}))
        groupby = params.get('groupby')
        if not import_compat and groupby:
            groupby_type = [Model._fields[x.split(':')[0]].type for x in groupby]
            domain = [('id', 'in', ids)] if ids else domain
            groups_data = Model.read_group(domain, field_names, groupby, lazy=False)

            # read_group(lazy=False) returns a dict only for final groups (with actual data),
            # not for intermediary groups. The full group tree must be re-constructed.
            tree = GroupsTreeNode(Model, field_names, groupby, groupby_type)
            for leaf in groups_data:
                tree.insert_leaf(leaf)

            response_data = self.from_group_data(fields, tree)
        else:
            Model = Model.with_context(import_compat=import_compat)
            records = Model.browse(ids) if ids else Model.search(domain, offset=0, limit=False, order=False)

            if not Model._is_an_ordinary_table():
                fields = [field for field in fields if field['name'] != 'id']

            export_data = records.export_data(field_names).get('datas',[])
            response_data = self.from_data(columns_headers, export_data)
            return response_data

    @api.model
    def get_export_mapping_models_list(self):
        return [
            'connector.attribute.mapping', 'connector.option.mapping',
            'connector.order.mapping', 'connector.partner.mapping', 
            'connector.category.mapping', 'connector.product.mapping', 'connector.template.mapping'
        ]

    def export_mapping(self):
        domain = [('instance_id', '=', self.instance_id.id)]
        models = self.get_export_mapping_models_list()
        csv_files = []
        csv_file_names = []
        for i in models:
            # data = self.env[i].search(domain)
            fields = self.env[i].fields_get_keys()
            field_list = []
            for field in fields:
                field_list.append({ "label":str(field.replace('_', ' ').capitalize()), "name":str(field)})
            data = {"model":i, "fields":field_list, "ids":False, "domain":[], "import_compat":True}
            result = self.base(json.dumps(data))
            csv_files.append(result)
            csv_file_names.append(i.replace('.', ' ').capitalize()+ '.csv')
        
        zipped_file = io.BytesIO()
        zip_name = "connector-mappings-"+ str(date.today()) 
        try:
            with zipfile.ZipFile(zipped_file,'w') as f:
                for file_name,file in zip(csv_file_names, csv_files):
                    f.writestr(file_name, file)
            binary_data = base64.b64encode(zipped_file.getvalue())
            attachment_id = self.env['ir.attachment'].create({'name': zip_name, 'datas': binary_data, 'type': 'binary'}).id
        except Exception as e:
            return self.env['message.wizard'].genrated_message("<h4 class='text-danger'>Failed to generate the zip due to </h4>" + str(e))
        return {
             'type' : 'ir.actions.act_url',
             'url': "/web/content/"+str(attachment_id)+"/"+zip_name+".zip",
             'target': 'new',
             'tag': 'reload'
            }
