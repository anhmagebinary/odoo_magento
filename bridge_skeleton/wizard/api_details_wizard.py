# -*- coding: utf-8 -*-
##########################################################################
#
#    Copyright (c) 2017-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#
##########################################################################

from odoo import fields, models, _

class ApiDetailsWizard(models.TransientModel):
    _name = "api.details.wizard"
    _description = "Api Details Wizard"

    name = fields.Char(
        string='Base URL',
        required=True,
    )
    user = fields.Char(
        string='API User Name',
        required=True)
    update_pwd = fields.Boolean(
        string='Update Password')
    pwd = fields.Char(
        string='API Password')

    def button_set_api_details(self):
        self.ensure_one()
        ctx = dict(self._context or {})
        if self._context.get('active_id'):
            connection_obj = self.env['connector.instance'].browse(self._context['active_id'])
            msg = ""
            name, user, pwd, update_pwd = self.name, self.user, self.pwd, self.update_pwd
            if name != connection_obj.name:
                msg += "<b>Url</b>"
            if user != connection_obj.user:
                msg = msg + "<b>, User</b>" if msg else "<b>User</b>"
            data = {
                'name':name,
                'user':user
            }
            if update_pwd:
                if pwd != connection_obj.pwd:
                    msg = msg + "<b>, Password</b>" if msg else "<b>Password</b>"
                    data['pwd'] = pwd
            connection_obj.write(data)
            if msg:
                msg = "<p class='text-danger'>{0} has been modified of <b>{1}({2})</b> instance.</p>".format(msg, connection_obj.instance_name, connection_obj.ecomm_type)
                connection_obj.message_post(body=_(msg))
        return self.env['message.wizard'].genrated_message('Credentials has been updated successfully', name='Credentails updated successfully')
