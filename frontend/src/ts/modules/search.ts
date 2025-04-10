/**
 * Search Module - Handles search functionality across the application
 */

interface SearchOptions {
    selector: string;
    searchableItems: string;
    searchableText: string;
    noResultsMessage?: string;
    minQueryLength?: number;
    highlightMatches?: boolean;
}

/**
 * Initialize search functionality across the app
 */
export function initSearchFunctionality(): void {
    const searchInputs = document.querySelectorAll('.search-input');
    if (!searchInputs.length) return;
    
    searchInputs.forEach(input => {
        if (!(input instanceof HTMLInputElement)) return;
        
        const inputElement = input as HTMLInputElement;
        const options: SearchOptions = {
            selector: inputElement.dataset.searchTarget || '',
            searchableItems: inputElement.dataset.searchItems || '.searchable-item',
            searchableText: inputElement.dataset.searchText || '',
            noResultsMessage: inputElement.dataset.noResults || 'No results found',
            minQueryLength: parseInt(inputElement.dataset.minLength || '2', 10),
            highlightMatches: inputElement.dataset.highlight === 'true'
        };
        
        if (options.selector) {
            setupSearch(inputElement, options);
        }
    });
}

/**
 * Set up search functionality for a specific input
 */
function setupSearch(input: HTMLInputElement, options: SearchOptions): void {
    const container = document.querySelector(options.selector);
    if (!container) {
        console.warn(`Search container not found: ${options.selector}`);
        return;
    }
    
    const items = container.querySelectorAll(options.searchableItems);
    if (!items.length) {
        console.warn(`No searchable items found: ${options.searchableItems}`);
        return;
    }
    
    // Create no results message element
    const noResultsEl = document.createElement('div');
    noResultsEl.className = 'no-search-results';
    noResultsEl.textContent = options.noResultsMessage || 'No results found';
    noResultsEl.style.display = 'none';
    container.appendChild(noResultsEl);
    
    // Handle search input
    input.addEventListener('input', debounce(() => {
        const query = input.value.trim().toLowerCase();
        
        // Show all items if query is too short
        if (query.length < (options.minQueryLength || 2)) {
            items.forEach(item => {
                if (item instanceof HTMLElement) {
                    item.style.display = '';
                    
                    // Remove any highlights
                    if (options.highlightMatches) {
                        removeHighlights(item);
                    }
                }
            });
            noResultsEl.style.display = 'none';
            return;
        }
        
        let matchFound = false;
        
        // Search in items
        items.forEach(item => {
            if (!(item instanceof HTMLElement)) return;
            
            let searchableText = '';
            
            // Get text to search in
            if (options.searchableText) {
                const textElement = item.querySelector(options.searchableText);
                searchableText = textElement ? textElement.textContent || '' : '';
            } else {
                searchableText = item.textContent || '';
            }
            
            searchableText = searchableText.toLowerCase();
            
            // Check if item matches search
            if (searchableText.includes(query)) {
                item.style.display = '';
                matchFound = true;
                
                // Highlight matches if enabled
                if (options.highlightMatches) {
                    highlightMatches(item, query);
                }
            } else {
                item.style.display = 'none';
                
                // Remove any highlights
                if (options.highlightMatches) {
                    removeHighlights(item);
                }
            }
        });
        
        // Show or hide no results message
        noResultsEl.style.display = matchFound ? 'none' : 'block';
    }, 300));
    
    // Clear search button
    const clearBtn = input.parentElement?.querySelector('.clear-search');
    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            input.value = '';
            input.dispatchEvent(new Event('input'));
            input.focus();
        });
    }
}

/**
 * Highlight search matches in text
 */
function highlightMatches(element: Element, query: string): void {
    // First remove any existing highlights
    removeHighlights(element);
    
    // Get all text nodes in the element
    const textNodes = getTextNodes(element);
    
    textNodes.forEach(node => {
        const text = node.nodeValue;
        if (!text) return;
        
        const lowerText = text.toLowerCase();
        const queryRegex = new RegExp(`(${escapeRegex(query)})`, 'gi');
        
        if (lowerText.includes(query.toLowerCase())) {
            const parent = node.parentNode;
            if (!parent) return;
            
            // Replace the text with highlighted version
            const newHtml = text.replace(queryRegex, '<mark class="search-highlight">$1</mark>');
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = newHtml;
            
            // Replace the text node with the highlighted content
            while (tempDiv.firstChild) {
                parent.insertBefore(tempDiv.firstChild, node);
            }
            
            parent.removeChild(node);
        }
    });
}

/**
 * Remove highlight spans from an element
 */
function removeHighlights(element: Element): void {
    const highlights = element.querySelectorAll('.search-highlight');
    
    highlights.forEach(highlight => {
        const parent = highlight.parentNode;
        if (!parent) return;
        
        // Replace the highlight with its text content
        const text = document.createTextNode(highlight.textContent || '');
        parent.replaceChild(text, highlight);
        
        // Normalize the parent to merge adjacent text nodes
        parent.normalize();
    });
}

/**
 * Get all text nodes within an element
 */
function getTextNodes(element: Element): Text[] {
    const textNodes: Text[] = [];
    const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT, null);
    
    let node: Text | null;
    while (node = walker.nextNode() as Text) {
        // Skip nodes that are already within highlights
        if (!node.parentElement?.closest('.search-highlight')) {
            textNodes.push(node);
        }
    }
    
    return textNodes;
}

/**
 * Escape special regex characters
 */
function escapeRegex(string: string): string {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/**
 * Debounce function to limit how often a function can be called
 */
function debounce<F extends (...args: any[]) => any>(func: F, wait: number): (...args: Parameters<F>) => void {
    let timeout: number | null = null;
    
    return function(...args: Parameters<F>): void {
        const later = () => {
            timeout = null;
            func(...args);
        };
        
        if (timeout !== null) {
            clearTimeout(timeout);
        }
        
        timeout = window.setTimeout(later, wait) as unknown as number;
    };
} 