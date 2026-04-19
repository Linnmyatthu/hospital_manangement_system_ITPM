document.addEventListener('DOMContentLoaded', () => {
  const modal = document.getElementById('transferModal');
  const wardSelect = document.getElementById('newWardSelect');
  const errorMsg = document.getElementById('wardGenderError');

  window.openTransferModal = (button) => {
    const patientId = button.dataset.patientId;
    const patientName = button.dataset.patientName;
    const patientGender = button.dataset.patientGender;
    const currentWard = button.dataset.currentWard;

    document.getElementById('transferPatientId').value = patientId;
    document.getElementById('transferPatientName').value = patientName;
    document.getElementById('transferPatientGender').value = patientGender;
    document.getElementById('currentWard').value = currentWard;
    modal.classList.add('open');

    if (wardSelect) wardSelect.addEventListener('change', validateWardGender);
  };

  window.closeTransferModal = () => {
    modal.classList.remove('open');
    document.getElementById('transferForm').reset();
    if (errorMsg) errorMsg.style.display = 'none';
  };

  function validateWardGender() {
    const selectedWard = wardSelect.options[wardSelect.selectedIndex];
    const wardGender = selectedWard.getAttribute('data-gender');
    const patientGender = document.getElementById('transferPatientGender').value;
    const currentWardValue = document.getElementById('currentWard').value;

    if (selectedWard.text === currentWardValue) {
      errorMsg.style.display = 'block';
      errorMsg.textContent = `⚠️ Patient is already in ${selectedWard.text}.`;
      return false;
    }
    if (wardGender !== 'Mixed' && wardGender !== patientGender) {
      errorMsg.style.display = 'block';
      errorMsg.textContent = `⚠️ Gender mismatch! ${selectedWard.text} is for ${wardGender}s only. Patient is ${patientGender}.`;
      return false;
    }
    errorMsg.style.display = 'none';
    return true;
  }

  window.submitTransfer = (e) => {
    e.preventDefault();
    if (!validateWardGender()) {
      alert('❌ Cannot transfer: Ward selection is invalid!');
      return false;
    }

    const patientId = document.getElementById('transferPatientId').value;
    const patientName = document.getElementById('transferPatientName').value;
    const currentWard = document.getElementById('currentWard').value;
    const selectedWard = wardSelect.options[wardSelect.selectedIndex];
    const newWardId = wardSelect.value;
    const newWard = selectedWard.text;
    const reason = document.getElementById('transferReason').value;

    if (confirm(`✅ Confirm Transfer\n\nPatient: ${patientName} (${patientId})\nFrom: ${currentWard}\nTo: ${newWard}\nReason: ${reason}\n\nProceed?`)) {
      const numericId = patientId.replace(/^P0*/, '');
      const formData = new FormData();
      formData.append('new_ward_id', newWardId);
      formData.append('reason', reason);

      fetch(`/api/patients/${numericId}/transfer`, { method: 'POST', body: formData })
        .then(res => res.json())
        .then(data => {
          if (data.success) {
            alert(`✅ ${patientName} transferred to ${newWard}.`);
            closeTransferModal();
            location.reload();
          } else {
            alert('❌ Transfer failed: ' + (data.error || 'Unknown error'));
          }
        })
        .catch(() => alert('❌ Network error. Please try again.'));
    }
    return false;
  };

  window.dischargePatient = (button) => {
    const patientId = button.dataset.patientId;
    const patientName = button.dataset.patientName;
    if (confirm(`⚠️ Discharge Confirmation\n\nAre you sure you want to discharge:\n\nPatient: ${patientName}\nID: ${patientId}\n\nProceed with discharge?`)) {
      const numericId = patientId.replace(/^P0*/, '');
      fetch(`/api/patients/${numericId}/discharge`, { method: 'POST' })
        .then(res => res.json())
        .then(data => {
          if (data.success) {
            alert(`✅ ${patientName} has been discharged.`);
            location.reload();
          } else {
            alert('❌ Discharge failed: ' + (data.error || 'Unknown error'));
          }
        })
        .catch(() => alert('❌ Network error. Please try again.'));
    }
  };

  window.viewPatient = (id) => {
    const numericId = id.replace(/^P/, '');
    window.location.href = `/patients/${numericId}`;
  };

  window.onclick = function(event) {
    if (event.target === modal) closeTransferModal();
  };

  function updateWardStatistics() {
    const wardCards = document.querySelectorAll('.ward-card');
    wardCards.forEach(card => {
      const rows = card.querySelectorAll('.ward-table tbody tr:not(.empty-row)');
      // optional: count occupied beds
    });
  }
  updateWardStatistics();
});