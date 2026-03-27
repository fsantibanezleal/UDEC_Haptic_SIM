/**
 * Main application for UDEC Haptic SIM.
 *
 * Uses REST API for ALL interactions (reliable, no WebSocket dependency).
 * Keyboard WASD+QE moves probe, Arrow keys move selected body,
 * Auto Demo animates the scene.
 */
(function () {
    'use strict';

    const probePos = { x: 0, y: 0, z: 2 };
    const PROBE_SPEED = 0.06;
    const BODY_STEP = 0.12;
    const keysDown = {};
    let demoRunning = false;
    let demoTime = 0;
    let renderer = null;
    let statusEl = null;

    window.addEventListener('DOMContentLoaded', init);

    // ---- Visible status logging ----
    function log(msg) {
        console.log('[HapticSIM]', msg);
        if (statusEl) statusEl.textContent = msg;
    }

    function logError(msg) {
        console.error('[HapticSIM]', msg);
        if (statusEl) {
            statusEl.textContent = 'ERROR: ' + msg;
            statusEl.style.color = '#f85149';
        }
    }

    // ---- API helpers ----
    async function apiGet(path) {
        const resp = await fetch(path);
        if (!resp.ok) throw new Error(`GET ${path}: ${resp.status}`);
        return resp.json();
    }

    async function apiPost(path, body) {
        const resp = await fetch(path, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        if (!resp.ok) throw new Error(`POST ${path}: ${resp.status}`);
        return resp.json();
    }

    // ---- Core: fetch scene and render ----
    async function fetchAndRender() {
        try {
            const state = await apiGet('/api/scene');
            if (!state || !state.bodies) {
                logError('Invalid scene state');
                return;
            }
            renderer.updateFromState(state);
            log(`Scene: ${state.bodies.length} bodies, ${state.collision_count} collisions`);
        } catch (e) {
            logError('Fetch failed: ' + e.message);
        }
    }

    // ---- Init ----
    async function init() {
        const canvas = document.getElementById('renderCanvas');
        if (!canvas) { console.error('No canvas'); return; }

        // Status element for debug messages
        statusEl = document.getElementById('wsStatus');

        // Check Three.js loaded
        if (typeof THREE === 'undefined') {
            logError('Three.js failed to load from CDN!');
            canvas.style.background = '#1a0000';
            return;
        }

        log('Initializing...');

        try {
            renderer = new Renderer3D(canvas);
        } catch (e) {
            logError('Renderer init failed: ' + e.message);
            return;
        }

        // Load initial scene via REST
        log('Loading scene...');
        await fetchAndRender();

        // ---- Keyboard ----
        window.addEventListener('keydown', (e) => {
            keysDown[e.code] = true;
            if (['ArrowUp','ArrowDown','ArrowLeft','ArrowRight',
                 'PageUp','PageDown','Space'].includes(e.code)) {
                e.preventDefault();
            }
        });
        window.addEventListener('keyup', (e) => { keysDown[e.code] = false; });

        // ---- Buttons ----
        setupButtons();
        setupSliders();
        setupToggles();
        setupTransformButtons();

        // ---- Main loop ----
        setInterval(mainLoop, 80);

        // ---- Render loop ----
        (function animate() {
            requestAnimationFrame(animate);
            renderer.render();
        })();

        renderer._handleResize();
        log('Ready — WASD moves probe, arrows move body');
    }

    // ---- Main loop (keyboard + demo) ----
    async function mainLoop() {
        let needsUpdate = false;

        // Probe movement (WASD + QE)
        if (keysDown['KeyW']) { probePos.z -= PROBE_SPEED; needsUpdate = true; }
        if (keysDown['KeyS']) { probePos.z += PROBE_SPEED; needsUpdate = true; }
        if (keysDown['KeyA']) { probePos.x -= PROBE_SPEED; needsUpdate = true; }
        if (keysDown['KeyD']) { probePos.x += PROBE_SPEED; needsUpdate = true; }
        if (keysDown['KeyQ']) { probePos.y -= PROBE_SPEED; needsUpdate = true; }
        if (keysDown['KeyE']) { probePos.y += PROBE_SPEED; needsUpdate = true; }

        probePos.x = Math.max(-3, Math.min(3, probePos.x));
        probePos.y = Math.max(-3, Math.min(3, probePos.y));
        probePos.z = Math.max(-3, Math.min(3, probePos.z));

        if (needsUpdate) {
            syncSliders();
            try {
                await apiPost('/api/probe', probePos);
                await fetchAndRender();
            } catch (e) { logError(e.message); }
        }

        // Body movement (Arrow keys)
        const idx = getSelectedBody();
        let bdx = 0, bdy = 0, bdz = 0;
        if (keysDown['ArrowLeft']) bdx = -BODY_STEP;
        if (keysDown['ArrowRight']) bdx = BODY_STEP;
        if (keysDown['ArrowUp']) bdz = -BODY_STEP;
        if (keysDown['ArrowDown']) bdz = BODY_STEP;
        if (keysDown['PageUp']) bdy = BODY_STEP;
        if (keysDown['PageDown']) bdy = -BODY_STEP;

        if (bdx || bdy || bdz) {
            try {
                await apiPost('/api/transform', {
                    body_index: idx, transform_type: 'translate',
                    dx: bdx, dy: bdy, dz: bdz,
                });
                await fetchAndRender();
            } catch (e) { logError(e.message); }
        }

        // Auto demo
        if (demoRunning) {
            demoTime += 0.08;
            await runDemo();
        }
    }

    function getSelectedBody() {
        const sel = document.getElementById('bodySelect');
        return sel ? (parseInt(sel.value) || 0) : 0;
    }

    function syncSliders() {
        const map = { X: probePos.x, Y: probePos.y, Z: probePos.z };
        for (const [axis, val] of Object.entries(map)) {
            const sl = document.getElementById('probe' + axis);
            const sp = document.getElementById('probe' + axis + 'Val');
            if (sl) sl.value = val.toFixed(2);
            if (sp) sp.textContent = val.toFixed(2);
        }
    }

    // ---- Demo ----
    async function runDemo() {
        const cycle = demoTime % 10;
        try {
            if (cycle < 3) {
                await apiPost('/api/transform', {
                    body_index: 0, transform_type: 'translate',
                    dx: 0.05, dy: 0, dz: 0,
                });
            } else if (cycle < 6) {
                const t = (cycle - 3) / 3;
                probePos.x = -1 + t * 2;
                probePos.y = 0.3;
                probePos.z = 0.3;
                syncSliders();
                await apiPost('/api/probe', probePos);
            } else if (cycle < 9) {
                const a = (cycle - 6) * Math.PI * 0.7;
                probePos.x = 1.2 * Math.cos(a);
                probePos.z = 1.2 * Math.sin(a);
                probePos.y = 0.3 + 0.4 * Math.sin(a * 2);
                syncSliders();
                await apiPost('/api/probe', probePos);
            } else {
                await apiPost('/api/scene/reset', {});
            }
            await fetchAndRender();
        } catch (e) { logError(e.message); }
    }

    // ---- Button setup ----
    function setupButtons() {
        const resetBtn = document.getElementById('resetBtn');
        if (resetBtn) {
            resetBtn.addEventListener('click', async () => {
                try {
                    await apiPost('/api/scene/reset', {});
                    await fetchAndRender();
                    log('Scene reset');
                } catch (e) { logError(e.message); }
            });
        }

        const demoBtn = document.getElementById('demoBtn');
        if (demoBtn) {
            demoBtn.addEventListener('click', () => {
                demoRunning = !demoRunning;
                demoBtn.textContent = demoRunning ? '■ Stop Demo' : '▶ Auto Demo';
                demoBtn.classList.toggle('active', demoRunning);
                demoTime = 0;
                log(demoRunning ? 'Demo started' : 'Demo stopped');
            });
        }

        // Help
        const helpModal = document.getElementById('helpModal');
        const helpBtn = document.getElementById('helpBtn');
        const closeHelp = document.getElementById('closeHelp');
        if (helpBtn) helpBtn.addEventListener('click', () => helpModal.classList.remove('hidden'));
        if (closeHelp) closeHelp.addEventListener('click', () => helpModal.classList.add('hidden'));
        if (helpModal) helpModal.addEventListener('click', (e) => {
            if (e.target === helpModal) helpModal.classList.add('hidden');
        });

        // File upload
        const objFile = document.getElementById('objFile');
        if (objFile) {
            objFile.addEventListener('change', async () => {
                if (!objFile.files.length) return;
                const fd = new FormData();
                fd.append('file', objFile.files[0]);
                try {
                    await fetch('/api/scene/load', { method: 'POST', body: fd });
                    await fetchAndRender();
                } catch (e) { logError(e.message); }
                objFile.value = '';
            });
        }
    }

    function setupSliders() {
        // Probe sliders
        ['X', 'Y', 'Z'].forEach(axis => {
            const sl = document.getElementById('probe' + axis);
            if (!sl) return;
            sl.addEventListener('input', async () => {
                const val = parseFloat(sl.value);
                document.getElementById('probe' + axis + 'Val').textContent = val.toFixed(2);
                probePos[axis.toLowerCase()] = val;
                try {
                    await apiPost('/api/probe', probePos);
                    await fetchAndRender();
                } catch (e) { logError(e.message); }
            });
        });

        // Physics sliders
        [
            { id: 'stiffness', key: 'stiffness', valId: 'stiffnessVal' },
            { id: 'damping', key: 'damping', valId: 'dampingVal' },
            { id: 'maxForce', key: 'max_force', valId: 'maxForceVal' },
            { id: 'contactDist', key: 'contact_threshold', valId: 'contactDistVal' },
        ].forEach(({ id, key, valId }) => {
            const sl = document.getElementById(id);
            if (!sl) return;
            sl.addEventListener('input', async () => {
                document.getElementById(valId).textContent = parseFloat(sl.value).toFixed(2);
                try {
                    const body = {};
                    body[key] = parseFloat(sl.value);
                    await apiPost('/api/settings', body);
                } catch (e) { logError(e.message); }
            });
        });
    }

    function setupToggles() {
        const showOctree = document.getElementById('showOctree');
        const depthRow = document.getElementById('octreeDepthRow');
        if (showOctree) {
            showOctree.addEventListener('change', async () => {
                renderer.setShowOctree(showOctree.checked);
                if (depthRow) depthRow.style.display = showOctree.checked ? 'flex' : 'none';
                try {
                    await apiPost('/api/settings', { show_octree: showOctree.checked });
                    await fetchAndRender();
                    log(showOctree.checked ? 'Octree visible' : 'Octree hidden');
                } catch (e) { logError(e.message); }
            });
        }
        const octreeDepth = document.getElementById('octreeDepth');
        if (octreeDepth) {
            octreeDepth.addEventListener('input', async () => {
                document.getElementById('octreeDepthVal').textContent = octreeDepth.value;
                try {
                    await apiPost('/api/settings', { octree_max_depth: parseInt(octreeDepth.value) });
                    await fetchAndRender();
                } catch (e) { logError(e.message); }
            });
        }

        const showAABB = document.getElementById('showAABB');
        if (showAABB) {
            showAABB.addEventListener('change', () => {
                renderer.setShowAABB(showAABB.checked);
            });
        }

        const showForce = document.getElementById('showForce');
        if (showForce) {
            showForce.addEventListener('change', () => {
                renderer.showForce = showForce.checked;
            });
        }
    }

    function setupTransformButtons() {
        document.querySelectorAll('.transform-buttons button').forEach(btn => {
            btn.addEventListener('click', async () => {
                const idx = getSelectedBody();
                const dir = btn.dataset.dir;
                const type = btn.dataset.type;
                const s = 0.2;

                const params = {
                    body_index: idx,
                    transform_type: type,
                    dx: 0, dy: 0, dz: 0,
                    angle: 0, axis_x: 0, axis_y: 1, axis_z: 0,
                };

                if (type === 'translate') {
                    if (dir === 'x+') params.dx = s;
                    else if (dir === 'x-') params.dx = -s;
                    else if (dir === 'y+') params.dy = s;
                    else if (dir === 'y-') params.dy = -s;
                    else if (dir === 'z+') params.dz = s;
                    else if (dir === 'z-') params.dz = -s;
                } else if (type === 'rotate') {
                    if (dir === 'ry+') params.angle = 15;
                    else if (dir === 'ry-') params.angle = -15;
                }

                try {
                    await apiPost('/api/transform', params);
                    await fetchAndRender();
                    log(`${type} body ${idx}: ${dir}`);
                } catch (e) { logError(e.message); }
            });
        });
    }
})();
