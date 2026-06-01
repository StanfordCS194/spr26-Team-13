// Glasses coach adapter.
//
// Posts the user's spoken transcript and app context to /api/chat. The backend
// can now either answer conversationally or run one of the supported workout
// actions, while this adapter keeps the UI listening for the same response event.
(function () {
  async function askTrainARCoach(message, options = {}) {
    const cleanMessage = String(message || '').trim();
    if (!cleanMessage) {
      throw new Error('Message is required.');
    }

    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text: cleanMessage,
        session_id: getCoachSessionId(options),
        context: buildCoachContext(options),
        auth: await getSupabaseAuthPayload(),
      }),
    });

    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(payload.error || 'Coach assistant failed.');
    }

    // Normalize on `response` so existing listeners (CoachOverlay, wake-word
    // border reset) keep working unchanged.
    const reply = String(payload.reply || '').trim();
    const expectsFollowUp = looksLikeQuestion(reply);
    const normalized = {
      response: reply,
      expectsFollowUp,
      action: payload.action || null,
      actionResult: payload.action_result || null,
      uiPatch: payload.ui_patch || null,
      sources: payload.sources || [],
      mode: payload.mode || 'chat',
      clientTurnId: options.clientTurnId || null,
    };

    if (normalized.uiPatch) {
      window.dispatchEvent(new CustomEvent('trainar:coach-action', {
        detail: normalized,
      }));
    }

    window.dispatchEvent(new CustomEvent('trainar:coach-response', {
      detail: normalized,
    }));

    // Speak the reply through whatever audio route the native shell is on
    // (phone speaker, AirPods, Ray-Ban Meta, …). The WebView bootstrap
    // forwards this CustomEvent to a `speakResponse` postMessage, which
    // AppleVoiceBridge handles with AVSpeechSynthesizer.
    if (reply) {
      window.dispatchEvent(new CustomEvent('trainar:speak', {
        detail: { text: reply, continueListening: expectsFollowUp },
      }));
    }

    if (window.sendTrainARNativeCommand) {
      window.sendTrainARNativeCommand('coachResponse', {
        response: reply,
        continueListening: expectsFollowUp,
      });
    }

    return normalized;
  }

  function looksLikeQuestion(value) {
    const text = String(value || '').trim();
    if (!text) return false;
    if (/[?]\s*$/.test(text)) return true;
    return /^(what|which|who|when|where|why|how|do|does|did|can|could|would|should|is|are|am|will)\b/i.test(text);
  }

  function buildCoachContext(options = {}) {
    const activeProgramId = options.activeProgramId || null;
    const activeProgram = getActiveProgram(activeProgramId);

    return {
      activeProgramId,
      activeProgram,
      trainingProfile: window.TRAINAR_TRAINING_PROFILE || null,
      currentWorkout: options.currentWorkout || null,
      pendingLogConfirmation: options.pendingLogConfirmation || null,
      programs: (window.PROGRAMS || []).slice(0, 10),
      programDetail: window.PROGRAM_DETAIL || null,
      recentSessions: (window.TRAINAR_SESSIONS || []).slice(0, 20),
      personalRecords: (window.TRAINAR_PRS || []).slice(0, 20),
      devices: window.TRAINAR_DEVICES || [],
      glasses: window.TRAINAR_GLASSES_STATE || {},
    };
  }

  function getCoachSessionId(options = {}) {
    if (options.currentWorkout?.sessionId) return `workout:${options.currentWorkout.sessionId}`;
    if (options.activeProgramId) return `program:${options.activeProgramId}`;

    const storageKey = 'trainar.coachSessionId';
    try {
      const existing = window.localStorage && window.localStorage.getItem(storageKey);
      if (existing) return existing;

      const created = `browser:${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
      if (window.localStorage) window.localStorage.setItem(storageKey, created);
      return created;
    } catch (_err) {
      return 'browser:ephemeral';
    }
  }

  async function getSupabaseAuthPayload() {
    if (!window.trainarSupabase?.auth?.getSession) return null;
    try {
      const { data } = await window.trainarSupabase.auth.getSession();
      const token = data?.session?.access_token;
      return token ? { access_token: token } : null;
    } catch (_err) {
      return null;
    }
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
