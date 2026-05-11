// Web side of the native iOS bridge.
//
// The native wrapper dispatches `trainar:glasses` events into the page. This
// file keeps a small global state object so existing React screens can stay
// lightweight while the native shell becomes the source of glasses state.
(function () {
  const state = {
    connected: false,
    battery: null,
    deviceName: null,
    lastEvent: null,
  };

  function emitState() {
    window.dispatchEvent(new CustomEvent('trainar:glasses-state', {
      detail: { ...state },
    }));
  }

  function handleGlassesEvent(event) {
    const detail = event.detail || {};
    const payload = detail.payload || {};

    state.lastEvent = detail;

    if (detail.type === 'connected') {
      state.connected = true;
      state.deviceName = payload.deviceName || state.deviceName;
      state.battery = payload.battery ? Number(payload.battery) : state.battery;
    }

    if (detail.type === 'disconnected') {
      state.connected = false;
      state.deviceName = payload.deviceName || state.deviceName;
    }

    emitState();
  }

  function sendNativeCommand(type, payload = {}) {
    if (!window.TrainARNative || typeof window.TrainARNative.postMessage !== 'function') {
      return false;
    }

    window.TrainARNative.postMessage(type, payload);
    return true;
  }

  window.TRAINAR_GLASSES_STATE = state;
  window.sendTrainARNativeCommand = sendNativeCommand;
  window.addEventListener('trainar:glasses', handleGlassesEvent);
})();

