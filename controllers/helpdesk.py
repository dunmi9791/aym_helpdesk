from odoo import http
from odoo.http import request, content_disposition
import base64
import logging  # Import the logging module

_logger = logging.getLogger(__name__)

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
            category = request.env['helpdesk.ticket.category'].sudo().browse(category_id)
            if category.exists():
                fields = category.field_ids
                return request.render('aym_helpdesk.portal_create_helpdesk_ticket_form', {
                    'category': category,
                    'fields': fields,
                })
            else:
                return request.render('aym_helpdesk.invalid_category')
        else:
            categories = request.env['helpdesk.ticket.category'].sudo().search([])
            return request.render('aym_helpdesk.portal_select_category', {
                'categories': categories,
            })


    @http.route(['/my/helpdesk/form/submit'], type='http', auth='user', website=True, csrf=False, methods=['POST'])
    def portal_helpdesk_form_submit(self, **post):
        # Define the maximum file size and allowed MIME types
        MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
        ALLOWED_MIME_TYPES = ['image/jpeg', 'image/png', 'application/pdf']
        _logger.info('Starting portal_helpdesk_form_submit with post data: %s', post)

        category_id = int(post.get('category_id'))
        category = request.env['helpdesk.ticket.category'].sudo().browse(category_id)
        if not category.exists():
            return request.render('aym_helpdesk.invalid_category')

        # Initialize the errors list
        errors = []

        # Common ticket values
        vals = {
            'name': post.get('subject') or 'No Subject',
            'description': post.get('description'),
            'category_id': category_id,
            'partner_id': request.env.user.partner_id.id,
        }

        # Prepare custom fields
        custom_fields = []
        for field in category.field_ids:
            field_name = 'field_%s' % field.id
            field_type = field.field_type
            custom_field_vals = {
                'field_id': field.id,
            }

            if field_type == 'binary':
                # Handle file upload
                uploaded_file = request.httprequest.files.get(field_name)
                if uploaded_file:
                    _logger.info('File %s uploaded successfully.', uploaded_file.filename)
                    # Validate file size and type
                    if uploaded_file.content_length > MAX_FILE_SIZE:
                        errors.append(f"The file '{uploaded_file.filename}' exceeds the maximum allowed size of 10 MB.")
                    if uploaded_file.mimetype not in ALLOWED_MIME_TYPES:
                        errors.append(f"The file '{uploaded_file.filename}' has an invalid file type.")

                    # If there are no errors, process the file
                    if not errors:
                        file_content = uploaded_file.read()
                        encoded_content = base64.b64encode(file_content)
                        custom_field_vals['value_binary'] = encoded_content
                        # custom_field_vals['value_binary'] = base64.b64encode(file_content)
                        custom_field_vals['filename'] = uploaded_file.filename
                        custom_field_vals['mimetype'] = uploaded_file.mimetype
                        _logger.info('Encoded content length: %s bytes', len(encoded_content))


                else:
                    if field.required:
                        errors.append(f"The field '{field.name}' is required.")
            else:
                field_value = post.get(field_name)
                if field_type in ['char', 'text', 'selection']:
                    custom_field_vals['value_text'] = field_value
                elif field_type == 'integer':
                    custom_field_vals['value_integer'] = int(field_value) if field_value else 0
                elif field_type == 'float':
                    custom_field_vals['value_float'] = float(field_value) if field_value else 0.0
                elif field_type == 'date':
                    custom_field_vals['value_date'] = field_value
                elif field_type == 'datetime':
                    custom_field_vals['value_datetime'] = field_value
                elif field_type == 'boolean':
                    custom_field_vals['value_boolean'] = True if post.get(field_name) else False

                # Validate required fields (moved outside of 'elif field_type == 'boolean'')
                if field.required and not field_value:
                    errors.append(f"The field '{field.name}' is required.")

            custom_fields.append((0, 0, custom_field_vals))
            _logger.info('Processed field %s of type %s with values: %s', field.name, field_type, custom_field_vals)

        # If there are errors, re-render the form with error messages
        if errors:
            return request.render('aym_helpdesk.portal_create_helpdesk_ticket_form', {
                'category': category,
                'fields': category.field_ids,
                'errors': errors,
                'post': post,
            })

        vals['custom_field_ids'] = custom_fields
        _logger.info('Processed field %s of type %s with values: %s', field.name, field_type, custom_field_vals)

        # Create the ticket
        request.env['helpdesk.ticket'].sudo().create(vals)
        return request.render('aym_helpdesk.ticket_submission_success')

    @http.route(['/my/helpdesk/download/<int:field_id>'], type='http', auth='user', website=True)
    def download_attachment(self, field_id, **kw):
        custom_field = request.env['helpdesk.ticket.custom.field'].sudo().browse(field_id)
        
        # Check if the field exists and belongs to the current user
        if not custom_field.exists() or custom_field.ticket_id.partner_id != request.env.user.partner_id:
            return request.not_found()
            
        if not custom_field.value_binary:
            return request.not_found()
            
        # Get the filename, use a default if not set
        filename = custom_field.filename or 'download'
        
        # Prepare the response with the file
        return request.make_response(
            base64.b64decode(custom_field.value_binary),
            headers=[
                ('Content-Type', custom_field.mimetype or 'application/octet-stream'),
                ('Content-Disposition', content_disposition(filename)),
            ]
        )