/**
 * The tabletop stadium (plan Phase 3).
 *
 * Premium tabletop, not broadcast realism: a miniature field on a table, warm
 * key light, felt and wood. Everything is procedural R3F geometry. No Blender,
 * no .glb, no external assets (plan 7.1) so this can never become the reason
 * the project stalls.
 *
 * The game only models seven field segments, so the scene visualizes exactly
 * that and nothing more. No players, no routes, no formations.
 */

import { Canvas } from "@react-three/fiber";
import { useFrame } from "@react-three/fiber";
import { useEffect, useMemo, useRef, useState } from "react";
import * as THREE from "three";

import type { Ball, CardColor } from "../api/types";

/** Playable segments, matching ccf/field.py minus the unused index 0. */
const SEGMENTS: Ball[] = ["1", "2", "3", "Z3", "Z2", "Z1"];

const SEG_W = 1.55;
const FIELD_LEN = SEGMENTS.length * SEG_W;
const HALF = FIELD_LEN / 2;

/** World x for a segment's centre. */
function xFor(ball: Ball): number {
  const i = SEGMENTS.indexOf(ball);
  const index = i === -1 ? 0 : i;
  return -HALF + SEG_W * (index + 0.5);
}

const TEAM_HEX: Record<CardColor, string> = { red: "#c8443c", black: "#33333c" };

// ---------------------------------------------------------------------- ball

function Football({ target, arc }: { target: number; arc: boolean }) {
  const ref = useRef<THREE.Group>(null);
  const pos = useRef(target);
  const spin = useRef(0);

  useFrame((_, dt) => {
    const g = ref.current;
    if (!g) return;
    const delta = target - pos.current;
    const dist = Math.abs(delta);

    if (dist > 0.002) {
      // Critically-damped-ish ease so the ball settles rather than snapping.
      pos.current += delta * Math.min(1, dt * 4.2);
      spin.current += dt * (arc ? 9 : 6) * Math.sign(delta || 1);
      // Hop on the way. Punts and kicks get a taller arc.
      const travelled = 1 - Math.min(1, dist / Math.max(0.6, Math.abs(delta) + dist));
      g.position.y = 0.3 + Math.sin(travelled * Math.PI) * (arc ? 1.5 : 0.42);
    } else {
      pos.current = target;
      g.position.y += (0.3 - g.position.y) * Math.min(1, dt * 6);
      spin.current += dt * 0.55;
    }

    g.position.x = pos.current;
    g.rotation.z = spin.current;
  });

  return (
    <group ref={ref} position={[target, 0.3, 0]}>
      {/* Lathe would be prettier; a squashed icosahedron reads correctly at
          this scale and costs far less. */}
      <mesh castShadow scale={[0.34, 0.21, 0.21]}>
        <icosahedronGeometry args={[1, 2]} />
        <meshStandardMaterial color="#7c431f" roughness={0.55} metalness={0.04} />
      </mesh>
      <mesh scale={[0.352, 0.06, 0.216]}>
        <icosahedronGeometry args={[1, 2]} />
        <meshStandardMaterial color="#f3ece1" roughness={0.4} />
      </mesh>
    </group>
  );
}

// --------------------------------------------------------------------- field

function Field({ offense }: { offense: CardColor }) {
  const stripes = useMemo(
    () =>
      SEGMENTS.map((seg, i) => ({
        seg,
        x: -HALF + SEG_W * (i + 0.5),
        endzone: seg.startsWith("Z"),
      })),
    [],
  );

  return (
    <group>
      {/* table */}
      <mesh receiveShadow rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.16, 0]}>
        <planeGeometry args={[26, 18]} />
        <meshStandardMaterial color="#4a3524" roughness={0.9} />
      </mesh>

      {/* felt bed */}
      <mesh receiveShadow position={[0, -0.06, 0]}>
        <boxGeometry args={[FIELD_LEN + 0.7, 0.12, 5.1]} />
        <meshStandardMaterial color="#123a2b" roughness={0.98} />
      </mesh>

      {stripes.map(({ seg, x, endzone }) => (
        <group key={seg} position={[x, 0, 0]}>
          <mesh receiveShadow position={[0, 0.005, 0]}>
            <boxGeometry args={[SEG_W - 0.06, 0.02, 4.4]} />
            <meshStandardMaterial
              color={endzone ? "#17553d" : "#1d6647"}
              roughness={0.95}
            />
          </mesh>
          {/* yard line on the near edge of each segment */}
          <mesh position={[-SEG_W / 2 + 0.03, 0.02, 0]}>
            <boxGeometry args={[0.035, 0.01, 4.4]} />
            <meshStandardMaterial color="#f0ece2" roughness={0.6} />
          </mesh>
        </group>
      ))}

      {/* end zone floods the far end in the offense's colour */}
      <mesh position={[HALF - SEG_W / 2, 0.021, 0]}>
        <boxGeometry args={[SEG_W - 0.1, 0.012, 4.4]} />
        <meshStandardMaterial
          color={TEAM_HEX[offense]}
          emissive={TEAM_HEX[offense]}
          emissiveIntensity={0.32}
          roughness={0.8}
        />
      </mesh>

      <Uprights x={HALF + 0.28} />
      <Uprights x={-HALF - 0.28} />
      <Crowd />
    </group>
  );
}

function Uprights({ x }: { x: number }) {
  const gold = "#d8b45a";
  return (
    <group position={[x, 0, 0]}>
      <mesh castShadow position={[0, 0.45, 0]}>
        <cylinderGeometry args={[0.045, 0.045, 0.9, 10]} />
        <meshStandardMaterial color={gold} metalness={0.55} roughness={0.35} />
      </mesh>
      <mesh castShadow position={[0, 0.9, 0]} rotation={[Math.PI / 2, 0, 0]}>
        <cylinderGeometry args={[0.035, 0.035, 1.7, 10]} />
        <meshStandardMaterial color={gold} metalness={0.55} roughness={0.35} />
      </mesh>
      {[-0.85, 0.85].map((z) => (
        <mesh key={z} castShadow position={[0, 1.4, z]}>
          <cylinderGeometry args={[0.035, 0.035, 1.0, 10]} />
          <meshStandardMaterial color={gold} metalness={0.55} roughness={0.35} />
        </mesh>
      ))}
    </group>
  );
}

/** Instanced blocks, not spectators. Suggests a stadium at zero cost. */
function Crowd() {
  const rows = useMemo(() => {
    const out: Array<[number, number, number, number]> = [];
    for (let side = -1; side <= 1; side += 2) {
      for (let r = 0; r < 3; r++) {
        for (let i = 0; i < 26; i++) {
          const x = -HALF - 0.6 + (i / 25) * (FIELD_LEN + 1.2);
          const z = side * (2.9 + r * 0.42);
          out.push([x, 0.16 + r * 0.2, z, (i * 37 + r * 11) % 5]);
        }
      }
    }
    return out;
  }, []);

  const palette = ["#2b3f52", "#334a5e", "#2a3646", "#3a5068", "#26333f"];

  return (
    <group>
      {rows.map(([x, y, z, tint], i) => (
        <mesh key={i} position={[x, y, z]}>
          <boxGeometry args={[0.16, 0.3, 0.16]} />
          <meshStandardMaterial color={palette[tint] ?? palette[0]} roughness={1} />
        </mesh>
      ))}
    </group>
  );
}

// -------------------------------------------------------------------- camera

/**
 * Fixed broadcast shots, not free orbit (plan 3.3). The camera eases toward the
 * active shot so cuts never feel abrupt.
 */
type Shot = "broadcast" | "endzone" | "wide";

const SHOTS: Record<Shot, { pos: [number, number, number]; look: [number, number, number] }> = {
  broadcast: { pos: [0, 6.0, 8.0], look: [0, -0.15, 0] },
  endzone: { pos: [HALF + 4.2, 2.4, 0.2], look: [HALF - 1.5, 0.5, 0] },
  wide: { pos: [0, 9.4, 8.6], look: [0, -0.2, 0] },
};

function CameraDirector({ shot, reduced }: { shot: Shot; reduced: boolean }) {
  const target = useRef(new THREE.Vector3(...SHOTS.broadcast.look));

  useFrame(({ camera }, dt) => {
    const want = SHOTS[shot];
    const lerp = reduced ? 1 : Math.min(1, dt * 1.8);
    camera.position.lerp(new THREE.Vector3(...want.pos), lerp);
    target.current.lerp(new THREE.Vector3(...want.look), lerp);
    camera.lookAt(target.current);
  });

  return null;
}

// --------------------------------------------------------------------- scene

export interface StadiumProps {
  ball: Ball;
  offense: CardColor;
  /** Set while a kick is in flight so the ball takes a tall arc. */
  arc?: boolean;
  shot?: Shot;
}

export default function StadiumScene({ ball, offense, arc = false, shot = "broadcast" }: StadiumProps) {
  const [reduced, setReduced] = useState(false);
  useEffect(() => {
    if (typeof matchMedia !== "function") return;
    const mq = matchMedia("(prefers-reduced-motion: reduce)");
    setReduced(mq.matches);
    const on = () => setReduced(mq.matches);
    mq.addEventListener("change", on);
    return () => mq.removeEventListener("change", on);
  }, []);

  return (
    <Canvas
      shadows
      dpr={[1, 2]}
      camera={{ position: SHOTS.broadcast.pos, fov: 34 }}
      style={{ width: "100%", height: "100%", display: "block" }}
    >
      <color attach="background" args={["#0e2b20"]} />
      <fog attach="fog" args={["#0e2b20", 14, 30]} />

      {/* Warm key from the offense's side, cool rim opposite. Tabletop tone
          comes from lighting and material, not polygon count. */}
      <ambientLight intensity={0.42} />
      <directionalLight
        position={[-4, 7.5, 5]}
        intensity={1.5}
        color="#ffe6c2"
        castShadow
        shadow-mapSize={[1024, 1024]}
      />
      <directionalLight position={[5, 4, -5]} intensity={0.55} color="#8fc8ff" />
      <pointLight position={[0, 3.4, 0]} intensity={14} distance={13} color="#ffd9a0" />

      <CameraDirector shot={shot} reduced={reduced} />
      <Field offense={offense} />
      <Football target={xFor(ball)} arc={arc} />
    </Canvas>
  );
}
