// Theme Switcher & Interactive Navigation Logic
document.addEventListener('DOMContentLoaded', () => {
    // ── Theme Switcher (Desktop & Mobile) ──────────────────────────
    const themeBtns = document.querySelectorAll('#themeToggle, #themeToggleMobile');
    const savedTheme = localStorage.getItem('theme');

    // SVG Icon Definitions
    const sunIcon = `<svg class="icon-svg icon-md" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>`;
    const moonIcon = `<svg class="icon-svg icon-md" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>`;
    const menuIcon = `<svg class="icon-svg icon-md" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="3" y1="12" x2="21" y2="12"></line><line x1="3" y1="6" x2="21" y2="6"></line><line x1="3" y1="18" x2="21" y2="18"></line></svg>`;
    const closeIcon = `<svg class="icon-svg icon-md" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>`;

    const applyTheme = (isDark) => {
        document.body.classList.toggle('dark-theme', isDark);
        themeBtns.forEach(btn => {
            btn.innerHTML = isDark ? sunIcon : moonIcon;
            btn.setAttribute('aria-label', isDark ? 'Switch to Light Theme' : 'Switch to Dark Theme');
        });
    };

    // Initialize with saved theme or default light
    applyTheme(savedTheme === 'dark');

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
        navToggle.innerHTML = menuIcon;
        navToggle.addEventListener('click', () => {
            const isOpen = mobileNav.classList.toggle('show');
            navToggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
            navToggle.innerHTML = isOpen ? closeIcon : menuIcon;
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

