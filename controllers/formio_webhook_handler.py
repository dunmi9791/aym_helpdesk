from odoo import models, fields, api, http
from odoo.http import request
import requests

class FormioWebhookHandler(models.AbstractModel):
    _name = 'formio.webhook.handler'

    @api.model
    def handle_webhook(self, form_id, submission_data):
        # Validate the form ID to ensure it's relevant for the helpdesk
        form_category = request.env['helpdesk.ticket.category'].sudo().search([('formio_form_id', '=', form_id)], limit=1)
        if form_category:
            submission_data['category_id'] = form_category.id
            self.env['formio.integration.controller'].handle_form_submission(submission_data)



class FormioSubmissionHandler(models.AbstractModel):
    _name = 'formio.submission.handler'

    @api.model
    def handle_form_submission(self, submission_data):
        # Create a helpdesk ticket based on the submission data
        request.env['helpdesk.ticket'].sudo().create_ticket_from_formio(submission_data)