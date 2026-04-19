document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    const table = document.getElementById('patientTable');
    const rows = table ? table.querySelectorAll('tbody tr') : [];
    const noResults = document.getElementById('patientNoResults');

    function filterTable() {
        if (!searchInput) return;
        const query = searchInput.value.toLowerCase().trim();
        let visible = 0;
        rows.forEach(row => {
            const idCell = row.cells[0];
            const nameCell = row.cells[1];
            if (!idCell || !nameCell) return;
            const idText = idCell.textContent.toLowerCase();
            const nameText = nameCell.textContent.toLowerCase();
            const matches = query === '' || idText.includes(query) || nameText.includes(query);
            row.style.display = matches ? '' : 'none';
            if (matches) visible++;
        });
        if (noResults) noResults.style.display = visible === 0 ? 'block' : 'none';
    }

    if (searchInput) searchInput.addEventListener('input', filterTable);
    filterTable();
});

function viewPatient(patientId) {
    window.location.href = `/patients/${patientId}`;
}

function openTransferModal(button) {
    const patientId = button.getAttribute('data-patient-id');
    const patientName = button.getAttribute('data-patient-name');
    const patientGender = button.getAttribute('data-patient-gender');
    const currentWard = button.getAttribute('data-current-ward');

    document.getElementById('transferPatientId').value = patientId;
    document.getElementById('transferPatientName').value = patientName;
    document.getElementById('transferPatientGender').value = patientGender;
    document.getElementById('currentWard').value = currentWard || 'Unknown';
    document.getElementById('transferReason').value = '';
    document.getElementById('wardGenderError').style.display = 'none';

    const modal = document.getElementById('transferModal');
    if (modal) modal.style.display = 'block';
}

function closeTransferModal() {
    const modal = document.getElementById('transferModal');
    if (modal) modal.style.display = 'none';
}

async function submitTransfer(event) {
    event.preventDefault();
    const patientId = document.getElementById('transferPatientId').value;
    const newWardId = document.getElementById('newWardSelect').value;
    const reason = document.getElementById('transferReason').value;

    if (!newWardId) {
        alert('Please select a new ward.');
        return false;
    }
    if (!reason.trim()) {
        alert('Please provide a reason for transfer.');
        return false;
    }

    const formData = new FormData();
    formData.append('new_ward_id', newWardId);
    formData.append('reason', reason);

    try {
        const response = await fetch(`/api/patients/${patientId}/transfer`, {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        if (data.success) {
            alert('Patient transferred successfully.');
            window.location.reload();
        } else {
            alert(data.error || 'Transfer failed.');
        }
    } catch (err) {
        alert('An error occurred. Please try again.');
    }
    return false;
}

async function dischargePatient(patientId, patientName) {
    if (!confirm(`Are you sure you want to discharge ${patientName}? This action cannot be undone.`)) {
        return;
    }
    try {
        const response = await fetch(`/api/patients/${patientId}/discharge`, {
            method: 'POST'
        });
        const data = await response.json();
        if (data.success) {
            alert('Patient discharged successfully.');
            window.location.reload();
        } else {
            alert(data.error || 'Discharge failed.');
        }
    } catch (err) {
        alert('An error occurred. Please try again.');
    }
}