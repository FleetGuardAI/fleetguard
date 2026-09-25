import React, { useEffect, useMemo, useRef, useState } from 'react';
import { ArrowRight } from 'lucide-react';
import { motion } from 'framer-motion';
import { Canvas, useFrame } from '@react-three/fiber';
import { Html } from '@react-three/drei';
import * as THREE from 'three';

export function HeroSection({ onDemo }) {
  return (
    <section className="relative flex h-screen min-h-[800px] w-full flex-col justify-center overflow-hidden bg-[#050b14]">
      <div className="absolute right-0 top-24 z-[1] hidden h-[500px] w-[52%] max-w-[760px] pointer-events-auto md:block">
        <Canvas shadows dpr={[1, 1.25]} camera={{ position: [0, 5.8, 8.5], fov: 38, near: 0.1, far: 40 }}>
          <CompactFleetScene />
        </Canvas>
      </div>
      <div className="absolute inset-0 z-0 bg-gradient-to-r from-[#050b14]/95 via-[#050b14]/50 to-transparent" />
      <div className="absolute inset-0 z-0 bg-gradient-to-b from-transparent via-transparent to-[#050b14]/90" />
      <div className="absolute inset-x-0 bottom-0 z-0 h-40 bg-gradient-to-t from-[#050b14] via-transparent to-transparent" />

      <div className="container relative z-10 mx-auto flex h-full max-w-7xl flex-col justify-between px-6 pt-24 pointer-events-none">
        <div className="flex flex-1 flex-col justify-center pointer-events-auto">
          <div className="max-w-2xl">
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7 }}>
              <div className="mb-6 text-[10px] font-bold uppercase tracking-widest text-white/50">
                FLEET INTELLIGENCE FOR A MORE EFFICIENT TOMORROW
              </div>
              <h1 className="mb-6 text-5xl font-medium leading-[1.05] tracking-tight text-white sm:text-6xl md:text-7xl lg:text-[80px]">
                Every mile <br />has a story.<br />
                <span className="font-normal text-[#15803d]">We help you understand it.</span>
              </h1>
              <p className="mb-10 max-w-xl text-lg font-light leading-relaxed text-white/60 sm:text-xl">
                The vaahan connects your vehicles, drivers, trips, expenses and more— turning fleet activity into operational and financial intelligence.
              </p>
              <div className="flex flex-col gap-4 sm:flex-row">
                <a href="#platform" className="inline-flex items-center justify-center rounded bg-[#15803d] px-8 py-3.5 text-sm font-medium text-white transition-colors hover:bg-[#166534]">
                  Explore the Platform <ArrowRight className="ml-2 h-4 w-4" />
                </a>
                <button type="button" onClick={onDemo} className="inline-flex items-center justify-center rounded border border-white/20 bg-transparent px-8 py-3.5 text-sm font-medium text-white transition-colors hover:bg-white/5">
                  Book a Demo
                </button>
              </div>
            </motion.div>
          </div>
        </div>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7, delay: 0.3 }} className="flex items-center gap-12 pb-12 pointer-events-auto">
          {['DATA', 'CONTEXT', 'INTELLIGENCE', 'ACTION'].map((label) => (
            <div key={label}>
              <div className="text-xs font-semibold uppercase tracking-[0.18em] text-white/80">{label}</div>
              <div className="mt-1 text-[10px] text-white/40">Connected fleet signal</div>
            </div>
          ))}
        </motion.div>
      </div>

      <div className="absolute right-8 top-32 z-20 hidden pointer-events-auto lg:block">
        <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.7, delay: 0.5 }} className="w-48 rounded-xl border border-white/5 bg-[#0b120f]/55 p-3 shadow-2xl backdrop-blur-md">
          <div className="mb-3 border-b border-white/10 pb-2 text-[10px] font-bold uppercase tracking-wider text-white/80">Live Fleet</div>
          <div className="space-y-2 text-[10px] text-white/60">
            <div className="flex items-center gap-2"><span className="h-1.5 w-1.5 rounded-full bg-[#67d89a]" />Signal detected</div>
            <div className="flex items-center gap-2"><span className="h-1.5 w-1.5 rounded-full bg-[#e8a33d]" />Context added</div>
            <div className="flex items-center gap-2"><span className="h-1.5 w-1.5 rounded-full bg-[#9ed7b3]" />Next action clarified</div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}

function CompactFleetScene() {
  const world = useRef();
  const reducedMotion = typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const [activeEvent, setActiveEvent] = useState('FUEL');
  const [activeRoute, setActiveRoute] = useState(null);

  const routes = useMemo(() => [
    { id: 'foreground', points: [[-3.55, 0.22, 1.45], [-2.2, 0.25, 1.1], [-0.65, 0.35, 0.65], [0.8, 0.32, 0.15], [3.55, 0.25, -0.25]], scale: 1.24, speed: 0.105, delay: 0.12, color: '#d9eee0' },
    { id: 'middle-a', points: [[-3.2, 0.02, -0.2], [-1.65, 0.08, -0.35], [-0.35, 0.2, 0.05], [1.2, 0.18, 0.75], [3.25, 0.12, 1.1]], scale: 0.92, speed: 0.14, delay: 0.43, color: '#9ed7b3' },
    { id: 'middle-b', points: [[-2.7, -0.08, -1.25], [-1.35, -0.04, -1.05], [0.1, 0.08, -0.45], [1.55, 0.04, -0.85], [2.8, 0.02, -1.35]], scale: 0.9, speed: 0.12, delay: 0.68, color: '#79bd94' },
    { id: 'background', points: [[-2.45, -0.18, -1.9], [-1.2, -0.15, -1.75], [0.2, -0.08, -1.45], [1.55, -0.12, -1.65], [2.7, -0.15, -1.9]], scale: 0.68, speed: 0.09, delay: 0.28, color: '#5d9c78' },
  ], []);

  const events = useMemo(() => [
    { id: 'FUEL', label: 'FUEL SIGNAL', route: 'foreground', position: [-0.55, 0.72, 0.68], color: '#e8a33d', detail: 'Context added' },
    { id: 'TRIP', label: 'TRIP CONTEXT', route: 'middle-a', position: [1.18, 0.55, 0.73], color: '#67d89a', detail: 'Action clarified' },
    { id: 'RISK', label: 'RISK SIGNAL', route: 'middle-b', position: [0.42, 0.42, -0.47], color: '#e99486', detail: 'Review suggested' },
  ], []);

  useEffect(() => {
    if (reducedMotion) return undefined;
    const timer = window.setInterval(() => {
      setActiveEvent((current) => events[(events.findIndex((event) => event.id === current) + 1) % events.length].id);
    }, 5000);
    return () => window.clearInterval(timer);
  }, [events, reducedMotion]);

  useFrame((state) => {
    if (!world.current) return;
    world.current.rotation.y += (((state.pointer.x || 0) * 0.045) - world.current.rotation.y) * 0.04;
    world.current.rotation.x += (((state.pointer.y || 0) * -0.02) - world.current.rotation.x) * 0.04;
  });

  const selectedEvent = events.find((event) => event.id === activeEvent) || events[0];
  return (
    <>
      <color attach="background" args={['#050b14']} />
      <ambientLight intensity={0.7} />
      <directionalLight position={[2, 6, 4]} intensity={2.1} color="#dcffe8" castShadow />
      <pointLight position={[0, 1.8, 0]} intensity={4} distance={7} color="#4bd486" />
      <group ref={world}>
        <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.36, -0.15]} receiveShadow>
          <planeGeometry args={[7.9, 4.15]} />
          <meshStandardMaterial color="#09130f" roughness={0.95} transparent opacity={0.72} />
        </mesh>
        {routes.map((route) => (
          <React.Fragment key={route.id}>
            {route.points.slice(0, -1).map((point, index) => (
              <SceneLine key={`${route.id}-${index}`} start={point} end={route.points[index + 1]} active={activeRoute === route.id} />
            ))}
            <MiniTruck route={route.points} speed={reducedMotion ? 0 : route.speed} delay={route.delay} scale={route.scale} color={route.color} active={activeRoute === route.id} onPointerOver={() => setActiveRoute(route.id)} onPointerOut={() => setActiveRoute(null)} onClick={() => setActiveEvent(events.find((event) => event.route === route.id)?.id || 'FUEL')} />
          </React.Fragment>
        ))}
        <IntelligenceHub active={activeRoute !== null} onPointerOver={() => setActiveRoute('hub')} onPointerOut={() => setActiveRoute(null)} onClick={() => setActiveEvent('FUEL')} />
        {events.map((event) => (
          <React.Fragment key={event.id}>
            <SceneLine start={event.position} end={[0, 0.62, 0]} active={selectedEvent.id === event.id || activeRoute === event.route} />
            <SignalPacket start={event.position} color={event.color} paused={reducedMotion} />
            <group position={event.position} onPointerOver={() => setActiveEvent(event.id)} onClick={() => setActiveEvent(event.id)}>
              <mesh>
                <octahedronGeometry args={[0.13, 0]} />
                <meshStandardMaterial color={event.color} emissive={event.color} emissiveIntensity={selectedEvent.id === event.id ? 1.1 : 0.35} />
              </mesh>
              <Html center position={[0, 0.22, 0]} distanceFactor={7} className="pointer-events-none">
                <div className={`whitespace-nowrap rounded border px-2 py-1 text-[8px] font-semibold uppercase tracking-[0.14em] ${selectedEvent.id === event.id ? 'border-white/30 bg-[#07110c]/90 text-white' : 'border-white/10 bg-[#07110c]/55 text-white/45'}`}>
                  {event.label}
                </div>
              </Html>
            </group>
          </React.Fragment>
        ))}
        <Html center position={[0, 1.48, 0]} distanceFactor={7} className="pointer-events-none">
          <div className="rounded-lg border border-emerald-200/30 bg-[#07110c]/90 px-3 py-2 text-center shadow-[0_0_24px_rgba(74,209,124,0.14)] backdrop-blur-md">
            <div className="text-[8px] uppercase tracking-[0.18em] text-emerald-200/70">Fleet intelligence</div>
            <div className="text-[11px] font-semibold text-white">Context → action</div>
          </div>
        </Html>
        <Html center position={[0, -0.86, 0]} distanceFactor={7} className="pointer-events-none">
          <div className="rounded-full border border-white/10 bg-[#07110c]/80 px-3 py-1 text-[8px] font-semibold uppercase tracking-[0.15em] text-white/70">
            {selectedEvent.id} · {selectedEvent.detail}
          </div>
        </Html>
      </group>
    </>
  );
}

function IntelligenceHub({ active, onPointerOver, onPointerOut, onClick }) {
  const rings = useRef();
  useFrame((state) => {
    if (rings.current) rings.current.rotation.z = state.clock.elapsedTime * 0.35;
  });
  return (
    <group position={[0, 0.4, 0]} onPointerOver={onPointerOver} onPointerOut={onPointerOut} onClick={onClick}>
      <mesh>
        <cylinderGeometry args={[0.42, 0.53, 0.38, 24]} />
        <meshStandardMaterial color="#1e5138" emissive="#3b9b63" emissiveIntensity={active ? 1.1 : 0.65} metalness={0.45} roughness={0.25} />
      </mesh>
      <group ref={rings}>
        <mesh rotation={[Math.PI / 2.4, 0.2, 0]}>
          <torusGeometry args={[0.68, 0.025, 8, 48]} />
          <meshStandardMaterial color="#8fe9ae" emissive="#4ad17c" emissiveIntensity={active ? 1.5 : 0.8} />
        </mesh>
        <mesh rotation={[Math.PI / 2.1, -0.35, 0]}>
          <torusGeometry args={[0.52, 0.018, 8, 48]} />
          <meshStandardMaterial color="#4f9d70" emissive="#4ad17c" emissiveIntensity={0.7} />
        </mesh>
      </group>
      {[-1, 1].map((x) => <mesh key={x} position={[x * 0.48, 0.1, 0]}><sphereGeometry args={[0.055, 10, 10]} /><meshBasicMaterial color="#a4f2bd" /></mesh>)}
    </group>
  );
}

function MiniTruck({ route, speed, delay, scale, color, active, onPointerOver, onPointerOut, onClick }) {
  const ref = useRef();
  useFrame((state) => {
    if (!ref.current) return;
    const progress = (state.clock.elapsedTime * speed + delay) % 1;
    const index = Math.min(route.length - 2, Math.floor(progress * (route.length - 1)));
    const local = progress * (route.length - 1) - index;
    const from = new THREE.Vector3(...route[index]);
    const to = new THREE.Vector3(...route[index + 1]);
    ref.current.position.copy(from.lerp(to, local));
    ref.current.rotation.y = Math.atan2(to.x - from.x, to.z - from.z);
  });
  return (
    <group ref={ref} scale={scale} onPointerOver={onPointerOver} onPointerOut={onPointerOut} onClick={onClick} castShadow>
      <mesh scale={active ? 1.08 : 1}><boxGeometry args={[0.38, 0.25, 0.7]} /><meshStandardMaterial color={color} emissive={active ? '#4ad17c' : '#000000'} emissiveIntensity={active ? 0.55 : 0} metalness={0.45} roughness={0.35} /></mesh>
      <mesh position={[0, 0.19, 0.12]}><boxGeometry args={[0.33, 0.19, 0.28]} /><meshStandardMaterial color="#3f9b67" emissive="#2f784f" emissiveIntensity={0.45} /></mesh>
      {[-0.16, 0.16].map((x) => <mesh key={x} position={[x, -0.15, -0.18]} rotation={[Math.PI / 2, 0, 0]}><cylinderGeometry args={[0.08, 0.08, 0.06, 10]} /><meshStandardMaterial color="#101713" /></mesh>)}
      <mesh position={[0, 0.05, 0]} scale={[1.8, 1.7, 1.45]} visible={false}><boxGeometry args={[0.38, 0.25, 0.7]} /><meshBasicMaterial transparent opacity={0} /></mesh>
    </group>
  );
}

function SignalPacket({ start, color, paused }) {
  const ref = useRef();
  useFrame((state) => {
    if (!ref.current || paused) return;
    const progress = (state.clock.elapsedTime * 0.18 + Math.abs(start[0]) * 0.08) % 1;
    ref.current.position.set(start[0] * (1 - progress), start[1] * (1 - progress) + 0.62 * progress, start[2] * (1 - progress));
  });
  return <mesh ref={ref}><sphereGeometry args={[0.052, 8, 8]} /><meshBasicMaterial color={color} /></mesh>;
}

function SceneLine({ start, end, active = false }) {
  return <line><bufferGeometry attach="geometry" setFromPoints={[new THREE.Vector3(...start), new THREE.Vector3(...end)]} /><lineBasicMaterial color={active ? '#a4f2bd' : '#4f9d70'} transparent opacity={active ? 0.82 : 0.25} /></line>;
}
