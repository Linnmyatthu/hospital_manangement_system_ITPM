document.addEventListener('DOMContentLoaded', () => {
    // ========== PATIENT SEARCH ==========
    const searchInput = document.getElementById('searchInput');
    const patientTable = document.getElementById('patientTable');

    if (searchInput && patientTable) {
        searchInput.addEventListener('keyup', function() {
            const searchTerm = this.value.toLowerCase().trim();
            const rows = patientTable.tBodies[0].getElementsByTagName('tr');

            Array.from(rows).forEach(row => {
                const name = row.cells[1].textContent.toLowerCase(); // Name column
                const id = row.cells[0].textContent.toLowerCase(); // ID column
                const shouldShow = name.includes(searchTerm) || id.includes(searchTerm);
                row.style.display = shouldShow ? '' : 'none';
            });
        });
    }

    // ========== TRANSFER MODAL FUNCTIONS ==========
    window.openTransferModal = function(patientId, patientName, gender, currentWard) {
        document.getElementById('transferPatientId').value = patientId;
        document.getElementById('transferPatientName').value = patientName;
        document.getElementById('transferPatientGender').value = gender;
        document.getElementById('currentWard').value = currentWard;
        document.getElementById('transferModal').classList.add('show');
    }

    window.closeTransferModal = function() {
        document.getElementById('transferModal').classList.remove('show');
        document.getElementById('transferForm').reset();
    }

    // ========== VIEW PATIENT ==========
    window.viewPatient = function(patientId) {
        window.location.href = `patient-detail.html?id=${patientId}`;
    }

    // ========== DISCHARGE PATIENT ==========
    window.dischargePatient = function(patientId, patientName) {
        if (confirm(`Are you sure you want to discharge ${patientName}?`)) {
            alert(`Patient ${patientName} discharged successfully!`);
            // In a real app, you'd make an API call here
        }
    }

    // ========== TRANSFER FORM SUBMIT ==========
    window.submitTransfer = function(event) {
        event.preventDefault();
        
        const patientId = document.getElementById('transferPatientId').value;
        const patientName = document.getElementById('transferPatientName').value;
        const newWard = document.getElementById('newWardSelect').options[document.getElementById('newWardSelect').selectedIndex].text;
        const reason = document.getElementById('transferReason').value;

        alert(`Patient ${patientName} transferred to ${newWard} successfully!`);
        closeTransferModal();
        return false;
    }

    // ========== GENDER VALIDATION FOR WARD SELECTION ==========
    const newWardSelect = document.getElementById('newWardSelect');
    const patientGender = document.getElementById('transferPatientGender');
    const wardGenderError = document.getElementById('wardGenderError');

    if (newWardSelect && patientGender && wardGenderError) {
        newWardSelect.addEventListener('change', function() {
            const selectedOption = this.options[this.selectedIndex];
            const wardGender = selectedOption.getAttribute('data-gender');
            const patientGenderValue = patientGender.value;

            if (wardGender && patientGenderValue && wardGender !== 'Mixed' && wardGender !== patientGenderValue) {
                wardGenderError.style.display = 'block';
                this.setCustomValidity('Gender mismatch');
            } else {
                wardGenderError.style.display = 'none';
                this.setCustomValidity('');
            }
        });
    }
});