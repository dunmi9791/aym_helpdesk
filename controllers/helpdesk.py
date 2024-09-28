# from odoo import http
# from odoo.http import request
# import json
#
# class HelpdeskPortal(http.Controller):
#
#     @http.route(['/my/helpdesk', '/my/helpdesk/page/<int:page>'], type='http', auth='user', website=True)
#     def portal_my_helpdesk(self, page=1, **kw):
#         # Fetch tickets associated with the logged-in user
#         tickets = request.env['helpdesk.ticket'].search([
#             ('partner_id', '=', request.env.user.partner_id.id)
#         ])
#         values = {
#             'tickets': tickets,
#         }
#         return request.render('aym_helpdesk.portal_my_helpdesk', values)
#
#     @http.route(['/my/helpdesk/ticket/create'], type='http', auth='user', website=True, csrf=False)
#     def portal_create_helpdesk_ticket(self, **post):
#         if request.httprequest.method == 'POST':
#             vals = {
#                 'name': post.get('name'),
#                 'description': post.get('description'),
#                 'partner_id': request.env.user.partner_id.id,
#                 'partner_name': request.env.user.partner_id.name,
#                 'partner_email': request.env.user.partner_id.email,
#                 'priority': post.get('priority', '0'),
#                 'category_id': int(post.get('category_id')),
#             }
#             request.env['helpdesk.ticket'].create(vals)
#             return request.redirect('/my/helpdesk')
#
#         categories = request.env['helpdesk.ticket.category'].search([])  # Fetch available categories
#         return request.render('aym_helpdesk.portal_create_helpdesk_ticket', {
#             'categories': categories,
#         })
#
#     @http.route(['/my/helpdesk/category_form_url'], type='json', auth='user')
#     def get_category_form_url(self, category_id):
#         """Returns the form URL for the given category."""
#         category = request.env['helpdesk.ticket.category'].browse(category_id)
#         return json.dumps({'form_url': category.form_url if category.form_url else ''})

from odoo import http
from odoo.http import request

class HelpdeskPortal(http.Controller):

    @http.route(['/my/helpdesk', '/my/helpdesk/page/<int:page>'], type='http', auth='user', website=True)
    def portal_my_helpdesk(self, page=1, **kw):
        tickets = request.env['helpdesk.ticket'].search([
            ('partner_id', '=', request.env.user.partner_id.id)
        ])
        values = {
            'tickets': tickets,
        }
        return request.render('aym_helpdesk.portal_my_helpdesk', values)

    @http.route(['/my/helpdesk/ticket/create'], type='http', auth='user', website=True, csrf=False)
    def portal_create_helpdesk_ticket(self, **post):
        if 'category_id' in post:
            category_id = int(post.get('category_id'))
            category = request.env['helpdesk.ticket.category'].browse(category_id)
            if category.form_url:
                return request.redirect(category.form_url)
            else:
                return request.render('your_module.no_form_available', {'category': category})
        else:
            categories = request.env['helpdesk.ticket.category'].search([])
            return request.render('aym_helpdesk.portal_select_category', {
                'categories': categories,
            })

    @http.route(['/my/helpdesk/form/submit'], type='http', auth='public', website=True, csrf=False)
    def portal_helpdesk_form_submit(self, **post):
        # Extract form data and create a helpdesk ticket
        vals = {
            'name': post.get('subject') or 'No Subject',
            'description': post.get('description'),
            'partner_name': post.get('name') or 'Anonymous',
            'partner_email': post.get('email'),
            'category_id': int(post.get('category_id')) if post.get('category_id') else None,
        }
        # Find or create the partner
        partner = request.env['res.partner'].sudo().search([('email', '=', vals['partner_email'])], limit=1)
        if not partner:
            partner = request.env['res.partner'].sudo().create({
                'name': vals['partner_name'],
                'email': vals['partner_email'],
            })
        vals['partner_id'] = partner.id
        request.env['helpdesk.ticket'].sudo().create(vals)
        return request.render('aym_helpdesk.ticket_submission_success')
