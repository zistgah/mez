/* providers.js — handoff adapters. THE CYCLER DOES NOT OWN A VENDOR.
 *
 * The spec is explicit: expose ChatGPT, Claude and Gemini as provider links and do not silently
 * prefer one. So the list is alphabetical, none is marked default, and clipboard is the
 * zero-credential mode that works when every one of them is unreachable.
 *
 * A provider here is a URL and nothing else. No key, no account, no SDK, no telemetry. Where a
 * service accepts the prompt in the address it is seeded; where it does not, the prompt is on
 * your clipboard and you paste it. Both are handoff — neither is integration.
 */
export const PROVIDERS = [
  { id: 'chatgpt', name: 'ChatGPT',    url: p => 'https://chatgpt.com/?q=' + encodeURIComponent(p) },
  { id: 'claude',  name: 'Claude',     url: () => 'https://claude.ai/new' },
  { id: 'gemini',  name: 'Gemini',     url: () => 'https://gemini.google.com/app' },
  { id: 'other',   name: 'Another AI', url: () => localStorage.getItem('mez.otherAI') || 'about:blank' }
];

/* Optional adapters. Neither is required and neither is configured. */
export const ADAPTERS = [
  { id: 'clipboard', title: 'Clipboard handoff', keyless: true, default: true,
    what: 'the prompt is built here and carried by you. Nothing is transmitted.' },
  { id: 'local', title: 'A server on this machine', keyless: true, default: false,
    what: 'HTTP to localhost. Nothing leaves the machine.', example: 'http://localhost:8080/v1/chat/completions' },
  { id: 'remote', title: 'A configured endpoint', keyless: false, default: false,
    what: 'your address, your key. Credentials stay out of artifacts and are never committed.' }
];
