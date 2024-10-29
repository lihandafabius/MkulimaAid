function togglePasswordVisibility(fieldId) {
    const passwordField = document.getElementById(fieldId);
    const icon = passwordField.nextElementSibling.querySelector('svg');
    const tooltip = bootstrap.Tooltip.getInstance(icon); // Get tooltip instance if using tooltips

    if (passwordField.type === 'password') {
        passwordField.type = 'text';
        icon.classList.replace('bi-eye', 'bi-eye-slash');
        if (tooltip) tooltip.setContent({ '.tooltip-inner': 'Hide Password' });
    } else {
        passwordField.type = 'password';
        icon.classList.replace('bi-eye-slash', 'bi-eye');
        if (tooltip) tooltip.setContent({ '.tooltip-inner': 'Show Password' });
    }
}
