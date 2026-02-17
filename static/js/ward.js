document.addEventListener('DOMContentLoaded', () => {
  const settingsToggle = document.getElementById('settingsToggle');
  const settingsMenu = document.getElementById('settingsMenu');
  const menuToggle = document.getElementById('menuToggle');
  const sidebar = document.getElementById('sidebar');

  /* SETTINGS DROPDOWN */
  if (settingsToggle && settingsMenu) {
    settingsToggle.addEventListener('click', () => {
      settingsMenu.classList.toggle('open');
    });

    document.addEventListener('click', (e) => {
      if (!settingsMenu.contains(e.target) && !settingsToggle.contains(e.target)) {
        settingsMenu.classList.remove('open');
      }
    });
  }

  /* MOBILE SIDEBAR TOGGLE */
  if (menuToggle && sidebar) {
    menuToggle.addEventListener('click', () => {
      sidebar.classList.toggle('sidebar-open');
      sidebar.classList.toggle('sidebar-closed');
    });

    document.addEventListener('click', (e) => {
      if (!sidebar.contains(e.target) && !menuToggle.contains(e.target)) {
        sidebar.classList.remove('sidebar-open');
        sidebar.classList.add('sidebar-closed');
      }
    });
  }

  /* MODAL FUNCTIONS */
  const modal = document.getElementById('transferModal');
  const wardSelect = document.getElementById('newWardSelect');
  const errorMsg = document.getElementById('wardGenderError');

  window.openTransferModal = (id, name, gender, currentWard) => {
    document.getElementById('transferPatientId').value = id;
    document.getElementById('transferPatientName').value = name;
    document.getElementById('transferPatientGender').value = gender;
    document.getElementById('currentWard').value = currentWard;
    modal.classList.add('open');
    
    // Add ward selection validation listener
    wardSelect.addEventListener('change', validateWardGender);
  };

  window.closeTransferModal = () => {
    modal.classList.remove('open');
    document.getElementById('transferForm').reset();
    errorMsg.style.display = 'none';
  };

  function validateWardGender() {
    const selectedWard = wardSelect.options[wardSelect.selectedIndex];
    const wardGender = selectedWard.getAttribute('data-gender');
    const patientGender = document.getElementById('transferPatientGender').value;
    const currentWardValue = document.getElementById('currentWard').value;

    // Check if transferring to the same ward
    if (selectedWard.text === currentWardValue) {
      errorMsg.style.display = 'block';
      errorMsg.textContent = `⚠️ Patient is already in ${selectedWard.text}.`;
      return false;
    }

    // Check gender compatibility
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
    const newWard = selectedWard.text;
    const reason = document.getElementById('transferReason').value;

    // Show confirmation
    if (confirm(`✅ Confirm Transfer\n\nPatient: ${patientName} (${patientId})\nFrom: ${currentWard}\nTo: ${newWard}\nReason: ${reason}\n\nProceed with transfer?`)) {
      // Here you would send data to your backend
      // Example: fetch('/api/transfer', { method: 'POST', body: JSON.stringify(data) })
      
      alert(`✅ Success!\n\nPatient ${patientName} has been transferred from ${currentWard} to ${newWard}.`);
      
      // Close modal and refresh page
      closeTransferModal();
      location.reload();
    }

    return false;
  };

  window.dischargePatient = (id, name) => {
    if (confirm(`⚠️ Discharge Confirmation\n\nAre you sure you want to discharge:\n\nPatient: ${name}\nID: ${id}\n\nThis action will:\n• Remove patient from the ward\n• Update status to "Discharged"\n• Free up the bed for new admissions\n\nProceed with discharge?`)) {
      // Here you would send discharge request to backend
      // Example: fetch('/api/discharge', { method: 'POST', body: JSON.stringify({ patientId: id }) })
      
      alert(`✅ Discharge Successful\n\nPatient ${name} (${id}) has been discharged.\n\nDischarge summary has been generated and the bed is now available.`);
      
      // Remove the row or refresh the page
      location.reload();
    }
  };

  window.viewPatient = (id) => {
    window.location.href = `patient-detail.html?id=${id}`;
  };

  /* LIGHT/DARK MODE TOGGLE */
  const lightModeToggle = document.getElementById('lightModeToggle');
  if (lightModeToggle) {
    lightModeToggle.addEventListener('click', () => {
      if (typeof toggleThemeFromButton === 'function') {
        toggleThemeFromButton(); // defined in theme.js
      } else {
        const html = document.documentElement;
        const currentTheme = html.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        html.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        lightModeToggle.textContent = newTheme === 'light' ? 'Dark mode' : 'Light mode';
      }
    });
  }

  // Close modal when clicking outside
  window.onclick = function(event) {
    if (event.target === modal) {
      closeTransferModal();
    }
  };

  /* COUNT WARD STATISTICS */
  function updateWardStatistics() {
    const wardCards = document.querySelectorAll('.ward-card');
    
    wardCards.forEach(card => {
      const rows = card.querySelectorAll('.ward-table tbody tr:not(.empty-row)');
      const emptyRows = card.querySelectorAll('.ward-table tbody tr.empty-row');
      
      const occupied = rows.length;
      const available = emptyRows.length;
      const total = occupied + available;
      
      // Update badges if needed
      console.log(`Ward statistics - Occupied: ${occupied}, Available: ${available}, Total: ${total}`);
    });
  }

  updateWardStatistics();
});
