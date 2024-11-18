odoo.define('aym_helpdesk.helpdesk_form_url', function (require) {
    'use strict';

    var ajax = require('web.ajax');  // Make sure you use Odoo's ajax module

    $(document).ready(function () {
        $('#category_id').change(function () {
            var categoryId = $(this).val();
            if (categoryId) {
                ajax.jsonRpc('/my/helpdesk/category_form_url', 'call', {
                    'category_id': categoryId
                }).then(function (response) {
                    console.log("Response from backend:", response); // Log the response
                    var formUrl = response.form_url;
                    if (formUrl) {
                        $('#form-url-container').show();
                        $('#form-url').attr('href', formUrl);
                    } else {
                        $('#form-url-container').hide();
                    }
                }).catch(function () {
                    $('#form-url-container').hide();
                });
            } else {
                $('#form-url-container').hide();
            }
        });
    });
});

