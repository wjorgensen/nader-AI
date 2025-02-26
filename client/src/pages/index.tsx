import { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { STLLoader } from 'three/addons/loaders/STLLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

export default function Home() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [loadingProgress, setLoadingProgress] = useState(0);
  const [loadingError, setLoadingError] = useState<string | null>(null);

  useEffect(() => {
    if (!canvasRef.current || !containerRef.current) return;

    // Scene setup
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xf0f0f0); // Light gray background for better contrast
    
    // Setup renderer
    const renderer = new THREE.WebGLRenderer({
      canvas: canvasRef.current,
      antialias: true,
    });
    
    // Get container dimensions
    const width = containerRef.current.clientWidth;
    const height = containerRef.current.clientHeight;
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    
    // Camera setup
    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 1000);
    camera.position.set(0, 0, 20); // Position the camera directly in front
    
    // Add orbit controls
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.25;
    
    // Lighting
    // Ambient light
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);
    
    // Directional lights from multiple angles
    const frontLight = new THREE.DirectionalLight(0xffffff, 0.8);
    frontLight.position.set(0, 0, 10);
    scene.add(frontLight);
    
    const topLight = new THREE.DirectionalLight(0xffffff, 0.8);
    topLight.position.set(0, 10, 0);
    scene.add(topLight);
    
    // Load STL model
    const loader = new STLLoader();
    
    loader.load('/front_man.stl', (geometry) => {
      console.log("STL loaded:", geometry);
      
      // Create a simple black material instead of texture
      const material = new THREE.MeshPhongMaterial({ 
        color: 0x000000,  // Black color
        specular: 0x222222,
        shininess: 30,
        side: THREE.DoubleSide // Render both sides of faces
      });
      
      // Create mesh
      const mesh = new THREE.Mesh(geometry, material);
      
      // Center geometry
      geometry.computeBoundingBox();
      const boundingBox = geometry.boundingBox!;
      const center = new THREE.Vector3();
      boundingBox.getCenter(center);
      geometry.translate(-center.x, -center.y, -center.z);
      
      // Adjust scale
      const size = new THREE.Vector3();
      boundingBox.getSize(size);
      const maxDim = Math.max(size.x, size.y, size.z);
      const scale = 10 / maxDim; // Scale to fit in a 10x10x10 box
      mesh.scale.set(scale, scale, scale);
      
      // Rotate the model 180 degrees in the opposite direction on X axis
      mesh.rotation.x = -Math.PI;
      mesh.rotation.y = Math.PI / 2;
      
      // Add to scene
      scene.add(mesh);
      
      // Position camera to view the model
      camera.position.set(0, 0, 15); // Place directly in front
      
      // Turn off auto-rotation
      controls.autoRotate = false;
      
      // Lock the controls to prevent spinning
      controls.enableDamping = false;
      controls.enableZoom = true;
      controls.enablePan = false;
      controls.enableRotate = true; // Keep rotation enabled for user interaction
      
      console.log("Model added to scene with scale:", scale);
      setIsLoading(false);
      
      // Focus controls on the mesh's center
      controls.target.set(0, 0, 0);
      controls.update();
    }, 
    // Progress callback
    (xhr) => {
      const progress = Math.round((xhr.loaded / xhr.total) * 100);
      console.log(`${progress}% loaded`);
      setLoadingProgress(progress);
    },
    // Error callback
    (error) => {
      console.error('An error occurred loading the STL file:', error);
      setLoadingError('Failed to load 3D model. Please try again later.');
      setIsLoading(false);
    });

    // Animation loop
    const animate = () => {
      requestAnimationFrame(animate);
      controls.update(); // Required for damping and auto-rotation
      renderer.render(scene, camera);
    };
    animate();

    // Handle resize
    const handleResize = () => {
      if (!containerRef.current) return;
      const width = containerRef.current.clientWidth;
      const height = containerRef.current.clientHeight;
      renderer.setSize(width, height);
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      controls.dispose();
    };
  }, []);

  return (
    <div 
      ref={containerRef}
      style={{ 
        position: 'relative', 
        width: '100vw', 
        height: '100vh',
        background: '#f0f0f0' 
      }}
    >
      <canvas ref={canvasRef} />
      {isLoading && (
        <div
          style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            background: 'rgba(255, 255, 255, 0.9)',
            padding: '20px',
            borderRadius: '10px',
            boxShadow: '0 4px 8px rgba(0, 0, 0, 0.1)',
            textAlign: 'center',
            zIndex: 1000
          }}
        >
          <div 
            style={{
              border: '4px solid #f3f3f3',
              borderTop: '4px solid #3498db',
              borderRadius: '50%',
              width: '40px',
              height: '40px',
              animation: 'spin 1s linear infinite',
              margin: '0 auto 10px'
            }}
          />
          <p style={{ margin: 0, fontFamily: 'sans-serif' }}>
            Loading 3D Model... {loadingProgress}%
          </p>
          <style jsx>{`
            @keyframes spin {
              0% { transform: rotate(0deg); }
              100% { transform: rotate(360deg); }
            }
          `}</style>
        </div>
      )}
      {loadingError && (
        <div
          style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            background: 'rgba(255, 255, 255, 0.9)',
            padding: '20px',
            borderRadius: '10px',
            boxShadow: '0 4px 8px rgba(0, 0, 0, 0.1)',
            textAlign: 'center',
            color: 'red',
            zIndex: 1000
          }}
        >
          {loadingError}
        </div>
      )}
    </div>
  );
}
