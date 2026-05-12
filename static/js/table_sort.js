/**
 * Table Sorting JavaScript
 * Click-to-sort functionality for table headers
 * Toggle ASC/DESC with visual arrow indicators
 * Client-side sorting for current page data
 */

// Sort state tracking
const sortState = {
    column: null,
    direction: 'asc', // 'asc' or 'desc'
};

/**
 * Initialize table sorting on page load
 */
document.addEventListener('DOMContentLoaded', function() {
    initializeTableSorting();
});

/**
 * Initialize sorting for all sortable tables
 */
function initializeTableSorting() {
    const sortableTables = document.querySelectorAll('table[data-sortable]');
    
    sortableTables.forEach(table => {
        const headers = table.querySelectorAll('th[data-sortable]');
        
        headers.forEach((header, index) => {
            // Add cursor pointer style
            header.style.cursor = 'pointer';
            header.classList.add('select-none', 'hover:bg-gray-100', 'transition-colors', 'duration-150');
            
            // Add sort indicator container if not exists
            if (!header.querySelector('.sort-indicator')) {
                const indicator = document.createElement('span');
                indicator.className = 'sort-indicator ml-2 inline-block transition-transform duration-200';
                indicator.innerHTML = getSortIcon('none');
                header.appendChild(indicator);
            }
            
            // Add click event listener
            header.addEventListener('click', function() {
                sortTable(table, index, this);
            });
        });
    });
}

/**
 * Sort table by column index
 */
function sortTable(table, columnIndex, headerElement) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    // Determine sort direction
    const currentDirection = headerElement.dataset.sortDirection || 'none';
    let newDirection = 'asc';
    
    if (currentDirection === 'asc') {
        newDirection = 'desc';
    } else if (currentDirection === 'desc') {
        newDirection = 'asc';
    }
    
    // Update sort state
    sortState.column = columnIndex;
    sortState.direction = newDirection;
    
    // Clear all sort indicators
    const allHeaders = table.querySelectorAll('th[data-sortable]');
    allHeaders.forEach(header => {
        header.dataset.sortDirection = 'none';
        const indicator = header.querySelector('.sort-indicator');
        if (indicator) {
            indicator.innerHTML = getSortIcon('none');
        }
    });
    
    // Update current header sort indicator
    headerElement.dataset.sortDirection = newDirection;
    const indicator = headerElement.querySelector('.sort-indicator');
    if (indicator) {
        indicator.innerHTML = getSortIcon(newDirection);
    }
    
    // Get data type for sorting
    const dataType = headerElement.dataset.sortType || 'string';
    
    // Sort rows
    rows.sort((rowA, rowB) => {
        const cellA = rowA.cells[columnIndex];
        const cellB = rowB.cells[columnIndex];
        
        // Get sort values (use data-sort-value if available, otherwise text content)
        let valueA = cellA.dataset.sortValue || cellA.textContent.trim();
        let valueB = cellB.dataset.sortValue || cellB.textContent.trim();
        
        // Convert values based on data type
        switch (dataType) {
            case 'number':
                valueA = parseFloat(valueA.replace(/[^0-9.-]/g, '')) || 0;
                valueB = parseFloat(valueB.replace(/[^0-9.-]/g, '')) || 0;
                break;
            case 'date':
                valueA = new Date(valueA).getTime() || 0;
                valueB = new Date(valueB).getTime() || 0;
                break;
            case 'string':
            default:
                valueA = valueA.toLowerCase();
                valueB = valueB.toLowerCase();
                break;
        }
        
        // Compare values
        let comparison = 0;
        if (valueA > valueB) {
            comparison = 1;
        } else if (valueA < valueB) {
            comparison = -1;
        }
        
        // Apply sort direction
        return newDirection === 'asc' ? comparison : -comparison;
    });
    
    // Add fade effect
    tbody.style.opacity = '0.5';
    
    // Re-append sorted rows
    setTimeout(() => {
        rows.forEach(row => tbody.appendChild(row));
        
        // Restore opacity with transition
        tbody.style.transition = 'opacity 0.2s ease-in-out';
        tbody.style.opacity = '1';
        
        // Add row animation
        rows.forEach((row, index) => {
            row.style.animation = `fadeIn 0.3s ease-in-out ${index * 0.02}s`;
        });
    }, 100);
}

/**
 * Get sort icon HTML based on direction
 */
function getSortIcon(direction) {
    switch (direction) {
        case 'asc':
            return `
                <svg class="w-4 h-4 inline-block" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M14.707 12.707a1 1 0 01-1.414 0L10 9.414l-3.293 3.293a1 1 0 01-1.414-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 010 1.414z" clip-rule="evenodd"/>
                </svg>
            `;
        case 'desc':
            return `
                <svg class="w-4 h-4 inline-block" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd"/>
                </svg>
            `;
        case 'none':
        default:
            return `
                <svg class="w-4 h-4 inline-block opacity-30" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M5 12a1 1 0 102 0V6.414l1.293 1.293a1 1 0 001.414-1.414l-3-3a1 1 0 00-1.414 0l-3 3a1 1 0 001.414 1.414L5 6.414V12zM15 8a1 1 0 10-2 0v5.586l-1.293-1.293a1 1 0 00-1.414 1.414l3 3a1 1 0 001.414 0l3-3a1 1 0 00-1.414-1.414L15 13.586V8z"/>
                </svg>
            `;
    }
}

/**
 * Sort table programmatically
 */
function sortTableByColumn(tableId, columnIndex, direction = 'asc') {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const headers = table.querySelectorAll('th[data-sortable]');
    const targetHeader = headers[columnIndex];
    
    if (targetHeader) {
        targetHeader.dataset.sortDirection = direction === 'asc' ? 'none' : 'asc';
        sortTable(table, columnIndex, targetHeader);
    }
}

/**
 * Reset table sorting
 */
function resetTableSort(tableId) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const headers = table.querySelectorAll('th[data-sortable]');
    headers.forEach(header => {
        header.dataset.sortDirection = 'none';
        const indicator = header.querySelector('.sort-indicator');
        if (indicator) {
            indicator.innerHTML = getSortIcon('none');
        }
    });
    
    sortState.column = null;
    sortState.direction = 'asc';
}

/**
 * Get current sort state
 */
function getSortState() {
    return { ...sortState };
}

// Add CSS animation for row fade-in
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(-5px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
`;
document.head.appendChild(style);

// Export functions for use in other scripts
window.CRMTableSort = {
    sortTableByColumn,
    resetTableSort,
    getSortState,
};
