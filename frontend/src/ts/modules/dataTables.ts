/**
 * DataTables Module - Provides sorting, filtering and pagination for tables
 */

interface SortOptions {
    column: number;
    order: 'asc' | 'desc';
}

interface DataTableOptions {
    perPage?: number;
    sortable?: boolean;
    filterable?: boolean;
    paginationSelector?: string;
    filterSelector?: string;
}

/**
 * Initialize data tables functionality
 */
export function initDataTables(): void {
    const tables = document.querySelectorAll('table.data-table');
    
    tables.forEach(table => {
        const tableElement = table as HTMLTableElement;
        const options: DataTableOptions = {
            perPage: parseInt(tableElement.dataset.perPage || '10', 10),
            sortable: tableElement.classList.contains('sortable'),
            filterable: tableElement.classList.contains('filterable'),
            paginationSelector: tableElement.dataset.pagination,
            filterSelector: tableElement.dataset.filter
        };
        
        initDataTable(tableElement, options);
    });
}

/**
 * Initialize a single data table
 */
function initDataTable(table: HTMLTableElement, options: DataTableOptions): void {
    if (!table) return;
    
    const tbody = table.querySelector('tbody');
    if (!tbody) return;
    
    const rows = Array.from(tbody.querySelectorAll('tr')).map(row => row as HTMLTableRowElement);
    const headers = table.querySelectorAll('thead th');
    
    // Initialize state
    let currentPage = 1;
    let filteredRows = [...rows];
    let sortOptions: SortOptions | null = null;
    
    // Initialize sort functionality
    if (options.sortable) {
        headers.forEach((header, index) => {
            header.classList.add('sortable');
            header.addEventListener('click', () => {
                // Toggle sort order or set initial
                let order: 'asc' | 'desc' = 'asc';
                if (sortOptions && sortOptions.column === index) {
                    order = sortOptions.order === 'asc' ? 'desc' : 'asc';
                }
                
                sortOptions = { column: index, order };
                
                // Update UI
                headers.forEach(h => h.classList.remove('asc', 'desc'));
                header.classList.add(order);
                
                // Re-render table
                renderTable();
            });
        });
    }
    
    // Initialize filter functionality
    if (options.filterable && options.filterSelector) {
        const filterInput = document.querySelector(options.filterSelector) as HTMLInputElement;
        if (filterInput) {
            filterInput.addEventListener('input', () => {
                const query = filterInput.value.toLowerCase();
                
                // Filter rows
                if (query.trim() === '') {
                    filteredRows = [...rows];
                } else {
                    filteredRows = rows.filter(row => {
                        const text = row.textContent?.toLowerCase() || '';
                        return text.includes(query);
                    });
                }
                
                // Reset to first page
                currentPage = 1;
                
                // Re-render table
                renderTable();
            });
        }
    }
    
    // Initialize pagination
    if (options.perPage && options.perPage > 0 && options.paginationSelector) {
        const paginationContainer = document.querySelector(options.paginationSelector);
        if (paginationContainer) {
            paginationContainer.addEventListener('click', (e) => {
                const target = e.target as HTMLElement;
                if (target.tagName === 'BUTTON' && target.classList.contains('page')) {
                    e.preventDefault();
                    currentPage = parseInt(target.dataset.page || '1', 10);
                    renderTable();
                }
            });
        }
    }
    
    // Render function
    function renderTable(): void {
        // Sort if needed
        if (sortOptions) {
            const { column, order } = sortOptions;
            filteredRows.sort((a, b) => {
                const aValue = getCellValue(a, column);
                const bValue = getCellValue(b, column);
                
                if (order === 'asc') {
                    return aValue.localeCompare(bValue);
                } else {
                    return bValue.localeCompare(aValue);
                }
            });
        }
        
        if (!tbody) return;
        
        // Apply pagination
        let rowsToShow = filteredRows;
        if (options.perPage && options.perPage > 0) {
            const start = (currentPage - 1) * options.perPage;
            const end = start + options.perPage;
            rowsToShow = filteredRows.slice(start, end);
        }
        
        // Render rows
        tbody.innerHTML = '';
        if (rowsToShow.length === 0) {
            const noDataRow = document.createElement('tr');
            const noDataCell = document.createElement('td');
            noDataCell.colSpan = headers.length;
            noDataCell.textContent = 'No data available';
            noDataCell.className = 'no-data';
            noDataRow.appendChild(noDataCell);
            tbody.appendChild(noDataRow);
        } else {
            rowsToShow.forEach(row => {
                tbody.appendChild(row);
            });
        }
        
        // Update pagination
        updatePagination();
    }
    
    // Helper to get cell value
    function getCellValue(row: HTMLTableRowElement, index: number): string {
        const cell = row.cells[index];
        return cell ? cell.textContent?.trim() || '' : '';
    }
    
    // Update pagination controls
    function updatePagination(): void {
        if (!options.paginationSelector || !options.perPage) return;
        
        const container = document.querySelector(options.paginationSelector);
        if (!container) return;
        
        const totalPages = Math.ceil(filteredRows.length / options.perPage);
        
        // Create pagination controls
        container.innerHTML = '';
        
        if (totalPages <= 1) return;
        
        // Previous button
        const prevBtn = document.createElement('button');
        prevBtn.className = `page prev ${currentPage === 1 ? 'disabled' : ''}`;
        prevBtn.innerHTML = '&laquo;';
        prevBtn.disabled = currentPage === 1;
        prevBtn.dataset.page = String(Math.max(1, currentPage - 1));
        container.appendChild(prevBtn);
        
        // Page buttons
        const maxButtons = 5;
        const startPage = Math.max(1, currentPage - Math.floor(maxButtons / 2));
        const endPage = Math.min(totalPages, startPage + maxButtons - 1);
        
        for (let i = startPage; i <= endPage; i++) {
            const pageBtn = document.createElement('button');
            pageBtn.className = `page ${i === currentPage ? 'active' : ''}`;
            pageBtn.textContent = String(i);
            pageBtn.dataset.page = String(i);
            container.appendChild(pageBtn);
        }
        
        // Next button
        const nextBtn = document.createElement('button');
        nextBtn.className = `page next ${currentPage === totalPages ? 'disabled' : ''}`;
        nextBtn.innerHTML = '&raquo;';
        nextBtn.disabled = currentPage === totalPages;
        nextBtn.dataset.page = String(Math.min(totalPages, currentPage + 1));
        container.appendChild(nextBtn);
    }
    
    // Initial render
    renderTable();
} 