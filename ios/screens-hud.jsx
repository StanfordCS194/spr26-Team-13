// HUD demo viewer.
//
// This is intentionally optional: the normal TrainAR app does not depend on
// camera access or the HUD screen. When opened, it renders a glasses-style
// overlay over a live phone camera preview when possible, with a mock motion
// background as the fallback.

const HUD_DEMO_FACING_MODES = ['environment', 'user'];

const HudDemoScreen = ({
  programId,
  day,
  step,
  rest,
  coachResponse,
  notice,
  workoutActive = false,
  onClose,
}) => {
  const videoRef = React.useRef(null);
  const streamRef = React.useRef(null);
  const [cameraStatus, setCameraStatus] = React.useState('idle');
  const [cameraError, setCameraError] = React.useState('');
  const [sourceMode, setSourceMode] = React.useState('mock');
  const [facingMode, setFacingMode] = React.useState('environment');
  const [now, setNow] = React.useState(() => Date.now());
  const [externalState, setExternalState] = React.useState(() => window.TRAINAR_HUD_STATE || null);

  const hudState = deriveTrainARHudState({
    programId,
    day,
    step,
    rest,
    coachResponse,
    notice,
    workoutActive,
    now,
    fallback: externalState,
  });

  React.useEffect(() => {
    document.documentElement.classList.add('trainar-hud-active');
    document.body.classList.add('trainar-hud-active');
    const root = document.getElementById('root');
    if (root) root.classList.add('trainar-hud-active');
    return () => {
      document.documentElement.classList.remove('trainar-hud-active');
      document.body.classList.remove('trainar-hud-active');
      if (root) root.classList.remove('trainar-hud-active');
    };
  }, []);

  React.useEffect(() => {
    if (window.TRAINAR_NATIVE_APP && window.sendTrainARNativeCommand) {
      window.sendTrainARNativeCommand('hudScreenActive');
    }
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, []);

  React.useEffect(() => {
    const onHudState = (event) => setExternalState(event.detail || null);
    window.addEventListener('trainar:hud-state', onHudState);
    return () => window.removeEventListener('trainar:hud-state', onHudState);
  }, []);

  React.useEffect(() => {
    const onNativeCamera = (event) => {
      const detail = event.detail || {};
      if (detail.status === 'streaming') {
        setSourceMode('native-camera');
        setCameraStatus('streaming');
        setCameraError('');
        return;
      }
      if (detail.status === 'stopped') {
        setCameraStatus('idle');
        setSourceMode('mock');
        return;
      }
      setCameraStatus(detail.status || 'failed');
      setCameraError(detail.message || 'Native camera preview failed.');
      setSourceMode('mock');
    };
    window.addEventListener('trainar:native-camera', onNativeCamera);
    return () => window.removeEventListener('trainar:native-camera', onNativeCamera);
  }, []);

  React.useEffect(() => () => {
    stopHudCameraStream(streamRef);
    if (window.TRAINAR_NATIVE_APP && window.sendTrainARNativeCommand) {
      window.sendTrainARNativeCommand('stopHudCamera');
    }
  }, []);

  const startCamera = React.useCallback(async (nextFacingMode = facingMode) => {
    if (window.TRAINAR_NATIVE_APP && window.sendTrainARNativeCommand) {
      stopHudCameraStream(streamRef);
      setCameraStatus('starting');
      setCameraError('');
      window.sendTrainARNativeCommand('startHudCamera', { facingMode: nextFacingMode });
      return;
    }

    if (!navigator.mediaDevices?.getUserMedia) {
      setCameraStatus('unavailable');
      setCameraError(window.isSecureContext === false
        ? 'Camera API is blocked because this page is not a secure context.'
        : 'Camera API is not exposed in this WebView/browser.');
      setSourceMode('mock');
      return;
    }

    stopHudCameraStream(streamRef);
    setCameraStatus('starting');
    setCameraError('');

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: false,
        video: {
          facingMode: { ideal: nextFacingMode },
          width: { ideal: 1280 },
          height: { ideal: 720 },
        },
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      setFacingMode(nextFacingMode);
      setSourceMode('camera');
      setCameraStatus('streaming');
    } catch (err) {
      console.warn('HUD camera preview unavailable:', err);
      setCameraStatus('failed');
      setCameraError(err?.message || err?.name || 'Camera preview failed.');
      setSourceMode('mock');
    }
  }, [facingMode]);

  React.useEffect(() => {
    if (window.TRAINAR_NATIVE_APP && window.sendTrainARNativeCommand) {
      window.setTimeout(() => startCamera('environment'), 250);
    }
  }, [startCamera]);

  const useMockSource = () => {
    stopHudCameraStream(streamRef);
    if (window.TRAINAR_NATIVE_APP && window.sendTrainARNativeCommand) {
      window.sendTrainARNativeCommand('stopHudCamera');
    }
    setSourceMode('mock');
    setCameraStatus('idle');
    setCameraError('');
  };

  const switchCamera = () => {
    const nextIndex = (HUD_DEMO_FACING_MODES.indexOf(facingMode) + 1) % HUD_DEMO_FACING_MODES.length;
    setFacingMode(HUD_DEMO_FACING_MODES[nextIndex]);
    if (sourceMode === 'native-camera' && window.sendTrainARNativeCommand) {
      window.sendTrainARNativeCommand('switchHudCamera');
      return;
    }
    startCamera(HUD_DEMO_FACING_MODES[nextIndex]);
  };

  return (
    <Screen padTop={0} padBottom={0} style={{ background: sourceMode === 'native-camera' ? 'transparent' : '#050605', overflow: 'hidden' }}>
      <style>{`
        @media (orientation: landscape) {
          .hud-demo-controls {
            left: 8px !important;
            right: auto !important;
            top: calc(env(safe-area-inset-top, 0px) + 18px) !important;
            bottom: auto !important;
            width: 34px !important;
            flex-direction: column !important;
            justify-content: flex-start !important;
            align-items: center !important;
            gap: 6px !important;
            z-index: 20 !important;
          }

          .hud-demo-controls-group {
            flex-direction: column !important;
            gap: 6px !important;
          }

          .hud-demo-control-button {
            width: 30px !important;
            height: 30px !important;
            min-width: 30px !important;
            opacity: 0.72 !important;
          }

          .hud-demo-status-pill {
            width: 30px !important;
            height: 30px !important;
            padding: 0 !important;
            justify-content: center !important;
            border-radius: 9999px !important;
            font-size: 0 !important;
            opacity: 0.72 !important;
          }

          .hud-demo-status-pill span {
            margin: 0 !important;
          }
        }
      `}</style>
      <div style={{
        position: 'absolute',
        inset: 0,
        overflow: 'hidden',
        background: sourceMode === 'native-camera' ? 'transparent' : '#050605',
        minHeight: '100dvh',
      }}>
        {sourceMode === 'camera' ? (
          <video
            ref={videoRef}
            playsInline
            muted
            autoPlay
            style={{
              position: 'absolute',
              inset: 0,
              width: '100%',
              height: '100%',
              objectFit: 'cover',
              transform: facingMode === 'user' ? 'scaleX(-1)' : 'none',
              background: '#050605',
            }}
          />
        ) : sourceMode === 'native-camera' ? (
          <div style={{ position: 'absolute', inset: 0, background: 'transparent' }} />
        ) : (
          <HudMockScene now={now} />
        )}

        <HudLensVignette />
        <HudOverlay state={hudState} />
      </div>

      <div className="hud-demo-controls" style={{
        position: 'absolute',
        top: 'calc(env(safe-area-inset-top, 0px) + 10px)',
        left: 'calc(env(safe-area-inset-left, 0px) + 32px)',
        right: 14,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: 10,
        zIndex: 10,
      }}>
        <button onClick={onClose} className="press hud-demo-control-button" aria-label="Close HUD demo" style={hudIconButtonStyle()}>
          <Icon name="chevron-left" size={19} />
        </button>
        <div className="hud-demo-status-pill" style={{
          height: 34,
          padding: '0 12px',
          borderRadius: 9999,
          display: 'inline-flex',
          alignItems: 'center',
          gap: 8,
          background: 'rgba(0,0,0,0.42)',
          border: '1px solid rgba(255,255,255,0.14)',
          color: '#f8faf5',
          backdropFilter: 'blur(14px)',
          WebkitBackdropFilter: 'blur(14px)',
          fontSize: 12,
          fontWeight: 700,
        }}>
          <span style={{
            width: 7,
            height: 7,
            borderRadius: 9999,
            background: (sourceMode === 'camera' || sourceMode === 'native-camera') ? '#c5f23e' : '#f5c542',
            boxShadow: (sourceMode === 'camera' || sourceMode === 'native-camera') ? '0 0 12px rgba(197,242,62,0.8)' : '0 0 12px rgba(245,197,66,0.7)',
          }} />
          {(sourceMode === 'camera' || sourceMode === 'native-camera') ? 'Camera HUD' : 'Mock HUD'}
        </div>
        <div className="hud-demo-controls-group" style={{ display: 'flex', gap: 8 }}>
          {sourceMode === 'camera' && (
            <button onClick={switchCamera} className="press hud-demo-control-button" aria-label="Switch camera" style={hudIconButtonStyle()}>
              <Icon name="rotate" size={18} />
            </button>
          )}
          {sourceMode === 'native-camera' && (
            <button onClick={switchCamera} className="press hud-demo-control-button" aria-label="Switch camera" style={hudIconButtonStyle()}>
              <Icon name="rotate" size={18} />
            </button>
          )}
          <button
            onClick={(sourceMode === 'camera' || sourceMode === 'native-camera') ? useMockSource : () => startCamera()}
            className="press hud-demo-control-button"
            aria-label={(sourceMode === 'camera' || sourceMode === 'native-camera') ? 'Use mock source' : 'Start camera'}
            style={hudIconButtonStyle()}
          >
            <Icon name={(sourceMode === 'camera' || sourceMode === 'native-camera') ? 'video' : 'camera'} size={18} />
          </button>
        </div>
      </div>

      {(cameraStatus === 'failed' || cameraStatus === 'unavailable') && (
        <div style={{
          position: 'absolute',
          left: 'calc(env(safe-area-inset-left, 0px) + 36px)',
          right: 18,
          bottom: 'calc(env(safe-area-inset-bottom, 0px) + 22px)',
          zIndex: 12,
          padding: '10px 12px',
          borderRadius: 12,
          background: 'rgba(0,0,0,0.58)',
          border: '1px solid rgba(245,197,66,0.36)',
          color: '#fff7d6',
          fontSize: 12,
          lineHeight: 1.35,
          backdropFilter: 'blur(14px)',
          WebkitBackdropFilter: 'blur(14px)',
        }}>
          {cameraError || 'Camera preview is unavailable here, so the HUD is using the mock feed.'}
        </div>
      )}
    </Screen>
  );
};

function HudOverlay({ state }) {
  const setProgress = state.setProgress || 'Set 1 of 1';
  const targetSummary = state.targetSummary || 'Ready';
  const restActive = Number.isFinite(state.restRemainingSeconds);
  const restProgress = restActive && state.restDurationSeconds
    ? 1 - Math.max(0, Math.min(1, state.restRemainingSeconds / state.restDurationSeconds))
    : 0;

  return (
    <div style={{ position: 'absolute', inset: 0, zIndex: 4, pointerEvents: 'none' }}>
      <HudPanel style={{ top: 64, left: 'calc(env(safe-area-inset-left, 0px) + 36px)', width: 292 }}>
        <div style={hudPanelTitleStyle()}>Workout</div>
        <HudLine label="Exercise" value={state.exerciseName || 'Workout'} strong />
        <HudLine label="Set" value={setProgress} />
        <HudLine label="Target" value={targetSummary} />
        <HudLine label="Next" value={state.nextAction || 'Follow the active set'} muted />
      </HudPanel>

      <div style={{
        position: 'absolute',
        top: 66,
        right: 18,
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        height: 32,
        padding: '0 10px',
        borderRadius: 9999,
        background: 'rgba(0,0,0,0.46)',
        border: '1px solid rgba(197,242,62,0.35)',
        color: '#dfff7a',
        fontSize: 11,
        fontWeight: 750,
        backdropFilter: 'blur(12px)',
        WebkitBackdropFilter: 'blur(12px)',
      }}>
        <span style={{
          width: 8,
          height: 8,
          borderRadius: 9999,
          background: '#c5f23e',
          boxShadow: '0 0 12px rgba(197,242,62,0.95)',
        }} />
        Tracking
      </div>

      {restActive && (
        <div style={{
          position: 'absolute',
          left: 'calc(env(safe-area-inset-left, 0px) + 36px)',
          right: 18,
          bottom: 38,
          display: 'flex',
          flexDirection: 'column',
          gap: 8,
        }}>
          <div style={{
            alignSelf: 'flex-start',
            height: 30,
            padding: '0 12px',
            display: 'inline-flex',
            alignItems: 'center',
            borderRadius: 9999,
            background: 'rgba(245,197,66,0.16)',
            border: '1px solid rgba(245,197,66,0.45)',
            color: '#ffe58a',
            fontSize: 12,
            fontWeight: 750,
          }}>
            Rest {state.restRemainingSeconds}s
          </div>
          <div style={{
            height: 8,
            borderRadius: 9999,
            background: 'rgba(255,255,255,0.16)',
            overflow: 'hidden',
            border: '1px solid rgba(255,255,255,0.12)',
          }}>
            <div style={{
              width: `${Math.round(restProgress * 100)}%`,
              height: '100%',
              borderRadius: 9999,
              background: '#f5c542',
              boxShadow: '0 0 14px rgba(245,197,66,0.58)',
              transition: 'width 600ms linear',
            }} />
          </div>
        </div>
      )}

      {state.notification && (
        <div style={{
          position: 'absolute',
          left: 'calc(env(safe-area-inset-left, 0px) + 36px)',
          right: 32,
          bottom: restActive ? 96 : 34,
          minHeight: 44,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          textAlign: 'center',
          padding: '8px 12px',
          borderRadius: 14,
          background: 'rgba(0,0,0,0.56)',
          border: '1px solid rgba(197,242,62,0.26)',
          color: '#f9fff0',
          fontSize: 13,
          fontWeight: 700,
          backdropFilter: 'blur(14px)',
          WebkitBackdropFilter: 'blur(14px)',
        }}>
          {state.notification}
        </div>
      )}
    </div>
  );
}

function HudPanel({ children, style }) {
  return (
    <div style={{
      position: 'absolute',
      padding: '13px 14px',
      borderRadius: 12,
      background: 'rgba(0,0,0,0.48)',
      border: '1px solid rgba(255,255,255,0.16)',
      boxShadow: '0 14px 42px rgba(0,0,0,0.28)',
      backdropFilter: 'blur(14px)',
      WebkitBackdropFilter: 'blur(14px)',
      color: '#f9fff0',
      ...style,
    }}>
      {children}
    </div>
  );
}

function HudLine({ label, value, strong = false, muted = false }) {
  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: '68px minmax(0, 1fr)',
      gap: 8,
      alignItems: 'baseline',
      marginTop: 8,
      minWidth: 0,
    }}>
      <div style={{ fontSize: 10, color: 'rgba(249,255,240,0.58)', fontWeight: 700 }}>{label}</div>
      <div style={{
        fontSize: strong ? 16 : 12,
        lineHeight: 1.18,
        color: muted ? 'rgba(249,255,240,0.66)' : '#f9fff0',
        fontWeight: strong ? 760 : 680,
        overflowWrap: 'anywhere',
      }}>{value}</div>
    </div>
  );
}

function HudMockScene({ now }) {
  const phase = (now / 1000) % 12;
  return (
    <div style={{
      position: 'absolute',
      inset: 0,
      background: `
        radial-gradient(circle at ${28 + phase * 2}% 22%, rgba(197,242,62,0.14), transparent 16%),
        linear-gradient(145deg, #181b17 0%, #0d1110 46%, #232824 100%)
      `,
    }}>
      <div style={{
        position: 'absolute',
        left: '9%',
        right: '9%',
        top: '19%',
        height: '20%',
        borderRadius: 18,
        background: 'linear-gradient(90deg, rgba(130,140,128,0.9), rgba(59,64,59,0.95))',
        boxShadow: '0 22px 70px rgba(0,0,0,0.48)',
        transform: `translateY(${Math.sin(phase) * 5}px)`,
      }} />
      <div style={{
        position: 'absolute',
        left: '18%',
        bottom: '12%',
        width: '64%',
        height: '42%',
        borderRadius: 24,
        border: '1px solid rgba(255,255,255,0.08)',
        background: 'linear-gradient(140deg, rgba(255,255,255,0.12), rgba(255,255,255,0.03))',
        transform: `perspective(700px) rotateX(58deg) rotateZ(${Math.sin(phase / 2) * 1.5}deg)`,
      }} />
      <div style={{
        position: 'absolute',
        left: '36%',
        bottom: '28%',
        width: '28%',
        height: '28%',
        borderRadius: 9999,
        background: 'rgba(22,24,22,0.92)',
        border: '18px solid rgba(118,126,116,0.9)',
        boxShadow: '0 12px 36px rgba(0,0,0,0.4)',
      }} />
      <div style={{
        position: 'absolute',
        left: 0,
        right: 0,
        bottom: 0,
        height: '34%',
        background: 'linear-gradient(0deg, rgba(0,0,0,0.58), transparent)',
      }} />
    </div>
  );
}

function HudLensVignette() {
  return (
    <>
      <div style={{
        position: 'absolute',
        inset: 0,
        background: 'radial-gradient(circle at center, transparent 48%, rgba(0,0,0,0.48) 100%)',
        zIndex: 2,
        pointerEvents: 'none',
      }} />
      <div style={{
        position: 'absolute',
        inset: 12,
        border: '1px solid rgba(197,242,62,0.12)',
        borderRadius: 28,
        zIndex: 3,
        pointerEvents: 'none',
      }} />
    </>
  );
}

function deriveTrainARHudState({ programId, day, step, rest, coachResponse, notice, workoutActive, now, fallback }) {
  if (!step && fallback?.workoutActive) {
    const remaining = calculateRestRemaining(fallback.rest, now);
    return {
      ...fallback,
      restRemainingSeconds: remaining,
      restDurationSeconds: fallback.restDurationSeconds || fallback.rest?.durationSeconds || null,
    };
  }

  if (!step) {
    const program = programId
      ? (window.PROGRAMS || []).find((item) => item.id === programId)
      : null;
    return {
      workoutActive: false,
      exerciseName: 'No active workout',
      setProgress: 'Idle',
      repProgress: '--',
      targetSummary: program ? `${program.name} ready` : 'Waiting for workout',
      nextAction: program ? 'Say "start it" to begin' : 'Say "make a workout"',
      restRemainingSeconds: null,
      restDurationSeconds: null,
      notification: notice || coachResponse?.response || null,
    };
  }

  const program = (window.PROGRAMS || []).find((item) => item.id === programId) || (window.PROGRAMS || [])[0] || {};
  const detail = programId && window.getProgramDetail
    ? (window.getProgramDetail(programId) || window.PROGRAM_DETAIL || { exercises: [] })
    : (window.PROGRAM_DETAIL || { exercises: [] });
  const selectedDay = day?.id
    ? (detail.days || []).find((item) => item.id === day.id) || day
    : (day || (detail.days || [])[0] || null);
  const exercises = getDayExercises(selectedDay, detail);
  const exerciseName = step?.exerciseName || exercises[0]?.name || program.name || 'Workout';
  const currentExercise = exercises.find((exercise) => (
    normalizeCoachName(exercise.name) === normalizeCoachName(exerciseName)
  )) || exercises[0] || {};
  const setNumber = Number.parseInt(step?.setNumber, 10) || 1;
  const setCount = Number.parseInt(step?.setCount || currentExercise.sets, 10) || 1;
  const repTarget = step?.repTarget || currentExercise.reps || null;
  const loadTarget = step?.loadTarget || currentExercise.load || null;
  const restSeconds = rest?.durationSeconds || step?.restSeconds || parseRestSecondsForCoach(currentExercise.rest);
  const restRemainingSeconds = calculateRestRemaining(rest, now);

  let nextAction = step ? 'Complete the active set' : 'Start a workout';
  if (Number.isFinite(restRemainingSeconds)) nextAction = 'Recover and prepare';
  else if (setNumber < setCount) nextAction = 'Advance when this set is done';
  else if (step) nextAction = 'Finish or move to next exercise';

  return {
    workoutActive,
    exerciseName,
    setProgress: step ? `Set ${setNumber} of ${setCount}` : 'No active set',
    repProgress: repTarget ? `0 / ${repTarget}` : '--',
    targetSummary: [loadTarget, repTarget ? `${repTarget} reps` : null].filter(Boolean).join(' x ') || 'Ready',
    nextAction,
    restRemainingSeconds,
    restDurationSeconds: restSeconds,
    notification: notice || coachResponse?.response || null,
  };
}

function buildTrainARHudStateSnapshot({ programId, day, step, rest, coachResponse, notice, workoutActive }) {
  return deriveTrainARHudState({
    programId,
    day,
    step,
    rest,
    coachResponse,
    notice,
    workoutActive,
    now: Date.now(),
    fallback: null,
  });
}

function calculateRestRemaining(rest, now) {
  if (!rest?.durationSeconds || !rest?.startedAt) return null;
  const startedAt = new Date(rest.startedAt).getTime();
  if (!Number.isFinite(startedAt)) return null;
  const elapsed = Math.max(0, Math.floor((now - startedAt) / 1000));
  return Math.max(0, Number(rest.durationSeconds) - elapsed);
}

function stopHudCameraStream(streamRef) {
  if (!streamRef.current) return;
  streamRef.current.getTracks().forEach((track) => track.stop());
  streamRef.current = null;
}

function hudIconButtonStyle() {
  return {
    width: 38,
    height: 38,
    borderRadius: 9999,
    border: '1px solid rgba(255,255,255,0.14)',
    background: 'rgba(0,0,0,0.42)',
    color: '#f8faf5',
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    backdropFilter: 'blur(14px)',
    WebkitBackdropFilter: 'blur(14px)',
    cursor: 'pointer',
  };
}

function hudPanelTitleStyle() {
  return {
    fontSize: 10,
    fontWeight: 800,
    letterSpacing: 0,
    textTransform: 'uppercase',
    color: 'rgba(197,242,62,0.9)',
    marginBottom: 6,
  };
}

Object.assign(window, {
  HudDemoScreen,
  deriveTrainARHudState,
  buildTrainARHudStateSnapshot,
});
