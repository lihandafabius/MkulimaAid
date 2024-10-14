// Theme toggling
const themeSwitcher = document.getElementById('bd-theme');
const themeIcon = document.querySelector('.theme-icon-active');
const themeText = document.getElementById('bd-theme-text');

// Set initial theme based on system preference
const setTheme = (theme) => {
    document.documentElement.setAttribute('data-bs-theme', theme);
    themeText.innerHTML = theme.charAt(0).toUpperCase() + theme.slice(1);
    themeIcon.innerHTML = `<use href="#${theme === 'dark' ? 'moon-stars-fill' : 'sun-fill'}"></use>`;
};

document.querySelectorAll('[data-bs-theme-value]').forEach(button => {
    button.addEventListener('click', () => {
        const value = button.getAttribute('data-bs-theme-value');
        setTheme(value);
    });
});

// Apply the auto theme based on system settings
const prefersDarkScheme = window.matchMedia('(prefers-color-scheme: dark)').matches;
setTheme(prefersDarkScheme ? 'dark' : 'light');
