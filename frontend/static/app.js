/**
 * SquiidVault UI Framework
 * Modern JavaScript functionality for the UI components
 */

// Initialize the application when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    initSidebar();
    initDarkMode();
    initDropdowns();
    initForms();
    initNotifications();
    initAnimations();
    initDataTables();
    initSearchFunctionality();
});

/**
 * Sidebar functionality
 */
function initSidebar() {
    const sidebar = document.getElementById('sidebar');
    const toggleButton = document.getElementById('toggle-sidebar');
    const mobileMenuToggle = document.getElementById('mobile-menu-toggle');
    
    if (!sidebar) return;
    
    // Toggle sidebar collapse state
    if (toggleButton) {
        toggleButton.addEventListener('click', function() {
            sidebar.classList.toggle('collapsed');
            // Save preference in localStorage
            localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
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
    document.addEventListener('click', function(e) {
        const isMobile = window.innerWidth <= 1024;
        if (isMobile && sidebar.classList.contains('mobile-open') && 
            !sidebar.contains(e.target) && e.target !== mobileMenuToggle) {
            sidebar.classList.remove('mobile-open');
        }
    });
}

/**
 * Dark/Light mode toggle
 */
function initDarkMode() {
    const darkModeToggle = document.getElementById('dark-mode-toggle');
    
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
function initDropdowns() {
    const dropdownToggles = document.querySelectorAll('.dropdown-toggle');
    
    dropdownToggles.forEach(toggle => {
        toggle.addEventListener('click', function(e) {
            e.preventDefault();
            const dropdown = this.nextElementSibling;
            
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
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.dropdown')) {
            document.querySelectorAll('.dropdown-menu.active').forEach(menu => {
                menu.classList.remove('active');
            });
        }
    });
}

/**
 * Form enhancements
 */
function initForms() {
    // Auto-expanding textareas
    const textareas = document.querySelectorAll('textarea.auto-expand');
    
    textareas.forEach(textarea => {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
        
        // Initial height
        textarea.style.height = 'auto';
        textarea.style.height = (textarea.scrollHeight) + 'px';
    });
    
    // Form validation
    const forms = document.querySelectorAll('form.validate');
    
    forms.forEach(form => {
        // Add input event listeners for live validation
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                validateInput(this);
            });
            
            input.addEventListener('input', function() {
                if (this.classList.contains('error')) {
                    validateInput(this);
                }
            });
        });
        
        form.addEventListener('submit', function(e) {
            let valid = true;
            
            // Check required fields
            const requiredFields = form.querySelectorAll('[required]');
            requiredFields.forEach(field => {
                if (!validateInput(field)) {
                    valid = false;
                }
            });
            
            if (!valid) {
                e.preventDefault();
                
                // Focus first invalid field
                const firstInvalid = form.querySelector('.error');
                if (firstInvalid) {
                    firstInvalid.focus();
                }
                
                // Show validation error message
                showNotification('Please fix the form errors before submitting.', 'error');
            } else if (form.classList.contains('ajax-form')) {
                // Handle AJAX form submission
                e.preventDefault();
                submitFormAjax(form);
            }
        });
    });
    
    // AJAX form submission setup
    const ajaxForms = document.querySelectorAll('form.ajax-form');
    ajaxForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            submitFormAjax(form);
        });
    });
    
    // File upload previews
    const fileInputs = document.querySelectorAll('input[type="file"].preview');
    fileInputs.forEach(input => {
        const previewContainer = document.createElement('div');
        previewContainer.className = 'file-preview';
        input.parentNode.insertBefore(previewContainer, input.nextSibling);
        
        input.addEventListener('change', function() {
            previewContainer.innerHTML = '';
            
            if (this.files && this.files[0]) {
                const file = this.files[0];
                
                // Check if it's an image
                if (file.type.match('image.*')) {
                    const reader = new FileReader();
                    
                    reader.onload = function(e) {
                        const img = document.createElement('img');
                        img.src = e.target.result;
                        img.className = 'file-preview-image';
                        previewContainer.appendChild(img);
                    }
                    
                    reader.readAsDataURL(file);
                } else {
                    // For non-image files, show name and type
                    const fileInfo = document.createElement('div');
                    fileInfo.className = 'file-preview-info';
                    fileInfo.innerHTML = `
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                            <polyline points="14 2 14 8 20 8"></polyline>
                            <line x1="16" y1="13" x2="8" y2="13"></line>
                            <line x1="16" y1="17" x2="8" y2="17"></line>
                            <polyline points="10 9 9 9 8 9"></polyline>
                        </svg>
                        <span>${file.name}</span>
                    `;
                    previewContainer.appendChild(fileInfo);
                }
            }
        });
    });
}

/**
 * Validate a single form input
 * @param {HTMLElement} input - The input element to validate
 * @returns {boolean} - Whether the input is valid
 */
function validateInput(input) {
    let valid = true;
    let errorMessage = '';
    
    // Check for empty required fields
    if (input.hasAttribute('required') && !input.value.trim()) {
        valid = false;
        errorMessage = 'This field is required';
    }
    
    // Email validation
    else if (input.type === 'email' && input.value.trim()) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(input.value.trim())) {
            valid = false;
            errorMessage = 'Please enter a valid email address';
        }
    }
    
    // URL validation
    else if (input.type === 'url' && input.value.trim()) {
        try {
            new URL(input.value.trim());
        } catch (e) {
            valid = false;
            errorMessage = 'Please enter a valid URL';
        }
    }
    
    // Number validation
    else if (input.type === 'number' && input.value.trim()) {
        if (input.hasAttribute('min') && parseFloat(input.value) < parseFloat(input.getAttribute('min'))) {
            valid = false;
            errorMessage = `Value must be at least ${input.getAttribute('min')}`;
        }
        else if (input.hasAttribute('max') && parseFloat(input.value) > parseFloat(input.getAttribute('max'))) {
            valid = false;
            errorMessage = `Value must be at most ${input.getAttribute('max')}`;
        }
    }
    
    // Pattern validation
    else if (input.hasAttribute('pattern') && input.value.trim()) {
        const pattern = new RegExp(input.getAttribute('pattern'));
        if (!pattern.test(input.value.trim())) {
            valid = false;
            errorMessage = input.getAttribute('data-error-pattern') || 'Please match the requested format';
        }
    }
    
    // Custom validation message
    if (input.validity && !input.validity.valid) {
        valid = false;
        errorMessage = input.validationMessage;
    }
    
    // Update UI
    if (!valid) {
        input.classList.add('error');
        
        // Find or create error message element
        let errorEl = input.nextElementSibling;
        if (!errorEl || !errorEl.classList.contains('error-message')) {
            errorEl = document.createElement('div');
            errorEl.className = 'error-message';
            input.parentNode.insertBefore(errorEl, input.nextSibling);
        }
        
        errorEl.textContent = errorMessage;
        errorEl.style.display = 'block';
    } else {
        input.classList.remove('error');
        
        // Hide error message if exists
        const errorEl = input.nextElementSibling;
        if (errorEl && errorEl.classList.contains('error-message')) {
            errorEl.style.display = 'none';
        }
    }
    
    return valid;
}

/**
 * Submit a form via AJAX
 * @param {HTMLFormElement} form - The form to submit
 */
function submitFormAjax(form) {
    const submitBtn = form.querySelector('[type="submit"]');
    const originalBtnText = submitBtn ? submitBtn.innerHTML : '';
    
    // Disable submit button and show loading
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="spin">
                <path d="M21 12a9 9 0 1 1-6.219-8.56"></path>
            </svg>
            Submitting...
        `;
    }
    
    // Get form data
    const formData = new FormData(form);
    
    // Convert FormData to JSON object for API call
    const formDataObj = {};
    formData.forEach((value, key) => {
        formDataObj[key] = value;
    });
    
    // Get form action URL
    const action = form.getAttribute('action') || window.location.href;
    const method = form.getAttribute('method') || 'POST';
    
    // Send request using our API utility
    let apiPromise;
    
    if (method.toUpperCase() === 'GET') {
        apiPromise = API.get(action, formDataObj);
    } else if (method.toUpperCase() === 'PUT') {
        apiPromise = API.put(action, formDataObj);
    } else if (method.toUpperCase() === 'DELETE') {
        apiPromise = API.delete(action);
    } else {
        // Default to POST
        apiPromise = API.post(action, formDataObj);
    }
    
    apiPromise
        .then(result => {
            // Reset button
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalBtnText;
            }
            
            // Show success message
            let message = 'Form submitted successfully';
            let redirectUrl = '';
            
            if (result) {
                message = result.message || message;
                redirectUrl = result.redirect || '';
            }
            
            showNotification(message, 'success');
            
            // Reset form
            form.reset();
            
            // Redirect if specified
            if (redirectUrl) {
                setTimeout(() => {
                    window.location.href = redirectUrl;
                }, 500);
            }
            
            // Trigger success event
            const event = new CustomEvent('form:success', { detail: result });
            form.dispatchEvent(event);
        })
        .catch(error => {
            console.error('Error submitting form:', error);
            
            // Reset button
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalBtnText;
            }
            
            // Handle error response
            let message = 'Form submission failed';
            
            if (error.data && error.data.message) {
                message = error.data.message;
            } else if (error.data && error.data.errors) {
                // Handle field-specific errors
                const errors = error.data.errors;
                Object.keys(errors).forEach(field => {
                    const input = form.querySelector(`[name="${field}"]`);
                    if (input) {
                        input.classList.add('error');
                        
                        // Add error message
                        let errorEl = input.nextElementSibling;
                        if (!errorEl || !errorEl.classList.contains('error-message')) {
                            errorEl = document.createElement('div');
                            errorEl.className = 'error-message';
                            input.parentNode.insertBefore(errorEl, input.nextSibling);
                        }
                        
                        errorEl.textContent = errors[field];
                        errorEl.style.display = 'block';
                    }
                });
                
                message = 'Please correct the errors in the form';
            }
            
            showNotification(message, 'error');
            
            // Trigger error event
            const event = new CustomEvent('form:error', { detail: error.data || { message: error.message } });
            form.dispatchEvent(event);
        });
}

/**
 * Notification system
 */
function initNotifications() {
    // Create notifications container if it doesn't exist
    if (!document.getElementById('notifications-container')) {
        const container = document.createElement('div');
        container.id = 'notifications-container';
        document.body.appendChild(container);
    }
    
    // Close notification when clicking the close button
    document.addEventListener('click', function(e) {
        if (e.target.closest('.notification .close')) {
            const notification = e.target.closest('.notification');
            closeNotification(notification);
        }
    });
}

/**
 * Close a notification
 * @param {HTMLElement} notification - The notification element to close
 */
function closeNotification(notification) {
    notification.classList.add('fade-out');
    
    setTimeout(() => {
        notification.remove();
    }, 300);
}

/**
 * Show notification message
 * @param {string} message - Notification message
 * @param {string} type - Notification type (success, error, warning, info)
 * @param {boolean} autoHide - Whether to auto-hide the notification
 * @param {number} duration - Duration in milliseconds before auto-hiding
 */
function showNotification(message, type = 'info', autoHide = true, duration = 5000) {
    const notificationsContainer = document.getElementById('notifications-container');
    
    if (!notificationsContainer) {
        // Create notifications container if it doesn't exist
        const container = document.createElement('div');
        container.id = 'notifications-container';
        document.body.appendChild(container);
    }
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification ${type} ${autoHide ? 'auto-hide' : ''}`;
    
    // Create notification content
    notification.innerHTML = `
        <div class="notification-content">
            <div class="notification-message">${message}</div>
            <button class="close">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M18 6 6 18"></path>
                    <path d="m6 6 12 12"></path>
                </svg>
            </button>
        </div>
    `;
    
    // Add notification to container
    notificationsContainer.appendChild(notification);
    
    // Auto-hide after specified duration
    if (autoHide) {
        setTimeout(() => {
            if (notification.parentNode) {
                closeNotification(notification);
            }
        }, duration);
    }
    
    // Animate in
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);
}

/**
 * Initialize animations
 */
function initAnimations() {
    // Animate elements when they come into view
    const animatedElements = document.querySelectorAll('.animate-on-scroll');
    
    if (animatedElements.length === 0) return;
    
    // Create intersection observer
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animated');
                // Unobserve after animation
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.1
    });
    
    // Observe each element
    animatedElements.forEach(element => {
        observer.observe(element);
    });
}

/**
 * Initialize data tables
 */
function initDataTables() {
    const tables = document.querySelectorAll('.data-table');
    
    tables.forEach(table => {
        // Get sorting controls
        const sortHeader = table.querySelector('.sort-header');
        const sortSelect = table.querySelector('.sort-select');
        const sortOrderBtn = table.querySelector('.sort-order');
        
        if (!sortHeader || !sortSelect || !sortOrderBtn) return;
        
        // Set up sorting functionality
        sortSelect.addEventListener('change', function() {
            sortTable(table, this.value, sortOrderBtn.getAttribute('data-order'));
        });
        
        sortOrderBtn.addEventListener('click', function() {
            const currentOrder = this.getAttribute('data-order');
            const newOrder = currentOrder === 'asc' ? 'desc' : 'asc';
            this.setAttribute('data-order', newOrder);
            
            // Update icon
            if (newOrder === 'desc') {
                this.querySelector('svg').innerHTML = `
                    <path d="m6 15 6 6 6-6"></path>
                    <path d="m6 9 6-6 6 6"></path>
                `;
            } else {
                this.querySelector('svg').innerHTML = `
                    <path d="m6 9 6-6 6 6"></path>
                    <path d="m6 15 6 6 6-6"></path>
                `;
            }
            
            sortTable(table, sortSelect.value, newOrder);
        });
        
        // Initial sort
        sortTable(table, sortSelect.value, sortOrderBtn.getAttribute('data-order'));
    });
}

/**
 * Sort a table by column
 * @param {HTMLElement} table - The table element
 * @param {string} column - The column to sort by
 * @param {string} order - The sort order (asc or desc)
 */
function sortTable(table, column, order) {
    const rows = Array.from(table.querySelectorAll('tbody tr'));
    const tbody = table.querySelector('tbody');
    
    rows.sort((a, b) => {
        let valA = a.getAttribute(`data-${column}`);
        let valB = b.getAttribute(`data-${column}`);
        
        // Handle numbers
        if (!isNaN(valA) && !isNaN(valB)) {
            valA = parseFloat(valA);
            valB = parseFloat(valB);
        } else {
            valA = valA.toLowerCase();
            valB = valB.toLowerCase();
        }
        
        if (order === 'asc') {
            return valA > valB ? 1 : -1;
        } else {
            return valA < valB ? 1 : -1;
        }
    });
    
    // Clear and append sorted rows
    tbody.innerHTML = '';
    rows.forEach(row => tbody.appendChild(row));
}

/**
 * Initialize search functionality
 */
function initSearchFunctionality() {
    const searchInputs = document.querySelectorAll('.search-input');
    
    searchInputs.forEach(input => {
        const form = input.closest('form');
        const clearBtn = input.nextElementSibling;
        
        // Show clear button when input has value
        input.addEventListener('input', function() {
            if (clearBtn && clearBtn.classList.contains('search-clear')) {
                clearBtn.style.display = this.value.length > 0 ? 'flex' : 'none';
            }
        });
        
        // Clear search
        if (clearBtn && clearBtn.classList.contains('search-clear')) {
            clearBtn.addEventListener('click', function() {
                input.value = '';
                clearBtn.style.display = 'none';
                
                // If part of filter form, trigger search update
                if (form && form.classList.contains('filter-form')) {
                    form.dispatchEvent(new Event('submit'));
                }
            });
            
            // Initial state
            clearBtn.style.display = input.value.length > 0 ? 'flex' : 'none';
        }
    });
    
    // Setup filter forms for AJAX filtering
    const filterForms = document.querySelectorAll('form.filter-form');
    
    filterForms.forEach(form => {
        // Debounce timer
        let debounceTimer;
        
        // Listen to input and change events
        form.addEventListener('input', function(e) {
            if (e.target.type !== 'checkbox' && e.target.type !== 'radio') {
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(() => {
                    this.dispatchEvent(new Event('submit'));
                }, 300);
            }
        });
        
        form.addEventListener('change', function(e) {
            if (e.target.type === 'checkbox' || e.target.type === 'radio' || e.target.tagName === 'SELECT') {
                this.dispatchEvent(new Event('submit'));
            }
        });
        
        // Handle form submission
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const targetContainer = document.querySelector(this.getAttribute('data-target'));
            
            if (!targetContainer) return;
            
            // Add loading state
            targetContainer.classList.add('loading');
            
            // Build query params object
            const queryParams = {};
            for (const [key, value] of formData.entries()) {
                if (value) {
                    queryParams[key] = value;
                }
            }
            
            // Update URL if needed
            if (this.hasAttribute('data-update-url')) {
                const url = new URL(window.location);
                
                // Clear existing search parameters
                for (const key of [...url.searchParams.keys()]) {
                    url.searchParams.delete(key);
                }
                
                // Add new parameters
                for (const [key, value] of Object.entries(queryParams)) {
                    url.searchParams.append(key, value);
                }
                
                window.history.replaceState({}, '', url);
            }
            
            // Fetch filtered results using API utility
            const actionUrl = this.getAttribute('action') || window.location.pathname;
            
            API.get(actionUrl, queryParams)
                .then(html => {
                    targetContainer.innerHTML = html;
                    targetContainer.classList.remove('loading');
                    
                    // Re-initialize components in the new content
                    initAnimations();
                    
                    // Trigger event for custom handling
                    const event = new CustomEvent('filter:updated', { detail: { container: targetContainer } });
                    document.dispatchEvent(event);
                })
                .catch(error => {
                    console.error('Error fetching filtered results:', error);
                    targetContainer.classList.remove('loading');
                    showNotification('Failed to update results. Please try again.', 'error');
                });
        });
    });
}

/**
 * API utilities for AJAX requests
 */
const API = {
    /**
     * Ensures a URL is properly formatted as an API endpoint
     * @param {string} url - The URL to format
     * @returns {string} - The formatted API URL
     */
    _formatApiUrl: function(url) {
        // If URL already starts with /api, return as is
        if (url.startsWith('/api/')) {
            return url;
        }
        
        // If URL starts with /, add api prefix
        if (url.startsWith('/')) {
            return `/api${url}`;
        }
        
        // If URL doesn't start with /, add /api/ prefix
        return `/api/${url}`;
    },
    
    /**
     * Handle API response
     * @param {Response} response - The fetch response
     * @returns {Promise} - Promise resolving to response data
     */
    _handleResponse: function(response) {
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            return response.json().then(data => {
                if (!response.ok) {
                    throw { status: response.status, data };
                }
                return data;
            });
        } else {
            return response.text().then(text => {
                if (!response.ok) {
                    throw { status: response.status, text };
                }
                return text;
            });
        }
    },
    
    /**
     * Send a GET request
     * @param {string} url - The URL to send the request to
     * @param {Object} params - Query parameters
     * @returns {Promise} - Promise resolving to response data
     */
    get: function(url, params = {}) {
        // Format URL as API endpoint
        const apiUrl = this._formatApiUrl(url);
        
        // Build query string
        const queryString = new URLSearchParams(params).toString();
        const fullUrl = queryString ? `${apiUrl}?${queryString}` : apiUrl;
        
        return fetch(fullUrl, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(this._handleResponse);
    },
    
    /**
     * Send a POST request
     * @param {string} url - The URL to send the request to
     * @param {Object} data - The data to send
     * @returns {Promise} - Promise resolving to response data
     */
    post: function(url, data = {}) {
        // Format URL as API endpoint
        const apiUrl = this._formatApiUrl(url);
        
        return fetch(apiUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify(data)
        })
        .then(this._handleResponse);
    },
    
    /**
     * Send a PUT request
     * @param {string} url - The URL to send the request to
     * @param {Object} data - The data to send
     * @returns {Promise} - Promise resolving to response data
     */
    put: function(url, data = {}) {
        // Format URL as API endpoint
        const apiUrl = this._formatApiUrl(url);
        
        return fetch(apiUrl, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify(data)
        })
        .then(this._handleResponse);
    },
    
    /**
     * Send a DELETE request
     * @param {string} url - The URL to send the request to
     * @returns {Promise} - Promise resolving to response data
     */
    delete: function(url) {
        // Format URL as API endpoint
        const apiUrl = this._formatApiUrl(url);
        
        return fetch(apiUrl, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(this._handleResponse);
    }
}; 