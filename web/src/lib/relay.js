// Nostr relay gateway client
// Uses relay.nostr.band as a CORS-capable gateway

const RELAYS = [
  'wss://relay.nostr.band',
  'wss://nos.lol',
  'wss://relay.damus.io',
];

const APP_TAG = 'agentboss';
const JOB_TAG = 'job';

// ── Relay Connection ───────────────────────────────

export function createRelayClient() {
  let ws = null;
  let onEvent = null;
  let onEOSE = null;
  let currentSubId = null;
  let currentRelayIndex = 0;

  function connect(relayUrl = RELAYS[currentRelayIndex]) {
    return new Promise((resolve, reject) => {
      if (currentRelayIndex >= RELAYS.length) {
        reject(new Error('All relays failed'));
        return;
      }
      const url = relayUrl || RELAYS[currentRelayIndex];
      ws = new WebSocket(url);

      ws.onopen = () => resolve();
      ws.onerror = () => {
        ws.close();
        currentRelayIndex++;
        if (currentRelayIndex < RELAYS.length) {
          connect().then(resolve).catch(reject);
        } else {
          reject(new Error('All relays failed'));
        }
      };

      ws.onmessage = (msg) => {
        const data = JSON.parse(msg.data);
        const [type, subId, event] = data;

        if (type === 'EOSE' && subId === currentSubId) {
          if (onEOSE) onEOSE();
        }
        if (type === 'EVENT' && subId === currentSubId && onEvent) {
          onEvent(event);
        }
      };
    });
  }

  function subscribe(subId, filter) {
    currentSubId = subId;
    ws.send(JSON.stringify(['REQ', subId, filter]));
  }

  function unsubscribe(subId) {
    ws.send(JSON.stringify(['CLOSE', subId]));
    currentSubId = null;
  }

  function publish(event) {
    return new Promise((resolve, reject) => {
      ws.send(JSON.stringify(['EVENT', event]));

      const timeout = setTimeout(() => {
        reject(new Error('Publish timeout'));
      }, 10000);

      const handler = (msg) => {
        const data = JSON.parse(msg.data);
        if (data[0] === 'OK' && data[1] === event.id) {
          clearTimeout(timeout);
          ws.removeEventListener('message', handler);
          resolve({ accepted: data[2], message: data[3] });
        }
      };

      ws.addEventListener('message', handler);
    });
  }

  function close() {
    if (ws) ws.close();
    currentRelayIndex = 0;
  }

  return {
    connect,
    subscribe,
    unsubscribe,
    publish,
    close,
    onEvent: (fn) => { onEvent = fn; },
    onEOSE: (fn) => { onEOSE = fn; },
  };
}

// ── Job Event Helpers ────────────────────────────

export function parseJobEvent(event) {
  try {
    const content = JSON.parse(event.content);
    const province = extractTag(event, 'province');
    const city = extractTag(event, 'city');
    const dTag = extractTag(event, 'd');
    return {
      id: event.id,
      pubkey: event.pubkey,
      created_at: event.created_at,
      d_tag: dTag,
      title: content.title || '',
      company: content.company || '',
      salary: content.salary_range || '',
      description: content.description || '',
      contact: content.contact || '',
      province,
      city,
      content_raw: event.content,
    };
  } catch {
    return null;
  }
}

function extractTag(event, name) {
  const tag = event.tags.find((t) => t[0] === name);
  return tag ? tag[1] : '';
}

export function generateDTag() {
  return Math.random().toString(36).substring(2, 10) + Date.now().toString(36);
}

// ── Job Queries ─────────────────────────────────

export function buildJobFilter(opts = {}) {
  const filter = {
    kinds: [30078],
    '#t': [APP_TAG, JOB_TAG],
    limit: opts.limit || 50,
  };
  if (opts.province) filter['#province'] = [opts.province];
  if (opts.city) filter['#city'] = [opts.city];
  if (opts.since) filter.since = opts.since;
  return filter;
}

export { RELAYS, APP_TAG, JOB_TAG };
