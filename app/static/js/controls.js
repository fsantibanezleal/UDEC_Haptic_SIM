/**
 * UI Controls handler.
 *
 * Binds slider, button, and checkbox events to the WebSocket
 * and renderer, keeping the simulation parameters in sync.
 */
class Controls {
    constructor(ws, renderer) {
        this.ws = ws;
        this.renderer = renderer;
        this._setupProbeSliders();
        this._setupPhysicsSliders();
        this._setupDisplayToggles();
        this._setupButtons();
        this._setupTransformButtons();
        this._setupFileUpload();
        this._setupHelpModal();
    }

    // ---- Probe sliders ----

    _setupProbeSliders() {
        const axes = ['X', 'Y', 'Z'];
        axes.forEach(axis => {
            const slider = document.getElementById(`probe${axis}`);
            const valSpan = document.getElementById(`probe${axis}Val`);
            if (!slider) return;

            slider.addEventListener('input', () => {
                valSpan.textContent = parseFloat(slider.value).toFixed(2);
                this._sendProbe();
            });
        });
    }

    _sendProbe() {
        const x = parseFloat(document.getElementById('probeX').value);
        const y = parseFloat(document.getElementById('probeY').value);
        const z = parseFloat(document.getElementById('probeZ').value);
        this.ws.sendProbe(x, y, z);
    }

    // ---- Physics parameter sliders ----

    _setupPhysicsSliders() {
        const params = [
            { id: 'stiffness', key: 'stiffness', valId: 'stiffnessVal' },
            { id: 'damping', key: 'damping', valId: 'dampingVal' },
            { id: 'maxForce', key: 'max_force', valId: 'maxForceVal' },
            { id: 'contactDist', key: 'contact_threshold', valId: 'contactDistVal' },
        ];

        params.forEach(({ id, key, valId }) => {
            const slider = document.getElementById(id);
            const valSpan = document.getElementById(valId);
            if (!slider) return;

            slider.addEventListener('input', () => {
                valSpan.textContent = parseFloat(slider.value).toFixed(2);
                const settings = {};
                settings[key] = parseFloat(slider.value);
                this.ws.sendSettings(settings);
            });
        });
    }

    // ---- Display toggles ----

    _setupDisplayToggles() {
        const showOctree = document.getElementById('showOctree');
        if (showOctree) {
            showOctree.addEventListener('change', () => {
                this.renderer.setShowOctree(showOctree.checked);
                this.ws.sendSettings({ show_octree: showOctree.checked });
            });
        }

        const showAABB = document.getElementById('showAABB');
        if (showAABB) {
            showAABB.addEventListener('change', () => {
                this.renderer.setShowAABB(showAABB.checked);
            });
        }

        const showForce = document.getElementById('showForce');
        if (showForce) {
            showForce.addEventListener('change', () => {
                this.renderer.showForce = showForce.checked;
            });
        }
    }

    // ---- Scene buttons ----

    _setupButtons() {
        const resetBtn = document.getElementById('resetBtn');
        if (resetBtn) {
            resetBtn.addEventListener('click', () => {
                this.ws.sendReset();
            });
        }
    }

    // ---- Transform buttons ----

    _setupTransformButtons() {
        const step = 0.15;
        const rotStep = 15;

        document.querySelectorAll('.transform-buttons button').forEach(btn => {
            btn.addEventListener('click', () => {
                const sel = document.getElementById('bodySelect');
                const idx = sel ? parseInt(sel.value) : 0;
                const dir = btn.dataset.dir;
                const type = btn.dataset.type;

                if (type === 'translate') {
                    const params = { dx: 0, dy: 0, dz: 0 };
                    if (dir === 'x+') params.dx = step;
                    else if (dir === 'x-') params.dx = -step;
                    else if (dir === 'y+') params.dy = step;
                    else if (dir === 'y-') params.dy = -step;
                    else if (dir === 'z+') params.dz = step;
                    else if (dir === 'z-') params.dz = -step;
                    this.ws.sendTransform(idx, 'translate', params);
                } else if (type === 'rotate') {
                    const params = { axis_x: 0, axis_y: 1, axis_z: 0 };
                    if (dir === 'ry+') params.angle = rotStep;
                    else if (dir === 'ry-') params.angle = -rotStep;
                    this.ws.sendTransform(idx, 'rotate', params);
                }
            });
        });
    }

    // ---- File upload ----

    _setupFileUpload() {
        const input = document.getElementById('objFile');
        if (!input) return;

        input.addEventListener('change', async () => {
            if (!input.files.length) return;
            const file = input.files[0];
            const formData = new FormData();
            formData.append('file', file);

            try {
                const resp = await fetch('/api/scene/load', {
                    method: 'POST',
                    body: formData,
                });
                const result = await resp.json();
                console.log('OBJ load result:', result);
                // Request fresh state
                this.ws.requestStep();
            } catch (e) {
                console.error('Failed to upload OBJ:', e);
            }

            input.value = '';
        });
    }

    // ---- Help modal ----

    _setupHelpModal() {
        const modal = document.getElementById('helpModal');
        const openBtn = document.getElementById('helpBtn');
        const closeBtn = document.getElementById('closeHelp');

        if (openBtn && modal) {
            openBtn.addEventListener('click', () => {
                modal.classList.remove('hidden');
            });
        }

        if (closeBtn && modal) {
            closeBtn.addEventListener('click', () => {
                modal.classList.add('hidden');
            });
        }

        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.classList.add('hidden');
                }
            });
        }
    }
}

window.Controls = Controls;
