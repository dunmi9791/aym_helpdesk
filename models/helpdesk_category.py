from odoo import models, fields, api
from dateutil import relativedelta
from datetime import datetime
from datetime import date
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError


class StockLocation(models.Model):
    _inherit = 'helpdesk.ticket.category'


    form_url = fields.Char(string='Form URL')

