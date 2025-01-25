function togglePasswordVisibility(fieldId, iconContainerId) {
    const passwordField = document.getElementById(fieldId);
    const iconContainer = document.getElementById(iconContainerId);
    const showIcon = iconContainer.querySelector('#show-eye-icon');
    const hideIcon = iconContainer.querySelector('#hide-eye-icon');
    const tooltip = bootstrap.Tooltip.getInstance(iconContainer);

    if (passwordField.type === 'password') {
        passwordField.type = 'text';
        showIcon.style.display = 'none';
        hideIcon.style.display = 'inline';
        tooltip.setContent({ '.tooltip-inner': 'Hide Password' });
    } else {
        passwordField.type = 'password';
        showIcon.style.display = 'inline';
        hideIcon.style.display = 'none';
        tooltip.setContent({ '.tooltip-inner': 'Show Password' });
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});
