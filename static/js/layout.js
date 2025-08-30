document.addEventListener('DOMContentLoaded', () => {
  const palette = document.getElementById('layout-palette');
  const floorNav = document.getElementById('floor-nav');
  const floorContainer = document.getElementById('floor-container');
  const layoutInput = document.getElementById('layout_json');
  if (!palette || !floorNav || !floorContainer || !layoutInput) return;

  let floors = [];
  let currentIndex = -1;

  function updateInput() {
    const data = floors.map(f => ({ name: f.name, data: f.canvas.toJSON() }));
    layoutInput.value = JSON.stringify(data);
  }

  function loadFloor(index) {
    currentIndex = index;
    floorNav.querySelectorAll('.nav-link').forEach((b, i) => {
      b.classList.toggle('active', i === index);
    });
    floorContainer.innerHTML = '';
    const canvasEl = document.createElement('canvas');
    canvasEl.width = floorContainer.clientWidth;
    canvasEl.height = floorContainer.clientHeight;
    floorContainer.appendChild(canvasEl);
    const canvas = new fabric.Canvas(canvasEl);
    floors[index].canvas = canvas;
    canvas.loadFromJSON(floors[index].data || {}, () => {
      canvas.renderAll();
    });
    canvas.on('object:modified', updateInput);
    canvas.on('object:added', updateInput);

    let isPanning = false;
    canvas.on('mouse:down', opt => {
      if (opt.e.shiftKey) {
        isPanning = true;
        canvas.selection = false;
      }
    });
    canvas.on('mouse:move', opt => {
      if (isPanning && opt && opt.e) {
        const e = opt.e;
        canvas.relativePan({ x: e.movementX, y: e.movementY });
      }
    });
    canvas.on('mouse:up', () => {
      canvas.selection = true;
      isPanning = false;
    });
    canvas.on('mouse:wheel', opt => {
      let zoom = canvas.getZoom();
      zoom *= 0.999 ** opt.e.deltaY;
      if (zoom > 4) zoom = 4;
      if (zoom < 0.2) zoom = 0.2;
      canvas.zoomToPoint({ x: opt.e.offsetX, y: opt.e.offsetY }, zoom);
      opt.e.preventDefault();
      opt.e.stopPropagation();
    });

    document.addEventListener('keydown', e => {
      if (e.key === 'Delete') {
        const obj = canvas.getActiveObject();
        if (obj) {
          canvas.remove(obj);
          updateInput();
        }
      } else if ((e.ctrlKey || e.metaKey) && e.key === 'd') {
        const obj = canvas.getActiveObject();
        if (obj) {
          const clone = fabric.util.object.clone(obj);
          clone.set({ left: obj.left + 10, top: obj.top + 10 });
          canvas.add(clone);
          updateInput();
        }
      }
    });

    canvas.on('mouse:dblclick', e => {
      const obj = e.target;
      if (obj && obj.type === 'group') {
        const text = obj.item(1); // second item is text
        const val = prompt('Nom de la pièce', text.text);
        if (val !== null) {
          text.text = val;
          canvas.requestRenderAll();
          updateInput();
        }
      }
    });
  }

  function addFloor(name, data) {
    const floor = { name: name || `Étage ${floors.length + 1}`, data: data || {} };
    floors.push(floor);
    const li = document.createElement('li');
    li.className = 'nav-item';
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'nav-link';
    btn.textContent = floor.name;
    btn.addEventListener('click', () => loadFloor(floors.indexOf(floor)));
    li.appendChild(btn);
    floorNav.appendChild(li);
    loadFloor(floors.length - 1);
    updateInput();
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
    const type = e.dataTransfer.getData('type');
    const label = e.dataTransfer.getData('label') || type;
    const canvas = floors[currentIndex].canvas;
    const rect = new fabric.Rect({ width: 80, height: 40, fill: '#fff', stroke: '#000', strokeWidth: 1 });
    const text = new fabric.Text(label, { fontSize: 14, originX: 'center', originY: 'center' });
    const group = new fabric.Group([rect, text], { left: e.offsetX, top: e.offsetY });
    canvas.add(group);
    updateInput();
  });

  // Snap to grid (10px)
  function snapToGrid(value) {
    return Math.round(value / 10) * 10;
  }
  function applySnapping(opt) {
    opt.target.set({
      left: snapToGrid(opt.target.left),
      top: snapToGrid(opt.target.top)
    });
  }
  function attachSnapping(canvas) {
    canvas.on('object:moving', applySnapping);
  }

  // Load from existing data
  try {
    const initial = JSON.parse(layoutInput.value || '[]');
    if (initial.length) {
      initial.forEach(f => addFloor(f.name, f.data));
      floors.forEach(f => attachSnapping(f.canvas));
    } else {
      addFloor();
      attachSnapping(floors[0].canvas);
    }
  } catch {
    addFloor();
    attachSnapping(floors[0].canvas);
  }
});

