/**
 * Interactions JavaScript
 * Modal open/close with backdrop click and escape key
 * Sidebar collapse/expand toggle
 * Alert auto-dismiss after timeout
 * Search bar autocomplete dropdown behavior
 */

/**
 * Initialize all interactions on page load
 */
document.addEventListener('DOMContentLoaded', function() {
    initializeModals();
    initializeSidebar();
    initializeAlerts();
    initializeSearchBars();
});

// ============================================================================
// MODAL INTERACTIONS
// ============================================================================

/**
 * Initialize modal functionality
 */
function initializeModals() {
    // Modal open triggers
    const modalTriggers = document.querySelectorAll('[data-modal-target]');
    modalTriggers.forEach(trigger => {
        trigger.addEventListener('click', function(e) {
            e.preventDefault();
            const modalId = this.dataset.modalTarget;
            openModal(modalId);
        });
    });
    
    // Modal close buttons
    const closeButtons = document.querySelectorAll('[data-modal-close]');
    closeButtons.forEach(button => {
        button.addEventListener('click', function() {
            const modal = this.closest('[data-modal]');
            if (modal) {
                closeModal(modal.id);
            }
        });
    });
    
    // Close modal on backdrop click
    const modals = document.querySelectorAll('[data-modal]');
    modals.forEach(modal => {
        const backdrop = modal.querySelector('[data-modal-backdrop]');
        if (backdrop) {
            backdrop.addEventListener('click', function(e) {
                if (e.target === this) {
                    closeModal(modal.id);
                }
            });
        }
    });
    
    // Close modal on escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            const openModal = document.querySelector('[data-modal].modal-open');
            if (openModal) {
                closeModal(openModal.id);
            }
        }
    });
}

/**
 * Open modal by ID
 */
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;
    
    // Add open class
    modal.classList.add('modal-open');
    modal.classList.remove('hidden');
    
    // Prevent body scroll
    document.body.style.overflow = 'hidden';
    
    // Fade in animation
    setTimeout(() => {
        modal.style.opacity = '1';
        const modalContent = modal.querySelector('[data-modal-content]');
        if (modalContent) {
            modalContent.style.transform = 'scale(1)';
        }
    }, 10);
    
    // Focus first input if exists
    const firstInput = modal.querySelector('input, textarea, select');
    if (firstInput) {
        setTimeout(() => firstInput.focus(), 300);
    }
    
    // Trigger custom event
    modal.dispatchEvent(new CustomEvent('modal:opened', { detail: { modalId } }));
}

/**
 * Close modal by ID
 */
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;
    
    // Fade out animation
    modal.style.opacity = '0';
    const modalContent = modal.querySelector('[data-modal-content]');
    if (modalContent) {
        modalContent.style.transform = 'scale(0.95)';
    }
    
    // Remove open class and hide after animation
    setTimeout(() => {
        modal.classList.remove('modal-open');
        modal.classList.add('hidden');
        
        // Restore body scroll
        document.body.style.overflow = '';
    }, 200);
    
    // Trigger custom event
    modal.dispatchEvent(new CustomEvent('modal:closed', { detail: { modalId } }));
}

/**
 * Close all open modals
 */
function closeAllModals() {
    const openModals = document.querySelectorAll('[data-modal].modal-open');
    openModals.forEach(modal => closeModal(modal.id));
}

// ============================================================================
// SIDEBAR INTERACTIONS
// ============================================================================

let sidebarState = {
    isCollapsed: false,
    isMobileOpen: false,
};

/**
 * Initialize sidebar functionality
 */
function initializeSidebar() {
    const sidebar = document.querySelector('[data-sidebar]');
    if (!sidebar) return;
    
    // Load saved state from localStorage
    const savedState = localStorage.getItem('sidebarCollapsed');
    if (savedState === 'true') {
        collapseSidebar();
    }
    
    // Toggle button
    const toggleButton = document.querySelector('[data-sidebar-toggle]');
    if (toggleButton) {
        toggleButton.addEventListener('click', function() {
            toggleSidebar();
        });
    }
    
    // Mobile menu button
    const mobileToggle = document.querySelector('[data-sidebar-mobile-toggle]');
    if (mobileToggle) {
        mobileToggle.addEventListener('click', function() {
            toggleMobileSidebar();
        });
    }
    
    // Close sidebar on mobile when clicking outside
    document.addEventListener('click', function(e) {
        if (window.innerWidth < 768 && sidebarState.isMobileOpen) {
            if (!sidebar.contains(e.target) && !e.target.closest('[data-sidebar-mobile-toggle]')) {
                closeMobileSidebar();
            }
        }
    });
    
    // Handle window resize
    window.addEventListener('resize', function() {
        if (window.innerWidth >= 768 && sidebarState.isMobileOpen) {
            closeMobileSidebar();
        }
    });
}

/**
 * Toggle sidebar collapse/expand
 */
function toggleSidebar() {
    if (sidebarState.isCollapsed) {
        expandSidebar();
    } else {
        collapseSidebar();
    }
}

/**
 * Collapse sidebar
 */
function collapseSidebar() {
    const sidebar = document.querySelector('[data-sidebar]');
    if (!sidebar) return;
    
    sidebar.classList.add('sidebar-collapsed');
    sidebarState.isCollapsed = true;
    
    // Save state
    localStorage.setItem('sidebarCollapsed', 'true');
    
    // Trigger custom event
    sidebar.dispatchEvent(new CustomEvent('sidebar:collapsed'));
}

/**
 * Expand sidebar
 */
function expandSidebar() {
    const sidebar = document.querySelector('[data-sidebar]');
    if (!sidebar) return;
    
    sidebar.classList.remove('sidebar-collapsed');
    sidebarState.isCollapsed = false;
    
    // Save state
    localStorage.setItem('sidebarCollapsed', 'false');
    
    // Trigger custom event
    sidebar.dispatchEvent(new CustomEvent('sidebar:expanded'));
}

/**
 * Toggle mobile sidebar
 */
function toggleMobileSidebar() {
    if (sidebarState.isMobileOpen) {
        closeMobileSidebar();
    } else {
        openMobileSidebar();
    }
}

/**
 * Open mobile sidebar
 */
function openMobileSidebar() {
    const sidebar = document.querySelector('[data-sidebar]');
    if (!sidebar) return;
    
    sidebar.classList.add('sidebar-mobile-open');
    sidebarState.isMobileOpen = true;
    
    // Prevent body scroll
    document.body.style.overflow = 'hidden';
    
    // Add backdrop
    const backdrop = document.createElement('div');
    backdrop.className = 'sidebar-mobile-backdrop fixed inset-0 bg-black bg-opacity-50 z-30 transition-opacity duration-300';
    backdrop.dataset.sidebarBackdrop = '';
    document.body.appendChild(backdrop);
    
    setTimeout(() => {
        backdrop.style.opacity = '1';
    }, 10);
    
    backdrop.addEventListener('click', closeMobileSidebar);
}

/**
 * Close mobile sidebar
 */
function closeMobileSidebar() {
    const sidebar = document.querySelector('[data-sidebar]');
    if (!sidebar) return;
    
    sidebar.classList.remove('sidebar-mobile-open');
    sidebarState.isMobileOpen = false;
    
    // Restore body scroll
    document.body.style.overflow = '';
    
    // Remove backdrop
    const backdrop = document.querySelector('[data-sidebar-backdrop]');
    if (backdrop) {
        backdrop.style.opacity = '0';
        setTimeout(() => backdrop.remove(), 300);
    }
}

// ============================================================================
// ALERT INTERACTIONS
// ============================================================================

/**
 * Initialize alert functionality
 */
function initializeAlerts() {
    const alerts = document.querySelectorAll('[data-alert]');
    
    alerts.forEach(alert => {
        // Auto-dismiss timeout
        const autoDismiss = alert.dataset.autoDismiss;
        if (autoDismiss) {
            const timeout = parseInt(autoDismiss) || 5000;
            setTimeout(() => {
                dismissAlert(alert);
            }, timeout);
        }
        
        // Close button
        const closeButton = alert.querySelector('[data-alert-close]');
        if (closeButton) {
            closeButton.addEventListener('click', function() {
                dismissAlert(alert);
            });
        }
    });
}

/**
 * Dismiss alert with animation
 */
function dismissAlert(alert) {
    if (typeof alert === 'string') {
        alert = document.getElementById(alert);
    }
    
    if (!alert) return;
    
    // Slide up animation
    alert.style.maxHeight = alert.offsetHeight + 'px';
    alert.style.overflow = 'hidden';
    alert.style.transition = 'all 0.3s ease-out';
    
    setTimeout(() => {
        alert.style.maxHeight = '0';
        alert.style.opacity = '0';
        alert.style.marginBottom = '0';
        alert.style.paddingTop = '0';
        alert.style.paddingBottom = '0';
    }, 10);
    
    setTimeout(() => {
        alert.remove();
    }, 300);
}

/**
 * Show alert programmatically
 */
function showAlert(message, type = 'info', autoDismiss = 5000) {
    const alertContainer = document.getElementById('alert-container') || document.body;
    
    const alertColors = {
        success: 'bg-green-100 border-green-500 text-green-700',
        error: 'bg-red-100 border-red-500 text-red-700',
        warning: 'bg-yellow-100 border-yellow-500 text-yellow-700',
        info: 'bg-blue-100 border-blue-500 text-blue-700',
    };
    
    const alert = document.createElement('div');
    alert.className = `alert ${alertColors[type] || alertColors.info} border-l-4 p-4 mb-4 transition-all duration-300`;
    alert.dataset.alert = '';
    alert.dataset.autoDismiss = autoDismiss;
    alert.style.opacity = '0';
    alert.style.transform = 'translateY(-10px)';
    
    alert.innerHTML = `
        <div class="flex items-center justify-between">
            <p class="flex-1">${message}</p>
            <button data-alert-close class="ml-4 text-current opacity-70 hover:opacity-100 transition-opacity">
                <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
                </svg>
            </button>
        </div>
    `;
    
    alertContainer.insertBefore(alert, alertContainer.firstChild);
    
    // Fade in animation
    setTimeout(() => {
        alert.style.opacity = '1';
        alert.style.transform = 'translateY(0)';
    }, 10);
    
    // Initialize alert functionality
    if (autoDismiss) {
        setTimeout(() => dismissAlert(alert), autoDismiss);
    }
    
    const closeButton = alert.querySelector('[data-alert-close]');
    if (closeButton) {
        closeButton.addEventListener('click', () => dismissAlert(alert));
    }
    
    return alert;
}

// ============================================================================
// SEARCH BAR INTERACTIONS
// ============================================================================

/**
 * Initialize search bar functionality
 */
function initializeSearchBars() {
    const searchBars = document.querySelectorAll('[data-search-bar]');
    
    searchBars.forEach(searchBar => {
        const input = searchBar.querySelector('input[type="search"], input[type="text"]');
        const dropdown = searchBar.querySelector('[data-search-dropdown]');
        
        if (!input || !dropdown) return;
        
        // Show dropdown on focus
        input.addEventListener('focus', function() {
            if (this.value.length >= 2) {
                showSearchDropdown(dropdown);
            }
        });
        
        // Hide dropdown on blur (with delay to allow click on dropdown items)
        input.addEventListener('blur', function() {
            setTimeout(() => {
                hideSearchDropdown(dropdown);
            }, 200);
        });
        
        // Filter dropdown on input
        input.addEventListener('input', function() {
            if (this.value.length >= 2) {
                showSearchDropdown(dropdown);
                // Trigger custom event for AJAX search
                searchBar.dispatchEvent(new CustomEvent('search:input', {
                    detail: { query: this.value }
                }));
            } else {
                hideSearchDropdown(dropdown);
            }
        });
        
        // Handle dropdown item clicks
        dropdown.addEventListener('click', function(e) {
            const item = e.target.closest('[data-search-item]');
            if (item) {
                const value = item.dataset.searchValue || item.textContent.trim();
                input.value = value;
                hideSearchDropdown(dropdown);
                
                // Trigger custom event
                searchBar.dispatchEvent(new CustomEvent('search:selected', {
                    detail: { value, item }
                }));
            }
        });
        
        // Close dropdown on escape
        input.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                hideSearchDropdown(dropdown);
                this.blur();
            }
        });
    });
}

/**
 * Show search dropdown
 */
function showSearchDropdown(dropdown) {
    dropdown.classList.remove('hidden');
    setTimeout(() => {
        dropdown.style.opacity = '1';
        dropdown.style.transform = 'translateY(0)';
    }, 10);
}

/**
 * Hide search dropdown
 */
function hideSearchDropdown(dropdown) {
    dropdown.style.opacity = '0';
    dropdown.style.transform = 'translateY(-5px)';
    setTimeout(() => {
        dropdown.classList.add('hidden');
    }, 200);
}

/**
 * Update search dropdown content
 */
function updateSearchDropdown(searchBarId, items) {
    const searchBar = document.getElementById(searchBarId);
    if (!searchBar) return;
    
    const dropdown = searchBar.querySelector('[data-search-dropdown]');
    if (!dropdown) return;
    
    if (items.length === 0) {
        dropdown.innerHTML = '<div class="p-4 text-gray-500 text-center">No se encontraron resultados</div>';
    } else {
        dropdown.innerHTML = items.map(item => `
            <div class="search-item p-3 hover:bg-gray-100 cursor-pointer transition-colors duration-150" 
                 data-search-item 
                 data-search-value="${item.value}">
                ${item.label}
            </div>
        `).join('');
    }
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Debounce function for performance optimization
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Export functions for use in other scripts
window.CRMInteractions = {
    // Modals
    openModal,
    closeModal,
    closeAllModals,
    
    // Sidebar
    toggleSidebar,
    collapseSidebar,
    expandSidebar,
    toggleMobileSidebar,
    
    // Alerts
    dismissAlert,
    showAlert,
    
    // Search
    showSearchDropdown,
    hideSearchDropdown,
    updateSearchDropdown,
    
    // Utilities
    debounce,
};
