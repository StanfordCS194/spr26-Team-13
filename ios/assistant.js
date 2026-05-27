// Glasses coach adapter.
//
// Posts the user's spoken transcript to the thin /api/chat backend, which
// returns a free-form trainer reply. The richer tool-calling /api/assistant/chat
// route is left untouched for other callers; buildCoachContext is preserved
// below so a future integration can switch back without a JS rewrite.
(function () {
  async function askTrainARCoach(message, options = {}) {
    const cleanMessage = String(message || '').trim();
    if (!cleanMessage) {
      throw new Error('Message is required.');
    }

    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: cleanMessage }),
    });

    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(payload.error || 'Coach assistant failed.');
    }

    // Normalize on `response` so existing listeners (CoachOverlay, wake-word
    // border reset) keep working unchanged.
    const reply = String(payload.reply || '').trim();
    const normalized = { response: reply };

    window.dispatchEvent(new CustomEvent('trainar:coach-response', {
      detail: normalized,
    }));

    // Speak the reply through whatever audio route the native shell is on
    // (phone speaker, AirPods, Ray-Ban Meta, …). The WebView bootstrap
    // forwards this CustomEvent to a `speakResponse` postMessage, which
    // AppleVoiceBridge handles with AVSpeechSynthesizer.
    if (reply) {
      window.dispatchEvent(new CustomEvent('trainar:speak', {
        detail: { text: reply },
      }));
    }

    if (window.sendTrainARNativeCommand) {
      window.sendTrainARNativeCommand('coachResponse', {
        response: reply,
      });
    }

    return normalized;
  }

  function buildCoachContext(options = {}) {
    const activeProgramId = options.activeProgramId || null;
    const activeProgram = getActiveProgram(activeProgramId);

    return {
      activeProgramId,
      activeProgram,
      currentWorkout: options.currentWorkout || null,
      programs: (window.PROGRAMS || []).slice(0, 10),
      programDetail: window.PROGRAM_DETAIL || null,
      recentSessions: (window.TRAINAR_SESSIONS || []).slice(0, 20),
      personalRecords: (window.TRAINAR_PRS || []).slice(0, 20),
      devices: window.TRAINAR_DEVICES || [],
      glasses: window.TRAINAR_GLASSES_STATE || {},
    };
  }

  function getActiveProgram(activeProgramId) {
    if (activeProgramId && window.getProgramDetail) {
      const detail = window.getProgramDetail(activeProgramId);
      const listItem = (window.PROGRAMS || []).find((program) => program.id === activeProgramId);
      if (detail || listItem) {
        return {
          ...(listItem || {}),
          ...(detail || {}),
        };
      }
    }

    const first = (window.PROGRAMS || [])[0] || null;
    if (!first) return null;
    const detail = window.getProgramDetail ? window.getProgramDetail(first.id) : window.PROGRAM_DETAIL;
    return {
      ...first,
      ...(detail || {}),
    };
  }

  Object.assign(window, {
    askTrainARCoach,
    buildTrainARCoachContext: buildCoachContext,
  });
})();

