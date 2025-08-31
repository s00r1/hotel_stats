document.addEventListener('DOMContentLoaded', () => {
  const palette = document.getElementById('layout-palette');
  const floorNav = document.getElementById('floor-nav');
  const floorContainer = document.getElementById('floor-container');
  const layoutInput = document.getElementById('layout_json');
  const widthInput = document.getElementById('cell_width');
  const heightInput = document.getElementById('cell_height');
  if (!palette || !floorNav || !floorContainer || !layoutInput) return;

  let floors = [];
  let currentIndex = -1;
  let selected = null;

  function updateInput() {
    const seen = new Set();
    const data = [];
    floors.forEach(f => {
      if (!f.stage) return;
      f.data = f.stage.toJSON();
      const key = f.name.trim().toLowerCase();
      if (seen.has(key)) return;
      seen.add(key);
      data.push({ name: f.name, data: f.data });
    });
    layoutInput.value = JSON.stringify(data);
  }

  function snap(v) {
    return Math.round(v / 10) * 10;
  }

  function setupGroup(group) {
    group.on('dragend', () => {
      group.position({ x: snap(group.x()), y: snap(group.y()) });
      updateInput();
    });
    group.on('dblclick', () => {
      const text = group.findOne('Text');
      const val = prompt('Nom de la pièce', text.text());
      if (val !== null) {
        text.text(val);
        updateInput();
      }
    });
    group.on('mousedown', () => {
      selected = group;
    });
  }

  function loadFloor(index) {
    currentIndex = index;
    floorNav.querySelectorAll('.nav-link').forEach((b, i) => {
      b.classList.toggle('active', i === index);
    });
    floorContainer.innerHTML = '';
    const stageData = floors[index].data;
    let stage;
    if (stageData) {
      stage = Konva.Node.create(stageData, floorContainer);
      stage.width(floorContainer.clientWidth);
      stage.height(floorContainer.clientHeight);
    } else {
      stage = new Konva.Stage({
        container: floorContainer,
        width: floorContainer.clientWidth,
        height: floorContainer.clientHeight
      });
      const layer = new Konva.Layer();
      stage.add(layer);
    }
    floors[index].stage = stage;
    stage.find('Group').each(g => setupGroup(g));

    stage.on('mousedown', e => {
      if (e.evt.shiftKey) {
        stage.draggable(true);
      }
    });
    stage.on('mouseup', () => stage.draggable(false));
    stage.on('wheel', e => {
      e.evt.preventDefault();
      const scaleBy = 1.05;
      const oldScale = stage.scaleX();
      const pointer = stage.getPointerPosition();
      const mousePointTo = {
        x: (pointer.x - stage.x()) / oldScale,
        y: (pointer.y - stage.y()) / oldScale
      };
      const newScale = e.evt.deltaY > 0 ? oldScale / scaleBy : oldScale * scaleBy;
      stage.scale({ x: newScale, y: newScale });
      const newPos = {
        x: pointer.x - mousePointTo.x * newScale,
        y: pointer.y - mousePointTo.y * newScale
      };
      stage.position(newPos);
      stage.batchDraw();
    });
    stage.on('click', e => {
      if (e.target === stage) {
        selected = null;
      }
    });
    updateInput();
  }

  function addFloor(name, data) {
    if (!name) {
      const existing = new Set(floors.map(f => f.name.trim().toLowerCase()));
      let idx = floors.length + 1;
      while (existing.has(`étage ${idx}`)) idx++;
      name = `Étage ${idx}`;
    }
    const floor = { name, data: data || null, stage: null };
    floors.push(floor);
    const li = document.createElement('li');
    li.className = 'nav-item d-flex align-items-center gap-1';
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'nav-link flex-grow-1';
    btn.textContent = floor.name;
    btn.addEventListener('click', () => loadFloor(floors.indexOf(floor)));
    const renameBtn = document.createElement('button');
    renameBtn.type = 'button';
    renameBtn.className = 'btn btn-sm btn-outline-secondary';
    renameBtn.innerHTML = '<i class="bi bi-pencil"></i>';
    renameBtn.addEventListener('click', () => {
      const val = prompt("Nom de l'étage", floor.name);
      if (val !== null && val.trim()) {
        floor.name = val.trim();
        btn.textContent = floor.name;
        updateInput();
      }
    });
    const deleteBtn = document.createElement('button');
    deleteBtn.type = 'button';
    deleteBtn.className = 'btn btn-sm btn-outline-danger';
    deleteBtn.innerHTML = '<i class="bi bi-trash"></i>';
    deleteBtn.addEventListener('click', () => {
      const idx = floors.indexOf(floor);
      if (idx !== -1) {
        floors.splice(idx, 1);
        li.remove();
        if (floors.length) {
          loadFloor(Math.min(idx, floors.length - 1));
        } else {
          currentIndex = -1;
          floorContainer.innerHTML = '';
        }
        updateInput();
      }
    });
    li.append(btn, renameBtn, deleteBtn);
    floorNav.appendChild(li);
    loadFloor(floors.length - 1);
  }

  document.getElementById('add-floor').addEventListener('click', () => addFloor());

  palette.querySelectorAll('.layout-item').forEach(item => {
    item.addEventListener('dragstart', e => {
      e.dataTransfer.setData('type', item.dataset.type);
      e.dataTransfer.setData('label', item.dataset.label || item.textContent.trim());
    });
  });

  floorContainer.addEventListener('dragover', e => e.preventDefault());
  floorContainer.addEventListener('drop', e => {
    e.preventDefault();
    if (currentIndex === -1) return;
    const stage = floors[currentIndex].stage;
    const layer = stage.findOne('Layer');
    const type = e.dataTransfer.getData('type');
    const label = e.dataTransfer.getData('label') || type;
    const group = new Konva.Group({ x: e.offsetX, y: e.offsetY, draggable: true });
    group.setAttr('type', type);
    const w = parseInt(widthInput?.value) || 80;
    const h = parseInt(heightInput?.value) || 40;
    const rect = new Konva.Rect({ width: w, height: h, stroke: '#000', fill: '#fff', strokeWidth: 1 });
    const text = new Konva.Text({ text: label, fontSize: 14, width: w, align: 'center' });
    text.y((h - text.height()) / 2);
    group.add(rect);
    group.add(text);
    layer.add(group);
    setupGroup(group);
    layer.draw();
    updateInput();
  });

  document.addEventListener('keydown', e => {
    if (e.key === 'Delete' && selected && currentIndex !== -1) {
      selected.destroy();
      floors[currentIndex].stage.batchDraw();
      selected = null;
      updateInput();
    } else if ((e.ctrlKey || e.metaKey) && e.key === 'd' && selected && currentIndex !== -1) {
      const clone = selected.clone({ x: selected.x() + 10, y: selected.y() + 10 });
      floors[currentIndex].stage.findOne('Layer').add(clone);
      setupGroup(clone);
      floors[currentIndex].stage.batchDraw();
      selected = clone;
      updateInput();
    }
  });

  try {
    const initial = JSON.parse(layoutInput.value || '[]');
    if (initial.length) {
      initial.forEach(f => addFloor(f.name, f.data));
    } else {
      addFloor();
    }
  } catch {
    addFloor();
  }
});

