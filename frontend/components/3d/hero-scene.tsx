"use client";

import { Suspense, useRef, useMemo } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import {
  PresentationControls,
  MeshDistortMaterial,
  Environment,
  ContactShadows,
} from "@react-three/drei";
import * as THREE from "three";

/**
 * Abstract metallic artifact — slowly rotating, morphing sphere
 * that subtly follows mouse position for a premium feel.
 */
function HeroArtifact() {
  const meshRef = useRef<THREE.Mesh>(null!);
  const mouseRef = useRef({ x: 0, y: 0 });
  const { viewport } = useThree();

  useFrame((state) => {
    if (!meshRef.current) return;

    // Track mouse via pointer
    const pointer = state.pointer;
    mouseRef.current.x = THREE.MathUtils.lerp(mouseRef.current.x, pointer.x, 0.05);
    mouseRef.current.y = THREE.MathUtils.lerp(mouseRef.current.y, pointer.y, 0.05);

    // Slow rotation + mouse influence
    meshRef.current.rotation.y = state.clock.elapsedTime * 0.12 + mouseRef.current.x * 0.3;
    meshRef.current.rotation.x =
      Math.sin(state.clock.elapsedTime * 0.08) * 0.15 + mouseRef.current.y * 0.15;
    meshRef.current.rotation.z = Math.sin(state.clock.elapsedTime * 0.05) * 0.05;
  });

  return (
    <mesh ref={meshRef} scale={2.2} position={[0, 0, 0]}>
      <icosahedronGeometry args={[1, 6]} />
      <MeshDistortMaterial
        color="#FF4500"
        emissive="#00E5FF"
        emissiveIntensity={0.35}
        roughness={0.15}
        metalness={0.92}
        distort={0.2}
        speed={1.5}
        envMapIntensity={2}
      />
    </mesh>
  );
}

/**
 * Floating particles orbiting the artifact
 */
function OrbitalParticles({ count = 50 }: { count?: number }) {
  const meshRef = useRef<THREE.InstancedMesh>(null!);

  const data = useMemo(() => {
    const pos = new Float32Array(count * 3);
    const speeds = new Float32Array(count);
    for (let i = 0; i < count; i++) {
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      const r = 2.8 + Math.random() * 2;
      pos[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      pos[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
      pos[i * 3 + 2] = r * Math.cos(phi);
      speeds[i] = 0.2 + Math.random() * 0.4;
    }
    return { pos, speeds };
  }, [count]);

  const dummy = useMemo(() => new THREE.Object3D(), []);

  useFrame((state) => {
    if (!meshRef.current) return;
    for (let i = 0; i < count; i++) {
      const t = state.clock.elapsedTime * data.speeds[i] + i * 0.4;
      const orbitAngle = t * 0.5;
      dummy.position.set(
        data.pos[i * 3] * Math.cos(orbitAngle * 0.3) + Math.sin(t) * 0.15,
        data.pos[i * 3 + 1] + Math.cos(t * 0.7) * 0.25,
        data.pos[i * 3 + 2] * Math.sin(orbitAngle * 0.3) + Math.cos(t * 0.4) * 0.15,
      );
      const s = 0.015 + Math.sin(t * 2.5) * 0.008;
      dummy.scale.setScalar(s);
      dummy.updateMatrix();
      meshRef.current.setMatrixAt(i, dummy.matrix);
    }
    meshRef.current.instanceMatrix.needsUpdate = true;
  });

  return (
    <instancedMesh ref={meshRef} args={[undefined, undefined, count]}>
      <sphereGeometry args={[1, 8, 8]} />
      <meshBasicMaterial color="#00E5FF" transparent opacity={0.5} />
    </instancedMesh>
  );
}

/**
 * Wireframe ring accent orbiting the artifact
 */
function AccentRing() {
  const ref = useRef<THREE.Mesh>(null!);

  useFrame((state) => {
    if (!ref.current) return;
    ref.current.rotation.x = state.clock.elapsedTime * 0.08 + 0.5;
    ref.current.rotation.z = state.clock.elapsedTime * 0.05;
  });

  return (
    <mesh ref={ref} scale={3.2}>
      <torusGeometry args={[1, 0.008, 16, 100]} />
      <meshBasicMaterial color="#FF4500" transparent opacity={0.25} />
    </mesh>
  );
}

function LoadingFallback() {
  return (
    <mesh scale={2}>
      <icosahedronGeometry args={[1, 2]} />
      <meshBasicMaterial color="#FF4500" wireframe />
    </mesh>
  );
}

/**
 * HeroScene — Full-width premium 3D hero canvas.
 * Renders an abstract metallic artifact with particles and accent ring.
 * Responds to mouse movement for an interactive feel.
 */
export function HeroScene() {
  return (
    <div className="pointer-events-auto absolute inset-0 z-0">
      <Canvas
        camera={{ position: [0, 0, 6], fov: 40 }}
        gl={{ alpha: true, antialias: true }}
        style={{ background: "transparent" }}
        dpr={[1, 2]}
      >
        <ambientLight intensity={0.2} />
        <directionalLight position={[5, 5, 5]} intensity={0.6} color="#FFFFFF" />
        <pointLight position={[-4, 3, 4]} intensity={0.8} color="#FF4500" distance={12} />
        <pointLight position={[4, -2, 3]} intensity={0.4} color="#00E5FF" distance={10} />
        <pointLight position={[0, 0, -3]} intensity={0.2} color="#FF4500" distance={8} />

        <Suspense fallback={<LoadingFallback />}>
          <PresentationControls
            speed={1.2}
            rotation={[0, 0, 0]}
            polar={[-0.3, 0.3]}
            azimuth={[-0.4, 0.4]}
          >
            <HeroArtifact />
            <OrbitalParticles count={45} />
            <AccentRing />
          </PresentationControls>

          <Environment preset="studio" environmentIntensity={0.4} />
          <ContactShadows
            position={[0, -2.5, 0]}
            opacity={0.25}
            scale={8}
            blur={3}
            color="#FF4500"
          />
        </Suspense>
      </Canvas>
    </div>
  );
}
