// Shared UI primitives for the TrainAR iOS app.
// Mirrors the design handoff but trimmed to just what the signup flow needs.

const Icon = ({ name, size = 20, stroke = 'currentColor', strokeWidth = 1.75, style = {} }) => {
  const common = {
    width: size, height: size, viewBox: '0 0 24 24', fill: 'none',
    stroke, strokeWidth, strokeLinecap: 'round', strokeLinejoin: 'round', style,
  };
  switch (name) {
    case 'arrow-right': return <svg {...common}><path d="M5 12h14M13 5l7 7-7 7"/></svg>;
    case 'arrow-left':  return <svg {...common}><path d="M19 12H5M11 5l-7 7 7 7"/></svg>;
    case 'mail':        return <svg {...common}><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 7 9-7"/></svg>;
    case 'eye':         return <svg {...common}><path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/></svg>;
    case 'eye-off':     return <svg {...common}><path d="M3 3l18 18M10.6 10.6a3 3 0 0 0 4.2 4.2"/><path d="M9.9 5.1A10.7 10.7 0 0 1 12 5c6 0 10 7 10 7a17.4 17.4 0 0 1-3.2 3.9M6.6 6.6A17.4 17.4 0 0 0 2 12s4 7 10 7c1.4 0 2.7-.3 3.9-.7"/></svg>;
    case 'bolt':        return <svg {...common}><path d="M13 2L4 14h7l-1 8 9-12h-7l1-8z"/></svg>;
    case 'check':       return <svg {...common}><path d="M5 12l5 5L20 7"/></svg>;
    case 'glasses':     return <svg {...common}><circle cx="6.5" cy="14" r="3.5"/><circle cx="17.5" cy="14" r="3.5"/><path d="M10 14c.5-1 1.5-1 2 0M3 9l3.5-2M21 9l-3.5-2"/></svg>;
    case 'x':           return <svg {...common}><path d="M6 6l12 12M6 18L18 6"/></svg>;
    case 'camera':      return <svg {...common}><path d="M3 7h4l2-3h6l2 3h4v12H3V7z"/><circle cx="12" cy="13" r="4"/></svg>;
    case 'upload':      return <svg {...common}><path d="M12 15V4M7 9l5-5 5 5"/><path d="M5 17v3h14v-3"/></svg>;
    case 'sparkle':     return <svg {...common}><path d="M12 3v4M12 17v4M3 12h4M17 12h4M5.5 5.5l2.5 2.5M16 16l2.5 2.5M5.5 18.5L8 16M16 8l2.5-2.5"/></svg>;
    case 'chevron-right': return <svg {...common}><path d="M9 6l6 6-6 6"/></svg>;
    case 'flash':       return <svg {...common}><path d="M13 2L4 14h7l-1 8 9-12h-7l1-8z" fill={stroke}/></svg>;
    case 'image':       return <svg {...common}><rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="10" r="1.5"/><path d="M21 16l-5-5-9 9"/></svg>;
    case 'rotate':      return <svg {...common}><path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5"/></svg>;
    default: return null;
  }
};

const Pill = ({ children, accent, style = {} }) => (
  <span style={{
    display: 'inline-flex', alignItems: 'center', gap: 6,
    height: 24, padding: '0 10px', borderRadius: 9999,
    fontSize: 11, fontWeight: 500, letterSpacing: 0.2,
    background: accent ? 'var(--accent-soft)' : 'var(--overlay-2)',
    color: accent ? 'var(--accent)' : 'var(--text-2)',
    border: '1px solid ' + (accent ? 'rgba(197,242,62,0.3)' : 'var(--hairline)'),
    ...style,
  }}>{children}</span>
);

const Card = ({ children, style = {}, padding = 20, onClick }) => (
  <div onClick={onClick} className={onClick ? 'press' : ''} style={{
    background: 'var(--surface-1)', border: '1px solid var(--hairline)',
    borderRadius: 'var(--r-card)', padding,
    cursor: onClick ? 'pointer' : 'default',
    ...style,
  }}>{children}</div>
);

const Button = ({ children, onClick, variant = 'primary', size = 'lg', iconRight, style = {}, disabled }) => {
  const sizes = {
    lg: { height: 56, padding: '0 24px', fontSize: 16 },
    md: { height: 44, padding: '0 18px', fontSize: 14 },
    sm: { height: 32, padding: '0 14px', fontSize: 13 },
  }[size];
  const variants = {
    primary: { background: 'var(--accent)',   color: 'var(--on-accent)', border: 'none' },
    ghost:   { background: 'transparent',     color: 'var(--text-1)',   border: '1px solid var(--hairline-2)' },
    surface: { background: 'var(--surface-2)', color: 'var(--text-1)',   border: '1px solid var(--hairline)' },
  }[variant];
  return (
    <button onClick={onClick} disabled={disabled} className="press" style={{
      ...sizes, ...variants,
      borderRadius: 9999,
      display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 8,
      fontFamily: 'var(--font-sans)', fontWeight: 600,
      cursor: disabled ? 'not-allowed' : 'pointer',
      opacity: disabled ? 0.5 : 1,
      width: '100%',
      ...style,
    }}>
      <span>{children}</span>
      {iconRight && <Icon name={iconRight} size={size === 'sm' ? 16 : 18} />}
    </button>
  );
};

// Labelled input row, used by every form field in the signup flow.
const Field = ({ label, icon, type = 'text', value, onChange, placeholder, trailing, autoFocus }) => (
  <div style={{ marginBottom: 16 }}>
    <label style={{
      display: 'block', fontSize: 11, color: 'var(--text-3)',
      marginBottom: 8, letterSpacing: 0.4, textTransform: 'uppercase', fontWeight: 600,
    }}>{label}</label>
    <div style={{
      display: 'flex', alignItems: 'center', gap: 10,
      padding: '0 16px', height: 56, borderRadius: 16,
      background: 'var(--surface-1)', border: '1px solid var(--hairline)',
    }}>
      {icon && <Icon name={icon} size={18} stroke="var(--text-3)" />}
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        autoFocus={autoFocus}
        style={{
          flex: 1, background: 'transparent', border: 'none', outline: 'none',
          color: 'var(--text-1)', fontSize: 15, fontFamily: 'var(--font-sans)',
        }}
      />
      {trailing}
    </div>
  </div>
);

Object.assign(window, { Icon, Pill, Card, Button, Field });
