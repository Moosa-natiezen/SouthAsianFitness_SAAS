"use client";

import { Suspense, useRef, useMemo } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { PresentationControls, MeshDistortMaterial, Environment, ContactShadows } from "@react-three/drei";
import * as THREE from "three";

interface MacroSphereProps {
  proteinProgress: number; // 0-100
  calorieProgress: number; // 0-100
}

/**
 * 3D sphere that morphs and glows based on macro progress.
 * Color transitions from dim terracotta (low) → glowing saffron (high).
 */
function SphereMesh({ proteinProgress, calorieProgress }: MacroSphereProps) {
  const meshRef = useRef<THREE.Mesh>(null!);

  // Blend progress into a 0-1 value (average of both)
  const overallProgress = Math.min(100, (proteinProgress + calorieProgress) / 2) / 100;

  // Color transitions: low = muted terracotta, high = bright saffron
  const baseColor = useMemo(() => new THREE.Color("#DC143C"), []);
  const glowColor = useMemo(() => new THREE.Color("#7B61FF"), []);
  const currentColor = useMemo(
    () => baseColor.clone().lerp(glowColor, overallProgress),
    [baseColor, glowColor, overallProgress],
  );

  // Emissive intensity increases with progress
  const emissiveIntensity = 0.1 + overallProgress * 0.6;
  const distort = 0.15 + overallProgress * 0.2;

  useFrame((state) => {
    if (!meshRef.current) return;
    // Gentle idle rotation
    meshRef.current.rotation.y = state.clock.elapsedTime * 0.15;
    meshRef.current.rotation.x = Math.sin(state.clock.elapsedTime * 0.1) * 0.1;
  });

  return (
    <mesh ref={meshRef} scale={1.8}>
      <sphereGeometry args={[1, 64, 64]} />
      <MeshDistortMaterial
        color={currentColor}
        emissive={currentColor}
        emissiveIntensity={emissiveIntensity}
        roughness={0.2}
        metalness={0.8}
        distort={distort}
        speed={2}
        envMapIntensity={1.5}
      />
    </mesh>
  );
}

/**
 * Ambient particles floating around the sphere
 */
function Particles({ count = 40 }: { count?: number }) {
  const meshRef = useRef<THREE.InstancedMesh>(null!);

  const positions = useMemo(() => {
    const pos = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      const r = 2.5 + Math.random() * 1.5;
      pos[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      pos[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
      pos[i * 3 + 2] = r * Math.cos(phi);
    }
    return pos;
  }, [count]);

  const dummy = useMemo(() => new THREE.Object3D(), []);

  useFrame((state) => {
    if (!meshRef.current) return;
    for (let i = 0; i < count; i++) {
      const t = state.clock.elapsedTime * 0.3 + i * 0.5;
      dummy.position.set(
        positions[i * 3] + Math.sin(t) * 0.2,
        positions[i * 3 + 1] + Math.cos(t * 0.7) * 0.3,
        positions[i * 3 + 2] + Math.sin(t * 0.5) * 0.2,
      );
      const scale = 0.02 + Math.sin(t * 2) * 0.01;
      dummy.scale.setScalar(scale);
      dummy.updateMatrix();
      meshRef.current.setMatrixAt(i, dummy.matrix);
    }
    meshRef.current.instanceMatrix.needsUpdate = true;
  });

  return (
    <instancedMesh ref={meshRef} args={[undefined, undefined, count]}>
      <sphereGeometry args={[1, 8, 8]} />
      <meshBasicMaterial color="#7B61FF" transparent opacity={0.6} />
    </instancedMesh>
  );
}

/**
 * Loading fallback inside the Canvas
 */
function LoadingFallback() {
  return (
    <mesh scale={1.5}>
      <sphereGeometry args={[1, 16, 16]} />
      <meshBasicMaterial color="#818CF8" wireframe />
    </mesh>
  );
}

/**
 * 3D MacroSphere — interactive sphere that visualizes nutrition progress.
 * Embed in a fixed-size container. The Canvas handles its own rendering.
 */
export function MacroSphere({ proteinProgress, calorieProgress }: MacroSphereProps) {
  return (
    <div className="relative h-64 w-64 pointer-events-auto">
      <Canvas
        camera={{ position: [0, 0, 5], fov: 45 }}
        gl={{ alpha: true, antialias: true }}
        style={{ background: "transparent" }}
      >
        <ambientLight intensity={0.3} />
        <directionalLight position={[5, 5, 5]} intensity={0.8} color="#FFFFFF" />
        <pointLight position={[-3, 2, 4]} intensity={0.5} color="#7B61FF" />
        <pointLight position={[3, -2, 3]} intensity={0.3} color="#818CF8" />

        <Suspense fallback={<LoadingFallback />}>
          <PresentationControls
            speed={1.5}
            rotation={[0, 0, 0]}
            polar={[-0.4, 0.4]}
            azimuth={[-0.6, 0.6]}
          >
            <SphereMesh
              proteinProgress={proteinProgress}
              calorieProgress={calorieProgress}
            />
            <Particles count={35} />
          </PresentationControls>

          <Environment preset="studio" environmentIntensity={0.3} />
          <ContactShadows
            position={[0, -1.8, 0]}
            opacity={0.3}
            scale={5}
            blur={2.5}
            color="#818CF8"
          />
        </Suspense>
      </Canvas>
    </div>
  );
}
