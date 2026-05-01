/**
 * WaveDivider — SVG wave separator between sections.
 *
 * Props:
 *  fill        — fill color of the wave (default: '#ffffff')
 *  flip        — mirror the wave vertically (boolean)
 *  variant     — 'gentle' | 'sharp' | 'soft' (wave shape)
 *  height      — SVG height in px (default: 60)
 *  className   — extra class names
 */
export default function WaveDivider({ fill = '#ffffff', flip = false, variant = 'gentle', height = 60, className = '' }) {
  const paths = {
    gentle: 'M0,40 C360,80 720,0 1080,40 C1260,60 1380,50 1440,40 L1440,80 L0,80 Z',
    sharp:  'M0,80 L0,40 C240,70 480,10 720,50 C960,90 1200,20 1440,60 L1440,80 Z',
    soft:   'M0,80 L0,60 C360,20 720,80 1080,40 C1260,20 1380,50 1440,30 L1440,80 Z',
  };

  const d = paths[variant] || paths.gentle;

  return (
    <div
      className={`wave-divider ${className}`}
      style={{ height, transform: flip ? 'scaleY(-1)' : undefined }}
      aria-hidden="true"
    >
      <svg
        viewBox={`0 0 1440 80`}
        preserveAspectRatio="none"
        xmlns="http://www.w3.org/2000/svg"
        style={{ height: '100%', width: '100%' }}
      >
        <path fill={fill} d={d} />
      </svg>
    </div>
  );
}
