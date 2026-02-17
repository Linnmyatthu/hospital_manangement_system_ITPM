document.addEventListener('DOMContentLoaded', function() {
    console.log('Wards.js loaded - page specific functionality only');
    
    // Search functionality
    const searchInput = document.getElementById('wardSearch');
    const statusFilter = document.getElementById('wardStatusFilter');
    const table = document.getElementById('wardsTable');
    const rows = table ? table.querySelectorAll('tbody tr') : [];
    const noResults = document.getElementById('noResultsMessage');

    console.log('Found', rows.length, 'rows for search');

    // Simplified function to get cell text
    function getCellText(cell) {
        if (!cell) return '';
        
        // Get the raw text content
        let text = cell.textContent.trim();
        
        // If it contains a colon, take the part after the last colon
        // This handles both "Ward name: Cardiology" and just "Cardiology"
        if (text.includes(':')) {
            const parts = text.split(':');
            text = parts[parts.length - 1].trim();
        }
        
        return text;
    }

    // Filter table function
    function filterTable() {
        if (!searchInput || !statusFilter) {
            console.log('Missing search input or status filter');
            return;
        }
        
        const searchTerm = searchInput.value.toLowerCase().trim();
        const statusValue = statusFilter.value.toLowerCase();
        
        console.log('Searching for:', searchTerm ? `"${searchTerm}"` : 'empty', 'Status:', statusValue);
        
        let visibleCount = 0;

        rows.forEach((row, index) => {
            // Skip rows with colspan (like "no wards found" row)
            if (row.cells.length < 8 || row.querySelector('td[colspan]')) {
                return;
            }
            
            // Get ward name (first cell)
            let wardName = '';
            if (row.cells[0]) {
                wardName = getCellText(row.cells[0]).toLowerCase();
            }
            
            // Get ward type (third cell)
            let wardType = '';
            if (row.cells[2]) {
                wardType = getCellText(row.cells[2]).toLowerCase();
            }
            
            // Get status (seventh cell)
            let status = '';
            if (row.cells[6]) {
                const statusBadge = row.cells[6].querySelector('.badge');
                if (statusBadge) {
                    status = statusBadge.textContent.trim().toLowerCase();
                } else {
                    status = getCellText(row.cells[6]).toLowerCase();
                }
            }
            
            // Debug first few rows (only when searching)
            if (index < 3 && searchTerm) {
                console.log(`Row ${index}:`, {
                    name: wardName,
                    type: wardType,
                    status: status
                });
            }
            
            // Check if search term matches name OR type
            const matchesSearch = searchTerm === '' || 
                                 wardName.includes(searchTerm) || 
                                 wardType.includes(searchTerm);
            
            // Check if status matches filter
            const matchesStatus = statusValue === 'all' || status.includes(statusValue);
            
            // Show/hide row
            if (matchesSearch && matchesStatus) {
                row.style.display = '';
                visibleCount++;
            } else {
                row.style.display = 'none';
            }
        });

        console.log('Visible rows:', visibleCount);
        
        // Show/hide no results message
        if (noResults) {
            noResults.style.display = visibleCount === 0 ? 'block' : 'none';
            if (visibleCount === 0 && searchTerm) {
                console.log('No results found for:', searchTerm);
            }
        }
    }

    // Add event listeners for search
    if (searchInput) {
        searchInput.addEventListener('input', filterTable);
        console.log('Search listener added');
    }
    
    if (statusFilter) {
        statusFilter.addEventListener('change', filterTable);
        console.log('Status filter listener added');
    }

    // Initial filter
    filterTable();
});

// Modal Functions
function openAddWardModal() {
    const modal = document.getElementById('addWardModal');
    if (modal) modal.style.display = 'block';
}

function closeAddWardModal() {
    const modal = document.getElementById('addWardModal');
    if (modal) modal.style.display = 'none';
}

function closeEditWardModal() {
    const modal = document.getElementById('editWardModal');
    if (modal) modal.style.display = 'none';
}

function closeDeleteModal() {
    const modal = document.getElementById('deleteWardModal');
    if (modal) modal.style.display = 'none';
}

function editWard(button) {
    console.log('Edit button clicked');
    
    const wardId = button.getAttribute('data-ward-id');
    const wardName = button.getAttribute('data-ward-name');
    const wardCode = button.getAttribute('data-ward-code');
    const wardType = button.getAttribute('data-ward-type');
    const wardCapacity = button.getAttribute('data-ward-capacity');
    const wardOccupied = button.getAttribute('data-ward-occupied');
    const wardConsultant = button.getAttribute('data-ward-consultant');
    
    document.getElementById('edit_ward_id').value = wardId;
    document.getElementById('edit_name').value = wardName;
    document.getElementById('edit_code').value = wardCode;
    
    const typeSelect = document.getElementById('edit_type');
    for (let i = 0; i < typeSelect.options.length; i++) {
        if (typeSelect.options[i].value === wardType) {
            typeSelect.selectedIndex = i;
            break;
        }
    }
    
    document.getElementById('edit_capacity').value = wardCapacity;
    document.getElementById('edit_occupied').value = wardOccupied;
    document.getElementById('edit_lead_consultant').value = wardConsultant || '';
    
    const form = document.getElementById('editWardForm');
    form.action = `/api/wards/${wardId}`;
    
    const modal = document.getElementById('editWardModal');
    if (modal) modal.style.display = 'block';
}

function deleteWard(button) {
    console.log('Delete button clicked');
    
    const wardId = button.getAttribute('data-ward-id');
    const wardName = button.getAttribute('data-ward-name');
    
    document.getElementById('deleteWardName').textContent = wardName;
    
    const deleteForm = document.getElementById('deleteWardForm');
    deleteForm.action = `/api/wards/${wardId}/delete`;
    
    const modal = document.getElementById('deleteWardModal');
    if (modal) modal.style.display = 'block';
}

function validateWardForm(form) {
    const capacity = parseInt(form.querySelector('[name="capacity"]')?.value) || 0;
    const occupied = parseInt(form.querySelector('[name="occupied"]')?.value) || 0;
    
    if (occupied > capacity) {
        alert('Occupied beds cannot exceed total capacity!');
        return false;
    }
    
    if (capacity <= 0) {
        alert('Total beds must be greater than 0!');
        return false;
    }
    
    return true;
}