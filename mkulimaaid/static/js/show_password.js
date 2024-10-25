function togglePasswordVisibility() {
    const passwordField = document.getElementById('password');
    const passwordField = document.getElementById('confirm_password');
    const passwordIcon = document.getElementById('togglePasswordIcon');

    if (passwordField.type === 'password') {
        passwordField.type = 'text';
        passwordIcon.classList.replace('bi-eye', 'bi-eye-slash');
    } else {
        passwordField.type = 'password';
        passwordIcon.classList.replace('bi-eye-slash', 'bi-eye');
    }
}

