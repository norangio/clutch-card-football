/**
 * Per-event scene effects (plan section 4).
 *
 * Each is driven by an explicit game event, never inferred from a snapshot
 * diff. All procedural: no textures, no sprites, no external assets.
 *
 * Every effect must degrade to nothing under reduced motion rather than
 * becoming a static artefact stuck on screen.
 */

import { useFrame } from "@react-three/fiber";
import { useMemo, useRef } from "react";
import * as THREE from "three";

import type { CardColor } from "../api/types";

const TEAM_HEX: Record<CardColor, string> = { red: "#c8443c", black: "#33333c" };

// ------------------------------------------------------------------ confetti

const CONFETTI_COUNT = 220;

/**
 * Instanced confetti burst. Runs on a local clock so it always plays from the
 * start when `active` flips, rather than joining mid-flight.
 */
export function Confetti({
  active,
  origin,
  color,
}: {
  active: boolean;
  origin: number;
  color: CardColor;
}) {
  const mesh = useRef<THREE.InstancedMesh>(null);
  const t = useRef(0);
  const dummy = useMemo(() => new THREE.Object3D(), []);

  const seeds = useMemo(
    () =>
      Array.from({ length: CONFETTI_COUNT }, (_, i) => ({
        // Deterministic scatter: a hash, not Math.random, so a replay of the
        // same game looks the same.
        vx: (((i * 73) % 100) / 100 - 0.5) * 3.4,
        vy: 2.6 + (((i * 37) % 100) / 100) * 3.4,
        vz: (((i * 191) % 100) / 100 - 0.5) * 3.0,
        spin: (((i * 53) % 100) / 100 - 0.5) * 9,
        tint: i % 3,
      })),
    [],
  );

  useFrame((_, dt) => {
    const m = mesh.current;
    if (!m) return;

    if (!active) {
      t.current = 0;
      m.visible = false;
      return;
    }

    m.visible = true;
    t.current += dt;
    const age = t.current;

    for (let i = 0; i < CONFETTI_COUNT; i++) {
      const s = seeds[i];
      if (!s) continue;
      const y = 0.4 + s.vy * age - 4.6 * age * age;
      if (y < -0.2) {
        // Park spent pieces far below the table instead of hiding per-instance.
        dummy.position.set(0, -50, 0);
      } else {
        dummy.position.set(origin + s.vx * age, y, s.vz * age);
        dummy.rotation.set(age * s.spin, age * s.spin * 0.7, age * s.spin * 0.4);
      }
      dummy.updateMatrix();
      m.setMatrixAt(i, dummy.matrix);
    }
    m.instanceMatrix.needsUpdate = true;
  });

  return (
    <instancedMesh
      ref={mesh}
      args={[undefined, undefined, CONFETTI_COUNT]}
      visible={false}
    >
      <planeGeometry args={[0.09, 0.055]} />
      <meshStandardMaterial
        color={TEAM_HEX[color]}
        side={THREE.DoubleSide}
        emissive={TEAM_HEX[color]}
        emissiveIntensity={0.35}
        roughness={0.6}
      />
    </instancedMesh>
  );
}

// -------------------------------------------------------------- drama lights

/**
 * Cuts the ambient and drops a hard spotlight at midfield. Used for war and
 * joker, where the whole point is that the table goes quiet.
 */
export function DramaLight({
  active,
  color,
  reduced,
}: {
  active: boolean;
  color: string;
  reduced: boolean;
}) {
  const light = useRef<THREE.SpotLight>(null);
  const level = useRef(0);

  useFrame((_, dt) => {
    const l = light.current;
    if (!l) return;
    const want = active ? 1 : 0;
    level.current += (want - level.current) * (reduced ? 1 : Math.min(1, dt * 5));
    l.intensity = level.current * 60;
  });

  return (
    <spotLight
      ref={light}
      position={[0, 5.2, 1.4]}
      angle={0.5}
      penumbra={0.75}
      intensity={0}
      color={color}
      distance={16}
      castShadow
    />
  );
}

/** Warm pulse over the scoring end zone. */
export function ScoreGlow({
  active,
  x,
  color,
  reduced,
}: {
  active: boolean;
  x: number;
  color: CardColor;
  reduced: boolean;
}) {
  const light = useRef<THREE.PointLight>(null);
  const t = useRef(0);

  useFrame((_, dt) => {
    const l = light.current;
    if (!l) return;
    if (!active) {
      t.current = 0;
      l.intensity = 0;
      return;
    }
    t.current += dt;
    // Two quick pulses then hold, so it reads as a celebration not a fade.
    const pulse = reduced ? 1 : 0.6 + 0.4 * Math.sin(t.current * 9);
    l.intensity = pulse * 26;
  });

  return (
    <pointLight
      ref={light}
      position={[x, 1.5, 0]}
      color={TEAM_HEX[color]}
      distance={9}
      intensity={0}
    />
  );
}

/** Field darkens on a safety: the offense just gave up two. */
export function SafetyDim({ active, reduced }: { active: boolean; reduced: boolean }) {
  const mesh = useRef<THREE.Mesh>(null);
  const level = useRef(0);

  useFrame((_, dt) => {
    const m = mesh.current;
    if (!m) return;
    const want = active ? 0.62 : 0;
    level.current += (want - level.current) * (reduced ? 1 : Math.min(1, dt * 6));
    const mat = m.material as THREE.MeshBasicMaterial;
    mat.opacity = level.current;
    m.visible = level.current > 0.01;
  });

  return (
    <mesh ref={mesh} position={[0, 1.2, 0]} visible={false}>
      <boxGeometry args={[40, 12, 30]} />
      <meshBasicMaterial
        color="#04100b"
        transparent
        opacity={0}
        side={THREE.BackSide}
        depthWrite={false}
      />
    </mesh>
  );
}
