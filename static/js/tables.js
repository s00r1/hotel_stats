document.addEventListener('DOMContentLoaded', () => {
  const tables = document.querySelectorAll('.sortable-table');

  // DataTables disponible -> initialisation classique
  if (typeof window.DataTable !== 'undefined') {
    const opts = {
      ordering: true,
      order: [],
      language: { url: 'https://cdn.datatables.net/plug-ins/2.0.8/i18n/fr-FR.json' },
      columnDefs: [{ targets: 'no-sort', orderable: false }]
    };
    tables.forEach(table => new DataTable(table, opts));
    return;
  }

  // Fallback léger : tri basique en JavaScript quand DataTables est absent
  tables.forEach(table => {
    const ths = table.querySelectorAll('th');
    ths.forEach((th, idx) => {
      if (th.classList.contains('no-sort')) return;
      th.style.cursor = 'pointer';
      th.addEventListener('click', () => {
        const tbody = table.tBodies[0];
        const rows = Array.from(tbody.querySelectorAll('tr'));
        const dir = th.dataset.sortDir === 'asc' ? 'desc' : 'asc';
        rows.sort((a, b) => {
          const aCell = a.children[idx];
          const bCell = b.children[idx];
          const aVal = aCell.dataset.order ?? aCell.textContent.trim();
          const bVal = bCell.dataset.order ?? bCell.textContent.trim();
          const aNum = parseFloat(aVal);
          const bNum = parseFloat(bVal);
          let cmp;
          if (!isNaN(aNum) && !isNaN(bNum)) {
            cmp = aNum - bNum;
          } else {
            cmp = aVal.localeCompare(bVal, undefined, { numeric: true, sensitivity: 'base' });
          }
          return dir === 'asc' ? cmp : -cmp;
        });
        rows.forEach(r => tbody.appendChild(r));
        ths.forEach(h => h.dataset.sortDir = '');
        th.dataset.sortDir = dir;
      });
    });
  });
});

