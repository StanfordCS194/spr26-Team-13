// Supabase browser client for the production iOS prototype.
// The publishable key is safe to ship to the browser; RLS protects user data.

(function () {
  const SUPABASE_URL = 'https://rcmlbgjqwpfzpiownxfy.supabase.co';
  const SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJjbWxiZ2pxd3BmenBpb3dueGZ5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzgyMjU2NzgsImV4cCI6MjA5MzgwMTY3OH0.fKcwQ0Jws91vA9PcHg8PdyWDhP8WXYg4WFU5ll8ubyo';

  if (!window.supabase || !window.supabase.createClient) {
    console.error('Supabase JS client failed to load.');
    return;
  }

  window.TRAINAR_SUPABASE_URL = SUPABASE_URL;
  window.TRAINAR_SUPABASE_KEY = SUPABASE_KEY;
  window.trainarSupabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_KEY, {
    auth: {
      autoRefreshToken: true,
      persistSession: true,
      detectSessionInUrl: true,
      storageKey: 'trainar.supabase.auth',
    },
  });
})();
