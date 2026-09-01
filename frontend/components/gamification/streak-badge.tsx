"use client";

import { Suspense, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Float, ContactShadows, Environment, PresentationControls, RoundedBox } from "@react-three/drei";
import * as THREE from "three";

/**
 * The 3D badge emblem — a metallic coin-like shape
 */
function BadgeEmblem() {
  const meshRef = useRef<THREE.Mesh>(null!);

  useFrame((state) => {
    if (!meshRef.current) return;
    meshRef.current.rotation.y = state.clock.elapsedTime * 0.3;
  });

  return (
    <Float speed={1.5} rotationIntensity={0.2} floatIntensity={0.5}>
      <PresentationControls
        speed={2}
        rotation={[0, 0, 0]}
        polar={[-Math.PI / 4, Math.PI / 4]}
        azimuth={[-Math.PI / 4, Math.PI / 4]}
      >
        <group ref={meshRef}>
          {/* Main badge body */}
          <mesh>
            <cylinderGeometry args={[0.9, 0.9, 0.15, 64]} />
            <meshPhysicalMaterial
              color="#c4854c"
              metalness={0.9}
              roughness={0.15}
              emissive="#c4854c"
              emissiveIntensity={0.15}
              envMapIntensity={2}
            />
          </mesh>

          {/* Inner ring */}
          <mesh position={[0, 0.08, 0]}>
            <torusGeometry args={[0.55, 0.04, 16, 64]} />
            <meshPhysicalMaterial
              color="#e8a838"
              metalness={0.95}
              roughness={0.1}
              emissive="#e8a838"
              emissiveIntensity={0.2}
            />
          </mesh>

          {/* Center star */}
          <mesh position={[0, 0.09, 0]}>
            <octahedronGeometry args={[0.22, 0]} />
            <meshPhysicalMaterial
              color="#f5f0e8"
              metalness={0.8}
              roughness={0.1}
              emissive="#e8a838"
              emissiveIntensity={0.4}
            />
          </mesh>

          {/* Outer decorative ring */}
          <mesh position={[0, 0.08, 0]}>
            <torusGeometry args={[0.78, 0.02, 16, 64]} />
            <meshPhysicalMaterial
              color="#d4a574"
              metalness={0.85}
              roughness={0.2}
            />
          </mesh>
        </group>
      </PresentationControls>
    </Float>
  );
}

function LoadingFallback() {
  return (
    <RoundedBox args={[1, 1, 0.2]} radius={0.1} smoothness={4}>
      <meshBasicMaterial color="#c4854c" wireframe />
    </RoundedBox>
  );
}

interface StreakBadgeProps {
  streak?: number;
}

/**
 * 3D collectible streak badge — floats, rotates, and is interactive.
 * Embed in a fixed-size container.
 */
export function StreakBadge({ streak = 1 }: StreakBadgeProps) {
  return (
    <div className="relative h-40 w-40 pointer-events-auto">
      <Canvas
        camera={{ position: [0, 0, 3.5], fov: 40 }}
        gl={{ alpha: true, antialias: true }}
        style={{ background: "transparent" }}
      >
        <ambientLight intensity={0.4} />
        <directionalLight position={[3, 4, 5]} intensity={0.7} color="#f5f0e8" />
        <pointLight position={[-2, 1, 3]} intensity={0.4} color="#e8a838" />

        <Suspense fallback={<LoadingFallback />}>
          <BadgeEmblem />
          <ContactShadows
            position={[0, -1.2, 0]}
            opacity={0.25}
            scale={4}
            blur={2}
            color="#c4854c"
          />
          <Environment preset="studio" environmentIntensity={0.4} />
        </Suspense>
      </Canvas>

      {/* Streak count overlay */}
      <div className="absolute bottom-2 left-1/2 -translate-x-1/2 rounded-full bg-[#0a0a0a]/80 px-3 py-1 text-xs font-bold text-[#e8a838] backdrop-blur-sm border border-[#e8a838]/20">
        🔥 {streak} day{streak !== 1 ? "s" : ""}
      </div>
    </div>
  );
}
