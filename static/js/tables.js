document.addEventListener('DOMContentLoaded', () => {
  if (typeof window.DataTable === 'undefined') {
    console.error('DataTables pas chargé !');
    return;
  }
  const opts = {
    ordering: true,
    order: [],
    language: { url: 'https://cdn.datatables.net/plug-ins/2.0.8/i18n/fr-FR.json' },
    columnDefs: [{ targets: 'no-sort', orderable: false }]
  };
  const pt = document.querySelector('#personsTable');
  if (pt) new DataTable(pt, opts);
  const ft = document.querySelector('#familiesTable');
  if (ft) new DataTable(ft, opts);
});

