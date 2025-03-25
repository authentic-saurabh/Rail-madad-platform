document.addEventListener('DOMContentLoaded', function() {
    const typeSelect = document.getElementById('type');
    const subTypeSelect = document.getElementById('subType');
    const imageUpload = document.getElementById('imageUpload');
    const imagePreview = document.getElementById('imagePreview');
    let categories;

    // Fetch the categories from the JSON file
    fetch('/static/categories.json')
        .then(response => response.json())
        .then(data => {
            categories = data;
            populateTypes();
        })
        .catch(error => console.error('Error loading categories:', error));

    function populateTypes() {
        typeSelect.innerHTML = '<option value="">Select Type</option>';
        categories.forEach(category => {
            const option = document.createElement('option');
            option.value = category.type;
            option.textContent = category.type;
            typeSelect.appendChild(option);
        });
    }

    typeSelect.addEventListener('change', function() {
        const selectedCategory = categories.find(cat => cat.type === this.value);
        populateSubTypes(selectedCategory ? selectedCategory.subtype : []);
    });

    function populateSubTypes(subtypes) {
        subTypeSelect.innerHTML = '<option value="">Select Sub Type</option>';
        subtypes.forEach(subtype => {
            const option = document.createElement('option');
            option.value = subtype;
            option.textContent = subtype;
            subTypeSelect.appendChild(option);
        });
        subTypeSelect.disabled = subtypes.length === 0;
    }

    // Image upload preview
    imageUpload.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                const img = document.createElement('img');
                img.src = e.target.result;
                imagePreview.innerHTML = '';
                imagePreview.appendChild(img);
            }
            reader.readAsDataURL(file);
        } else {
            imagePreview.innerHTML = '';
        }
    });

    document.getElementById('complaintForm').addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Create FormData object
        const formData = new FormData(this);
        
        // Add additional form data
        formData.append('type', typeSelect.value);
        formData.append('subType', subTypeSelect.value);
        
        // Here you would typically send the formData to your server
        // For demonstration, we'll just log it
        for (let [key, value] of formData.entries()) {
            console.log(key, value);
        }
        
        // In a real application, you'd use fetch or XMLHttpRequest to send the data
        // For example:
        /*
        fetch('/submit-complaint', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            console.log('Success:', data);
            // Handle success (e.g., show a success message, reset form)
        })
        .catch((error) => {
            console.error('Error:', error);
            // Handle error (e.g., show an error message)
        });
        */
    });
});


document.getElementById('categorizeBtn').addEventListener('click', function() {
    const imageInput = document.getElementById('imageUpload');
    const file = imageInput.files[0];

    if (!file) {
        alert('Please upload an image before categorizing.');
        return;
    }

    const formData = new FormData();
    formData.append('image', file);

    fetch('/cat_img', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (!data || typeof data !== 'object') {
            throw new Error('Invalid data received from the server.');
        }

        // Convert 'type' to string to ensure consistent comparison
        const type = (data.type || '').toString().trim(); // Trim any extra whitespace
        const subtype = (data.subtype || '').toString().trim(); // Trim any extra whitespace
        const details = data.details || '';

        if (type === '0') {
            // Handle the case where no issue is found
            alert('No context found, please enter details via mic or manually enter them.');

            // Clear type and subtype fields
            document.getElementById('type').value = '';
            document.getElementById('subType').value = '';

            // Clear details field
            document.getElementById('message').value = '';

        } else {
            // Normal case where type is identified
            const typeField = document.getElementById('type');
            const subTypeField = document.getElementById('subType');
            const messageField = document.getElementById('message');

            if (typeField && subTypeField && messageField) {
                // Find and set the type field value
                let typeMatched = false;
                [...typeField.options].forEach(option => {
                    if (option.textContent.trim() === type) {
                        typeField.value = option.value;
                        typeMatched = true;
                    }
                });

                if (!typeMatched) {
                    console.warn('Type value not found:', type);
                    return; // Exit early if type doesn't match
                }

                // Trigger the change event to populate the subType dropdown
                const event = new Event('change');
                typeField.dispatchEvent(event);

                // Wait until subType is populated before setting it
                setTimeout(function() {
                    let subTypeMatched = false;
                    [...subTypeField.options].forEach(option => {
                        if (option.textContent.trim() === subtype) {
                            subTypeField.value = option.value;
                            subTypeMatched = true;
                        }
                    });

                    if (!subTypeMatched) {
                        console.warn('SubType value not found:', subtype);
                    }

                    // Set the details field
                    messageField.value = details;

                }, 500); // Adjust the delay if necessary

            } else {
                console.error('One or more form elements not found.');
            }
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error categorizing the image.');
    });
});

    window.onload = function() {
        const incidentDateTimeField = document.getElementById('incidentDateTime');
        const now = new Date();
        const formattedDateTime = now.toISOString().slice(0, 16); // Get 'YYYY-MM-DDTHH:MM' format
        incidentDateTimeField.value = formattedDateTime;
    };

const micIcon = document.getElementById('micIcon');
const messageTextarea = document.getElementById('message');

// Check if the browser supports Web Speech API
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

if (SpeechRecognition) {
    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;

    micIcon.addEventListener('click', () => {
        if (micIcon.classList.contains('mic-active')) {
            recognition.stop();
        } else {
            recognition.start();
        }
    });

    recognition.onstart = function () {
        micIcon.classList.add('mic-active');
        micIcon.title = 'Listening... Click to stop';
    };

    recognition.onend = function () {
        micIcon.classList.remove('mic-active');
        micIcon.title = 'Click to start speech recognition';
    };

    recognition.onresult = function (event) {
        const transcript = event.results[0][0].transcript;
        
        // Instead of setting the text in the textarea, send it to /cat_text
        sendTextForCategorization(transcript);
    };

} else {
    micIcon.style.display = 'none'; // Hide the mic icon if browser doesn't support speech recognition
    alert('Speech Recognition is not supported in your browser. Please try using Chrome or a supported browser.');
}

// Function to send the recognized text to /cat_text
function sendTextForCategorization(transcript) {
    const formData = new FormData();
    formData.append('text', transcript);

    fetch('/cat_text', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (!data || typeof data !== 'object') {
            throw new Error('Invalid data received from the server.');
        }

        const type = (data.type || '').toString().trim();
        const subtype = (data.subtype || '').toString().trim();
        const details = data.details || '';

        if (type === '0') {
            alert('No context found, please enter details manually.');
        } else {
            const typeField = document.getElementById('type');
            const subTypeField = document.getElementById('subType');
            const messageField = document.getElementById('message');

            // Set the type value and trigger the change event
            let typeMatched = false;
            [...typeField.options].forEach(option => {
                if (option.textContent.trim() === type) {
                    typeField.value = option.value;
                    typeMatched = true;
                }
            });

            if (!typeMatched) {
                console.warn('Type value not found:', type);
                return;
            }

            // Trigger the change event to load the corresponding subtypes
            const event = new Event('change');
            typeField.dispatchEvent(event);

            // Wait until the subtype dropdown is populated before setting the value
            setTimeout(function() {
                let subTypeMatched = false;
                [...subTypeField.options].forEach(option => {
                    if (option.textContent.trim() === subtype) {
                        subTypeField.value = option.value;
                        subTypeMatched = true;
                    }
                });

                if (!subTypeMatched) {
                    console.warn('Subtype value not found:', subtype);
                }

                // Set the details field
                messageField.value = details;

            }, 500); // Adjust the delay as needed to ensure subtypes are loaded
        }
    })
    .catch(error => {
        console.error('Error categorizing the text:', error);
        alert('Error categorizing the text.');
    });
}

        document.getElementById('categorizeTextBtn').addEventListener('click', function() {
            const transcript = document.getElementById('message').value;
            sendTextForCategorization(transcript);
        });

document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('complaintForm');
    form.addEventListener('submit', function (e) {
        e.preventDefault(); // Prevent default form submission

        const formData = new FormData(form);

        // Debugging: Log form values
        console.log("Form Data:", {
            name: formData.get('name'),
            email: formData.get('email'),
            pnr: formData.get('pnr'),
            incidentDateTime: formData.get('incidentDateTime'),
            type: formData.get('type'),
            subType: formData.get('subType'),
            message: formData.get('message')
        });

        // Prepare data for submission
        const data = {
            name: formData.get('name'),
            email: formData.get('email'),
            pnr: formData.get('pnr'),
            incidentDateTime: formData.get('incidentDateTime'),
            type: formData.get('type'),
            subType: formData.get('subType'),
            message: formData.get('message'),
        };

        fetch('/add_complaint', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                alert('Complaint submitted successfully!');
                form.reset(); // Clear form after submission
            } else {
                alert('Error submitting complaint.');
            }
        })
        .catch(error => console.error('Error:', error));
    });
});
