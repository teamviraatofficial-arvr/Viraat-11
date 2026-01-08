/**
 * VIRAAT 3D Visualizer
 * Uses Three.js to render procedural military equipment or load glTF assets.
 */

const VisualizerModule = {
    scene: null,
    camera: null,
    renderer: null,
    controls: null,
    currentMesh: null,
    animationId: null,
    isRotating: true,
    gltfLoader: null,
    
    init() {
        this.container = document.getElementById('canvas3d');
        if (!this.container) return;

        // Scene setup
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x0a0e27); // Matches --bg-primary
        this.scene.fog = new THREE.FogExp2(0x0a0e27, 0.05);

        // Camera
        this.camera = new THREE.PerspectiveCamera(75, this.container.clientWidth / this.container.clientHeight, 0.1, 1000);
        this.camera.position.z = 5;
        this.camera.position.y = 2;

        // Renderer
        this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        this.container.appendChild(this.renderer.domElement);

        // Lights
        const ambientLight = new THREE.AmbientLight(0x404040, 2); // Soft white light
        this.scene.add(ambientLight);

        const directionalLight = new THREE.DirectionalLight(0x00d4aa, 2); // Primary color
        directionalLight.position.set(5, 5, 5);
        this.scene.add(directionalLight);
        
        const backLight = new THREE.DirectionalLight(0xff00ff, 1); // Accent color
        backLight.position.set(-5, 0, -5);
        this.scene.add(backLight);

        // Controls
        if (THREE.OrbitControls) {
            this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
            this.controls.enableDamping = true;
            this.controls.dampingFactor = 0.05;
        }

        // Grid
        const gridHelper = new THREE.GridHelper(20, 20, 0x2a3555, 0x141b36);
        this.scene.add(gridHelper);

        // glTF Loader
        if (typeof THREE.GLTFLoader !== 'undefined') {
            this.gltfLoader = new THREE.GLTFLoader();
        }

        // UI Bindings
        document.getElementById('closeVisualBtn')?.addEventListener('click', () => this.hide());
        document.getElementById('rotateBtn')?.addEventListener('click', (e) => {
             this.isRotating = !this.isRotating;
             e.target.classList.toggle('active', this.isRotating);
        });
        document.getElementById('wireframeBtn')?.addEventListener('click', (e) => {
            if(this.currentMesh) {
                this.currentMesh.traverse((child) => {
                    if (child.isMesh) {
                        if (Array.isArray(child.material)) {
                            child.material.forEach(m => m.wireframe = !m.wireframe);
                        } else {
                            child.material.wireframe = !child.material.wireframe;
                        }
                    }
                });
                e.target.classList.toggle('active', this.isWireframe());
            }
        });

        // Resize handler
        window.addEventListener('resize', () => this.onWindowResize(), false);
        
        this.animate();
    },

    isWireframe() {
        if(!this.currentMesh) return false;
        let isWireframe = false;
        this.currentMesh.traverse((child) => {
            if (child.isMesh && child.material) {
                isWireframe = Array.isArray(child.material) ? child.material[0].wireframe : child.material.wireframe;
            }
        });
        return isWireframe;
    },

    loadModel(modelId, modelName, assetPath) {
        this.show();
        this.clearScene();
        
        document.getElementById('modelLabel').textContent = `System: ${modelName || modelId}`;
        console.log(`Loading 3D Model: ${modelId}`);

        // Try to load glTF asset first if path provided
        if (assetPath && this.gltfLoader) {
            console.log(`Loading glTF from: ${assetPath}`);
            this.gltfLoader.load(
                assetPath,
                (gltf) => {
                    this.currentMesh = gltf.scene;
                    this.scene.add(this.currentMesh);
                    // Center and scale
                    const bbox = new THREE.Box3().setFromObject(this.currentMesh);
                    const size = bbox.getSize(new THREE.Vector3());
                    const maxDim = Math.max(size.x, size.y, size.z);
                    const scale = 2.0 / maxDim;
                    this.currentMesh.scale.multiplyScalar(scale);
                    const center = bbox.getCenter(new THREE.Vector3());
                    this.currentMesh.position.sub(center.multiplyScalar(scale));
                    console.log('glTF model loaded successfully');
                },
                undefined,
                (error) => {
                    console.warn(`Failed to load glTF: ${error.message}. Falling back to procedural generation.`);
                    this.loadProceduralModel(modelId);
                }
            );
        } else {
            // Fallback to procedural generation
            this.loadProceduralModel(modelId);
        }
    },

    loadProceduralModel(modelId) {
        // PROCEDURAL GENERATION FACTORY
        let mesh;
        
        if (modelId === 'ak47' || modelId === 'm4a1' || modelId === 'dlq33') {
            mesh = this.createRifle(modelId);
        } else if (modelId === 't90' || modelId === 'vehicle') {
             mesh = this.createTank();
        } else if (modelId === 'bunker') {
            mesh = this.createBunker();
        } else {
            mesh = this.createGenericBox();
        }
        
        this.currentMesh = mesh;
        this.scene.add(mesh);
    },
    
    // --- Procedural Asset Generators ---
    
    createRifle(type) {
        const group = new THREE.Group();
        const material = new THREE.MeshStandardMaterial({ 
            color: type === 'ak47' ? 0x8d5524 : 0x333333,
            roughness: 0.7,
            metalness: 0.6 
        });

        // Stock
        const stockGeo = new THREE.BoxGeometry(0.5, 0.6, 2);
        const stock = new THREE.Mesh(stockGeo, material);
        stock.position.z = 1.5;
        group.add(stock);
        
        // Body
        const bodyGeo = new THREE.BoxGeometry(0.4, 0.7, 1.5);
        const body = new THREE.Mesh(bodyGeo, material);
        group.add(body);
        
        // Barrel
        const barrelGeo = new THREE.CylinderGeometry(0.1, 0.1, 3, 16);
        const barrelMat = new THREE.MeshStandardMaterial({ color: 0x111111, metalness: 0.9 });
        const barrel = new THREE.Mesh(barrelGeo, barrelMat);
        barrel.rotation.z = Math.PI / 20; // Slight tilt removed, actually align with Z
        barrel.rotation.x = Math.PI / 2;
        barrel.position.z = -2;
        barrel.position.y = 0.2;
        group.add(barrel);
        
        // Scope (for DLQ/Sniper)
        if (type === 'dlq33') {
             const scopeGeo = new THREE.CylinderGeometry(0.15, 0.15, 1, 16);
             const scope = new THREE.Mesh(scopeGeo, barrelMat);
             scope.rotation.x = Math.PI / 2;
             scope.position.y = 0.8;
             group.add(scope);
        }
        
        // Magazine
        const magGeo = new THREE.BoxGeometry(0.3, 1.5, 0.5);
        const mag = new THREE.Mesh(magGeo, material);
        mag.rotation.x = 0.5;
        mag.position.y = -0.8;
        mag.position.z = 0.5;
        group.add(mag);

        return group;
    },

    createTank() {
        const group = new THREE.Group();
        const greenMat = new THREE.MeshStandardMaterial({ color: 0x2e4033, roughness: 0.8 });
        
        // Hull
        const hull = new THREE.Mesh(new THREE.BoxGeometry(2, 1, 3), greenMat);
        group.add(hull);
        
        // Turret
        const turret = new THREE.Mesh(new THREE.SphereGeometry(0.8, 32, 16), greenMat);
        turret.position.y = 0.8;
        turret.scale.y = 0.6;
        group.add(turret);
        
        // Barrel
        const barrel = new THREE.Mesh(new THREE.CylinderGeometry(0.1, 0.1, 3, 16), greenMat);
        barrel.rotation.x = Math.PI / 2;
        barrel.position.y = 0.8;
        barrel.position.z = -1.5;
        group.add(barrel);
        
        // Treads
        const treadGeo = new THREE.BoxGeometry(0.5, 0.5, 3.2);
        const treadMat = new THREE.MeshStandardMaterial({ color: 0x111111 });
        
        const leftTread = new THREE.Mesh(treadGeo, treadMat);
        leftTread.position.set(-1.1, -0.4, 0);
        group.add(leftTread);
        
        const rightTread = new THREE.Mesh(treadGeo, treadMat);
        rightTread.position.set(1.1, -0.4, 0);
        group.add(rightTread);
        
        return group;
    },
    
    createBunker() {
        const group = new THREE.Group();
        const concrete = new THREE.MeshStandardMaterial({ color: 0x888888, roughness: 0.9 });
        
        const base = new THREE.Mesh(new THREE.CylinderGeometry(2, 2.5, 1.5, 6), concrete);
        group.add(base);
        
        const dome = new THREE.Mesh(new THREE.SphereGeometry(2, 32, 16, 0, Math.PI * 2, 0, Math.PI / 2), concrete);
        dome.position.y = 0.75;
        group.add(dome);
        
        return group;
    },
    
    createGenericBox() {
        const geometry = new THREE.IcosahedronGeometry(1, 0);
        const material = new THREE.MeshStandardMaterial({ 
            color: 0x00d4aa, 
            wireframe: true 
        });
        return new THREE.Mesh(geometry, material);
    },

    clearScene() {
        if (this.currentMesh) {
            this.scene.remove(this.currentMesh);
            
            // Dispose geometries (simple traverse)
            this.currentMesh.traverse((child) => {
                if (child.isMesh) {
                    child.geometry.dispose();
                    if(Array.isArray(child.material)) child.material.forEach(m=>m.dispose());
                    else child.material.dispose();
                }
            });
            this.currentMesh = null;
        }
    },

    onWindowResize() {
        if (!this.camera || !this.renderer) return;
        this.camera.aspect = this.container.clientWidth / this.container.clientHeight;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
    },

    animate() {
        this.animationId = requestAnimationFrame(() => this.animate());
        
        if (this.currentMesh && this.isRotating) {
            this.currentMesh.rotation.y += 0.005;
        }
        
        if (this.controls) this.controls.update();
        if (this.renderer && this.scene) this.renderer.render(this.scene, this.camera);
    },

    show() {
        const visualContainer = document.getElementById('visualContainer');
        visualContainer.classList.remove('hidden');
        document.getElementById('mainApp').classList.add('split-mode');
        // Trigger resize after CSS transition
        setTimeout(() => this.onWindowResize(), 350);
    },

    hide() {
        document.getElementById('visualContainer').classList.add('hidden');
        document.getElementById('mainApp').classList.remove('split-mode');
        this.clearScene();
        // Stop Loop? Maybe keep it running cheaply
    }
};

window.VisualizerModule = VisualizerModule;
