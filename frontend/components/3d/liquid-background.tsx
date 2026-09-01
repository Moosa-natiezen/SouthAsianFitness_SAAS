"use client";

import { Suspense, useRef, useMemo, useCallback, useEffect, useState } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import * as THREE from "three";

/**
 * Custom GLSL vertex shader for liquid metal distortion.
 * Displaces vertices using layered simplex noise to create a
 * shifting, organic liquid titanium surface.
 */
const vertexShader = /* glsl */ `
  uniform float uTime;
  uniform vec2 uMouse;
  varying vec2 vUv;
  varying vec3 vNormal;
  varying vec3 vWorldPosition;

  // Simplex noise helpers
  vec3 mod289(vec3 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
  vec4 mod289(vec4 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
  vec4 permute(vec4 x) { return mod289(((x*34.0)+1.0)*x); }
  vec4 taylorInvSqrt(vec4 r) { return 1.79284291400159 - 0.85373472095314 * r; }

  float snoise(vec3 v) {
    const vec2 C = vec2(1.0/6.0, 1.0/3.0);
    const vec4 D = vec4(0.0, 0.5, 1.0, 2.0);
    vec3 i = floor(v + dot(v, C.yyy));
    vec3 x0 = v - i + dot(i, C.xxx);
    vec3 g = step(x0.yzx, x0.xyz);
    vec3 l = 1.0 - g;
    vec3 i1 = min(g.xyz, l.zxy);
    vec3 i2 = max(g.xyz, l.zxy);
    vec3 x1 = x0 - i1 + C.xxx;
    vec3 x2 = x0 - i2 + C.yyy;
    vec3 x3 = x0 - D.yyy;
    i = mod289(i);
    vec4 p = permute(permute(permute(
      i.z + vec4(0.0, i1.z, i2.z, 1.0))
      + i.y + vec4(0.0, i1.y, i2.y, 1.0))
      + i.x + vec4(0.0, i1.x, i2.x, 1.0));
    float n_ = 0.142857142857;
    vec3 ns = n_ * D.wyz - D.xzx;
    vec4 j = p - 49.0 * floor(p * ns.z * ns.z);
    vec4 x_ = floor(j * ns.z);
    vec4 y_ = floor(j - 7.0 * x_);
    vec4 x = x_ * ns.x + ns.yyyy;
    vec4 y = y_ * ns.x + ns.yyyy;
    vec4 h = 1.0 - abs(x) - abs(y);
    vec4 b0 = vec4(x.xy, y.xy);
    vec4 b1 = vec4(x.zw, y.zw);
    vec4 s0 = floor(b0)*2.0 + 1.0;
    vec4 s1 = floor(b1)*2.0 + 1.0;
    vec4 sh = -step(h, vec4(0.0));
    vec4 a0 = b0.xzyw + s0.xzyw*sh.xxyy;
    vec4 a1 = b1.xzyw + s1.xzyw*sh.zzww;
    vec3 p0 = vec3(a0.xy,h.x);
    vec3 p1 = vec3(a0.zw,h.y);
    vec3 p2 = vec3(a1.xy,h.z);
    vec3 p3 = vec3(a1.zw,h.w);
    vec4 norm = taylorInvSqrt(vec4(dot(p0,p0),dot(p1,p1),dot(p2,p2),dot(p3,p3)));
    p0 *= norm.x; p1 *= norm.y; p2 *= norm.z; p3 *= norm.w;
    vec4 m = max(0.6 - vec4(dot(x0,x0),dot(x1,x1),dot(x2,x2),dot(x3,x3)), 0.0);
    m = m * m;
    return 42.0 * dot(m*m, vec4(dot(p0,x0),dot(p1,x1),dot(p2,x2),dot(p3,x3)));
  }

  void main() {
    vUv = uv;

    // Multi-octave noise for organic liquid movement
    float slowTime = uTime * 0.15;
    float n1 = snoise(vec3(position.xy * 0.5, slowTime)) * 0.6;
    float n2 = snoise(vec3(position.xy * 1.2 + 10.0, slowTime * 0.7)) * 0.25;
    float n3 = snoise(vec3(position.xy * 2.5 + 20.0, slowTime * 1.3)) * 0.1;

    // Mouse influence — subtle bulge near cursor
    float mouseDist = length(position.xy - uMouse * 3.0);
    float mouseBulge = smoothstep(2.0, 0.0, mouseDist) * 0.3;

    float displacement = n1 + n2 + n3 + mouseBulge;

    vec3 newPos = position;
    newPos.z += displacement;

    // Recompute normals from displacement
    float eps = 0.01;
    float nx = snoise(vec3((position.xy + vec2(eps, 0.0)) * 0.5, slowTime)) * 0.6
             + snoise(vec3((position.xy + vec2(eps, 0.0)) * 1.2 + 10.0, slowTime * 0.7)) * 0.25;
    float ny = snoise(vec3((position.xy + vec2(0.0, eps)) * 0.5, slowTime)) * 0.6
             + snoise(vec3((position.xy + vec2(0.0, eps)) * 1.2 + 10.0, slowTime * 0.7)) * 0.25;

    vec3 computedNormal = normalize(vec3(
      (n1 + n2 - nx) / eps,
      (n1 + n2 - ny) / eps,
      1.0
    ));

    vNormal = normalize(normalMatrix * computedNormal);
    vWorldPosition = (modelMatrix * vec4(newPos, 1.0)).xyz;

    gl_Position = projectionMatrix * modelViewMatrix * vec4(newPos, 1.0);
  }
`;

/**
 * Custom fragment shader for liquid titanium material.
 * Creates a dark, reflective metallic surface that catches
 * the orbiting crimson/violet light.
 */
const fragmentShader = /* glsl */ `
  uniform float uTime;
  uniform vec3 uLightColor;
  uniform vec3 uLightPosition;
  varying vec2 vUv;
  varying vec3 vNormal;
  varying vec3 vWorldPosition;

  void main() {
    // Base titanium color — very dark with subtle blue-gray tint
    vec3 baseColor = vec3(0.04, 0.04, 0.06);

    // Fresnel effect for edge glow
    vec3 viewDir = normalize(cameraPosition - vWorldPosition);
    float fresnel = pow(1.0 - max(dot(viewDir, vNormal), 0.0), 3.0);

    // Light calculation — orbiting point light
    vec3 lightDir = normalize(uLightPosition - vWorldPosition);
    float diff = max(dot(vNormal, lightDir), 0.0);
    float spec = pow(max(dot(reflect(-lightDir, vNormal), viewDir), 0.0), 64.0);

    // Combine: dark metal + colored light reflection + specular highlight
    vec3 color = baseColor;
    color += uLightColor * diff * 0.4;
    color += uLightColor * spec * 1.2;
    color += uLightColor * fresnel * 0.15;

    // Subtle scan-line / noise for metallic grain
    float grain = fract(sin(dot(vUv * 400.0, vec2(12.9898, 78.233))) * 43758.5453);
    color += grain * 0.008;

    gl_FragColor = vec4(color, 1.0);
  }
`;

/**
 * The liquid metal plane with custom shader material.
 */
function LiquidPlane() {
  const meshRef = useRef<THREE.Mesh>(null!);
  const materialRef = useRef<THREE.ShaderMaterial>(null!);

  const uniforms = useMemo(
    () => ({
      uTime: { value: 0 },
      uMouse: { value: new THREE.Vector2(0, 0) },
      uLightColor: { value: new THREE.Color("#DC143C") },
      uLightPosition: { value: new THREE.Vector3(3, 2, 4) },
    }),
    [],
  );

  useFrame((state) => {
    if (!materialRef.current) return;

    const t = state.clock.elapsedTime;
    materialRef.current.uniforms.uTime.value = t;

    // Orbit the crimson light in a slow elliptical path
    const lx = Math.sin(t * 0.3) * 4;
    const ly = Math.cos(t * 0.2) * 2 + 1;
    const lz = Math.cos(t * 0.15) * 3 + 2;
    materialRef.current.uniforms.uLightPosition.value.set(lx, ly, lz);
  });

  const handlePointerMove = useCallback((e: THREE.Event) => {
    if (!materialRef.current) return;
    const me = e as PointerEvent;
    materialRef.current.uniforms.uMouse.value.set(
      (me.clientX / window.innerWidth) * 2 - 1,
      -(me.clientY / window.innerHeight) * 2 + 1,
    );
  }, []);

  useEffect(() => {
    window.addEventListener("pointermove", handlePointerMove);
    return () => window.removeEventListener("pointermove", handlePointerMove);
  }, [handlePointerMove]);

  return (
    <mesh ref={meshRef} rotation={[-0.1, 0, 0]} position={[0, 0, -2]}>
      <planeGeometry args={[16, 12, 128, 128]} />
      <shaderMaterial
        ref={materialRef}
        vertexShader={vertexShader}
        fragmentShader={fragmentShader}
        uniforms={uniforms}
      />
    </mesh>
  );
}

/**
 * Secondary violet accent light that drifts slowly.
 */
function VioletAccent() {
  const ref = useRef<THREE.PointLight>(null!);

  useFrame((state) => {
    if (!ref.current) return;
    const t = state.clock.elapsedTime;
    ref.current.position.set(
      Math.cos(t * 0.12) * 5,
      Math.sin(t * 0.08) * 2,
      Math.sin(t * 0.1) * 3,
    );
  });

  return <pointLight ref={ref} color="#7B61FF" intensity={15} distance={12} decay={2} />;
}

function CanvasFallback() {
  return null;
}

/**
 * LiquidBackground — Full-viewport WebGL canvas that sits behind
 * all app content. Renders a liquid titanium plane with orbiting
 * crimson and violet lights for an avant-garde chrome aesthetic.
 */
export function LiquidBackground() {
  const [ready, setReady] = useState(false);

  // Delay canvas mount to avoid hydration flash
  useEffect(() => {
    const raf = requestAnimationFrame(() => setReady(true));
    return () => cancelAnimationFrame(raf);
  }, []);

  if (!ready) return null;

  return (
    <div
      className="pointer-events-none fixed inset-0 z-0"
      style={{ background: "#05050A" }}
    >
      <Canvas
        camera={{ position: [0, 0, 5], fov: 60 }}
        gl={{ alpha: false, antialias: true, powerPreference: "high-performance" }}
        dpr={[1, 1.5]}
        style={{ background: "#05050A" }}
      >
        <Suspense fallback={<CanvasFallback />}>
          <ambientLight intensity={0.05} color="#1a1a2e" />
          <LiquidPlane />
          <VioletAccent />
        </Suspense>
      </Canvas>
    </div>
  );
}
