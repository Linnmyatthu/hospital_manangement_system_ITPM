document.addEventListener('DOMContentLoaded', () => {
  const patientSelect = document.getElementById('patientSelect');
  const patientInfo = document.getElementById('patientInfo');
  
  const submitBtn = document.getElementById('submitBtn');
  const successAlert = document.getElementById('successAlert');
  
  const treatmentSearch = document.getElementById('treatmentSearch');
  const treatmentsTable = document.getElementById('treatmentsTable');
  const noResults = document.getElementById('treatmentsNoResults');
  
  const treatmentDate = document.getElementById('treatmentDate');
  const treatmentTime = document.getElementById('treatmentTime');

  // auto-fill current date
  if (treatmentDate) {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    treatmentDate.value = `${year}-${month}-${day}`;
  }

  // auto-fill current time
  if (treatmentTime) {
    const now = new Date();
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    treatmentTime.value = `${hours}:${minutes}`;
  }

  // show patient info when selected
  if (patientSelect && patientInfo) {
    patientSelect.addEventListener('change', () => {
      if (patientSelect.value) {
        patientInfo.style.display = 'block';
        
        const option = patientSelect.options[patientSelect.selectedIndex];
        const text = option.text;
        
        document.getElementById('infoName').textContent = text.split('–')[0].trim();
        document.getElementById('infoWard').textContent = 'AMU';
        document.getElementById('infoConsultant').textContent = 'Dr. R. Morgan';
      } else {
        patientInfo.style.display = 'none';
      }
    });
  }

  // form submission
  if (submitBtn) {
    submitBtn.addEventListener('click', (e) => {
      e.preventDefault();
      
      const patientForm = document.getElementById('patientForm');
      const treatmentForm = document.getElementById('treatmentForm');
      
      if (patientForm.checkValidity() && treatmentForm.checkValidity()) {
        if (successAlert) {
          successAlert.style.display = 'flex';
          
          setTimeout(() => {
            successAlert.style.display = 'none';
            patientForm.reset();
            treatmentForm.reset();
            patientInfo.style.display = 'none';
            
            // Reset date and time after form reset
            if (treatmentDate) {
              const now = new Date();
              const year = now.getFullYear();
              const month = String(now.getMonth() + 1).padStart(2, '0');
              const day = String(now.getDate()).padStart(2, '0');
              treatmentDate.value = `${year}-${month}-${day}`;
            }
            
            if (treatmentTime) {
              const now = new Date();
              const hours = String(now.getHours()).padStart(2, '0');
              const minutes = String(now.getMinutes()).padStart(2, '0');
              treatmentTime.value = `${hours}:${minutes}`;
            }
          }, 2500);
        }
      } else {
        patientForm.reportValidity();
        treatmentForm.reportValidity();
      }
    });
  }

  // search treatments table
  if (treatmentSearch && treatmentsTable) {
    treatmentSearch.addEventListener('input', () => {
      const query = treatmentSearch.value.toLowerCase().trim();
      const rows = treatmentsTable.tBodies[0].rows;
      let visible = 0;

      Array.from(rows).forEach(row => {
        const patient = row.cells[0].textContent.toLowerCase();
        const treatment = row.cells[2].textContent.toLowerCase();

        const match = query === '' || patient.includes(query) || treatment.includes(query);

        row.style.display = match ? '' : 'none';
        if (match) visible++;
      });

      if (noResults) {
        noResults.style.display = visible === 0 ? 'block' : 'none';
      }
    });
  }
});