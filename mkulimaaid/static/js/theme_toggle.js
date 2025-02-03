document.addEventListener("DOMContentLoaded", function () {
    const themeSwitcher = document.getElementById('bd-theme');
    const themeIcon = document.querySelector('.theme-icon-active');
    const themeText = document.getElementById('bd-theme-text');
    const body = document.body;

    // Function to apply the theme
    const setTheme = (theme) => {
        if (theme === "light") {
            body.classList.add("light-theme");
            body.removeAttribute("data-bs-theme"); // Remove Bootstrap dark mode
        } else {
            body.classList.remove("light-theme");
            body.setAttribute("data-bs-theme", "dark"); // ✅ Use Bootstrap's built-in dark mode
        }

        // Update text & icon
        themeText.innerHTML = theme.charAt(0).toUpperCase() + theme.slice(1);
        themeIcon.innerHTML = `<use href="#${theme === 'dark' ? 'moon-stars-fill' : 'sun-fill'}"></use>`;

        // Store theme preference
        localStorage.setItem('theme', theme);
    };

    // Load stored theme or system preference
    const loadTheme = () => {
        const storedTheme = localStorage.getItem('theme');
        if (storedTheme) {
            setTheme(storedTheme);
        } else {
            const prefersDarkScheme = window.matchMedia('(prefers-color-scheme: dark)').matches;
            setTheme(prefersDarkScheme ? 'dark' : 'light');
        }
    };

    // Add event listeners to theme buttons
    document.querySelectorAll('[data-bs-theme-value]').forEach(button => {
        button.addEventListener('click', () => {
            const value = button.getAttribute('data-bs-theme-value');
            setTheme(value);
        });
    });

    // Watch for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        if (!localStorage.getItem('theme')) {
            setTheme(e.matches ? 'dark' : 'light');
        }
    });

    // Load theme on page load
    loadTheme();
});
