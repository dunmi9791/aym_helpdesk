from odoo import http
from odoo.http import request
import json

class HelpdeskPortal(http.Controller):

    @http.route(['/my/helpdesk', '/my/helpdesk/page/<int:page>'], type='http', auth='user', website=True)
    def portal_my_helpdesk(self, page=1, **kw):
        # Fetch tickets associated with the logged-in user
        tickets = request.env['helpdesk.ticket'].search([
            ('partner_id', '=', request.env.user.partner_id.id)
        ])
        values = {
            'tickets': tickets,
        }
        return request.render('aym_helpdesk.portal_my_helpdesk', values)

    @http.route(['/my/helpdesk/ticket/create'], type='http', auth='user', website=True, csrf=False)
    def portal_create_helpdesk_ticket(self, **post):
        if request.httprequest.method == 'POST':
            vals = {
                'name': post.get('name'),
                'description': post.get('description'),
                'partner_id': request.env.user.partner_id.id,
                'priority': post.get('priority', '0'),
                'category_id': int(post.get('category_id')),
            }
            request.env['helpdesk.ticket'].create(vals)
            return request.redirect('/my/helpdesk')

        categories = request.env['helpdesk.ticket.category'].search([])  # Fetch available categories
        return request.render('aym_helpdesk.portal_create_helpdesk_ticket', {
            'categories': categories,
        })

    @http.route(['/my/helpdesk/category_form_url'], type='json', auth='user')
    def get_category_form_url(self, category_id):
        """Returns the form URL for the given category."""
        category = request.env['helpdesk.ticket.category'].browse(category_id)
        return json.dumps({'form_url': category.form_url if category.form_url else ''})
