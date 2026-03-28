/**
 * Three.js 3D renderer for the haptic simulation.
 *
 * Renders triangle meshes with per-face collision colouring,
 * octree wireframes, a probe cursor (sphere), and a force
 * vector (arrow helper).
 */
class Renderer3D {
    constructor(canvas) {
        this.canvas = canvas;

        // Three.js core
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x0d1117);

        this.camera = new THREE.PerspectiveCamera(
            60,
            canvas.clientWidth / canvas.clientHeight,
            0.01,
            100
        );
        this.camera.position.set(2, 2, 4);

        this.renderer = new THREE.WebGLRenderer({
            canvas: canvas,
            antialias: true,
        });
        this.renderer.setPixelRatio(window.devicePixelRatio);
        this.renderer.setSize(canvas.clientWidth, canvas.clientHeight);

        // Orbit controls
        this.controls = new THREE.OrbitControls(this.camera, canvas);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.1;
        this.controls.target.set(0, 0.5, 0);

        // Lighting
        const ambientLight = new THREE.AmbientLight(0x404050, 0.6);
        this.scene.add(ambientLight);

        const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
        dirLight.position.set(5, 8, 5);
        this.scene.add(dirLight);

        const backLight = new THREE.DirectionalLight(0x4488cc, 0.3);
        backLight.position.set(-3, -2, -5);
        this.scene.add(backLight);

        // Grid helper
        const grid = new THREE.GridHelper(6, 12, 0x30363d, 0x21262d);
        grid.position.y = -1.5;
        this.scene.add(grid);

        // Axes helper
        const axes = new THREE.AxesHelper(1.5);
        axes.position.set(-2.5, -1.5, -2.5);
        this.scene.add(axes);

        // Probe cursor
        const probeGeo = new THREE.SphereGeometry(0.08, 16, 16);
        const probeMat = new THREE.MeshPhongMaterial({
            color: 0xffd700,
            emissive: 0x664400,
        });
        this.probeMesh = new THREE.Mesh(probeGeo, probeMat);
        this.scene.add(this.probeMesh);

        // Force arrow
        this.forceArrow = new THREE.ArrowHelper(
            new THREE.Vector3(0, 1, 0),
            new THREE.Vector3(0, 0, 0),
            0.5,
            0xff4444,
            0.08,
            0.06
        );
        this.forceArrow.visible = false;
        this.scene.add(this.forceArrow);

        // Contact anchor marker
        const anchorGeo = new THREE.SphereGeometry(0.04, 8, 8);
        const anchorMat = new THREE.MeshBasicMaterial({ color: 0x00ff88 });
        this.anchorMesh = new THREE.Mesh(anchorGeo, anchorMat);
        this.anchorMesh.visible = false;
        this.scene.add(this.anchorMesh);

        // Spring line (probe to anchor)
        const springMat = new THREE.LineBasicMaterial({
            color: 0x00ff88,
            transparent: true,
            opacity: 0.5,
        });
        const springGeo = new THREE.BufferGeometry().setFromPoints([
            new THREE.Vector3(), new THREE.Vector3(),
        ]);
        this.springLine = new THREE.Line(springGeo, springMat);
        this.springLine.visible = false;
        this.scene.add(this.springLine);

        // Body mesh storage
        this.bodyMeshes = [];

        // Octree wireframes
        this.octreeGroup = new THREE.Group();
        this.octreeGroup.visible = false;
        this.scene.add(this.octreeGroup);

        // AABB wireframes
        this.aabbGroup = new THREE.Group();
        this.aabbGroup.visible = false;
        this.scene.add(this.aabbGroup);

        // Settings
        this.showForce = true;
        this.showNormals = false;

        // FPS tracking
        this._frameCount = 0;
        this._lastFpsTime = performance.now();
        this.fps = 0;

        // Handle resize
        this._onResize = this._handleResize.bind(this);
        window.addEventListener('resize', this._onResize);
    }

    /**
     * Update the scene from server state.
     */
    updateFromState(state) {
        this._updateBodies(state.bodies || []);
        this._updateProbe(state.probe);
        this._updateForce(state.force);

        if (state.octree_nodes) {
            this._updateOctree(state.octree_nodes);
        }

        // Update overlay
        const colEl = document.getElementById('collisionDisplay');
        if (colEl) colEl.textContent = `Collisions: ${state.collision_count || 0}`;

        const forceEl = document.getElementById('forceDisplay');
        if (forceEl) {
            const mag = state.force ? state.force.magnitude : 0;
            forceEl.textContent = `Force: ${mag.toFixed(3)} N`;
        }
    }

    _updateBodies(bodies) {
        // Remove old meshes
        for (const m of this.bodyMeshes) {
            this.scene.remove(m);
            if (m.geometry) m.geometry.dispose();
            if (m.material) {
                if (Array.isArray(m.material)) {
                    m.material.forEach(mat => mat.dispose());
                } else {
                    m.material.dispose();
                }
            }
        }
        this.bodyMeshes = [];

        // Clear AABB
        while (this.aabbGroup.children.length > 0) {
            const c = this.aabbGroup.children[0];
            this.aabbGroup.remove(c);
            if (c.geometry) c.geometry.dispose();
            if (c.material) c.material.dispose();
        }

        for (const body of bodies) {
            const verts = body.vertices;
            const faces = body.faces;
            const color = body.color;
            const collisionFaces = new Set(body.collision_faces);

            const geometry = new THREE.BufferGeometry();

            // Build per-face vertices (unindexed for per-face coloring)
            const positions = [];
            const colors = [];

            const baseColor = new THREE.Color(color[0], color[1], color[2]);
            const collisionColor = new THREE.Color(1.0, 0.2, 0.15);

            const hasTexture = body.has_texture && body.tex_coords;

            for (let fi = 0; fi < faces.length; fi++) {
                const [i0, i1, i2] = faces[fi];
                const v0 = verts[i0];
                const v1 = verts[i1];
                const v2 = verts[i2];

                positions.push(v0[0], v0[1], v0[2]);
                positions.push(v1[0], v1[1], v1[2]);
                positions.push(v2[0], v2[1], v2[2]);

                let faceColor;
                if (collisionFaces.has(fi)) {
                    faceColor = collisionColor;
                } else if (hasTexture) {
                    // Generate checkerboard from UV coords as visual
                    // feedback that UV mapping is working
                    const tc = body.tex_coords;
                    const u0 = (i0 < tc.length) ? tc[i0][0] : 0;
                    const u1 = (i1 < tc.length) ? tc[i1][0] : 0;
                    const u2 = (i2 < tc.length) ? tc[i2][0] : 0;
                    const v0u = (i0 < tc.length) ? tc[i0][1] : 0;
                    const v1u = (i1 < tc.length) ? tc[i1][1] : 0;
                    const v2u = (i2 < tc.length) ? tc[i2][1] : 0;
                    const u = (u0 + u1 + u2) / 3;
                    const v = (v0u + v1u + v2u) / 3;
                    const checker = (Math.floor(u * 8) + Math.floor(v * 8)) % 2;
                    const shade = checker ? 0.9 : 0.5;
                    faceColor = new THREE.Color(
                        baseColor.r * shade,
                        baseColor.g * shade,
                        baseColor.b * shade
                    );
                } else {
                    faceColor = baseColor;
                }
                for (let k = 0; k < 3; k++) {
                    colors.push(faceColor.r, faceColor.g, faceColor.b);
                }
            }

            geometry.setAttribute('position',
                new THREE.Float32BufferAttribute(positions, 3));
            geometry.setAttribute('color',
                new THREE.Float32BufferAttribute(colors, 3));
            geometry.computeVertexNormals();

            const material = new THREE.MeshPhongMaterial({
                vertexColors: true,
                side: THREE.DoubleSide,
                transparent: true,
                opacity: color[3] || 1.0,
                shininess: 40,
            });

            const mesh = new THREE.Mesh(geometry, material);
            this.scene.add(mesh);
            this.bodyMeshes.push(mesh);

            // Wireframe overlay
            const wireMat = new THREE.MeshBasicMaterial({
                color: 0x446688,
                wireframe: true,
                transparent: true,
                opacity: 0.15,
            });
            const wireMesh = new THREE.Mesh(geometry.clone(), wireMat);
            this.scene.add(wireMesh);
            this.bodyMeshes.push(wireMesh);

            // AABB wireframe
            if (body.aabb_min && body.aabb_max) {
                const mn = body.aabb_min;
                const mx = body.aabb_max;
                const size = [mx[0] - mn[0], mx[1] - mn[1], mx[2] - mn[2]];
                const center = [(mn[0] + mx[0]) / 2, (mn[1] + mx[1]) / 2, (mn[2] + mx[2]) / 2];

                const boxGeo = new THREE.BoxGeometry(size[0], size[1], size[2]);
                const boxMat = new THREE.MeshBasicMaterial({
                    color: 0x58a6ff,
                    wireframe: true,
                    transparent: true,
                    opacity: 0.3,
                });
                const box = new THREE.Mesh(boxGeo, boxMat);
                box.position.set(center[0], center[1], center[2]);
                this.aabbGroup.add(box);
            }
        }

        // Update body select dropdown
        this._updateBodySelect(bodies);
        this._updateBodyInfo(bodies);
    }

    _updateProbe(probe) {
        if (!probe) return;
        const p = probe.position;
        this.probeMesh.position.set(p[0], p[1], p[2]);
    }

    _updateForce(force) {
        if (!force) return;

        const mag = force.magnitude || 0;

        if (this.showForce && mag > 0.001) {
            const v = force.vector;
            const dir = new THREE.Vector3(v[0], v[1], v[2]).normalize();
            const origin = this.probeMesh.position.clone();

            this.forceArrow.position.copy(origin);
            this.forceArrow.setDirection(dir);
            this.forceArrow.setLength(Math.min(mag * 2, 2), 0.08, 0.06);
            this.forceArrow.visible = true;
        } else {
            this.forceArrow.visible = false;
        }

        // Anchor marker and spring line
        if (force.is_contacting && force.anchor) {
            const a = force.anchor;
            this.anchorMesh.position.set(a[0], a[1], a[2]);
            this.anchorMesh.visible = true;

            const pts = this.springLine.geometry.attributes.position;
            pts.setXYZ(0, this.probeMesh.position.x, this.probeMesh.position.y, this.probeMesh.position.z);
            pts.setXYZ(1, a[0], a[1], a[2]);
            pts.needsUpdate = true;
            this.springLine.visible = true;
        } else {
            this.anchorMesh.visible = false;
            this.springLine.visible = false;
        }
    }

    _updateOctree(nodes) {
        // Clear old
        while (this.octreeGroup.children.length > 0) {
            const c = this.octreeGroup.children[0];
            this.octreeGroup.remove(c);
            if (c.geometry) c.geometry.dispose();
            if (c.material) c.material.dispose();
        }

        const maxDepth = Math.max(...nodes.map(n => n.depth), 1);

        for (const node of nodes) {
            if (!node.is_leaf) continue; // Only draw leaves

            const mn = node.min;
            const mx = node.max;
            const size = [mx[0] - mn[0], mx[1] - mn[1], mx[2] - mn[2]];
            const center = [
                (mn[0] + mx[0]) / 2,
                (mn[1] + mx[1]) / 2,
                (mn[2] + mx[2]) / 2,
            ];

            const depthRatio = node.depth / maxDepth;
            const hue = 0.15 + depthRatio * 0.5; // orange to cyan
            const color = new THREE.Color().setHSL(hue, 0.8, 0.5);

            const geo = new THREE.BoxGeometry(size[0], size[1], size[2]);
            const mat = new THREE.MeshBasicMaterial({
                color: color,
                wireframe: true,
                transparent: true,
                opacity: 0.15 + depthRatio * 0.2,
            });
            const box = new THREE.Mesh(geo, mat);
            box.position.set(center[0], center[1], center[2]);
            this.octreeGroup.add(box);
        }
    }

    _updateBodySelect(bodies) {
        const sel = document.getElementById('bodySelect');
        if (!sel) return;
        const current = sel.value;
        sel.innerHTML = '';
        bodies.forEach((b, i) => {
            const opt = document.createElement('option');
            opt.value = i;
            opt.textContent = b.name;
            sel.appendChild(opt);
        });
        if (current && current < bodies.length) {
            sel.value = current;
        }
    }

    _updateBodyInfo(bodies) {
        const el = document.getElementById('bodyInfo');
        if (!el) return;
        el.innerHTML = bodies.map((b, i) => {
            const numVerts = b.vertices.length;
            const numFaces = b.faces.length;
            const numColl = b.collision_faces.length;
            return `<div class="body-item">
                <span class="name">${b.name}</span>
                <span class="detail"> | V:${numVerts} F:${numFaces} C:${numColl}</span>
            </div>`;
        }).join('');
    }

    /**
     * Toggle octree visualisation.
     */
    setShowOctree(show) {
        this.octreeGroup.visible = show;
    }

    /**
     * Toggle AABB visualisation.
     */
    setShowAABB(show) {
        this.aabbGroup.visible = show;
    }

    /**
     * Render one frame.
     */
    render() {
        this.controls.update();
        this.renderer.render(this.scene, this.camera);

        // FPS counter
        this._frameCount++;
        const now = performance.now();
        if (now - this._lastFpsTime >= 1000) {
            this.fps = this._frameCount;
            this._frameCount = 0;
            this._lastFpsTime = now;
            const fpsEl = document.getElementById('fpsDisplay');
            if (fpsEl) fpsEl.textContent = `FPS: ${this.fps}`;
        }
    }

    _handleResize() {
        const parent = this.canvas.parentElement;
        const w = parent.clientWidth;
        const h = parent.clientHeight;
        this.camera.aspect = w / h;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(w, h);
    }

    dispose() {
        window.removeEventListener('resize', this._onResize);
    }
}

window.Renderer3D = Renderer3D;
