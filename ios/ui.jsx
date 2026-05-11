// Shared UI primitives for the TrainAR iOS app.
// Lucide-style strokes, sized to 20 by default.

const Icon = ({ name, size = 20, stroke = 'currentColor', strokeWidth = 1.75, style = {} }) => {
  const common = {
    width: size, height: size, viewBox: '0 0 24 24', fill: 'none',
    stroke, strokeWidth, strokeLinecap: 'round', strokeLinejoin: 'round', style,
  };
  switch (name) {
    case 'home':           return <svg {...common}><path d="M3 11l9-8 9 8"/><path d="M5 10v10h14V10"/></svg>;
    case 'plus':           return <svg {...common}><path d="M12 5v14M5 12h14"/></svg>;
    case 'lock':           return <svg {...common}><rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/></svg>;
    case 'trash':          return <svg {...common}><path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M6 6l1 14a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2l1-14M10 11v6M14 11v6"/></svg>;
    case 'edit':           return <svg {...common}><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4 12.5-12.5z"/></svg>;
    case 'check':          return <svg {...common}><path d="M5 12l5 5L20 7"/></svg>;
    case 'arrow-right':    return <svg {...common}><path d="M5 12h14M13 5l7 7-7 7"/></svg>;
    case 'arrow-left':     return <svg {...common}><path d="M19 12H5M11 5l-7 7 7 7"/></svg>;
    case 'arrow-up-right': return <svg {...common}><path d="M7 17L17 7M9 7h8v8"/></svg>;
    case 'chevron-right':  return <svg {...common}><path d="M9 6l6 6-6 6"/></svg>;
    case 'chevron-left':   return <svg {...common}><path d="M15 6l-6 6 6 6"/></svg>;
    case 'chevron-down':   return <svg {...common}><path d="M6 9l6 6 6-6"/></svg>;
    case 'chevron-up':     return <svg {...common}><path d="M18 15l-6-6-6 6"/></svg>;
    case 'camera':         return <svg {...common}><path d="M3 7h4l2-3h6l2 3h4v12H3V7z"/><circle cx="12" cy="13" r="4"/></svg>;
    case 'image':          return <svg {...common}><rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="10" r="1.5"/><path d="M21 16l-5-5-9 9"/></svg>;
    case 'upload':         return <svg {...common}><path d="M12 15V4M7 9l5-5 5 5"/><path d="M5 17v3h14v-3"/></svg>;
    case 'download':       return <svg {...common}><path d="M12 4v12M7 11l5 5 5-5"/><path d="M5 18v3h14v-3"/></svg>;
    case 'calendar':       return <svg {...common}><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/></svg>;
    case 'glasses':        return <svg {...common}><circle cx="6.5" cy="14" r="3.5"/><circle cx="17.5" cy="14" r="3.5"/><path d="M10 14c.5-1 1.5-1 2 0M3 9l3.5-2M21 9l-3.5-2"/></svg>;
    case 'dumbbell':       return <svg {...common}><path d="M3 9v6M21 9v6M6 6v12M18 6v12"/><path d="M6 12h12"/></svg>;
    case 'flame':          return <svg {...common}><path d="M12 3c2 4-3 5-3 9a3 3 0 0 0 6 0c0-1.5-1-2.5-2-3 1 4-1 6-1 6s-2-1-2-4 2-5 2-8z"/></svg>;
    case 'user':           return <svg {...common}><circle cx="12" cy="8" r="4"/><path d="M4 21c0-4.5 3.5-7 8-7s8 2.5 8 7"/></svg>;
    case 'bolt':           return <svg {...common}><path d="M13 2L4 14h7l-1 8 9-12h-7l1-8z"/></svg>;
    case 'sparkle':        return <svg {...common}><path d="M12 3v4M12 17v4M3 12h4M17 12h4M5.5 5.5l2.5 2.5M16 16l2.5 2.5M5.5 18.5L8 16M16 8l2.5-2.5"/></svg>;
    case 'mail':           return <svg {...common}><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 7 9-7"/></svg>;
    case 'eye':            return <svg {...common}><path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/></svg>;
    case 'eye-off':        return <svg {...common}><path d="M3 3l18 18M10.6 10.6a3 3 0 0 0 4.2 4.2"/><path d="M9.9 5.1A10.7 10.7 0 0 1 12 5c6 0 10 7 10 7a17.4 17.4 0 0 1-3.2 3.9M6.6 6.6A17.4 17.4 0 0 0 2 12s4 7 10 7c1.4 0 2.7-.3 3.9-.7"/></svg>;
    case 'play':           return <svg {...common}><path d="M6 4l14 8-14 8V4z" fill={stroke}/></svg>;
    case 'settings':       return <svg {...common}><circle cx="12" cy="12" r="3"/><path d="M19 12a7 7 0 0 0-.1-1.2l2-1.5-2-3.4-2.3.9a7 7 0 0 0-2-1.2L14 3h-4l-.5 2.6a7 7 0 0 0-2 1.2l-2.3-.9-2 3.4 2 1.5A7 7 0 0 0 5 12c0 .4 0 .8.1 1.2l-2 1.5 2 3.4 2.3-.9a7 7 0 0 0 2 1.2L10 21h4l.5-2.6a7 7 0 0 0 2-1.2l2.3.9 2-3.4-2-1.5c.1-.4.1-.8.1-1.2z"/></svg>;
    case 'bluetooth':      return <svg {...common}><path d="M7 7l10 10-5 5V2l5 5L7 17"/></svg>;
    case 'battery':        return <svg {...common}><rect x="2" y="7" width="18" height="10" rx="2"/><path d="M22 11v2"/><rect x="4" y="9" width="11" height="6" rx="1" fill={stroke}/></svg>;
    case 'flash':          return <svg {...common}><path d="M13 2L4 14h7l-1 8 9-12h-7l1-8z" fill={stroke}/></svg>;
    case 'grid':           return <svg {...common}><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>;
    case 'list':           return <svg {...common}><path d="M8 6h13M8 12h13M8 18h13"/><circle cx="4" cy="6" r="1" fill={stroke}/><circle cx="4" cy="12" r="1" fill={stroke}/><circle cx="4" cy="18" r="1" fill={stroke}/></svg>;
    case 'x':              return <svg {...common}><path d="M6 6l12 12M6 18L18 6"/></svg>;
    case 'rotate':         return <svg {...common}><path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5"/></svg>;
    case 'trending-up':    return <svg {...common}><path d="M3 17l6-6 4 4 8-8"/><path d="M14 7h7v7"/></svg>;
    case 'trophy':         return <svg {...common}><path d="M8 21h8M12 17v4M7 4h10v5a5 5 0 0 1-10 0V4z"/><path d="M17 4h3v3a3 3 0 0 1-3 3M7 4H4v3a3 3 0 0 0 3 3"/></svg>;
    case 'minus':          return <svg {...common}><path d="M5 12h14"/></svg>;
    case 'maximize':       return <svg {...common}><path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5"/></svg>;
    case 'more-horizontal':return <svg {...common}><circle cx="6" cy="12" r="1.5" fill={stroke}/><circle cx="12" cy="12" r="1.5" fill={stroke}/><circle cx="18" cy="12" r="1.5" fill={stroke}/></svg>;
    case 'file':           return <svg {...common}><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/></svg>;
    case 'folder':         return <svg {...common}><path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7z"/></svg>;
    case 'link':           return <svg {...common}><path d="M10 14a4 4 0 0 0 5.6 0l3-3a4 4 0 0 0-5.6-5.6l-1.5 1.5"/><path d="M14 10a4 4 0 0 0-5.6 0l-3 3a4 4 0 0 0 5.6 5.6l1.5-1.5"/></svg>;
    case 'video':          return <svg {...common}><rect x="3" y="6" width="13" height="12" rx="2"/><path d="M16 10l5-3v10l-5-3"/></svg>;
    case 'alert':          return <svg {...common}><path d="M12 3l10 18H2L12 3z"/><path d="M12 10v5M12 18v.01"/></svg>;
    case 'search':         return <svg {...common}><circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/></svg>;
    case 'monitor':        return <svg {...common}><rect x="3" y="4" width="18" height="13" rx="2"/><path d="M8 21h8M12 17v4"/></svg>;
    case 'cloud':          return <svg {...common}><path d="M7 18a4 4 0 0 1 0-8 5 5 0 0 1 9.6-1A4 4 0 0 1 17 18H7z"/></svg>;
    case 'star':           return <svg {...common}><path d="M12 3l2.9 6.1 6.6.7-4.9 4.6 1.4 6.6L12 17.8 5.9 21l1.4-6.6L2.5 9.8l6.6-.7L12 3z"/></svg>;
    case 'wifi':           return <svg {...common}><path d="M2 9a16 16 0 0 1 20 0M5 13a11 11 0 0 1 14 0M8.5 16.5a6 6 0 0 1 7 0"/><circle cx="12" cy="20" r="1" fill={stroke}/></svg>;
    case 'columns':        return <svg {...common}><rect x="3" y="4" width="7" height="16" rx="1"/><rect x="14" y="4" width="7" height="16" rx="1"/></svg>;
    case 'clock':          return <svg {...common}><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>;
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

const Button = ({ children, onClick, variant = 'primary', size = 'lg', icon, iconRight, style = {}, disabled }) => {
  const sizes = {
    lg: { height: 56, padding: '0 24px', fontSize: 16 },
    md: { height: 44, padding: '0 18px', fontSize: 14 },
    sm: { height: 32, padding: '0 14px', fontSize: 13 },
  }[size];
  const variants = {
    primary: { background: 'var(--accent)',    color: 'var(--on-accent)', border: 'none' },
    ghost:   { background: 'transparent',      color: 'var(--text-1)',    border: '1px solid var(--hairline-2)' },
    surface: { background: 'var(--surface-2)', color: 'var(--text-1)',    border: '1px solid var(--hairline)' },
    dark:    { background: 'var(--surface-3)', color: 'var(--text-1)',    border: '1px solid var(--hairline-2)' },
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
      {icon && <Icon name={icon} size={size === 'sm' ? 16 : 18} />}
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

// Progress ring — used by parsing + glasses status indicators.
const ProgressRing = ({ value, size = 64, stroke = 4, color = 'var(--accent)', track = 'var(--overlay-3)', children }) => {
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  return (
    <div style={{ position: 'relative', width: size, height: size }}>
      <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
        <circle cx={size / 2} cy={size / 2} r={r} stroke={track} strokeWidth={stroke} fill="none" />
        <circle cx={size / 2} cy={size / 2} r={r} stroke={color} strokeWidth={stroke} fill="none"
          strokeDasharray={c} strokeDashoffset={c * (1 - value)} strokeLinecap="round"
          style={{ transition: 'stroke-dashoffset 600ms cubic-bezier(.2,.7,.2,1)' }} />
      </svg>
      <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        {children}
      </div>
    </div>
  );
};

// Bottom tab bar — Train / History / You. Pulses Train icon when a workout is live.
const TabBar = ({ active, onTab, live = false }) => {
  const isNativeApp = Boolean(window.TRAINAR_NATIVE_APP);
  const tabs = [
    { id: 'home',     icon: 'dumbbell', label: 'Train' },
    { id: 'calendar', icon: 'calendar', label: 'History' },
    { id: 'profile',  icon: 'user',     label: 'You' },
  ];
  return (
    <div style={{
      position: isNativeApp ? 'fixed' : 'absolute',
      left: 16,
      right: 16,
      bottom: isNativeApp ? 'calc(env(safe-area-inset-bottom, 0px) + 10px)' : 14,
      height: 60,
      background: 'var(--tab-bar-bg)', backdropFilter: 'blur(20px)',
      WebkitBackdropFilter: 'blur(20px)',
      border: '1px solid var(--hairline-2)',
      borderRadius: 9999,
      display: 'flex', alignItems: 'center', justifyContent: 'space-around',
      padding: '0 8px', zIndex: 5,
      boxShadow: '0 10px 30px rgba(0,0,0,0.5)',
    }}>
      {tabs.map((t) => {
        const a = active === t.id;
        const showLive = live && t.id === 'home' && !a;
        return (
          <button key={t.id} onClick={() => onTab(t.id)} className="press" style={{
            background: a ? 'var(--accent-soft)' : 'transparent',
            border: a ? '1px solid rgba(197,242,62,0.3)' : '1px solid transparent',
            color: a ? 'var(--accent)' : 'var(--text-2)',
            height: 44, padding: a ? '0 14px' : '0 12px',
            borderRadius: 9999, display: 'flex', alignItems: 'center', gap: 6,
            cursor: 'pointer', fontFamily: 'var(--font-sans)', fontSize: 13, fontWeight: 600,
            transition: 'all 200ms', position: 'relative',
          }}>
            <span style={{ position: 'relative', display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}>
              <Icon name={t.icon} size={20} stroke={a ? 'var(--accent)' : (showLive ? 'var(--accent)' : 'var(--text-2)')} />
              {showLive && (
                <span style={{
                  position: 'absolute', top: -2, right: -3,
                  width: 8, height: 8, borderRadius: '50%',
                  background: 'var(--accent)',
                  boxShadow: '0 0 0 2px var(--tab-bar-bg), 0 0 8px var(--accent)',
                  animation: 'tabarLivePulse 1.6s ease-in-out infinite',
                }} />
              )}
            </span>
            {a && <span>{t.label}</span>}
          </button>
        );
      })}
    </div>
  );
};

// Glasses status pill — used in the Train tab header.
const GlassesPill = ({ connected = true, battery = 78, onClick }) => (
  <button onClick={onClick} className="press" style={{
    display: 'inline-flex', alignItems: 'center', gap: 8,
    height: 32, padding: '0 12px', borderRadius: 9999,
    background: connected ? 'rgba(197,242,62,0.1)' : 'var(--surface-1)',
    border: '1px solid ' + (connected ? 'rgba(197,242,62,0.25)' : 'var(--hairline)'),
    color: connected ? 'var(--accent)' : 'var(--text-2)', cursor: 'pointer',
    fontFamily: 'var(--font-sans)',
  }}>
    <div style={{
      width: 6, height: 6, borderRadius: 3,
      background: connected ? 'var(--accent)' : 'var(--text-3)',
    }} className={connected ? 'pulse-dot' : ''} />
    <span style={{ fontSize: 12, fontWeight: 600 }}>{connected ? 'Glasses' : 'No glasses'}</span>
    {connected && <span className="mono" style={{ fontSize: 11, opacity: 0.85 }}>· {battery}%</span>}
  </button>
);

// Striped placeholder block.
const Placeholder = ({ w = '100%', h = 100, label, style = {} }) => (
  <div className="stripe-placeholder" style={{
    width: w, height: h, borderRadius: 12,
    border: '1px dashed var(--hairline-2)',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    color: 'var(--text-3)', fontFamily: 'var(--font-mono)', fontSize: 10,
    letterSpacing: 0.5, textTransform: 'uppercase',
    ...style,
  }}>{label}</div>
);

Object.assign(window, { Icon, Pill, Card, Button, Field, ProgressRing, TabBar, GlassesPill, Placeholder });
