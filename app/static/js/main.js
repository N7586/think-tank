document.addEventListener('DOMContentLoaded', function() {
    // ===== DARK MODE TOGGLE =====
    const themeToggle = document.getElementById('themeToggle');
    const themeIcon = document.getElementById('themeIcon');
    const html = document.documentElement;

    function setTheme(theme) {
        html.classList.add('no-transition');
        html.setAttribute('data-theme', theme);
        localStorage.setItem('tsi-theme', theme);

        if (theme === 'dark') {
            themeIcon.classList.remove('bi-moon-fill');
            themeIcon.classList.add('bi-sun-fill');
        } else {
            themeIcon.classList.remove('bi-sun-fill');
            themeIcon.classList.add('bi-moon-fill');
        }

        requestAnimationFrame(function() {
            requestAnimationFrame(function() {
                html.classList.remove('no-transition');
            });
        });
    }

    // Load saved theme or default to light
    const savedTheme = localStorage.getItem('tsi-theme') || 'light';
    setTheme(savedTheme);

    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            const currentTheme = html.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            setTheme(newTheme);
        });
    }

    // ===== AUTO-DISMISS ALERTS =====
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
});
