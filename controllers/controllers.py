# -*- coding: utf-8 -*-
# from odoo import http


# class AymHelpdesk(http.Controller):
#     @http.route('/aym_helpdesk/aym_helpdesk', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/aym_helpdesk/aym_helpdesk/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('aym_helpdesk.listing', {
#             'root': '/aym_helpdesk/aym_helpdesk',
#             'objects': http.request.env['aym_helpdesk.aym_helpdesk'].search([]),
#         })

#     @http.route('/aym_helpdesk/aym_helpdesk/objects/<model("aym_helpdesk.aym_helpdesk"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('aym_helpdesk.object', {
#             'object': obj
#         })
