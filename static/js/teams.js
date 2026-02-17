document.addEventListener('DOMContentLoaded', () => {
  console.log('Teams.js loaded - teams specific functionality only');
  
  const searchInput = document.getElementById('teamSearch');
  const teamFilter = document.getElementById('teamFilter');
  const table = document.getElementById('teamsTable');
  const noResults = document.getElementById('teamsNoResults');

  // Filter by name / grade / specialty and team
  function applyFilter() {
    if (!table) return;

    const query = (searchInput?.value || '').toLowerCase().trim();
    const teamValue = teamFilter ? teamFilter.value : 'all';

    const rows = table.tBodies[0].rows;
    let visible = 0;

    Array.from(rows).forEach(row => {
      const name = row.cells[0].textContent.toLowerCase();
      const grade = row.cells[1].textContent.toLowerCase();
      const specialty = row.cells[2].textContent.toLowerCase();
      const team = row.cells[3].textContent;

      const matchesText =
        query === '' ||
        name.includes(query) ||
        grade.includes(query) ||
        specialty.includes(query);

      const matchesTeam =
        teamValue === 'all' || team === teamValue;

      const show = matchesText && matchesTeam;
      row.style.display = show ? '' : 'none';
      if (show) visible++;
    });

    if (noResults) {
      noResults.style.display = visible === 0 ? 'block' : 'none';
    }
  }

  // Add event listeners
  if (searchInput) searchInput.addEventListener('input', applyFilter);
  if (teamFilter) teamFilter.addEventListener('change', applyFilter);
  
  // Initial filter
  applyFilter();
});

// Modal functions for teams page
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