document.addEventListener('DOMContentLoaded', () => {
  const commonOpts = {
    ordering: true,
    order: [],
    language: { url: 'https://cdn.datatables.net/plug-ins/2.0.8/i18n/fr-FR.json' }
  };

  const init = (el) => {
    const opts = { ...commonOpts };
    const last = el.querySelector('thead th:last-child');
    if (last && last.textContent.trim() === 'Actions') {
      opts.columnDefs = [{ targets: -1, orderable: false }];
    }
    new DataTable(el, opts);
  };

  const persons = document.querySelector('#personsTable');
  if (persons) init(persons);

  const families = document.querySelector('#familiesTable');
  if (families) init(families);
});
