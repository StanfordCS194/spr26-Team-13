// Profile / "You" tab.
//
// Pulls the signed-in user out of useAuth() so the avatar/name/email reflect
// whoever just went through onboarding. Glasses + settings are static for now;
// when those wire up to a real backend they'll just need data sources, not
// shape changes.

const ProfileScreen = ({ user, glassesState = {}, onSignOut }) => {
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
  const nativeConnected = Boolean(glassesState.connected);
  const displayBattery = glassesState.battery || device?.battery_percent || 78;
  const displayName = glassesState.deviceName || device?.name || 'Mock Ray-Ban Meta';
  const isNativeBridge = Boolean(window.TRAINAR_NATIVE_APP);

  const sendMockCommand = (type, payload = {}) => {
    if (window.sendTrainARNativeCommand && window.sendTrainARNativeCommand(type, payload)) return;

    if (type === 'mockConnect') {
      window.dispatchEvent(new CustomEvent('trainar:glasses', {
        detail: { type: 'connected', payload: { deviceName: displayName, battery: String(displayBattery) } },
      }));
    }
    if (type === 'mockDisconnect') {
      window.dispatchEvent(new CustomEvent('trainar:glasses', {
        detail: { type: 'disconnected', payload: { deviceName: displayName } },
      }));
    }
    if (type === 'mockVoiceCommand') {
      window.dispatchEvent(new CustomEvent('trainar:glasses', {
        detail: { type: 'voiceCommand', payload: { transcript: payload.transcript || 'Start my workout' } },
      }));
    }
    if (type === 'mockPhotoCapture') {
      window.dispatchEvent(new CustomEvent('trainar:glasses', {
        detail: { type: 'photoCaptured', payload: { source: 'mock', contentType: 'image/jpeg' } },
      }));
    }
  };

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
                {device ? `${device.name || 'TrainAR'} · ${device.model || 'M2'}` : displayName}
              </div>
              <div className="mono" style={{ fontSize: 11, color: 'var(--text-3)', marginTop: 2 }}>
                SN · {(device?.serial_number || '8E40-B7C2').replace('-', '·')}
              </div>
            </div>
            <Pill accent>● {nativeConnected || device?.connection_status === 'connected' ? 'Connected' : 'Ready'}</Pill>
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
              <div className="mono" style={{ fontSize: 18, fontWeight: 600 }}>{displayBattery}%</div>
              <div style={{
                marginTop: 6, height: 3, borderRadius: 2,
                background: 'var(--overlay-2)', overflow: 'hidden',
              }}>
                <div style={{ width: `${displayBattery}%`, height: '100%', background: 'var(--accent)' }} />
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

          <div style={{
            marginTop: 14,
            paddingTop: 14,
            borderTop: '1px solid var(--hairline)',
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: 10,
              gap: 12,
            }}>
              <div>
                <div style={{ fontSize: 13, fontWeight: 700 }}>Glasses pairing demo</div>
                <div style={{ fontSize: 11, color: 'var(--text-3)', marginTop: 2 }}>
                  {isNativeBridge ? 'Native bridge controls' : 'Browser fallback controls'}
                </div>
              </div>
              <Pill>{nativeConnected ? 'Live' : 'Mock'}</Pill>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
              <button
                className="press"
                onClick={() => sendMockCommand(nativeConnected ? 'mockDisconnect' : 'mockConnect')}
                style={pairingButtonStyle(nativeConnected ? 'surface' : 'accent')}
              >
                <Icon name={nativeConnected ? 'x' : 'bluetooth'} size={16} />
                {nativeConnected ? 'Disconnect' : 'Connect'}
              </button>
              <button
                className="press"
                onClick={() => sendMockCommand('mockVoiceCommand', { transcript: 'Start my workout' })}
                style={pairingButtonStyle('surface')}
              >
                <Icon name="sparkle" size={16} />
                Voice prompt
              </button>
              <button
                className="press"
                onClick={() => sendMockCommand('mockPhotoCapture')}
                style={pairingButtonStyle('surface')}
              >
                <Icon name="camera" size={16} />
                Photo event
              </button>
              <button
                className="press"
                onClick={() => sendMockCommand('mockVoiceCommand', { transcript: 'What should I do?' })}
                style={pairingButtonStyle('surface')}
              >
                <Icon name="bolt" size={16} />
                Ask coach
              </button>
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
        <button
          onClick={onSignOut}
          className="press"
          style={{
            width: '100%',
            marginTop: 12,
            minHeight: 48,
            borderRadius: 16,
            background: 'var(--surface-1)',
            border: '1px solid var(--hairline)',
            color: '#FF8A7A',
            fontFamily: 'var(--font-sans)',
            fontSize: 14,
            fontWeight: 700,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 8,
            cursor: 'pointer',
          }}
        >
          <Icon name="x" size={16} stroke="#FF8A7A" />
          Sign out
        </button>
      </div>
    </Screen>
  );
};

Object.assign(window, { ProfileScreen });

const pairingButtonStyle = (variant) => ({
  minHeight: 40,
  borderRadius: 12,
  border: variant === 'accent' ? 'none' : '1px solid var(--hairline)',
  background: variant === 'accent' ? 'var(--accent)' : 'var(--surface-2)',
  color: variant === 'accent' ? 'var(--on-accent)' : 'var(--text-1)',
  fontFamily: 'var(--font-sans)',
  fontSize: 12,
  fontWeight: 700,
  display: 'inline-flex',
  alignItems: 'center',
  justifyContent: 'center',
  gap: 7,
  cursor: 'pointer',
  padding: '0 10px',
});
