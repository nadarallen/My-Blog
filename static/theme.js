// Theme Switcher & Interactive Navigation Logic
document.addEventListener('DOMContentLoaded', () => {
    // ── Theme Switcher (Desktop & Mobile) ──────────────────────────
    const themeBtns = document.querySelectorAll('#themeToggle, #themeToggleMobile');
    const savedTheme = localStorage.getItem('theme');

    const applyTheme = (isDark) => {
        document.body.classList.toggle('dark-theme', isDark);
        themeBtns.forEach(btn => {
            btn.textContent = isDark ? '☀️' : '🌙';
            btn.setAttribute('aria-label', isDark ? 'Switch to Light Theme' : 'Switch to Dark Theme');
        });
    };

    if (savedTheme === 'dark') {
        applyTheme(true);
    }

    themeBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const isDark = !document.body.classList.contains('dark-theme');
            localStorage.setItem('theme', isDark ? 'dark' : 'light');
            applyTheme(isDark);
        });
    });

    // ── Mobile Navigation Toggle ──────────────────────────────────
    const navToggle = document.getElementById('navToggle');
    const mobileNav = document.getElementById('mobileNav');

    if (navToggle && mobileNav) {
        navToggle.addEventListener('click', () => {
            const isOpen = mobileNav.classList.toggle('show');
            navToggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
            navToggle.textContent = isOpen ? '✕' : '☰';
        });
    }

    // ── Form Double-Submit Prevention & Loading Feedback ──────────
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function (e) {
            const submitBtn = this.querySelector('button[type="submit"]:not(.border-0)');
            if (submitBtn && !submitBtn.classList.contains('btn-loading')) {
                // If form is valid, show spinner and prevent duplicate click
                if (this.checkValidity ? this.checkValidity() : true) {
                    submitBtn.classList.add('btn-loading');
                }
            }
        });
    });
});

