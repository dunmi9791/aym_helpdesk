document.addEventListener("DOMContentLoaded", function() {
    const categoryField = document.querySelector("#category");
    const dynamicFieldsContainer = document.querySelector("#dynamic-fields-container");

    categoryField.addEventListener("change", function() {
        const categoryId = categoryField.value;
        if (categoryId) {
            fetch('/helpdesk/create_ticket/fields', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ category_id: categoryId }),
            })
            .then(response => response.json())
            .then(data => {
                if (data.fields) {
                    dynamicFieldsContainer.innerHTML = '';
                    data.fields.forEach(fieldName => {
                        let inputField = document.createElement('input');
                        inputField.setAttribute('type', 'text');
                        inputField.setAttribute('name', fieldName);
                        inputField.setAttribute('placeholder', fieldName);
                        inputField.required = true;  // Mark dynamic fields as required
                        dynamicFieldsContainer.appendChild(inputField);
                    });
                }
            })
            .catch(error => {
                console.error('Error fetching dynamic fields:', error);
                dynamicFieldsContainer.innerHTML = '<p style="color: red;">Failed to load fields. Please try again.</p>';
            });
        } else {
            dynamicFieldsContainer.innerHTML = '';
        }
    });
});
