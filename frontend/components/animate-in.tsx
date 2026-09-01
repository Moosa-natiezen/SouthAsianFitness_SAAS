"use client";

import { useEffect, useRef, type ReactNode } from "react";
import gsap from "gsap";

interface AnimateInProps {
  children: ReactNode;
  delay?: number;
  duration?: number;
  y?: number;
  x?: number;
  scale?: number;
  rotation?: number;
  blur?: number;
  stagger?: number;
  className?: string;
}

/**
 * GSAP-powered entrance animation component.
 * Elements cascade in with configurable stagger, fade-up, scale, and blur.
 */
export function AnimateIn({
  children,
  delay = 0,
  duration = 0.9,
  y = 30,
  x = 0,
  scale = 1,
  rotation = 0,
  blur = 6,
  className = "",
}: AnimateInProps) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const ctx = gsap.context(() => {
      gsap.fromTo(
        el,
        {
          opacity: 0,
          y,
          x,
          scale: scale < 1 ? scale : 1,
          rotation,
          filter: `blur(${blur}px)`,
        },
        {
          opacity: 1,
          y: 0,
          x: 0,
          scale: 1,
          rotation: 0,
          filter: "blur(0px)",
          duration,
          delay,
          ease: "power3.out",
        },
      );
    }, el);

    return () => ctx.revert();
  }, [delay, duration, y, x, scale, rotation, blur]);

  return (
    <div ref={ref} className={className} style={{ opacity: 0 }}>
      {children}
    </div>
  );
}

/**
 * Staggered container — animates children in sequence.
 * Each direct child gets a staggered delay.
 */
export function StaggerIn({
  children,
  className = "",
  stagger = 0.08,
  delay = 0,
}: {
  children: ReactNode;
  className?: string;
  stagger?: number;
  delay?: number;
}) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const children = el.children;
    if (!children.length) return;

    const ctx = gsap.context(() => {
      gsap.fromTo(
        children,
        {
          opacity: 0,
          y: 24,
          filter: "blur(4px)",
        },
        {
          opacity: 1,
          y: 0,
          filter: "blur(0px)",
          duration: 0.8,
          stagger,
          delay,
          ease: "power3.out",
        },
      );
    }, el);

    return () => ctx.revert();
  }, [stagger, delay]);

  return (
    <div ref={ref} className={className}>
      {children}
    </div>
  );
}


