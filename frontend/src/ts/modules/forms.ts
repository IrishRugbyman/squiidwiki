/**
 * Forms Module - Handles form validation, submission and file uploads
 */

import { showNotification } from './notifications';
// Custom validator types
export type ValidatorFn = (value: string) => boolean;

export interface ValidationRule {
  required?: boolean;
  minLength?: number;
  maxLength?: number;
  pattern?: RegExp;
  validate?: ValidatorFn;
  message?: string;
}

export interface ValidationRules {
  [fieldName: string]: ValidationRule;
}

// Input type guard functions
function isInputElement(element: HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement): element is HTMLInputElement {
    return 'type' in element && element.tagName.toLowerCase() === 'input';
}

function isTextAreaElement(element: HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement): element is HTMLTextAreaElement {
    return element.tagName.toLowerCase() === 'textarea';
}

/**
 * Form enhancements
 */
export function initForms(): void {
    // Auto-expanding textareas
    const textareas = document.querySelectorAll('textarea.auto-expand');
    
    textareas.forEach(textarea => {
        textarea.addEventListener('input', function(this: HTMLTextAreaElement) {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
        
        // Initial height
        const textareaElement = textarea as HTMLTextAreaElement;
        textareaElement.style.height = 'auto';
        textareaElement.style.height = (textareaElement.scrollHeight) + 'px';
    });
    
    // Form validation
    const forms = document.querySelectorAll('form.validate');
    
    forms.forEach(form => {
        // Add input event listeners for live validation
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('blur', function(this: HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement) {
                validateInput(this);
            });
            
            input.addEventListener('input', function(this: HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement) {
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
                if (!validateInput(field as HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement)) {
                    valid = false;
                }
            });
            
            if (!valid) {
                e.preventDefault();
                
                // Focus first invalid field
                const firstInvalid = form.querySelector('.error') as HTMLElement;
                if (firstInvalid) {
                    firstInvalid.focus();
                }
                
                // Show validation error message
                showNotification('Please fix the form errors before submitting.', 'error');
            } else if (form.classList.contains('ajax-form')) {
                // Handle AJAX form submission
                e.preventDefault();
                submitFormAjax(form as HTMLFormElement);
            }
        });
    });
    
    // AJAX form submission setup
    const ajaxForms = document.querySelectorAll('form.ajax-form');
    ajaxForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            submitFormAjax(form as HTMLFormElement);
        });
    });
    
    // Handle file upload previews in a separate function if needed
    initFileUploads();
}

/**
 * Initialize file uploads
 */
export function initFileUploads(): void {
    const fileInputs = document.querySelectorAll('input[type="file"].preview');
    
    fileInputs.forEach(input => {
        const fileInput = input as HTMLInputElement;
        const previewContainer = document.querySelector(`[data-preview-for="${fileInput.id}"]`);
        
        if (!previewContainer) return;
        
        fileInput.addEventListener('change', function() {
            if (!this.files || !this.files.length) return;
            
            // Clear existing previews
            previewContainer.innerHTML = '';
            
            // Create preview for each file
            Array.from(this.files).forEach(file => {
                if (file.type.startsWith('image/')) {
                    createImagePreview(file, previewContainer as HTMLElement);
                } else {
                    createFilePreview(file, previewContainer as HTMLElement);
                }
            });
        });
    });
}

/**
 * Create image preview for uploaded file
 */
function createImagePreview(file: File, container: HTMLElement): void {
    const reader = new FileReader();
    
    reader.onload = function(e) {
        const preview = document.createElement('div');
        preview.className = 'file-preview image-preview';
        preview.innerHTML = `
            <img src="${e.target?.result}" alt="${file.name}">
            <span class="file-name">${file.name}</span>
        `;
        container.appendChild(preview);
    };
    
    reader.readAsDataURL(file);
}

/**
 * Create generic file preview
 */
function createFilePreview(file: File, container: HTMLElement): void {
    const preview = document.createElement('div');
    preview.className = 'file-preview';
    preview.innerHTML = `
        <div class="file-icon">
            <i class="fas fa-file"></i>
        </div>
        <span class="file-name">${file.name}</span>
        <span class="file-size">${formatFileSize(file.size)}</span>
    `;
    container.appendChild(preview);
}

/**
 * Format file size in human readable format
 */
function formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Validate a form input
 */
export function validateInput(input: HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement): boolean {
    // Skip validation for disabled fields
    if (input.disabled) return true;
    
    let valid = true;
    let errorMessage = '';
    const value = input.value.trim();
    
    // Get custom validation rules from data attributes
    const rules: ValidationRule = {
        required: input.required
    };
    
    // Add input-specific validations based on input type
    if (isInputElement(input)) {
        // For HTMLInputElement
        rules.minLength = input.minLength !== -1 ? input.minLength : undefined;
        rules.maxLength = input.maxLength !== -1 ? input.maxLength : undefined;
        rules.pattern = input.pattern ? new RegExp(input.pattern) : undefined;
    } else if (isTextAreaElement(input)) {
        // For HTMLTextAreaElement
        rules.minLength = input.minLength !== -1 ? input.minLength : undefined;
        rules.maxLength = input.maxLength !== -1 ? input.maxLength : undefined;
    }
    
    // Check required
    if (rules.required && !value) {
        valid = false;
        errorMessage = input.dataset.errorRequired || 'This field is required';
    }
    // Check min length
    else if (rules.minLength && value.length < rules.minLength) {
        valid = false;
        errorMessage = input.dataset.errorMinLength || 
            `This field must be at least ${rules.minLength} characters`;
    }
    // Check max length
    else if (rules.maxLength && value.length > rules.maxLength) {
        valid = false;
        errorMessage = input.dataset.errorMaxLength || 
            `This field must be less than ${rules.maxLength} characters`;
    }
    // Check pattern
    else if (rules.pattern && !rules.pattern.test(value)) {
        valid = false;
        errorMessage = input.dataset.errorPattern || 'Invalid format';
    }
    
    // Set or remove error state
    if (valid) {
        input.classList.remove('error');
        const errorElement = input.parentElement?.querySelector('.error-message');
        if (errorElement) {
            errorElement.textContent = '';
            errorElement.classList.add('hidden');
        }
    } else {
        input.classList.add('error');
        let errorElement = input.parentElement?.querySelector('.error-message');
        
        if (!errorElement) {
            errorElement = document.createElement('div');
            errorElement.className = 'error-message';
            input.parentElement?.appendChild(errorElement);
        }
        
        errorElement.textContent = errorMessage;
        errorElement.classList.remove('hidden');
    }
    
    return valid;
}

/**
 * Submit a form via AJAX
 */
export function submitFormAjax(form: HTMLFormElement): void {
    // Simplified implementation
    const formData = new FormData(form);
    const url = form.action;
    const method = form.method.toUpperCase();
    
    // Convert formData to JSON for non-file forms
    const hasFileInputs = form.querySelector('input[type="file"]') !== null;
    let body: FormData | string = formData;
    
    if (!hasFileInputs) {
        const jsonData: Record<string, unknown> = {};
        formData.forEach((value, key) => {
            jsonData[key] = value;
        });
        body = JSON.stringify(jsonData);
    }
    
    // Show loading state
    form.classList.add('loading');
    const submitBtn = form.querySelector('button[type="submit"]');
    if (submitBtn) {
        submitBtn.setAttribute('disabled', 'disabled');
    }
    
    // Make the request
    fetch(url, {
        method,
        body,
        headers: hasFileInputs ? {} : {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        // Handle success
        if (data.success) {
            showNotification(data.message || 'Success!', 'success');
            if (form.dataset.redirect) {
                window.location.href = form.dataset.redirect;
            }
        } else {
            // Handle API error
            showNotification(data.error || 'An error occurred', 'error');
        }
    })
    .catch(error => {
        // Handle network error
        showNotification('Network error: ' + error.message, 'error');
    })
    .finally(() => {
        // Reset form state
        form.classList.remove('loading');
        if (submitBtn) {
            submitBtn.removeAttribute('disabled');
        }
    });
} 