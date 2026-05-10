// Profile / "You" tab.
//
// Pulls the signed-in user out of useAuth() so the avatar/name/email reflect
// whoever just went through onboarding. Glasses + settings are static for now;
// when those wire up to a real backend they'll just need data sources, not
// shape changes.

const ProfileScreen = ({ user }) => {
  // Backend friend can pass in `user` directly, or we fall back to whatever
  // useAuth has stashed in localStorage.
  const fallback = (() => {
    try {
      const raw = window.localStorage.getItem('trainar.auth.v1');
      return raw ? JSON.parse(raw) : null;
    } catch (_e) {
      return null;
    }
  })();
  const u = user || fallback || {};
  const name = u.name || 'Alex';
  const email = u.email || 'alex@stanford.edu';
  const initial = (name[0] || 'A').toUpperCase();
  const device = (window.TRAINAR_DEVICES || [])[0];

  const settingsRows = [
    { i: 'user',      l: 'Account & profile' },
    { i: 'bluetooth', l: 'Glasses & pairing' },
    { i: 'bolt',      l: 'Coaching & audio' },
    { i: 'upload',    l: 'Export & integrations' },
    { i: 'settings',  l: 'App preferences' },
  ];

  return (
    <Screen padTop={56} padBottom={120}>
      <div style={{ padding: '0 20px 24px' }}>
        <h1 style={{ fontSize: 28, fontWeight: 600, letterSpacing: -0.5, margin: 0 }}>Profile</h1>
      </div>

      {/* User card. */}
      <div style={{ padding: '0 20px 14px' }}>
        <Card>
          <div style={{ display: 'flex', alignItems: 'center', gap: 18, padding: '6px 4px' }}>
            <div style={{
              width: 72, height: 72, borderRadius: '50%',
              background: 'var(--accent)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 30, fontWeight: 600, color: 'var(--on-accent)',
              flexShrink: 0,
            }}>{initial}</div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: 19, fontWeight: 600, letterSpacing: -0.2 }}>{name}</div>
              <div style={{
                fontSize: 13, color: 'var(--text-3)', marginTop: 3,
                overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
              }}>{email}</div>
              <div style={{ display: 'flex', gap: 6, marginTop: 10 }}>
                <Pill>Member · Apr 2026</Pill>
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Connected glasses card. */}
      <div style={{ padding: '0 20px 14px' }}>
        <div style={{
          fontSize: 13, fontWeight: 600, color: 'var(--text-2)',
          marginBottom: 10, padding: '0 4px',
        }}>Connected glasses</div>
        <Card>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 16 }}>
            <div style={{
              width: 48, height: 48, borderRadius: 12, background: 'var(--accent-soft)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <Icon name="glasses" size={22} stroke="var(--accent)" />
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 15, fontWeight: 600 }}>
                {device ? `${device.name || 'TrainAR'} · ${device.model || 'M2'}` : 'TrainAR · M2'}
              </div>
              <div className="mono" style={{ fontSize: 11, color: 'var(--text-3)', marginTop: 2 }}>
                SN · {(device?.serial_number || '8E40-B7C2').replace('-', '·')}
              </div>
            </div>
            <Pill accent>● {device?.connection_status === 'connected' ? 'Connected' : 'Ready'}</Pill>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
            <div style={{
              padding: '12px 14px', borderRadius: 12,
              background: 'var(--surface-2)', border: '1px solid var(--hairline)',
            }}>
              <div style={{
                fontSize: 10, color: 'var(--text-3)', textTransform: 'uppercase',
                letterSpacing: 0.4, marginBottom: 4,
              }}>Battery</div>
              <div className="mono" style={{ fontSize: 18, fontWeight: 600 }}>{device?.battery_percent || 78}%</div>
              <div style={{
                marginTop: 6, height: 3, borderRadius: 2,
                background: 'var(--overlay-2)', overflow: 'hidden',
              }}>
                <div style={{ width: `${device?.battery_percent || 78}%`, height: '100%', background: 'var(--accent)' }} />
              </div>
            </div>
            <div style={{
              padding: '12px 14px', borderRadius: 12,
              background: 'var(--surface-2)', border: '1px solid var(--hairline)',
            }}>
              <div style={{
                fontSize: 10, color: 'var(--text-3)', textTransform: 'uppercase',
                letterSpacing: 0.4, marginBottom: 4,
              }}>Firmware</div>
              <div className="mono" style={{ fontSize: 18, fontWeight: 600 }}>{device?.firmware_version || '1.4.2'}</div>
              <div style={{ fontSize: 10, color: 'var(--accent)', marginTop: 6 }}>Up to date</div>
            </div>
          </div>
        </Card>
      </div>

      {/* Settings list. */}
      <div style={{ padding: '0 20px' }}>
        <div style={{
          fontSize: 13, fontWeight: 600, color: 'var(--text-2)',
          marginBottom: 10, padding: '0 4px',
        }}>Settings</div>
        <Card padding={4}>
          {settingsRows.map((row, i) => (
            <div key={i} className="press" style={{
              display: 'flex', alignItems: 'center', gap: 14,
              padding: '14px 14px',
              borderBottom: i < settingsRows.length - 1 ? '1px solid var(--hairline)' : 'none',
              cursor: 'pointer',
            }}>
              <div style={{
                width: 32, height: 32, borderRadius: 8,
                background: 'var(--surface-2)', border: '1px solid var(--hairline)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                <Icon name={row.i} size={16} stroke="var(--text-2)" />
              </div>
              <div style={{ flex: 1, fontSize: 14, fontWeight: 500 }}>{row.l}</div>
              <Icon name="chevron-right" size={16} stroke="var(--text-3)" />
            </div>
          ))}
        </Card>
      </div>
    </Screen>
  );
};

Object.assign(window, { ProfileScreen });
