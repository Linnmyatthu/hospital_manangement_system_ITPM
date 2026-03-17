document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('wardSearch');
    const statusFilter = document.getElementById('wardStatusFilter');
    const table = document.getElementById('wardsTable');
    const rows = table ? table.querySelectorAll('tbody tr') : [];
    const noResults = document.getElementById('noResultsMessage');

    function getCellText(cell) {
        if (!cell) return '';
        let text = cell.textContent.trim();
        if (text.includes(':')) {
            text = text.split(':')[text.split(':').length - 1].trim();
        }
        return text;
    }

    function filterTable() {
        if (!searchInput || !statusFilter) return;
        
        const searchTerm = searchInput.value.toLowerCase().trim();
        const statusValue = statusFilter.value.toLowerCase();
        
        let visibleCount = 0;

        rows.forEach((row) => {
            if (row.cells.length < 8 || row.querySelector('td[colspan]')) return;
            
            let wardName = '';
            if (row.cells[0]) wardName = getCellText(row.cells[0]).toLowerCase();
            
            let wardType = '';
            if (row.cells[2]) wardType = getCellText(row.cells[2]).toLowerCase();
            
            let status = '';
            if (row.cells[6]) {
                const statusBadge = row.cells[6].querySelector('.badge');
                if (statusBadge) {
                    status = statusBadge.textContent.trim().toLowerCase();
                } else {
                    status = getCellText(row.cells[6]).toLowerCase();
                }
            }
            
            const matchesSearch = searchTerm === '' || wardName.includes(searchTerm) || wardType.includes(searchTerm);
            const matchesStatus = statusValue === 'all' || status.includes(statusValue);
            
            row.style.display = matchesSearch && matchesStatus ? '' : 'none';
            if (matchesSearch && matchesStatus) visibleCount++;
        });
        
        if (noResults) {
            noResults.style.display = visibleCount === 0 ? 'block' : 'none';
        }
    }

    if (searchInput) searchInput.addEventListener('input', filterTable);
    if (statusFilter) statusFilter.addEventListener('change', filterTable);

    filterTable();
});

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