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

  if (addDoctorBtn && doctorModal) {
    addDoctorBtn.addEventListener('click', () => {
      modalTitle.textContent = 'Add new doctor';
      doctorForm.reset();
      document.getElementById('doctorOnDuty').checked = true;
      delete doctorForm.dataset.editingId;
      doctorModal.classList.add('open');
    });
  }

  document.querySelectorAll('.edit-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const doctorId = btn.dataset.id;
      if (!doctorId) return;

      fetch(`/api/doctors/${doctorId}`)
        .then(response => response.json())
        .then(doctor => {
          document.getElementById('doctorName').value = doctor.name;
          document.getElementById('doctorGrade').value = doctor.grade;
          document.getElementById('doctorSpecialty').value = doctor.specialty;
          document.getElementById('doctorTeam').value = doctor.team_id || '';
          document.getElementById('doctorWard').value = doctor.ward_id || '';
          document.getElementById('doctorPager').value = doctor.pager || '';
          document.getElementById('doctorEmail').value = doctor.email || '';
          document.getElementById('doctorOnDuty').checked = doctor.on_duty == 1;

          doctorForm.dataset.editingId = doctorId;
          modalTitle.textContent = 'Edit doctor';
          doctorModal.classList.add('open');
        })
        .catch(() => {});
    });
  });

  if (modalClose && doctorModal) {
    modalClose.addEventListener('click', () => doctorModal.classList.remove('open'));
  }
  if (modalCancel && doctorModal) {
    modalCancel.addEventListener('click', () => doctorModal.classList.remove('open'));
  }
  if (doctorModal) {
    doctorModal.addEventListener('click', (e) => {
      if (e.target === doctorModal) doctorModal.classList.remove('open');
    });
  }

  if (doctorForm) {
    doctorForm.addEventListener('submit', (e) => {
      e.preventDefault();

      if (!doctorForm.checkValidity()) {
        doctorForm.reportValidity();
        return;
      }

      const formData = {
        name: document.getElementById('doctorName').value,
        grade: document.getElementById('doctorGrade').value,
        specialty: document.getElementById('doctorSpecialty').value,
        team_id: document.getElementById('doctorTeam').value || null,
        ward_id: document.getElementById('doctorWard').value || null,
        pager: document.getElementById('doctorPager').value,
        email: document.getElementById('doctorEmail').value,
        on_duty: document.getElementById('doctorOnDuty').checked ? 1 : 0
      };

      const editingId = doctorForm.dataset.editingId;
      const url = editingId ? `/api/doctors/${editingId}` : '/api/doctors';
      const method = editingId ? 'PUT' : 'POST';

      fetch(url, {
        method: method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          doctorModal.classList.remove('open');
          doctorForm.reset();
          delete doctorForm.dataset.editingId;
          window.location.reload();
        } else {
          alert('Error saving doctor');
        }
      })
      .catch(() => {
        alert('Error saving doctor');
      });
    });
  }

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
        (grade === 'Junior' && (gradeText.includes('fy') || gradeText.includes('ct') || gradeText.includes('junior')));

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