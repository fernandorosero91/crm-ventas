/**
 * Form Validation JavaScript
 * Real-time validation for all form inputs with floating labels
 * Validates email format, phone format, min/max length
 * Shows/hides error messages dynamically
 * Displays loading spinner on form submit
 */

// Validation patterns
const VALIDATION_PATTERNS = {
    email: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
    phone: /^[\d\s\-\(\)\+]{7,20}$/,
};

// Validation messages in Spanish
const VALIDATION_MESSAGES = {
    required: 'Este campo es obligatorio',
    email: 'Ingrese un correo electrónico válido',
    phone: 'Ingrese un número de teléfono válido (7-20 caracteres)',
    minLength: 'Debe tener al menos {min} caracteres',
    maxLength: 'No debe exceder {max} caracteres',
    min: 'El valor mínimo es {min}',
    max: 'El valor máximo es {max}',
    pattern: 'El formato ingresado no es válido',
};

/**
 * Initialize form validation on page load
 */
document.addEventListener('DOMContentLoaded', function() {
    initializeFormValidation();
    initializeFloatingLabels();
    initializeFormSubmitHandlers();
});

/**
 * Initialize validation for all form inputs
 */
function initializeFormValidation() {
    const inputs = document.querySelectorAll('input, textarea, select');
    
    inputs.forEach(input => {
        // Validate on blur (when user leaves the field)
        input.addEventListener('blur', function() {
            validateField(this);
        });
        
        // Clear error on focus
        input.addEventListener('focus', function() {
            clearFieldError(this);
        });
        
        // Real-time validation for certain fields
        if (input.type === 'email' || input.type === 'tel' || input.dataset.realtimeValidation) {
            input.addEventListener('input', function() {
                if (this.value.length > 0) {
                    validateField(this);
                }
            });
        }
    });
}

/**
 * Initialize floating label animations
 */
function initializeFloatingLabels() {
    const inputs = document.querySelectorAll('.floating-input');
    
    inputs.forEach(input => {
        // Check if input has value on load
        if (input.value) {
            floatLabel(input);
        }
        
        // Float label on focus
        input.addEventListener('focus', function() {
            floatLabel(this);
        });
        
        // Unfloat label if empty on blur
        input.addEventListener('blur', function() {
            if (!this.value) {
                unfloatLabel(this);
            }
        });
        
        // Keep label floated if value exists
        input.addEventListener('input', function() {
            if (this.value) {
                floatLabel(this);
            }
        });
    });
}

/**
 * Float label above input
 */
function floatLabel(input) {
    const label = input.parentElement.querySelector('label');
    if (label) {
        label.classList.add('floating-label-active');
    }
}

/**
 * Return label to default position
 */
function unfloatLabel(input) {
    const label = input.parentElement.querySelector('label');
    if (label) {
        label.classList.remove('floating-label-active');
    }
}

/**
 * Validate a single field
 */
function validateField(field) {
    // Clear previous errors
    clearFieldError(field);
    
    const value = field.value.trim();
    const fieldType = field.type;
    const isRequired = field.hasAttribute('required');
    const minLength = field.getAttribute('minlength');
    const maxLength = field.getAttribute('maxlength');
    const min = field.getAttribute('min');
    const max = field.getAttribute('max');
    const pattern = field.getAttribute('pattern');
    
    // Required validation
    if (isRequired && !value) {
        showFieldError(field, VALIDATION_MESSAGES.required);
        return false;
    }
    
    // Skip further validation if field is empty and not required
    if (!value && !isRequired) {
        return true;
    }
    
    // Email validation
    if (fieldType === 'email' || field.dataset.validate === 'email') {
        if (!VALIDATION_PATTERNS.email.test(value)) {
            showFieldError(field, VALIDATION_MESSAGES.email);
            return false;
        }
    }
    
    // Phone validation
    if (fieldType === 'tel' || field.dataset.validate === 'phone') {
        if (!VALIDATION_PATTERNS.phone.test(value)) {
            showFieldError(field, VALIDATION_MESSAGES.phone);
            return false;
        }
    }
    
    // Min length validation
    if (minLength && value.length < parseInt(minLength)) {
        const message = VALIDATION_MESSAGES.minLength.replace('{min}', minLength);
        showFieldError(field, message);
        return false;
    }
    
    // Max length validation
    if (maxLength && value.length > parseInt(maxLength)) {
        const message = VALIDATION_MESSAGES.maxLength.replace('{max}', maxLength);
        showFieldError(field, message);
        return false;
    }
    
    // Min value validation (for number inputs)
    if (min && parseFloat(value) < parseFloat(min)) {
        const message = VALIDATION_MESSAGES.min.replace('{min}', min);
        showFieldError(field, message);
        return false;
    }
    
    // Max value validation (for number inputs)
    if (max && parseFloat(value) > parseFloat(max)) {
        const message = VALIDATION_MESSAGES.max.replace('{max}', max);
        showFieldError(field, message);
        return false;
    }
    
    // Pattern validation
    if (pattern) {
        const regex = new RegExp(pattern);
        if (!regex.test(value)) {
            showFieldError(field, VALIDATION_MESSAGES.pattern);
            return false;
        }
    }
    
    // If all validations pass, show success state
    showFieldSuccess(field);
    return true;
}

/**
 * Show error message for a field
 */
function showFieldError(field, message) {
    // Add error class to field
    field.classList.add('border-red-500', 'focus:border-red-500', 'focus:ring-red-500');
    field.classList.remove('border-green-500', 'focus:border-green-500', 'focus:ring-green-500');
    
    // Create or update error message element
    let errorElement = field.parentElement.querySelector('.field-error');
    if (!errorElement) {
        errorElement = document.createElement('p');
        errorElement.className = 'field-error text-red-500 text-sm mt-1 transition-opacity duration-200';
        field.parentElement.appendChild(errorElement);
    }
    
    errorElement.textContent = message;
    errorElement.style.opacity = '1';
}

/**
 * Show success state for a field
 */
function showFieldSuccess(field) {
    // Add success class to field
    field.classList.add('border-green-500', 'focus:border-green-500', 'focus:ring-green-500');
    field.classList.remove('border-red-500', 'focus:border-red-500', 'focus:ring-red-500');
    
    // Remove error message if exists
    const errorElement = field.parentElement.querySelector('.field-error');
    if (errorElement) {
        errorElement.style.opacity = '0';
        setTimeout(() => errorElement.remove(), 200);
    }
}

/**
 * Clear error state from a field
 */
function clearFieldError(field) {
    // Remove error and success classes
    field.classList.remove(
        'border-red-500', 'focus:border-red-500', 'focus:ring-red-500',
        'border-green-500', 'focus:border-green-500', 'focus:ring-green-500'
    );
    
    // Remove error message
    const errorElement = field.parentElement.querySelector('.field-error');
    if (errorElement) {
        errorElement.style.opacity = '0';
        setTimeout(() => errorElement.remove(), 200);
    }
}

/**
 * Initialize form submit handlers
 */
function initializeFormSubmitHandlers() {
    const forms = document.querySelectorAll('form[data-validate]');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Validate all fields
            const fields = this.querySelectorAll('input, textarea, select');
            let isValid = true;
            
            fields.forEach(field => {
                if (!validateField(field)) {
                    isValid = false;
                }
            });
            
            // If form is valid, show loading spinner and submit
            if (isValid) {
                showLoadingSpinner(this);
                
                // Submit form after a brief delay to show spinner
                setTimeout(() => {
                    this.submit();
                }, 300);
            } else {
                // Scroll to first error
                const firstError = this.querySelector('.border-red-500');
                if (firstError) {
                    firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    firstError.focus();
                }
            }
        });
    });
}

/**
 * Show loading spinner on form submit
 */
function showLoadingSpinner(form) {
    const submitButton = form.querySelector('button[type="submit"]');
    
    if (submitButton) {
        // Store original button content
        submitButton.dataset.originalContent = submitButton.innerHTML;
        
        // Disable button
        submitButton.disabled = true;
        
        // Add loading spinner
        submitButton.innerHTML = `
            <svg class="animate-spin h-5 w-5 inline-block mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Procesando...
        `;
    }
}

/**
 * Hide loading spinner (useful for AJAX forms)
 */
function hideLoadingSpinner(form) {
    const submitButton = form.querySelector('button[type="submit"]');
    
    if (submitButton && submitButton.dataset.originalContent) {
        submitButton.disabled = false;
        submitButton.innerHTML = submitButton.dataset.originalContent;
        delete submitButton.dataset.originalContent;
    }
}

/**
 * Validate entire form programmatically
 */
function validateForm(form) {
    const fields = form.querySelectorAll('input, textarea, select');
    let isValid = true;
    
    fields.forEach(field => {
        if (!validateField(field)) {
            isValid = false;
        }
    });
    
    return isValid;
}

// Export functions for use in other scripts
window.CRMValidation = {
    validateField,
    validateForm,
    showFieldError,
    showFieldSuccess,
    clearFieldError,
    showLoadingSpinner,
    hideLoadingSpinner,
};
