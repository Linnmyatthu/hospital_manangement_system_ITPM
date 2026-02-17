document.addEventListener('DOMContentLoaded', () => {
  const searchInput = document.getElementById('patientSearch');
  const statusFilter = document.getElementById('statusFilter');
  const table = document.getElementById('teamPatientsTable');
  const noResults = document.getElementById('patientsNoResults');

  // filter patients by name, age, ward, diagnosis and status
  function applyFilter() {
    if (!table) return;

    const query = (searchInput?.value || '').toLowerCase().trim();
    const status = statusFilter ? statusFilter.value : 'all';

    const rows = table.tBodies[0].rows;
    let visible = 0;

    Array.from(rows).forEach(row => {
      const name = row.cells[0].textContent.toLowerCase();
      const age = row.cells[1].textContent.toLowerCase();
      const ward = row.cells[3].textContent.toLowerCase();
      const diagnosis = row.cells[4].textContent.toLowerCase();
      const statusText = row.cells[7].textContent.trim();

      const matchesText =
        query === '' ||
        name.includes(query) ||
        age.includes(query) ||
        ward.includes(query) ||
        diagnosis.includes(query);

      const matchesStatus =
        status === 'all' || statusText === status;

      const show = matchesText && matchesStatus;
      row.style.display = show ? '' : 'none';
      if (show) visible++;
    });

    if (noResults) {
      noResults.style.display = visible === 0 ? 'block' : 'none';
    }
  }

  if (searchInput) searchInput.addEventListener('input', applyFilter);
  if (statusFilter) statusFilter.addEventListener('change', applyFilter);
});