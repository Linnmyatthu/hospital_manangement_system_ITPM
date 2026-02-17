document.addEventListener('DOMContentLoaded', () => {
    console.log('Base.js loaded - with complete sidebar toggle');
    
    const settingsToggle = document.getElementById('settingsToggle');
    const settingsMenu = document.getElementById('settingsMenu');
    const lightBtn = document.getElementById('lightModeToggle');
    const menuToggle = document.getElementById('menuToggle');
    const sidebar = document.getElementById('sidebar');

    /* SETTINGS DROPDOWN */
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

    /* LIGHT / DARK TOGGLE – uses shared theme.js */
    if (lightBtn) {
        lightBtn.addEventListener('click', () => {
            if (typeof toggleThemeFromButton === 'function') {
                toggleThemeFromButton();
            }
        });
    }

    /* MOBILE SIDEBAR TOGGLE */
    if (menuToggle && sidebar) {
        console.log('Menu toggle and sidebar found');
        
        // Set initial state for mobile
        function setInitialState() {
            if (window.innerWidth <= 960) {
                sidebar.classList.remove('sidebar-open');
                console.log('Mobile view - sidebar hidden');
            } else {
                sidebar.classList.remove('sidebar-open');
                console.log('Desktop view - sidebar visible');
            }
        }
        
        // Call initially
        setInitialState();
        
        // Toggle on click
        menuToggle.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            console.log('Menu toggle clicked');
            sidebar.classList.toggle('sidebar-open');
        });
        
        // Close when clicking outside on mobile
        document.addEventListener('click', (e) => {
            if (window.innerWidth <= 960) {
                const clickInsideSidebar = sidebar.contains(e.target);
                const clickOnMenu = menuToggle.contains(e.target);
                
                if (!clickInsideSidebar && !clickOnMenu && sidebar.classList.contains('sidebar-open')) {
                    console.log('Clicked outside - closing sidebar');
                    sidebar.classList.remove('sidebar-open');
                }
            }
        });
        
        // Handle window resize
        window.addEventListener('resize', () => {
            setInitialState();
        });
        
    } else {
        console.error('Menu toggle or sidebar not found!');
        if (!menuToggle) console.error('menuToggle element missing - check ID in HTML');
        if (!sidebar) console.error('sidebar element missing - check ID in HTML');
    }
});