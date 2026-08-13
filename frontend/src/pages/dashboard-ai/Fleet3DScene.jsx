import React, { useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Environment, PerspectiveCamera, Line, Float, Instance, Instances } from '@react-three/drei';
import * as THREE from 'three';

// ── Stylized Truck Rig ──
function StylizedTruck({ position, rotation }) {
  const truckRef = useRef();

  // Dark metallic material
  const bodyMaterial = useMemo(() => new THREE.MeshStandardMaterial({
    color: '#0a100d',
    roughness: 0.2,
    metalness: 0.8,
  }), []);

  // Green glowing accents
  const glowMaterial = useMemo(() => new THREE.MeshBasicMaterial({
    color: '#19B86A',
    toneMapped: false,
  }), []);

  const glassMaterial = useMemo(() => new THREE.MeshPhysicalMaterial({
    color: '#050b09',
    transmission: 0.9,
    opacity: 1,
    metalness: 0.5,
    roughness: 0.1,
    ior: 1.5,
  }), []);

  // Subtle hover animation
  useFrame(({ clock }) => {
    if (truckRef.current) {
      truckRef.current.position.y = position[1] + Math.sin(clock.getElapsedTime() * 2) * 0.05;
    }
  });

  return (
    <group ref={truckRef} position={position} rotation={rotation}>
      {/* Cab Body */}
      <mesh material={bodyMaterial} position={[0, 0.8, 1.2]} castShadow>
        <boxGeometry args={[1.6, 1.2, 1.2]} />
      </mesh>
      {/* Cab Hood */}
      <mesh material={bodyMaterial} position={[0, 0.4, 2.1]} castShadow>
        <boxGeometry args={[1.5, 0.6, 0.8]} />
      </mesh>
      {/* Windshield */}
      <mesh material={glassMaterial} position={[0, 1.0, 1.83]} rotation={[-0.2, 0, 0]}>
        <planeGeometry args={[1.4, 0.6]} />
      </mesh>
      {/* Trailer */}
      <mesh material={bodyMaterial} position={[0, 1.2, -1.8]} castShadow>
        <boxGeometry args={[1.8, 2.2, 4.8]} />
      </mesh>
      {/* Glowing Accents */}
      <mesh material={glowMaterial} position={[0.81, 0.3, 2.5]}>
        <boxGeometry args={[0.1, 0.1, 0.1]} />
      </mesh>
      <mesh material={glowMaterial} position={[-0.81, 0.3, 2.5]}>
        <boxGeometry args={[0.1, 0.1, 0.1]} />
      </mesh>
      <mesh material={glowMaterial} position={[0, 2.3, -4.21]}>
        <boxGeometry args={[1.8, 0.05, 0.05]} />
      </mesh>
      {/* Wheels */}
      {[-1.2, 1.2].map((z) =>
        [-0.9, 0.9].map((x) => (
          <mesh key={`${x}-${z}`} material={bodyMaterial} position={[x, 0.2, z]} rotation={[0, 0, Math.PI / 2]}>
            <cylinderGeometry args={[0.3, 0.3, 0.3, 16]} />
          </mesh>
        ))
      )}
      <mesh material={bodyMaterial} position={[-0.9, 0.2, -3.5]} rotation={[0, 0, Math.PI / 2]}>
        <cylinderGeometry args={[0.3, 0.3, 0.3, 16]} />
      </mesh>
      <mesh material={bodyMaterial} position={[0.9, 0.2, -3.5]} rotation={[0, 0, Math.PI / 2]}>
        <cylinderGeometry args={[0.3, 0.3, 0.3, 16]} />
      </mesh>
    </group>
  );
}

// ── Glowing Route Path ──
function RoutePath() {
  const points = useMemo(() => {
    const curve = new THREE.CatmullRomCurve3([
      new THREE.Vector3(-10, 0, -5),
      new THREE.Vector3(-4, 0, 2),
      new THREE.Vector3(0, 0, 0),
      new THREE.Vector3(5, 0, 4),
      new THREE.Vector3(12, 0, -2),
    ]);
    return curve.getPoints(100);
  }, []);

  return (
    <Line
      points={points}
      color="#19B86A"
      lineWidth={3}
      dashed={false}
      transparent
      opacity={0.8}
    />
  );
}

// ── Telemetry Particles ──
function TelemetryParticles({ count = 60 }) {
  const particles = useMemo(() => {
    const temp = [];
    for (let i = 0; i < count; i++) {
      temp.push({
        position: [
          (Math.random() - 0.5) * 20,
          Math.random() * 4,
          (Math.random() - 0.5) * 20
        ],
        scale: Math.random() * 0.05 + 0.02,
        speed: Math.random() * 0.01 + 0.005,
      });
    }
    return temp;
  }, [count]);

  const ref = useRef();
  
  useFrame(({ clock }) => {
    if (ref.current) {
      ref.current.children.forEach((inst, i) => {
        inst.position.y += particles[i].speed;
        if (inst.position.y > 4) inst.position.y = 0;
        inst.material.opacity = 1 - (inst.position.y / 4);
      });
    }
  });

  return (
    <Instances ref={ref} range={count} material={new THREE.MeshBasicMaterial({ color: '#36D98A', transparent: true })}>
      <sphereGeometry args={[1, 8, 8]} />
      {particles.map((data, i) => (
        <Instance key={i} position={data.position} scale={data.scale} />
      ))}
    </Instances>
  );
}

// ── Main Scene ──
function SceneContent() {
  const cameraRef = useRef();
  
  // Subtle mouse parallax
  useFrame(({ mouse }) => {
    if (cameraRef.current) {
      cameraRef.current.position.x = THREE.MathUtils.lerp(cameraRef.current.position.x, 8 + mouse.x * 2, 0.05);
      cameraRef.current.position.y = THREE.MathUtils.lerp(cameraRef.current.position.y, 6 + mouse.y * -1.5, 0.05);
      cameraRef.current.lookAt(0, 0, 0);
    }
  });

  return (
    <>
      <PerspectiveCamera ref={cameraRef} makeDefault position={[8, 6, 8]} fov={35} />
      
      {/* Lighting */}
      <ambientLight intensity={0.4} />
      <directionalLight position={[10, 10, 5]} intensity={1.5} color="#F3F7F5" castShadow />
      <pointLight position={[-5, 2, -5]} intensity={2} color="#19B86A" />
      <pointLight position={[0, 4, 2]} intensity={1.5} color="#36D98A" />
      
      <Environment preset="city" />

      {/* Grid Floor */}
      <gridHelper args={[40, 40, '#063C28', '#07110D']} position={[0, -0.1, 0]} />

      <Float speed={1.5} rotationIntensity={0.1} floatIntensity={0.2}>
        <StylizedTruck position={[0, 0, 0]} rotation={[0, -Math.PI / 6, 0]} />
      </Float>

      <RoutePath />
      <TelemetryParticles />

      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.15, 0]} receiveShadow>
        <planeGeometry args={[100, 100]} />
        <shadowMaterial opacity={0.4} />
      </mesh>
    </>
  );
}

export function Fleet3DScene() {
  return (
    <div className="w-full h-full absolute inset-0 pointer-events-none">
      <Canvas shadows dpr={[1, 2]} gl={{ antialias: true, alpha: true }}>
        <SceneContent />
      </Canvas>
    </div>
  );
}
