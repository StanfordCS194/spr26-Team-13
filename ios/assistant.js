// Glasses coach adapter.
//
// Supabase data is already loaded into window.* by data.js under the signed-in
// user's RLS-protected session. This adapter packages that state as context for
// the local assistant endpoint so coach responses can refer to saved programs,
// workout history, PRs, and device state.
(function () {
  async function getSupabaseAccessToken() {
    const client = window.trainarSupabase;
    if (!client || !client.auth || typeof client.auth.getSession !== 'function') {
      return null;
    }
    try {
      const { data, error } = await client.auth.getSession();
      if (error) return null;
      return data && data.session ? data.session.access_token : null;
    } catch (_err) {
      return null;
    }
  }

  async function askTrainARCoach(message, options = {}) {
    const cleanMessage = String(message || '').trim();
    if (!cleanMessage) {
      throw new Error('Message is required.');
    }

    const headers = { 'Content-Type': 'application/json' };
    const accessToken = await getSupabaseAccessToken();
    if (accessToken) {
      headers['Authorization'] = 'Bearer ' + accessToken;
    }

    const response = await fetch('/api/assistant/chat', {
      method: 'POST',
      headers,
      body: JSON.stringify({
        message: cleanMessage,
        context: buildCoachContext(options),
      }),
    });

    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(payload.error || 'Coach assistant failed.');
    }

    window.dispatchEvent(new CustomEvent('trainar:coach-response', {
      detail: payload,
    }));

    // Ask the native shell to speak the reply via AVSpeechSynthesizer.
    window.dispatchEvent(new CustomEvent('trainar:speak', {
      detail: { text: payload.response || '' },
    }));

    if (window.sendTrainARNativeCommand) {
      window.sendTrainARNativeCommand('coachResponse', {
        response: payload.response || '',
      });
      if (payload.response) {
        window.sendTrainARNativeCommand('speakResponse', {
          text: payload.response,
        });
      }
    }

    // Trigger a History refresh so newly-written sets show up.
    const action = (payload.action && payload.action.action) || '';
    if (['log_set', 'finish_workout', 'start_workout', 'start_exercise'].includes(action)) {
      window.dispatchEvent(new CustomEvent('trainar:history-changed'));
    }

    return payload;
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

