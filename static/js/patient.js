// Patient management functions
document.addEventListener('DOMContentLoaded', () => {
  const searchInput = document.getElementById('searchInput');
  if (searchInput) {
    searchInput.addEventListener('keyup', searchPatients);
  }
});

function openTransferModal(button) {
  document.getElementById('transferForm').reset();
  document.getElementById('wardGenderError').style.display = 'none';

  const patientId = button.getAttribute('data-patient-id');
  const patientName = button.getAttribute('data-patient-name');
  const patientGender = button.getAttribute('data-patient-gender');
  const currentWard = button.getAttribute('data-current-ward');

  document.getElementById('transferPatientId').value = patientId;
  document.getElementById('transferPatientName').value = patientName;
  document.getElementById('transferPatientGender').value = patientGender;
  document.getElementById('currentWard').value = currentWard;

  document.getElementById('transferModal').classList.add('open');
}

function closeTransferModal() {
  document.getElementById('transferModal').classList.remove('open');
}

function submitTransfer(event) {
  event.preventDefault();

  const newWardSelect = document.getElementById('newWardSelect');
  const selectedOption = newWardSelect.options[newWardSelect.selectedIndex];
  const wardGender = selectedOption.getAttribute('data-gender');
  const patientGender = document.getElementById('transferPatientGender').value;

  if (wardGender !== 'Mixed' && wardGender !== patientGender) {
    const errorMsg = document.getElementById('wardGenderError');
    errorMsg.style.display = 'block';
    errorMsg.textContent = `⚠️ Gender mismatch! ${selectedOption.text} is for ${wardGender} patients only.`;
    return false;
  }

  const formData = new FormData();
  formData.append('patient_id', document.getElementById('transferPatientId').value);
  formData.append('new_ward_id', newWardSelect.value);
  formData.append('reason', document.getElementById('transferReason').value);

  fetch(`/api/patients/${formData.get('patient_id')}/transfer`, {
    method: 'POST',
    body: formData
  })
  .then(response => {
    if (!response.ok) {
      throw new Error('Transfer failed');
    }
    return response.json();
  })
  .then(data => {
    alert('✅ Patient transferred successfully!');
    closeTransferModal();
    window.location.reload();
  })
  .catch(error => {
    alert('❌ Transfer failed. Please try again.');
  });

  return false;
}

function searchPatients() {
  const input = document.getElementById('searchInput');
  const filter = input.value.toUpperCase();
  const table = document.getElementById('patientTable');
  const tr = table.getElementsByTagName('tr');

  for (let i = 1; i < tr.length; i++) {
    let found = false;
    const td = tr[i].getElementsByTagName('td');
    for (let j = 0; j < td.length - 1; j++) {
      if (td[j]) {
        const text = td[j].textContent || td[j].innerText;
        if (text.toUpperCase().indexOf(filter) > -1) {
          found = true;
          break;
        }
      }
    }
    tr[i].style.display = found ? '' : 'none';
  }
}

function viewPatient(id) {
  window.location.href = `/patients/${id}`;
}

function dischargePatient(id, name) {
  if (confirm(`⚠️ Are you sure you want to discharge ${name} (ID: ${id})?`)) {
    fetch(`/api/patients/${id}/discharge`, { method: 'POST' })
      .then(response => {
        if (!response.ok) throw new Error('Discharge failed');
        alert(`✅ Patient ${name} has been successfully discharged.`);
        window.location.reload();
      })
      .catch(error => {
        alert('❌ Discharge failed. Please try again.');
      });
  }
}