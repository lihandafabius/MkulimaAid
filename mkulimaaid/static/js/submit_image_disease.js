// JavaScript function to submit the form for disease recognition
function selectModel(model, imageFilename) {
    console.log("Disease recognition button clicked"); // Debugging statement

    const form = document.createElement('form');
    form.method = 'POST';
    form.action = "{{ url_for('main.predict') }}";

    const modelInput = document.createElement('input');
    modelInput.type = 'hidden';
    modelInput.name = 'model';
    modelInput.value = model;
    form.appendChild(modelInput);

    const imageInput = document.createElement('input');
    imageInput.type = 'hidden';
    imageInput.name = 'image_filename';
    imageInput.value = imageFilename;
    form.appendChild(imageInput);

    // Add CSRF token
    const csrfToken = document.querySelector('input[name="csrf_token"]').value;
    const csrfInput = document.createElement('input');
    csrfInput.type = 'hidden';
    csrfInput.name = 'csrf_token';
    csrfInput.value = csrfToken;
    form.appendChild(csrfInput);

    console.log("Submitting form to", form.action); // Debugging statement
    document.body.appendChild(form);
    form.submit();
}