import React from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { keyed, Key } from './ease';
import { W, H } from './tokens';

export type Cam = { x: number; y: number; zoom: number; rx: number; ry: number; rz: number };
export type CamKey = Key<Cam>;

/**
 * A real camera over a flat "world" plane.
 *  x, y   – the world point (px) that sits at screen centre
 *  zoom   – 1 = world px are screen px; 3 = 3x closer
 *  rx/ry/rz – camera tilt in degrees, seen through perspective (depth)
 * Motion blur is derived from camera speed, so fast whips smear and holds are razor sharp.
 */
export const camAt = (frame: number, keys: CamKey[]): Cam => keyed<Cam>(frame, keys);

export const Camera: React.FC<{
  keys: CamKey[];
  children: React.ReactNode;
  worldW?: number; worldH?: number;
  background?: string;
  perspective?: number;
  maxBlur?: number;
  frameOverride?: number;
}> = ({ keys, children, worldW = W, worldH = H, background, perspective = 1400, maxBlur = 7, frameOverride }) => {
  const f0 = useCurrentFrame();
  const frame = frameOverride ?? f0;
  const c = camAt(frame, keys);
  const p = camAt(frame - 1, keys);
  // screen-space speed of the subject in px/frame
  const dx = (c.x * c.zoom - p.x * p.zoom);
  const dy = (c.y * c.zoom - p.y * p.zoom);
  const dz = Math.abs(Math.log(c.zoom / p.zoom)) * 900;
  const dr = (Math.abs(c.rx - p.rx) + Math.abs(c.ry - p.ry) + Math.abs(c.rz - p.rz)) * 14;
  const speed = Math.hypot(dx, dy) + dz + dr;
  const blur = Math.min(maxBlur, Math.max(0, (speed - 14) / 22));
  return (
    <AbsoluteFill style={{ background, overflow: 'hidden' }}>
      <AbsoluteFill style={{ perspective, perspectiveOrigin: '50% 50%', filter: blur > 0.15 ? `blur(${blur.toFixed(2)}px)` : undefined }}>
        <div
          style={{
            position: 'absolute', left: 0, top: 0, width: worldW, height: worldH,
            transformOrigin: '0 0',
            transformStyle: 'preserve-3d',
            transform: `translate(${W / 2}px, ${H / 2}px) rotateX(${c.rx}deg) rotateY(${c.ry}deg) rotateZ(${c.rz}deg) scale(${c.zoom}) translate(${-c.x}px, ${-c.y}px)`,
          }}
        >
          {children}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
