document.addEventListener('DOMContentLoaded', () => {
  if (typeof window.DataTable === 'undefined') {
    console.error('DataTables pas chargé !');
    return;
  }
  const opts = {
    ordering: true,
    order: [],
    language: { url: 'https://cdn.datatables.net/plug-ins/2.0.8/i18n/fr-FR.json' },
    columnDefs: [{ targets: -1, orderable: false }]
  };
  if (document.querySelector('#personsTable')) new DataTable('#personsTable', opts);
  if (document.querySelector('#familiesTable')) new DataTable('#familiesTable', opts);
});

