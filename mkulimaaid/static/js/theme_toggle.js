// Theme toggling script
const themeSwitcher = document.getElementById('bd-theme');
const themeIcon = document.querySelector('.theme-icon-active');
const themeText = document.getElementById('bd-theme-text');

// Function to set the theme
const setTheme = (theme) => {
    document.documentElement.setAttribute('data-bs-theme', theme);
    themeText.innerHTML = theme.charAt(0).toUpperCase() + theme.slice(1);
    themeIcon.innerHTML = `<use href="#${theme === 'dark' ? 'moon-stars-fill' : 'sun-fill'}"></use>`;
    localStorage.setItem('theme', theme); // Save preference to local storage
};

// Retrieve theme from local storage or set based on system preferences
const loadTheme = () => {
    const storedTheme = localStorage.getItem('theme');
    if (storedTheme) {
        setTheme(storedTheme);
    } else {
        const prefersDarkScheme = window.matchMedia('(prefers-color-scheme: dark)').matches;
        setTheme(prefersDarkScheme ? 'dark' : 'light');
    }
};

// Add event listeners to theme toggle buttons
document.querySelectorAll('[data-bs-theme-value]').forEach(button => {
    button.addEventListener('click', () => {
        const value = button.getAttribute('data-bs-theme-value');
        setTheme(value);
    });
});

// Listen for changes in system theme and apply auto mode dynamically
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
    if (!localStorage.getItem('theme')) {
        setTheme(e.matches ? 'dark' : 'light');
    }
});

// Load theme on page load
loadTheme();
