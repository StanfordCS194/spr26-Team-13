// Profile / "You" tab.
//
// Pulls the signed-in user out of useAuth() so the avatar/name/email reflect
// whoever just went through onboarding. Settings only expose controls that have
// visible behavior in the current app.

const ProfileScreen = ({ user, onEditTraining, onLogout }) => {
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
  const training = u.trainingProfile || window.TRAINAR_TRAINING_PROFILE || {};
  const equipment = Array.isArray(training.availableEquipment) ? training.availableEquipment : [];
  const [activeSettings, setActiveSettings] = React.useState('account');
  const [settingsSaved, setSettingsSaved] = React.useState('');
  const [settings, setSettings] = React.useState(() => {
    const saved = readProfileSettings();
    return {
      ...saved,
      displayName: saved.displayName || name,
      email,
    };
  });
  const displayName = settings.displayName || name;
  const initial = (displayName[0] || 'A').toUpperCase();

  React.useEffect(() => {
    try {
      window.localStorage.setItem('trainar.profile.settings.v1', JSON.stringify(settings));
    } catch (_e) {}
  }, [settings]);

  const updateSetting = (key, value) => {
    setSettings((prev) => ({ ...prev, [key]: value }));
    setSettingsSaved('Saved');
  };

  const settingsRows = [
    { id: 'account',    i: 'user',     l: 'Account & training', d: 'Name, email, training profile' },
    { id: 'connection', i: 'wifi',     l: 'Connection',         d: 'Check the local app server' },
    { id: 'data',       i: 'download', l: 'Export data',        d: 'Download local app data' },
  ];

  const exportLocalData = () => {
    const payload = {
      profile: { name: displayName, email, trainingProfile: training },
      programs: window.PROGRAMS || [],
      recentSessions: window.TRAINAR_SESSIONS || [],
      personalRecords: window.TRAINAR_PRS || [],
      pastWorkout: window.PAST_WORKOUT || null,
      localPreferences: settings,
      exportedAt: new Date().toISOString(),
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'trainar-local-data.json';
    link.click();
    URL.revokeObjectURL(url);
    setSettingsSaved('Exported');
  };

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
              <div style={{ fontSize: 19, fontWeight: 600, letterSpacing: -0.2 }}>{displayName}</div>
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

      {/* Training profile. */}
      <div style={{ padding: '0 20px 14px' }}>
        <div style={{
          fontSize: 13, fontWeight: 600, color: 'var(--text-2)',
          marginBottom: 10, padding: '0 4px',
        }}>Training profile</div>
        <Card>
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12 }}>
            <div style={{ minWidth: 0 }}>
              <div style={{ fontSize: 15, fontWeight: 700, textTransform: 'capitalize' }}>
                {String(training.trainingGoal || 'Not set').replace('_', ' ')}
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-3)', marginTop: 4, lineHeight: 1.35 }}>
                {training.workoutDaysPerWeek || '-'} days/week · {training.workoutSessionMinutes || '-'} min · {training.trainingExperience || 'experience not set'}
              </div>
            </div>
            <button
              onClick={onEditTraining}
              className="press"
              style={{
                width: 36, height: 36, borderRadius: 9999,
                background: 'var(--surface-2)', border: '1px solid var(--hairline)',
                color: 'var(--text-1)', display: 'flex',
                alignItems: 'center', justifyContent: 'center', cursor: 'pointer',
                flexShrink: 0,
              }}
              aria-label="Edit training profile"
            ><Icon name="edit" size={15} /></button>
          </div>

          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 14 }}>
            <Pill>{String(training.coachStyle || 'direct').replace('_', ' ')}</Pill>
            <Pill>{String(training.evidencePreference || 'concise')} evidence</Pill>
            {equipment.slice(0, 4).map((item) => (
              <Pill key={item}>{String(item).replace('_', ' ')}</Pill>
            ))}
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
          {settingsRows.map((row, i) => {
            const selected = activeSettings === row.id;
            return (
            <button key={row.id} className="press" onClick={() => setActiveSettings(row.id)} style={{
              width: '100%',
              display: 'flex', alignItems: 'center', gap: 14,
              padding: '14px 14px',
              borderBottom: i < settingsRows.length - 1 ? '1px solid var(--hairline)' : 'none',
              borderTop: 'none',
              borderLeft: 'none',
              borderRight: 'none',
              background: selected ? 'rgba(197,242,62,0.08)' : 'transparent',
              color: 'var(--text-1)',
              fontFamily: 'var(--font-sans)',
              textAlign: 'left',
              cursor: 'pointer',
            }}>
              <div style={{
                width: 32, height: 32, borderRadius: 8,
                background: selected ? 'var(--accent-soft)' : 'var(--surface-2)',
                border: '1px solid ' + (selected ? 'rgba(197,242,62,0.3)' : 'var(--hairline)'),
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                <Icon name={row.i} size={16} stroke={selected ? 'var(--accent)' : 'var(--text-2)'} />
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 14, fontWeight: 600 }}>{row.l}</div>
                <div style={{
                  fontSize: 11, color: 'var(--text-3)', marginTop: 2,
                  overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                }}>{row.d}</div>
              </div>
              <Icon name={selected ? 'chevron-down' : 'chevron-right'} size={16} stroke="var(--text-3)" />
            </button>
          );})}
        </Card>
      </div>

      <SettingsPanel
        active={activeSettings}
        settings={settings}
        savedLabel={settingsSaved}
        userEmail={email}
        training={training}
        onEditTraining={onEditTraining}
        onLogout={onLogout}
        onChange={updateSetting}
        onExport={exportLocalData}
      />
    </Screen>
  );
};

Object.assign(window, { ProfileScreen });

function readProfileSettings() {
  const defaults = {
    displayName: '',
    email: '',
  };
  try {
    const raw = window.localStorage.getItem('trainar.profile.settings.v1');
    return raw ? { ...defaults, ...JSON.parse(raw) } : defaults;
  } catch (_e) {
    return defaults;
  }
}

function SettingsPanel({
  active,
  settings,
  savedLabel,
  userEmail,
  training,
  onEditTraining,
  onLogout,
  onChange,
  onExport,
}) {
  const [serverStatus, setServerStatus] = React.useState('Not checked');
  const [checkingServer, setCheckingServer] = React.useState(false);
  const panelTitle = {
    account: 'Account & training',
    connection: 'Connection',
    data: 'Export data',
  }[active] || 'Settings';

  const checkServer = async () => {
    setCheckingServer(true);
    setServerStatus('Checking...');
    try {
      const response = await fetch('/ios/', { method: 'HEAD', cache: 'no-store' });
      setServerStatus(response.ok ? 'Reachable' : `HTTP ${response.status}`);
    } catch (_e) {
      setServerStatus('Unavailable');
    } finally {
      setCheckingServer(false);
    }
  };

  return (
    <div style={{ padding: '14px 20px 0' }}>
      <Card>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, marginBottom: 16 }}>
          <div>
            <div style={{ fontSize: 16, fontWeight: 700 }}>{panelTitle}</div>
            <div style={{ fontSize: 11, color: 'var(--text-3)', marginTop: 3 }}>
              {savedLabel || 'Only live controls are shown here'}
            </div>
          </div>
          {savedLabel && <Pill accent>{savedLabel}</Pill>}
        </div>

        {active === 'account' && (
          <div>
            <SettingsTextField
              label="Display name"
              value={settings.displayName}
              onChange={(value) => onChange('displayName', value)}
            />
            <ReadOnlyRow label="Email" value={userEmail} />
            <ReadOnlyRow
              label="Training goal"
              value={String(training.trainingGoal || 'Not set').replace('_', ' ')}
            />
            <Button onClick={onEditTraining} variant="surface" size="md" icon="edit" style={{ marginTop: 14 }}>
              Edit training profile
            </Button>
            <Button onClick={onLogout} variant="dark" size="md" icon="x" style={{ marginTop: 10 }}>
              Log out
            </Button>
          </div>
        )}

        {active === 'connection' && (
          <div>
            <ReadOnlyRow label="App server" value={window.location.origin || 'Local WebView'} />
            <ReadOnlyRow label="Coach route" value="/api/chat" />
            <ReadOnlyRow label="Status" value={serverStatus} />
            <Button
              onClick={checkServer}
              disabled={checkingServer}
              variant="surface"
              size="md"
              icon="wifi"
              style={{ marginTop: 14 }}
            >
              Check server
            </Button>
          </div>
        )}

        {active === 'data' && (
          <div>
            <ReadOnlyRow label="Programs loaded" value={String((window.PROGRAMS || []).length)} />
            <ReadOnlyRow label="Recent sessions" value={String((window.TRAINAR_SESSIONS || []).length)} />
            <ReadOnlyRow label="Personal records" value={String((window.TRAINAR_PRS || []).length)} />
            <Button onClick={onExport} variant="surface" size="md" icon="download" style={{ marginTop: 14 }}>
              Download JSON
            </Button>
          </div>
        )}
      </Card>
    </div>
  );
}

function SettingsTextField({ label, value, onChange }) {
  return (
    <label style={{ display: 'block', marginBottom: 14 }}>
      <div style={{ fontSize: 11, color: 'var(--text-3)', marginBottom: 7, fontWeight: 600 }}>{label}</div>
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        style={{
          width: '100%',
          height: 44,
          borderRadius: 12,
          border: '1px solid var(--hairline)',
          background: 'var(--surface-2)',
          color: 'var(--text-1)',
          fontFamily: 'var(--font-sans)',
          fontSize: 14,
          padding: '0 12px',
          boxSizing: 'border-box',
          outline: 'none',
        }}
      />
    </label>
  );
}

function ReadOnlyRow({ label, value }) {
  return (
    <div style={rowShellStyle}>
      <div>
        <div style={rowLabelStyle}>{label}</div>
        <div style={{ fontSize: 13, fontWeight: 600, textTransform: label === 'Training goal' ? 'capitalize' : 'none' }}>
          {value || '-'}
        </div>
      </div>
    </div>
  );
}

const rowShellStyle = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  gap: 14,
  padding: '12px 0',
  borderBottom: '1px solid var(--hairline)',
};

const rowLabelStyle = {
  fontSize: 11,
  color: 'var(--text-3)',
  marginBottom: 4,
  fontWeight: 600,
};
