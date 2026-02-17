document.addEventListener('DOMContentLoaded', () => {
    console.log('Base.js loaded - global functionality');
    
    const settingsToggle = document.getElementById('settingsToggle');
    const settingsMenu = document.getElementById('settingsMenu');
    const lightBtn = document.getElementById('lightModeToggle');
    const menuToggle = document.getElementById('menuToggle');
    const sidebar = document.getElementById('sidebar');

    /* ========== SETTINGS DROPDOWN ========== */
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

    /* ========== THEME TOGGLE ========== */
    if (lightBtn) {
        lightBtn.addEventListener('click', () => {
            if (typeof toggleThemeFromButton === 'function') {
                toggleThemeFromButton();
            }
        });
    }

    /* ========== MOBILE SIDEBAR TOGGLE ========== */
    if (menuToggle && sidebar) {
        console.log('✅ Menu toggle and sidebar found - initializing sidebar');
        
        // Set initial state based on screen size
        function setInitialState() {
            if (window.innerWidth <= 960) {
                sidebar.classList.remove('sidebar-open');
                console.log('📱 Mobile view - sidebar hidden');
            } else {
                sidebar.classList.remove('sidebar-open');
                console.log('💻 Desktop view - sidebar visible');
            }
        }
        
        // Call initially
        setInitialState();
        
        // Toggle on hamburger menu click
        menuToggle.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            console.log('🍔 Menu toggle clicked');
            sidebar.classList.toggle('sidebar-open');
            console.log('Sidebar open:', sidebar.classList.contains('sidebar-open'));
        });
        
        // Close when clicking outside on mobile
        document.addEventListener('click', (e) => {
            if (window.innerWidth <= 960) {
                const isClickInsideSidebar = sidebar.contains(e.target);
                const isClickOnMenu = menuToggle.contains(e.target);
                
                if (!isClickInsideSidebar && !isClickOnMenu && sidebar.classList.contains('sidebar-open')) {
                    console.log('👆 Clicked outside - closing sidebar');
                    sidebar.classList.remove('sidebar-open');
                }
            }
        });
        
        // Handle window resize (e.g., rotating phone)
        window.addEventListener('resize', () => {
            setInitialState();
        });
        
    } else {
        console.error('❌ Menu toggle or sidebar not found!');
        if (!menuToggle) console.error('   - menuToggle element missing (check ID in HTML)');
        if (!sidebar) console.error('   - sidebar element missing (check ID in HTML)');
    }
});