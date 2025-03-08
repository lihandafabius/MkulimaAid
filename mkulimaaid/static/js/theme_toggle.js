document.addEventListener("DOMContentLoaded", function () {
    const body = document.body;
    const themeText = document.getElementById('bd-theme-text');
    const themeIcon = document.querySelector('.theme-icon-active');

    // Function to apply the theme
    const setTheme = (theme) => {
        if (theme === "light") {
            body.classList.add("light-theme");
            body.classList.remove("dark-theme");
            body.removeAttribute("data-bs-theme"); // Remove Bootstrap dark mode
        } else {
            body.classList.remove("light-theme");
            body.classList.add("dark-theme");
            body.setAttribute("data-bs-theme", "dark"); // Apply Bootstrap dark mode
        }

        // Update text & icon
        if (themeText && themeIcon) {
            themeText.innerHTML = theme.charAt(0).toUpperCase() + theme.slice(1);
            themeIcon.innerHTML = `<use href="#${theme === 'dark' ? 'moon-stars-fill' : 'sun-fill'}"></use>`;
        }

        // Store theme preference
        localStorage.setItem('theme', theme);
    };

    // Load theme from localStorage or system preference
    const loadTheme = () => {
        const storedTheme = localStorage.getItem('theme');
        if (storedTheme) {
            setTheme(storedTheme);
        } else {
            const prefersDarkScheme = window.matchMedia('(prefers-color-scheme: dark)').matches;
            setTheme(prefersDarkScheme ? 'dark' : 'light');
        }
    };

    // Event listener for theme buttons
    document.querySelectorAll('[data-bs-theme-value]').forEach(button => {
        button.addEventListener('click', () => {
            const value = button.getAttribute('data-bs-theme-value');
            setTheme(value);
        });
    });

    // Detect system changes and update theme
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        if (!localStorage.getItem('theme')) {
            setTheme(e.matches ? 'dark' : 'light');
        }
    });

    // Apply theme on page load
    loadTheme();
});
