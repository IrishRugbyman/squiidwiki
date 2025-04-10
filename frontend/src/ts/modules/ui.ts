/**
 * UI Module - Handles core UI functionality like sidebar and theme
 */

/**
 * Sidebar functionality
 */
export function initSidebar(): void {
    const sidebar = document.getElementById('sidebar');
    const toggleButton = document.getElementById('toggle-sidebar');
    const mobileMenuToggle = document.getElementById('mobile-menu-toggle');
    
    if (!sidebar) return;
    
    // Toggle sidebar collapse state
    if (toggleButton) {
        toggleButton.addEventListener('click', function() {
            sidebar.classList.toggle('collapsed');
            // Save preference in localStorage
            localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed') ? 'true' : 'false');
        });
    }
    
    // Mobile menu toggle
    if (mobileMenuToggle) {
        mobileMenuToggle.addEventListener('click', function(e) {
            e.preventDefault();
            sidebar.classList.toggle('mobile-open');
        });
    }
    
    // Check for saved preference
    if (localStorage.getItem('sidebarCollapsed') === 'true') {
        sidebar.classList.add('collapsed');
    }
    
    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', function(e: MouseEvent) {
        const isMobile = window.innerWidth <= 1024;
        const target = e.target as HTMLElement;
        if (isMobile && sidebar.classList.contains('mobile-open') && 
            !sidebar.contains(target) && target !== mobileMenuToggle) {
            sidebar.classList.remove('mobile-open');
        }
    });
}

/**
 * Dark/Light mode toggle
 */
export function initDarkMode(): void {
    const darkModeToggle = document.getElementById('dark-mode-toggle') as HTMLInputElement;
    
    if (!darkModeToggle) return;
    
    // Check for saved preference
    const prefersDarkMode = localStorage.getItem('darkMode') === 'true';
    const systemPrefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    // Set initial dark mode state
    if (prefersDarkMode || (prefersDarkMode === null && systemPrefersDark)) {
        document.documentElement.classList.add('dark-mode');
        darkModeToggle.checked = true;
        localStorage.setItem('darkMode', 'true');
    }
    
    // Toggle dark mode
    darkModeToggle.addEventListener('change', function() {
        if (this.checked) {
            document.documentElement.classList.add('dark-mode');
            localStorage.setItem('darkMode', 'true');
        } else {
            document.documentElement.classList.remove('dark-mode');
            localStorage.setItem('darkMode', 'false');
        }
    });
}

/**
 * Dropdown menu functionality
 */
export function initDropdowns(): void {
    const dropdownToggles = document.querySelectorAll('.dropdown-toggle');
    
    dropdownToggles.forEach(toggle => {
        toggle.addEventListener('click', function(this: HTMLElement, e: Event) {
            e.preventDefault();
            const dropdown = this.nextElementSibling as HTMLElement;
            
            // Close all other dropdowns
            document.querySelectorAll('.dropdown-menu.active').forEach(menu => {
                if (menu !== dropdown) {
                    menu.classList.remove('active');
                }
            });
            
            // Toggle this dropdown
            dropdown.classList.toggle('active');
        });
    });
    
    // Close dropdowns when clicking outside
    document.addEventListener('click', function(e: MouseEvent) {
        if (!(e.target as HTMLElement).closest('.dropdown')) {
            document.querySelectorAll('.dropdown-menu.active').forEach(menu => {
                menu.classList.remove('active');
            });
        }
    });
}

/**
 * Initialize animations
 */
export function initAnimations(): void {
    // Add animations implementation when needed
} 