/**
 * 3D Interactive Formula 1 Car Scene using Three.js & GLTFLoader
 * Supports: GLB model loading (McLaren MP4/5), OrbitControls, camera presets,
 * dynamic stress underglow, tire thermals, and procedural PBR fallback.
 */

class F1Scene3D {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    if (!this.container) return;

    this.scene = null;
    this.camera = null;
    this.renderer = null;
    this.controls = null;
    this.carGroup = new THREE.Group();
    this.gltfCar = null;
    this.wheels = [];
    this.underglowLight = null;
    this.rearRainLight = null;
    this.currentMood = 'Calm';
    this.stressLevel = 20.0;
    this.carSpeed = 280;
    this.modelLoaded = false;

    this.init();
  }

  init() {
    const width = this.container.clientWidth;
    const height = this.container.clientHeight;

    // 1. Scene & Background
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x06080d);
    this.scene.fog = new THREE.FogExp2(0x06080d, 0.035);

    // 2. Camera
    this.camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
    this.setCameraPreset('pitwall');

    // 3. Renderer
    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
    this.renderer.setSize(width, height);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.renderer.outputEncoding = THREE.sRGBEncoding;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.15;
    this.container.appendChild(this.renderer.domElement);

    // 4. Orbit Controls
    if (THREE.OrbitControls) {
      this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
      this.controls.enableDamping = true;
      this.controls.dampingFactor = 0.05;
      this.controls.maxPolarAngle = Math.PI / 2 - 0.02; // Prevent below-floor camera clipping
      this.controls.minDistance = 2.0;
      this.controls.maxDistance = 16;
    }

    // 5. Lighting
    this.setupLighting();

    // 6. Floor Grid & Paddock Stage
    this.setupFloor();

    // 7. Build Procedural PBR Fallback first (immediate display)
    this.buildProceduralCar();

    // 8. Load the User's High-Detail McLaren MP4/5 GLB Model
    this.loadGLBModel('/assets/mclaren_mp45__formula_1.glb');

    // 9. Resize handler
    window.addEventListener('resize', () => this.onWindowResize());

    // 10. Start Animation Loop
    this.animate();
  }

  setupLighting() {
    const ambientLight = new THREE.AmbientLight(0xffffff, 1.2);
    this.scene.add(ambientLight);

    // Main studio directional light
    const keyLight = new THREE.DirectionalLight(0xffffff, 2.5);
    keyLight.position.set(6, 9, 6);
    keyLight.castShadow = true;
    keyLight.shadow.mapSize.width = 1024;
    keyLight.shadow.mapSize.height = 1024;
    keyLight.shadow.bias = -0.0001;
    this.scene.add(keyLight);

    // Cyan rim light
    const rimLightCyan = new THREE.DirectionalLight(0x00f0ff, 2.0);
    rimLightCyan.position.set(-7, 5, -6);
    this.scene.add(rimLightCyan);

    // Red racing accent light
    const fillLightRed = new THREE.DirectionalLight(0xff1801, 1.4);
    fillLightRed.position.set(7, 4, -7);
    this.scene.add(fillLightRed);

    // Dynamic Underglow Light
    this.underglowLight = new THREE.PointLight(0x00f0ff, 4.5, 8);
    this.underglowLight.position.set(0, 0.15, 0);
    this.scene.add(this.underglowLight);

    // Rear Strobe Rain Light
    this.rearRainLight = new THREE.PointLight(0xff0000, 3.5, 5);
    this.rearRainLight.position.set(0, 0.45, -2.4);
    this.scene.add(this.rearRainLight);
  }

  setupFloor() {
    const floorGeo = new THREE.PlaneGeometry(30, 30);
    const floorMat = new THREE.MeshStandardMaterial({
      color: 0x080b12,
      roughness: 0.8,
      metalness: 0.3,
    });
    const floor = new THREE.Mesh(floorGeo, floorMat);
    floor.rotation.x = -Math.PI / 2;
    floor.receiveShadow = true;
    this.scene.add(floor);

    // Paddock Neon Telemetry Grid
    const grid = new THREE.GridHelper(24, 24, 0x00f0ff, 0x141d2c);
    grid.position.y = 0.01;
    this.scene.add(grid);
  }

  buildProceduralCar() {
    const carbonMat = new THREE.MeshStandardMaterial({ color: 0x111622, roughness: 0.35, metalness: 0.8 });
    const bodyMat = new THREE.MeshStandardMaterial({ color: 0x00d2be, roughness: 0.2, metalness: 0.7, clearcoat: 1.0 });
    const rubberMat = new THREE.MeshStandardMaterial({ color: 0x1a1a1a, roughness: 0.9, metalness: 0.1 });
    const rimMat = new THREE.MeshStandardMaterial({ color: 0x222222, roughness: 0.3, metalness: 0.9 });
    const haloMat = new THREE.MeshStandardMaterial({ color: 0x0a0c10, roughness: 0.4, metalness: 0.85 });

    // Chassis & Nose
    const chassis = new THREE.Mesh(new THREE.BoxGeometry(0.75, 0.35, 3.4), bodyMat);
    chassis.position.set(0, 0.35, 0);
    chassis.castShadow = true;
    this.carGroup.add(chassis);

    const nose = new THREE.Mesh(new THREE.ConeGeometry(0.32, 1.4, 8), bodyMat);
    nose.rotation.x = Math.PI / 2;
    nose.position.set(0, 0.32, 2.3);
    nose.scale.set(1, 1, 0.5);
    nose.castShadow = true;
    this.carGroup.add(nose);

    // Front Wing
    const frontWing = new THREE.Mesh(new THREE.BoxGeometry(1.85, 0.04, 0.55), carbonMat);
    frontWing.position.set(0, 0.16, 2.6);
    frontWing.castShadow = true;
    this.carGroup.add(frontWing);

    // Sidepods
    for (let side of [-1, 1]) {
      const sidepod = new THREE.Mesh(new THREE.BoxGeometry(0.38, 0.32, 1.6), bodyMat);
      sidepod.position.set(side * 0.48, 0.32, -0.1);
      sidepod.castShadow = true;
      this.carGroup.add(sidepod);
    }

    // Cockpit Halo
    const haloRing = new THREE.Mesh(new THREE.TorusGeometry(0.24, 0.035, 8, 24, Math.PI), haloMat);
    haloRing.rotation.x = -Math.PI / 2 + 0.3;
    haloRing.position.set(0, 0.62, 0.3);
    this.carGroup.add(haloRing);

    // Rear Wing
    const rearWing = new THREE.Mesh(new THREE.BoxGeometry(1.4, 0.05, 0.45), carbonMat);
    rearWing.position.set(0, 0.78, -1.95);
    rearWing.castShadow = true;
    this.carGroup.add(rearWing);

    // Wheels
    const wheelConfigs = [
      { name: 'FL', x: -0.92, y: 0.33, z: 1.6, radius: 0.33, width: 0.32 },
      { name: 'FR', x: 0.92, y: 0.33, z: 1.6, radius: 0.33, width: 0.32 },
      { name: 'RL', x: -0.95, y: 0.35, z: -1.4, radius: 0.35, width: 0.42 },
      { name: 'RR', x: 0.95, y: 0.35, z: -1.4, radius: 0.35, width: 0.42 },
    ];

    this.wheels = [];
    for (let cfg of wheelConfigs) {
      const wheelGroup = new THREE.Group();
      wheelGroup.position.set(cfg.x, cfg.y, cfg.z);

      const tireMesh = new THREE.Mesh(new THREE.CylinderGeometry(cfg.radius, cfg.radius, cfg.width, 24), rubberMat);
      tireMesh.rotation.z = Math.PI / 2;
      tireMesh.castShadow = true;
      wheelGroup.add(tireMesh);

      const rimMesh = new THREE.Mesh(new THREE.CylinderGeometry(cfg.radius * 0.58, cfg.radius * 0.58, cfg.width * 1.02, 16), rimMat);
      rimMesh.rotation.z = Math.PI / 2;
      wheelGroup.add(rimMesh);

      this.carGroup.add(wheelGroup);
      this.wheels.push(wheelGroup);
    }

    this.scene.add(this.carGroup);
  }

  loadGLBModel(glbUrl) {
    if (!THREE.GLTFLoader) {
      console.warn('GLTFLoader not found, using procedural F1 model.');
      return;
    }

    console.log(`Loading 3D F1 GLB Model from: ${glbUrl}...`);
    const loader = new THREE.GLTFLoader();

    if (THREE.DRACOLoader) {
      const dracoLoader = new THREE.DRACOLoader();
      dracoLoader.setDecoderPath('https://www.gstatic.com/draco/versioned/decoders/1.5.6/');
      loader.setDRACOLoader(dracoLoader);
    }

    const loadingText = document.getElementById('modelLoadingText');
    const loadingPill = document.getElementById('modelLoadingPill');

    loader.load(
      glbUrl,
      (gltf) => {
        console.log('McLaren MP4/5 GLB Model loaded successfully!');
        const model = gltf.scene;

        // Compute Bounding Box to scale and position correctly
        const box = new THREE.Box3().setFromObject(model);
        const size = new THREE.Vector3();
        box.getSize(size);
        const center = new THREE.Vector3();
        box.getCenter(center);

        // Normalize size: make car approximately 4.8 units long
        const targetLength = 4.8;
        const maxHorizDim = Math.max(size.x, size.z);
        const scaleFactor = targetLength / (maxHorizDim > 0 ? maxHorizDim : 1);
        model.scale.set(scaleFactor, scaleFactor, scaleFactor);

        // Recompute box after scale to ground it
        const scaledBox = new THREE.Box3().setFromObject(model);
        const scaledCenter = new THREE.Vector3();
        scaledBox.getCenter(scaledCenter);

        // Center on X and Z, set bottom on Y=0 floor
        model.position.x = -scaledCenter.x;
        model.position.z = -scaledCenter.z;
        model.position.y = -scaledBox.min.y;

        // Enable shadows and enhance materials
        model.traverse((child) => {
          if (child.isMesh) {
            child.castShadow = true;
            child.receiveShadow = true;
            if (child.material) {
              child.material.side = THREE.DoubleSide;
              child.material.envMapIntensity = 1.2;
            }
          }
        });

        // Hide procedural car and display GLTF model
        this.scene.remove(this.carGroup);
        this.gltfCar = model;
        this.scene.add(this.gltfCar);
        this.modelLoaded = true;

        if (loadingText) loadingText.textContent = 'McLAREN MP4/5 (ONLINE)';
        if (loadingPill) loadingPill.style.borderColor = 'var(--f1-green)';
      },
      (xhr) => {
        if (xhr.lengthComputable) {
          const percent = Math.round((xhr.loaded / xhr.total) * 100);
          if (loadingText) loadingText.textContent = `LOADING MP4/5 (${percent}%)...`;
        }
      },
      (error) => {
        console.warn('Error loading GLB model (fallback to procedural car):', error);
        if (loadingText) loadingText.textContent = 'PRODUCERAL PBR (ACTIVE)';
      }
    );
  }

  setCameraPreset(preset) {
    if (!this.camera) return;

    if (preset === 'cockpit') {
      this.camera.position.set(0, 1.15, -0.1);
      this.camera.lookAt(0, 0.4, 4.0);
    } else if (preset === 'aero') {
      this.camera.position.set(4.5, 1.2, 0.2);
      this.camera.lookAt(0, 0.4, 0);
    } else if (preset === 'chase') {
      this.camera.position.set(2.8, 1.4, 3.8);
      this.camera.lookAt(0, 0.35, 0.5);
    } else {
      this.camera.position.set(3.8, 2.5, -3.2);
      this.camera.lookAt(0, 0.3, 0);
    }

    if (this.controls) {
      this.controls.target.set(0, 0.4, 0);
      this.controls.update();
    }
  }

  updateStressState(mood, stressLevel, telemetry) {
    this.currentMood = mood || 'Calm';
    this.stressLevel = stressLevel !== undefined ? stressLevel : 20.0;
    this.carSpeed = telemetry?.snapshot?.speed_kmh || 280;

    if (this.currentMood === 'Stressed') {
      this.underglowLight.color.setHex(0xff2a24); // Neon Crimson
      this.underglowLight.intensity = 5.5;
    } else if (this.currentMood === 'Tired') {
      this.underglowLight.color.setHex(0xffb800); // Warm Amber
      this.underglowLight.intensity = 3.8;
    } else {
      this.underglowLight.color.setHex(0x00f0ff); // Neon Cyan
      this.underglowLight.intensity = 3.5;
    }
  }

  onWindowResize() {
    if (!this.container || !this.renderer || !this.camera) return;
    const width = this.container.clientWidth;
    const height = this.container.clientHeight;
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height);
  }

  animate() {
    requestAnimationFrame(() => this.animate());

    const time = performance.now() * 0.001;

    // Spin Wheels on procedural car if active
    if (!this.modelLoaded && this.wheels.length > 0) {
      const wheelRotSpeed = (this.carSpeed / 100.0) * 0.25;
      for (let w of this.wheels) {
        w.rotation.x += wheelRotSpeed;
      }
    }

    // Dynamic Stress Pulsing on lights
    if (this.currentMood === 'Stressed') {
      const pulse = (Math.sin(time * 8.0) + 1.0) * 0.5;
      this.rearRainLight.intensity = 1.0 + pulse * 6.0;
      this.underglowLight.intensity = 3.5 + pulse * 3.0;
    } else if (this.currentMood === 'Tired') {
      const pulse = (Math.sin(time * 2.0) + 1.0) * 0.5;
      this.rearRainLight.intensity = 1.5 + pulse * 2.0;
      this.underglowLight.intensity = 2.5 + pulse * 2.0;
    } else {
      this.rearRainLight.intensity = 1.8;
      this.underglowLight.intensity = 3.5;
    }

    // Gentle engine vibration
    const activeCar = this.modelLoaded ? this.gltfCar : this.carGroup;
    if (activeCar) {
      activeCar.position.y = Math.sin(time * 40.0) * 0.0012;
    }

    if (this.controls) {
      this.controls.update();
    }

    this.renderer.render(this.scene, this.camera);
  }
}

window.F1Scene3D = F1Scene3D;
