document.addEventListener('DOMContentLoaded', () => {
  const palette = document.getElementById('layout-palette');
  if (!palette) return;

  function updateTextarea(floorDiv) {
    const table = floorDiv.querySelector('table');
    const textarea = floorDiv.querySelector('textarea');
    const rows = [];
    table.querySelectorAll('tr').forEach(tr => {
      const cells = [];
      tr.querySelectorAll('td').forEach(td => cells.push(td.textContent.trim()));
      rows.push(cells.join(','));
    });
    textarea.value = rows.join('\n');
  }

  function initCell(td, floorDiv) {
    td.addEventListener('dragover', e => e.preventDefault());
    td.addEventListener('drop', e => {
      e.preventDefault();
      const text = e.dataTransfer.getData('text/plain');
      if (text) {
        td.textContent = text;
        updateTextarea(floorDiv);
      }
    });
    td.addEventListener('dblclick', () => {
      const val = prompt('Nom de la pièce', td.textContent);
      if (val !== null) {
        td.textContent = val;
        updateTextarea(floorDiv);
      }
    });
  }

  function buildTable(floorDiv) {
    const textarea = floorDiv.querySelector('textarea');
    const wrapper = floorDiv.querySelector('.grid-wrapper');
    const data = textarea.value.trim()
      ? textarea.value.trim().split('\n').map(l => l.split(','))
      : [['']];
    const table = document.createElement('table');
    table.className = 'layout-grid';
    data.forEach(row => {
      const tr = document.createElement('tr');
      row.forEach(text => {
        const td = document.createElement('td');
        td.className = 'layout-cell';
        td.textContent = text;
        initCell(td, floorDiv);
        tr.appendChild(td);
      });
      table.appendChild(tr);
    });
    wrapper.innerHTML = '';
    wrapper.appendChild(table);
    updateTextarea(floorDiv);
  }

  function initFloor(floorDiv) {
    buildTable(floorDiv);
    floorDiv.querySelector('.add-row').addEventListener('click', () => {
      const table = floorDiv.querySelector('table');
      const cols = table.rows[0] ? table.rows[0].cells.length : 0;
      const tr = document.createElement('tr');
      for (let i = 0; i < cols; i++) {
        const td = document.createElement('td');
        td.className = 'layout-cell';
        initCell(td, floorDiv);
        tr.appendChild(td);
      }
      table.appendChild(tr);
      updateTextarea(floorDiv);
    });
    floorDiv.querySelector('.add-col').addEventListener('click', () => {
      const table = floorDiv.querySelector('table');
      const rows = table.rows.length;
      for (let i = 0; i < rows; i++) {
        const td = document.createElement('td');
        td.className = 'layout-cell';
        initCell(td, floorDiv);
        table.rows[i].appendChild(td);
      }
      updateTextarea(floorDiv);
    });
    floorDiv.querySelector('.remove-row').addEventListener('click', () => {
      const table = floorDiv.querySelector('table');
      if (table.rows.length > 0) {
        table.deleteRow(-1);
        updateTextarea(floorDiv);
      }
    });
    floorDiv.querySelector('.remove-col').addEventListener('click', () => {
      const table = floorDiv.querySelector('table');
      const rows = table.rows.length;
      if (rows > 0 && table.rows[0].cells.length > 0) {
        for (let i = 0; i < rows; i++) {
          table.rows[i].deleteCell(-1);
        }
        updateTextarea(floorDiv);
      }
    });
  }

  document.querySelectorAll('#floors .floor-item').forEach(initFloor);

  document.getElementById('add-floor').addEventListener('click', () => {
    const idx = document.querySelectorAll('#floors .floor-item').length;
    const div = document.createElement('div');
    div.className = 'floor-item border rounded p-2 mb-3';
    div.innerHTML = `
      <div class="mb-2">
        <label class="form-label">Nom de l'étage</label>
        <input type="text" class="form-control form-control-sm" name="floor_name_${idx}">
      </div>
      <div class="mb-2">
        <label class="form-label">Disposition</label>
        <div class="grid-wrapper mb-2"></div>
        <div class="mb-2 d-flex flex-wrap gap-2">
          <button type="button" class="btn btn-sm btn-outline-secondary add-row">Ajouter une ligne</button>
          <button type="button" class="btn btn-sm btn-outline-secondary add-col">Ajouter une colonne</button>
          <button type="button" class="btn btn-sm btn-outline-secondary remove-row">Supprimer une ligne</button>
          <button type="button" class="btn btn-sm btn-outline-secondary remove-col">Supprimer une colonne</button>
        </div>
        <textarea name="floor_rooms_${idx}" hidden></textarea>
      </div>
      <button type="button" class="btn btn-sm btn-outline-danger remove-floor">Supprimer</button>
    `;
    document.getElementById('floors').appendChild(div);
    initFloor(div);
  });

  document.getElementById('floors').addEventListener('click', e => {
    if (e.target.classList.contains('remove-floor')) {
      e.target.closest('.floor-item').remove();
    }
  });

  palette.querySelectorAll('.layout-item').forEach(item => {
    item.addEventListener('dragstart', e => {
      e.dataTransfer.setData('text/plain', item.dataset.value);
    });
  });
});
