function togglePasswordVisibility(fieldId) {
    const passwordField = document.getElementById(fieldId);
    const icon = passwordField.nextElementSibling.querySelector('svg');

    if (passwordField.type === 'password') {
        passwordField.type = 'text';
        icon.classList.replace('bi-eye', 'bi-eye-slash');
    } else {
        passwordField.type = 'password';
        icon.classList.replace('bi-eye-slash', 'bi-eye');
    }
}
