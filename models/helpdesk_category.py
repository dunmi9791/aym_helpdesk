from odoo import models, fields, api
from dateutil import relativedelta
from datetime import datetime
from datetime import date
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError
from odoo.http import request
import requests
import json


class StockLocation(models.Model):
    _inherit = 'helpdesk.ticket.category'

    form_url = fields.Char(string='Form URL')
    formio_form_id = fields.Char(string="Form.io Form ID")  # New field to store form ID
    name = fields.Char(string='Issue Category', required=True)
    functional_area = fields.Char(string='Functional Area')
    icon = fields.Char(string='Icon', help='FontAwesome icon name (e.g., "ticket", "question", "cog")', default='ticket')
    applicable_fields = fields.Text(string='Applicable Fields',
                                    help='Comma-separated list of applicable fields for this category.')
    recipient_email = fields.Char(string='Recipient Email/Handler')
    dynamic_states = fields.Text(string='Dynamic States', help='Comma-separated list of states for this category.')
    field_ids = fields.One2many('helpdesk.ticket.category.field', 'category_id', string='Custom Fields')


class HelpdeskTicketFormio(models.Model):
    _inherit = 'helpdesk.ticket'

    formio_submission_link = fields.Char(string="Form Submission Link")
    custom_field_ids = fields.One2many('helpdesk.ticket.custom.field', 'ticket_id', string='Custom Fields')
    custom_fields_display = fields.Html('Custom Fields', compute='_compute_custom_fields_display')

    def _compute_custom_fields_display(self):
        for ticket in self:
            content = '<table class="o_list_view table table-sm table-hover"><tbody>'
            for custom_field in ticket.custom_field_ids:
                field_name = custom_field.field_id.name or ''
                field_value = custom_field.value_display or ''
                content += '<tr><td><strong>{}</strong></td><td>{}</td></tr>'.format(
                    field_name,
                    field_value
                )
            content += '</tbody></table>'
            ticket.custom_fields_display = content

    @api.model
    def create_ticket_from_formio(self, form_data):
        # Extract necessary data from form_data
        category_id = form_data.get('category_id')
        description = form_data.get('description')
        name = form_data.get('name')
        form_submission_link = form_data.get('submission_link')

        # Create a new helpdesk ticket with the submitted data
        ticket = self.create({
            'name': name or 'New Helpdesk Ticket',
            'category_id': category_id,
            'description': description,
            'formio_submission_link': form_submission_link,
        })
        return ticket

    category_id = fields.Many2one('helpdesk.ticket.category', string='Issue Category')
    dynamic_data = fields.Text(string='Dynamic Data', help='Stores dynamic fields in JSON format')
    state = fields.Selection([('new', 'New')], string='State', default='new')

    @api.onchange('category_id')
    def _onchange_category_id(self):
        """
        Dynamically updates the form with fields and states based on the selected issue category.
        """
        if self.category_id:
            # Parse the applicable fields from the selected category
            applicable_fields = self.category_id.applicable_fields
            fields_list = applicable_fields.split(',') if applicable_fields else []

            # Store these fields in JSON format in the dynamic_data field
            dynamic_fields_dict = {field_name.strip(): '' for field_name in fields_list}
            self.dynamic_data = json.dumps(dynamic_fields_dict)

            # Parse the dynamic states from the selected category
            dynamic_states = self.category_id.dynamic_states
            states_list = [state.strip().lower().replace(' ', '_') for state in dynamic_states.split(',') if dynamic_states] if dynamic_states else []
            valid_states = [('new', 'New')] + [(state, state.replace('_', ' ').title()) for state in states_list]
            self._fields['state'].selection = valid_states
            self.state = valid_states[0][0]
        else:
            self.dynamic_data = ''
            self.state = 'new'
            self._fields['state'].selection = [('new', 'New')]

    def get_dynamic_fields(self):
        """
        Returns the dynamic fields as a dictionary.
        """
        return json.loads(self.dynamic_data) if self.dynamic_data else {}


class HelpdeskTicketCategoryField(models.Model):
    _name = 'helpdesk.ticket.category.field'
    _description = 'Helpdesk Ticket Category Fields'
    _order = 'sequence, id'

    category_id = fields.Many2one('helpdesk.ticket.category', string='Category', required=True, ondelete='cascade')
    name = fields.Char('Field Name', required=True)
    field_type = fields.Selection([
        ('char', 'Text'),
        ('text', 'Long Text'),
        ('integer', 'Integer'),
        ('float', 'Float'),
        ('selection', 'Selection'),
        ('date', 'Date'),
        ('datetime', 'DateTime'),
        ('boolean', 'Checkbox'),
        ('binary', 'File Upload'),
    ], required=True, default='char')
    selection_options = fields.Char('Selection Options', help='Comma-separated values for selection fields')
    required = fields.Boolean('Required')
    sequence = fields.Integer('Sequence', default=10)
    help_text = fields.Char('Help Text', help='Additional information for the field')
    active = fields.Boolean(string='Active', default=True)


    def toggle_active(self):
        for record in self:
            record.active = not record.active


class HelpdeskTicketCustomField(models.Model):
    _name = 'helpdesk.ticket.custom.field'
    _description = 'Helpdesk Ticket Custom Fields'

    ticket_id = fields.Many2one('helpdesk.ticket', required=True, ondelete='cascade')
    field_id = fields.Many2one('helpdesk.ticket.category.field', required=True)
    value_text = fields.Text('Text Value')
    value_integer = fields.Integer('Integer Value')
    value_float = fields.Float('Float Value')
    value_date = fields.Date('Date Value')
    value_datetime = fields.Datetime('DateTime Value')
    value_boolean = fields.Boolean('Boolean Value')
    value_binary = fields.Binary('File', attachment=True)  # New field for binary data
    filename = fields.Char('Filename')  # Original filename
    mimetype = fields.Char('MIME Type')
    field_type = fields.Selection(related='field_id.field_type', store=True)
    value_display = fields.Char('Value', compute='_compute_value_display', store=False)

    @api.depends('value_text', 'value_integer', 'value_float', 'value_date', 'value_datetime', 'value_boolean')
    def _compute_value_display(self):
        for record in self:
            field_type = record.field_id.field_type
            if field_type in ['char', 'text', 'selection']:
                record.value_display = record.value_text or ''
            elif field_type == 'integer':
                record.value_display = str(record.value_integer) if record.value_integer is not None else ''
            elif field_type == 'float':
                record.value_display = str(record.value_float) if record.value_float is not None else ''
            elif field_type == 'date':
                record.value_display = record.value_date.strftime('%Y-%m-%d') if record.value_date else ''
            elif field_type == 'datetime':
                record.value_display = record.value_datetime.strftime(
                    '%Y-%m-%d %H:%M:%S') if record.value_datetime else ''
            elif field_type == 'boolean':
                record.value_display = 'Yes' if record.value_boolean else 'No'
            elif field_type == 'binary':
                record.value_display = record.filename or 'Uploaded File'
            else:
                record.value_display = ''
