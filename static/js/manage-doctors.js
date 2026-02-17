document.addEventListener('DOMContentLoaded', () => {
  const addDoctorBtn = document.getElementById('addDoctorBtn');
  const doctorModal = document.getElementById('doctorModal');
  const modalClose = document.getElementById('modalClose');
  const modalCancel = document.getElementById('modalCancel');
  const modalTitle = document.getElementById('modalTitle');
  const doctorForm = document.getElementById('doctorForm');
  
  const doctorSearch = document.getElementById('doctorSearch');
  const gradeFilter = document.getElementById('gradeFilter');
  const doctorsTable = document.getElementById('doctorsTable');
  const noResults = document.getElementById('doctorsNoResults');

  // open add doctor modal
  if (addDoctorBtn && doctorModal) {
    addDoctorBtn.addEventListener('click', () => {
      modalTitle.textContent = 'Add new doctor';
      doctorForm.reset();
      doctorModal.classList.add('open');
    });
  }

  // close modal
  if (modalClose && doctorModal) {
    modalClose.addEventListener('click', () => {
      doctorModal.classList.remove('open');
    });
  }

  if (modalCancel && doctorModal) {
    modalCancel.addEventListener('click', () => {
      doctorModal.classList.remove('open');
    });
  }

  // close modal on outside click
  if (doctorModal) {
    doctorModal.addEventListener('click', (e) => {
      if (e.target === doctorModal) {
        doctorModal.classList.remove('open');
      }
    });
  }

  // open edit doctor modal
  document.querySelectorAll('.edit-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      modalTitle.textContent = 'Edit doctor';
      // In a real app, you'd load the doctor's data here
      doctorModal.classList.add('open');
    });
  });

  // form submit
  if (doctorForm) {
    doctorForm.addEventListener('submit', (e) => {
      e.preventDefault();
      
      if (doctorForm.checkValidity()) {
        // In a real app, save the data here
        alert('Doctor saved successfully!');
        doctorModal.classList.remove('open');
        doctorForm.reset();
      } else {
        doctorForm.reportValidity();
      }
    });
  }

  // search and filter doctors
  function applyFilter() {
    if (!doctorsTable) return;

    const query = (doctorSearch?.value || '').toLowerCase().trim();
    const grade = gradeFilter ? gradeFilter.value : 'all';

    const rows = doctorsTable.tBodies[0].rows;
    let visible = 0;

    Array.from(rows).forEach(row => {
      const name = row.cells[0].textContent.toLowerCase();
      const gradeText = row.cells[1].textContent.toLowerCase();
      const specialty = row.cells[2].textContent.toLowerCase();

      const matchesText =
        query === '' ||
        name.includes(query) ||
        gradeText.includes(query) ||
        specialty.includes(query);

      const matchesGrade =
        grade === 'all' ||
        (grade === 'Consultant' && gradeText.includes('consultant')) ||
        (grade === 'Registrar' && gradeText.includes('registrar')) ||
        (grade === 'Junior' && (gradeText.includes('fy') || gradeText.includes('ct')));

      const show = matchesText && matchesGrade;
      row.style.display = show ? '' : 'none';
      if (show) visible++;
    });

    if (noResults) {
      noResults.style.display = visible === 0 ? 'block' : 'none';
    }
  }

  if (doctorSearch) doctorSearch.addEventListener('input', applyFilter);
  if (gradeFilter) gradeFilter.addEventListener('change', applyFilter);
});