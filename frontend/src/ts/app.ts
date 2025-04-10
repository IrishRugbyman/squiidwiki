/**
 * SquiidVault UI Framework
 * Modern TypeScript functionality for the UI components
 */

// Import UI modules
import { initSidebar, initDarkMode, initDropdowns, initAnimations } from './modules/ui';
import { initForms } from './modules/forms';
import { initNotifications } from './modules/notifications';
import { initDataTables } from './modules/dataTables';
import { initSearchFunctionality } from './modules/search';

// Import API utilities
import * as api from './utils/api';

// Initialize the application when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize UI components
    initSidebar();
    initDarkMode();
    initDropdowns();
    initForms();
    initNotifications();
    initAnimations();
    initDataTables();
    initSearchFunctionality();
});

// Export API utilities globally for use in HTML templates
(window as any).api = api; 