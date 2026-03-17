document.addEventListener('DOMContentLoaded', () => {
    const settingsToggle = document.getElementById('settingsToggle');
    const settingsMenu = document.getElementById('settingsMenu');
    const lightBtn = document.getElementById('lightModeToggle');
    const menuToggle = document.getElementById('menuToggle');
    const sidebar = document.getElementById('sidebar');

    // Settings dropdown
    if (settingsToggle && settingsMenu) {
        settingsToggle.addEventListener('click', (e) => {
            e.stopPropagation();
            settingsMenu.classList.toggle('open');
        });

        document.addEventListener('click', (e) => {
            if (!settingsMenu.contains(e.target) && !settingsToggle.contains(e.target)) {
                settingsMenu.classList.remove('open');
            }
        });
    }

    // Light / Dark mode toggle (uses shared theme.js)
    if (lightBtn) {
        lightBtn.addEventListener('click', () => {
            if (typeof toggleThemeFromButton === 'function') {
                toggleThemeFromButton();
            }
        });
    }

    // Mobile sidebar toggle
    if (menuToggle && sidebar) {
        const setInitialState = () => {
            if (window.innerWidth <= 960) {
                sidebar.classList.remove('sidebar-open');
            } else {
                sidebar.classList.remove('sidebar-open');
            }
        };

        setInitialState();

        menuToggle.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            sidebar.classList.toggle('sidebar-open');
        });

        document.addEventListener('click', (e) => {
            if (window.innerWidth <= 960) {
                const clickInsideSidebar = sidebar.contains(e.target);
                const clickOnMenu = menuToggle.contains(e.target);
                if (!clickInsideSidebar && !clickOnMenu && sidebar.classList.contains('sidebar-open')) {
                    sidebar.classList.remove('sidebar-open');
                }
            }
        });

        window.addEventListener('resize', setInitialState);
    }
});