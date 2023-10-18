# -*- coding: utf-8 -*-
##########################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
##########################################################################

from odoo import api, models


class WkSkeleton(models.TransientModel):
    _inherit = "wk.skeleton"
    _description = " Skeleton for all XML RPC imports in Odoo"

    @api.model
    def get_ecomm_href(self, getcommtype=False):
        href_list = super(WkSkeleton, self).get_ecomm_href(getcommtype)
        href_list = {}
        if getcommtype=='magento2':
            href_list = {
                'user_guide':'https://webkul.com/blog/odoo-bridge-for-magento-v2',
                'rate_review':'https://store.webkul.com/Odoo-Bridge-For-Magento2.html',
                'extension':'https://store.webkul.com/Magento-2/Odoo-ERP.html',
                'name' : 'MAGENTO',
                'short_form' : 'MOB',
                'img_link' : '/odoo_magento_connect/static/src/img/magento-logo.png'
            }
        return href_list
