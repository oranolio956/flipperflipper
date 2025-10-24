/**
 * Mobile-Perfect Table to Card Converter
 * Automatically converts tables to mobile-friendly cards on small screens
 */

(function() {
    'use strict';
    
    // Convert tables to mobile cards
    function convertTablesToCards() {
        if (window.innerWidth <= 768) {
            document.querySelectorAll('table.table').forEach(table => {
                // Skip if already converted
                if (table.dataset.mobileConverted === 'true') return;
                
                const headers = Array.from(table.querySelectorAll('thead th')).map(th => th.textContent.trim());
                const rows = Array.from(table.querySelectorAll('tbody tr'));
                
                // Create mobile card container
                const cardContainer = document.createElement('div');
                cardContainer.className = 'mobile-card-list';
                cardContainer.dataset.tableId = table.id || '';
                
                rows.forEach((row, rowIndex) => {
                    const cells = Array.from(row.querySelectorAll('td'));
                    
                    // Create card
                    const card = document.createElement('div');
                    card.className = 'mobile-card';
                    card.dataset.rowIndex = rowIndex;
                    
                    // Card header (first cell usually contains main info)
                    const cardHeader = document.createElement('div');
                    cardHeader.className = 'mobile-card-header';
                    
                    const cardTitle = document.createElement('div');
                    cardTitle.className = 'mobile-card-title';
                    cardTitle.textContent = cells[0]?.textContent.trim() || 'Item ' + (rowIndex + 1);
                    cardHeader.appendChild(cardTitle);
                    
                    // Add status badge if exists
                    const statusBadge = cells[0]?.querySelector('.badge, .status-indicator');
                    if (statusBadge) {
                        cardHeader.appendChild(statusBadge.cloneNode(true));
                    }
                    
                    card.appendChild(cardHeader);
                    
                    // Card body
                    const cardBody = document.createElement('div');
                    cardBody.className = 'mobile-card-body';
                    
                    cells.forEach((cell, cellIndex) => {
                        if (cellIndex === 0) return; // Skip first cell (used in header)
                        
                        const cardRow = document.createElement('div');
                        cardRow.className = 'mobile-card-row';
                        
                        const label = document.createElement('div');
                        label.className = 'mobile-card-label';
                        label.textContent = headers[cellIndex] || '';
                        
                        const value = document.createElement('div');
                        value.className = 'mobile-card-value';
                        value.innerHTML = cell.innerHTML;
                        
                        cardRow.appendChild(label);
                        cardRow.appendChild(value);
                        cardBody.appendChild(cardRow);
                    });
                    
                    card.appendChild(cardBody);
                    
                    // Card actions (if row has action buttons)
                    const actionButtons = row.querySelectorAll('button, .btn, a.btn');
                    if (actionButtons.length > 0) {
                        const cardActions = document.createElement('div');
                        cardActions.className = 'mobile-card-actions';
                        
                        actionButtons.forEach(btn => {
                            const clonedBtn = btn.cloneNode(true);
                            // Copy event listeners
                            if (btn.onclick) {
                                clonedBtn.onclick = btn.onclick;
                            }
                            cardActions.appendChild(clonedBtn);
                        });
                        
                        card.appendChild(cardActions);
                    }
                    
                    cardContainer.appendChild(card);
                });
                
                // Hide table and show cards
                table.style.display = 'none';
                table.dataset.mobileConverted = 'true';
                table.parentNode.insertBefore(cardContainer, table.nextSibling);
            });
        } else {
            // Desktop view - show tables, hide cards
            document.querySelectorAll('table.table').forEach(table => {
                table.style.display = '';
            });
            document.querySelectorAll('.mobile-card-list').forEach(list => {
                list.remove();
            });
            document.querySelectorAll('table.table').forEach(table => {
                delete table.dataset.mobileConverted;
            });
        }
    }
    
    // Debounce function
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
    
    // Initialize on load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', convertTablesToCards);
    } else {
        convertTablesToCards();
    }
    
    // Re-convert on window resize (debounced)
    window.addEventListener('resize', debounce(convertTablesToCards, 250));
    
    // Expose function globally for dynamic content
    window.convertTablesToCards = convertTablesToCards;
})();
