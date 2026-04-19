document.addEventListener('DOMContentLoaded', () => {
  const searchInput = document.getElementById('teamSearch');
  const table = document.getElementById('teamsTable');
  const noResults = document.getElementById('teamsNoResults');

  function applyFilter() {
    if (!table) return;
    const query = (searchInput?.value || '').toLowerCase().trim();
    const rows = table.tBodies[0].rows;
    let visible = 0;
    Array.from(rows).forEach(row => {
      const teamName = row.cells[0].textContent.toLowerCase();
      const leadConsultant = row.cells[1].textContent.toLowerCase();
      const matchesText = query === '' || teamName.includes(query) || leadConsultant.includes(query);
      row.style.display = matchesText ? '' : 'none';
      if (matchesText) visible++;
    });
    if (noResults) noResults.style.display = visible === 0 ? 'block' : 'none';
  }

  if (searchInput) searchInput.addEventListener('input', applyFilter);
  applyFilter();
});

function openAddTeamModal() {
  const modal = document.getElementById('addTeamModal');
  if (modal) modal.style.display = 'block';
}

function closeAddTeamModal() {
  const modal = document.getElementById('addTeamModal');
  if (modal) modal.style.display = 'none';
}

function closeEditTeamModal() {
  const modal = document.getElementById('editTeamModal');
  if (modal) modal.style.display = 'none';
}