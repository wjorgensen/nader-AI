import { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { STLLoader } from 'three/addons/loaders/STLLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import styles from '../styles/Home.module.css';
import DataVisualization from './components/dataVisualization';
import JobForm, { JobFormData } from './components/JobForm';
import WalletConnect from './components/WalletConnect';

// Import the StatCardProps type from the DataVisualization component
import type { StatCardProps } from './components/dataVisualization';

// Test data for DataVisualization component - explicitly typed to match StatCardProps
const networkStatsData: StatCardProps[] = [
  // User network growth graph - square card
  { 
    title: 'Network Growth', 
    value: '50 Users', 
    type: 'graph' as const,
    size: 'medium' as const,
    data: { 
      values: [5, 8, 12, 17, 22, 28, 35, 42, 48, 50], 
      target: 50 
    } 
  },
  
  // Accounts DM'd - small card
  { 
    title: 'Accounts DM\'d', 
    value: '372',
    size: 'small' as const
  },
  
  // Activity updates - tall card
  { 
    title: 'Activity Updates', 
    value: '12 New', 
    type: 'activity' as const,
    size: 'tall' as const,
    data: { 
      updates: [
        { text: 'User johnsmith93 joined the network', time: '2 mins ago' },
        { text: 'Connection established with devTeam', time: '15 mins ago' },
        { text: 'New job posted: Senior React Dev', time: '45 mins ago' },
        { text: 'Profile match found for jobID#1234', time: '1 hour ago' },
        { text: 'Weekly network report generated', time: '3 hours ago' },
        { text: 'System maintenance completed', time: '1 day ago' },
        { text: 'New feature released: Enhanced matching', time: '2 days ago' }
      ] 
    } 
  },
  
  // Engineers by language - wide card
  { 
    title: 'Engineers by Language', 
    value: '126 Total', 
    type: 'languages' as const,
    size: 'wide' as const,
    data: { 
      languages: [
        { name: 'JavaScript', value: 42 },
        { name: 'Python', value: 38 },
        { name: 'Java', value: 29 },
        { name: 'C#', value: 24 },
        { name: 'Go', value: 17 },
        { name: 'Rust', value: 11 }
      ] 
    } 
  },
  
  // Success rate - small card
  { 
    title: 'Success Rate', 
    value: '98.5%',
    size: 'small' as const
  },
  
  // Response time - small card
  { 
    title: 'Avg Response', 
    value: '1.2s',
    size: 'small' as const
  }
];

export default function Home() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [loadingProgress, setLoadingProgress] = useState(0);
  const [loadingError, setLoadingError] = useState<string | null>(null);
  const [isInputFocused, setIsInputFocused] = useState(false);
  const [cursorPosition, setCursorPosition] = useState({ x: 0, y: 0 });
  const [messages, setMessages] = useState<{role: string, content: string | React.ReactNode}[]>([]);
  const [isThinking, setIsThinking] = useState(false);
  const [isConversationActive, setIsConversationActive] = useState(false);
  const [modelPosition, setModelPosition] = useState({ x: 0, y: 0 }); // For animation
  const [mounted, setMounted] = useState(false);
  const [showJobForm, setShowJobForm] = useState(false);
  const [showWalletConnect, setShowWalletConnect] = useState(false);
  const [paymentComplete, setPaymentComplete] = useState(false);

  useEffect(() => {
    if (!canvasRef.current || !containerRef.current) return;

    // Scene setup
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xf0f0f0); // Light gray background for better contrast
    
    // Create a focus point that the model will look at
    const focusPoint = new THREE.Vector3(0, 0, 0);
    const targetFocusPoint = new THREE.Vector3(0, 0, 0);
    
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
    
    // Track mouse position
    const mouse = new THREE.Vector2();
    
    // Add mouse move event listener
    const handleMouseMove = (event: MouseEvent) => {
      // Calculate normalized mouse coordinates (-1 to 1)
      // This handles both normal and shifted canvas states
      const canvasRect = canvasRef.current?.getBoundingClientRect();
      if (canvasRect) {
        // Calculate mouse position relative to the canvas center
        const canvasCenterX = canvasRect.left + canvasRect.width / 2;
        const canvasCenterY = canvasRect.top + canvasRect.height / 2;
        
        // Convert to normalized coordinates (-1 to 1)
        mouse.x = (event.clientX - canvasCenterX) / (canvasRect.width / 2);
        mouse.y = -(event.clientY - canvasCenterY) / (canvasRect.height / 2);
        
        // Update target focus point based on mouse (when not thinking)
        if (!isThinking) {
          targetFocusPoint.set(mouse.x * 3, mouse.y * 3, 0); // Reduced multiplier from 5 to 3
        }
      }
    };
    
    window.addEventListener('mousemove', handleMouseMove);
    
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
    
    // Add camera-following light for better front illumination
    const cameraLight = new THREE.DirectionalLight(0xffffff, 1.2);
    cameraLight.position.set(0, 0, 25); // Position behind where camera will be
    cameraLight.target.position.set(0, 0, 0); // Point at center/model
    scene.add(cameraLight);
    scene.add(cameraLight.target);
    
    // Create a variable to store the mesh
    let model: THREE.Mesh | null = null;
    
    // Load STL model
    const loader = new STLLoader();
    
    loader.load('/front_man.stl', (geometry) => {
      console.log("STL loaded:", geometry);
      
      // Create a wireframe material instead of solid material
      const material = new THREE.MeshBasicMaterial({ 
        color: 0x000000,  // Black color
        wireframe: true,
        wireframeLinewidth: 2, // Increased line width 
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
      const scale = 8.5 / maxDim; // Slightly increased from 8 to 8.5
      
      // Apply non-uniform scaling to squish the height
      mesh.scale.set(scale, scale, scale * 0.85); // Reduce z-scale by 15%
      
      // Rotate the model to fix the orientation
      mesh.rotation.x = Math.PI / 2;
      mesh.rotation.z = Math.PI;
      mesh.rotation.y = Math.PI;
      
      // Position the model in the scene
      mesh.position.y = 1; // Reduced from 3 to 1 to move it down
      
      // Store reference to the mesh
      model = mesh;
      
      // Add to scene
      scene.add(mesh);
      
      // Position camera to view the model
      camera.position.set(0, 0, 15); // Place directly in front
      
      console.log("Model added to scene with scale:", scale);
      setIsLoading(false);
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
      
      // Update focus point based on state
      if (isThinking) {
        // When thinking, set target focus point upward
        targetFocusPoint.set(0, 3, 0); // Look up, reduced from 5 to 3
      }
      // No else condition for input focus - we just use the mouse position
      
      // Smoothly interpolate the focus point
      focusPoint.x = THREE.MathUtils.lerp(focusPoint.x, targetFocusPoint.x, 0.05);
      focusPoint.y = THREE.MathUtils.lerp(focusPoint.y, targetFocusPoint.y, 0.05);
      focusPoint.z = THREE.MathUtils.lerp(focusPoint.z, targetFocusPoint.z, 0.05);
      
      if (model) {
        // Base rotations
        const baseRotationX = Math.PI / 2;
        const baseRotationY = Math.PI;
        const baseRotationZ = Math.PI;
        
        // Calculate how much to rotate based on focus point position
        const tiltFactor = 0.05; // Reduced from 0.1 to 0.05 for subtler movement
        
        // Calculate rotations based on where the focus point is relative to the model
        const targetTiltX = baseRotationX - focusPoint.y * tiltFactor;
        const targetTiltY = baseRotationY - focusPoint.x * tiltFactor;
        const targetTiltZ = baseRotationZ + focusPoint.x * tiltFactor * 0.5;
        
        // Apply smooth rotation
        model.rotation.x = THREE.MathUtils.lerp(model.rotation.x, targetTiltX, 0.05);
        model.rotation.y = THREE.MathUtils.lerp(model.rotation.y, targetTiltY, 0.05);
        model.rotation.z = THREE.MathUtils.lerp(model.rotation.z, targetTiltZ, 0.05);
      }
      
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
      
      // No model position updates needed here
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('mousemove', handleMouseMove);
      // Ensure clean animation loop termination
      renderer.dispose();
    };
  }, [isThinking]);

  // Add this function to handle auto-resizing of the textarea
  const autoResizeTextarea = () => {
    if (inputRef.current) {
      // Reset height to auto first to get the correct scrollHeight
      inputRef.current.style.height = 'auto';
      
      // Calculate new height (min of scrollHeight or max height of 120px)
      const newHeight = Math.min(inputRef.current.scrollHeight, 120);
      
      // Set the height
      inputRef.current.style.height = `${newHeight}px`;
      
      // Adjust message container's bottom margin based on input height
      const inputFormHeight = document.querySelector(`.${styles.inputFormContainer}`)?.clientHeight || 0;
      const messagesContainer = document.querySelector(`.${styles.messagesContainer}`);
      if (messagesContainer) {
        // Cast messagesContainer to HTMLElement to access style property
        (messagesContainer as HTMLElement).style.marginBottom = `${inputFormHeight + 20}px`;
      }
    }
  };

  // Update handleInputChange to also handle resizing
  const handleInputChange = (e: React.SyntheticEvent) => {
    // Cast the target to HTMLInputElement
    const input = e.target as HTMLInputElement;
    const inputWidth = input.offsetWidth;
    
    // Get cursor position
    const cursorPos = input.selectionStart || 0;
    
    // Create a temporary span to measure the text width up to the cursor
    const temp = document.createElement('span');
    temp.style.font = window.getComputedStyle(input).font;
    temp.innerHTML = input.value.substring(0, cursorPos).replace(/ /g, '&nbsp;');
    document.body.appendChild(temp);
    
    // Calculate normalized x position (-1 to 1)
    const textWidth = temp.getBoundingClientRect().width;
    const paddingLeft = parseInt(window.getComputedStyle(input).paddingLeft);
    const normalizedX = ((textWidth + paddingLeft) / inputWidth) * 2 - 1;
    
    document.body.removeChild(temp);
    
    setCursorPosition({ x: normalizedX, y: 0 });
    
    // Auto-resize the textarea
    autoResizeTextarea();
  };

  // Handle job form submission
  const handleJobFormSubmit = async (formData: JobFormData) => {
    try {
      // Hide the form
      setShowJobForm(false);
      
      // Add a user message confirming submission
      setMessages(prev => [...prev, {
        role: 'user', 
        content: `Submitted job: ${formData.companyName} - ${formData.jobDescription.substring(0, 50)}...`
      }]);
      
      // Set thinking state
      setIsThinking(true);
      
      // Call our API endpoint to get a job summary
      const response = await fetch('/api/hyperbolic', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          message: `Please provide a summary of this job posting and tell me you'll help find candidates:
          Company: ${formData.companyName}
          Company Description: ${formData.companyDescription}
          Job Description: ${formData.jobDescription}
          ` 
        }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to get response');
      }
      
      const data = await response.json();
      
      // Add AI response
      setMessages(prev => [...prev, {
        role: 'assistant', 
        content: data.response
      }]);
      
      // Show wallet connect after response
      setShowWalletConnect(true);
      
    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, {
        role: 'assistant', 
        content: 'Sorry, I encountered an error processing your job submission.'
      }]);
    } finally {
      setIsThinking(false);
    }
  };

  // Add handler for payment completion
  const handlePaymentComplete = () => {
    setShowWalletConnect(false);
    setPaymentComplete(true);
    
    // Add a confirmation message
    setMessages(prev => [...prev, {
      role: 'assistant',
      content: 'Payment received! I\'ll begin searching for within my network for potential candidates immediately and will email you with results. Thank you for your business!'
    }]);
  };

  // Update handleSubmit function to handle the job button
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!inputRef.current || !inputRef.current.value.trim()) return;
    
    const userMessage = inputRef.current.value.trim();
    
    // Add user message to messages array for display
    setMessages(prev => [...prev, {role: 'user', content: userMessage}]);
    
    // Activate conversation mode (moves model to left)
    setIsConversationActive(true);
    
    // Clear input
    inputRef.current.value = '';
    
    // Reset textarea height
    if (inputRef.current) {
      inputRef.current.style.height = 'auto';
    }

    // Check for special messages
    if (userMessage === 'Give me stats on your network') {
      // Add the DataVisualization component as a message
      setMessages(prev => [
        ...prev, 
        {
          role: 'assistant', 
          content: (
            <DataVisualization
              stats={networkStatsData}
            />
          )
        }
      ]);
      
      // Scroll to bottom after a short delay to ensure the component is rendered
      setTimeout(() => {
        const messagesContainer = document.querySelector(`.${styles.messagesContainer}`);
        if (messagesContainer) {
          messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
      }, 100);
      
      return;
    }

    // Check if this is the job form message
    if (userMessage === 'I have a job I want filled') {
      // If conversation is not active yet, wait for animation to complete before showing form
      if (!isConversationActive) {
        // First activate conversation mode
        setIsConversationActive(true);
        
        // Delay showing the form until animation completes (1.2s duration + small buffer)
        setTimeout(() => {
          setShowJobForm(true);
          
          // Wait a bit more for the form to render, then scroll to top
          setTimeout(() => {
            const formContainer = document.querySelector(`.${styles.jobFormContainer}`);
            if (formContainer) {
              const messagesContainer = document.querySelector(`.${styles.messagesContainer}`);
              if (messagesContainer) {
                // Cast formContainer to HTMLElement to access offsetTop
                messagesContainer.scrollTop = (formContainer as HTMLElement).offsetTop - 20;
              }
            }
          }, 100);
        }, 1300); // Wait for animation to complete (1.2s + 100ms buffer)
      } else {
        // If conversation is already active, show form immediately
        setShowJobForm(true);
        
        // Scroll to top of form after it renders
        setTimeout(() => {
          const formContainer = document.querySelector(`.${styles.jobFormContainer}`);
          if (formContainer) {
            const messagesContainer = document.querySelector(`.${styles.messagesContainer}`);
            if (messagesContainer) {
              // Cast formContainer to HTMLElement to access offsetTop
              messagesContainer.scrollTop = (formContainer as HTMLElement).offsetTop - 20;
            }
          }
        }, 100);
      }
      return;
    }
    
    // Set thinking state
    setIsThinking(true);
    
    try {
      // Call our API endpoint
      const response = await fetch('/api/hyperbolic', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: userMessage }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to get response');
      }
      
      const data = await response.json();
      
      // Log response to console
      console.log("AI Response:", data);
      
      // Add response to messages array for display
      setMessages(prev => [...prev, {role: 'assistant', content: data.response}]);
      
    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, {
        role: 'assistant', 
        content: 'Sorry, I encountered an error processing your request.'
      }]);
    } finally {
      setIsThinking(false);
    }
  };

  useEffect(() => setMounted(true), []);

  // Add this useEffect to handle auto-scrolling after new messages
  useEffect(() => {
    const messagesContainer = document.querySelector(`.${styles.messagesContainer}`);
    if (messagesContainer) {
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
  }, [messages]); // Scroll whenever messages update

  // Add this useEffect to handle initial margin adjustment
  useEffect(() => {
    if (mounted) {
      // Adjust message container margin when component mounts or conversation state changes
      const inputFormHeight = document.querySelector(`.${styles.inputFormContainer}`)?.clientHeight || 0;
      const messagesContainer = document.querySelector(`.${styles.messagesContainer}`);
      if (messagesContainer) {
        // Cast messagesContainer to HTMLElement to access style property
        (messagesContainer as HTMLElement).style.marginBottom = `${inputFormHeight + 20}px`;
      }
    }
  }, [mounted, isConversationActive]);

  return (
    <div 
      ref={containerRef}
      style={{ 
        position: 'relative', 
        width: '100vw', 
        height: '100vh',
        background: '#f0f0f0',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        overflow: 'hidden'
      }}
    >
      <canvas 
        ref={canvasRef} 
        className={isConversationActive ? styles.canvasShifted : styles.canvasNormal}
      />
      
      {/* Chat container - appears when conversation is active */}
      <div 
        className={`${styles.chatContainer} ${isConversationActive ? 
          styles.chatContainerActive : styles.chatContainerHidden}`}
      >
        <div className={styles.messagesContainer}>
          <div className={styles.messagesFadeTop}></div>
          {messages.map((msg, idx) => (
            <div 
              key={idx} 
              className={`${msg.role === 'user' ? styles.messageUser : styles.messageAI} 
                ${idx === messages.length - 1 ? styles.fadeIn : ''}`}
            >
              <div className={`${styles.messageText} ${typeof msg.content !== 'string' ? styles.visualizationMessage : ''}`}>
                {msg.content}
              </div>
              <div className={`${styles.messageLabel} 
                ${msg.role === 'user' ? styles.messageLabelUser : styles.messageLabelAI}`}>
                {msg.role === 'user' ? 'You' : 'AI'}
              </div>
            </div>
          ))}
          
          {/* Add Job Form */}
          {showJobForm && (
            <div className={`${styles.messageAI} ${styles.fadeIn} ${styles.jobFormContainer}`}>
              <div className={styles.messageText}>
                <p>Please fill out the job details:</p>
                <JobForm onSubmit={handleJobFormSubmit} />
              </div>
              <div className={`${styles.messageLabel} ${styles.messageLabelAI}`}>
                AI
              </div>
            </div>
          )}
          
          {/* Thinking animation */}
          {isThinking && (
            <div className={`${styles.thinkingIndicator} ${styles.fadeIn}`}>
              <div className={styles.dotContainer}>
                <span className={`${styles.dot} ${styles.pulse} ${styles.dotDelay0}`}></span>
                <span className={`${styles.dot} ${styles.pulse} ${styles.dotDelay1}`}></span>
                <span className={`${styles.dot} ${styles.pulse} ${styles.dotDelay2}`}></span>
              </div>
            </div>
          )}
          
          {/* Wallet Connect */}
          {showWalletConnect && (
            <div className={`${styles.messageAI} ${styles.fadeIn}`}>
              <div className={styles.messageText}>
                <WalletConnect onPaymentComplete={handlePaymentComplete} />
              </div>
              <div className={`${styles.messageLabel} ${styles.messageLabelAI}`}>
                AI
              </div>
            </div>
          )}
        </div>
      </div>
      
      {/* Container for input form and suggestion buttons */}
      <div className={`${styles.inputFormContainer} 
        ${mounted ? (isConversationActive
           ? styles.inputFormShifted
           : styles.inputFormNormal)
          : ''}`}
      >
        {/* Input form */}
        <form 
          onSubmit={handleSubmit}
          className={styles.inputForm}
        >
          <textarea
            ref={inputRef}
            placeholder="Type something..."
            onFocus={() => setIsInputFocused(true)}
            onBlur={() => setIsInputFocused(false)}
            onChange={handleInputChange}
            onKeyUp={handleInputChange}
            onClick={handleInputChange}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                // If shift is pressed with Enter, add a new line instead of submitting
                if (e.shiftKey) {
                  // Allow default behavior (new line) when Shift+Enter is pressed
                  return;
                } else {
                  // Otherwise prevent default (which would be a new line) and submit
                  e.preventDefault();
                  if (!isThinking) { // Only submit if not thinking
                    handleSubmit(e);
                  }
                }
              }
              
              // Also trigger resizing on keydown for immediate feedback
              setTimeout(autoResizeTextarea, 0);
            }}
            className={styles.inputField}
            rows={1}
            style={{ resize: 'none', overflow: 'auto' }}
          />
          <button 
            type="submit" 
            disabled={isThinking}
            className={`${styles.sendButton} ${isThinking ? 
              styles.sendButtonDisabled : styles.sendButtonEnabled}`}
          >
            Send
          </button>
        </form>
        
        {/* Suggested messages within the same container */}
        <div className={styles.suggestedMessages}>
          {['Who are you?', 'Give me stats on your network', 'I have a job I want filled'].map((suggestion, idx) => (
            <button 
              key={idx} 
              className={styles.suggestionButton}
              onClick={(e) => {
                if (inputRef.current) {
                  inputRef.current.value = suggestion;
                  const syntheticEvent = { preventDefault: () => {} } as React.FormEvent;
                  handleSubmit(syntheticEvent);
                }
              }}
            >
              {suggestion}
            </button>
          ))}
        </div>
      </div>
      
      {/* Loading state */}
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
        </div>
      )}
      
      {/* Error state */}
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
