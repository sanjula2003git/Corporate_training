/* Minimal Chrome DevTools Protocol driver. Node 22 has a global WebSocket,
   so this needs no npm install at all. */
import { spawn } from 'node:child_process';
import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';

export async function launch(port = 9222) {
  const profile = mkdtempSync(join(tmpdir(), 'leafcdp-'));
  const proc = spawn(CHROME, [
    '--headless=new',
    `--remote-debugging-port=${port}`,
    `--user-data-dir=${profile}`,
    '--no-first-run',
    '--no-default-browser-check',
    '--disable-gpu',
    '--hide-scrollbars',
    '--window-size=1400,1000',
    'about:blank'
  ], { stdio: 'ignore' });

  // wait for the debugging endpoint to answer
  for (let i = 0; i < 120; i++) {
    try {
      const r = await fetch(`http://127.0.0.1:${port}/json/version`);
      if (r.ok) break;
    } catch { }
    await sleep(120);
  }
  return { proc, port };
}

export async function attach(port = 9222) {
  const list = await (await fetch(`http://127.0.0.1:${port}/json`)).json();
  const page = list.find(t => t.type === 'page');
  if (!page) throw new Error('no page target');
  return connect(page.webSocketDebuggerUrl);
}

export function connect(url) {
  const ws = new WebSocket(url);
  let id = 0;
  const pending = new Map();
  const listeners = [];
  const ready = new Promise((res, rej) => {
    ws.addEventListener('open', () => res());
    ws.addEventListener('error', e => rej(e));
  });
  ws.addEventListener('message', ev => {
    const m = JSON.parse(ev.data);
    if (m.id && pending.has(m.id)) {
      const { res, rej } = pending.get(m.id);
      pending.delete(m.id);
      m.error ? rej(new Error(m.error.message)) : res(m.result);
    } else if (m.method) {
      for (const fn of listeners) fn(m);
    }
  });
  return {
    ready,
    on: fn => listeners.push(fn),
    send(method, params = {}) {
      return ready.then(() => new Promise((res, rej) => {
        const n = ++id;
        pending.set(n, { res, rej });
        ws.send(JSON.stringify({ id: n, method, params }));
      }));
    },
    close: () => ws.close()
  };
}

export const sleep = ms => new Promise(r => setTimeout(r, ms));

/* Evaluate an expression in the page and return its value. Throws on a page
   side exception so a broken selector never looks like a passing test. */
export async function evalIn(c, expr) {
  const r = await c.send('Runtime.evaluate', {
    expression: `(function(){ ${expr} })()`,
    returnByValue: true,
    awaitPromise: true
  });
  if (r.exceptionDetails) {
    throw new Error('page threw: ' +
      (r.exceptionDetails.exception?.description || r.exceptionDetails.text));
  }
  return r.result.value;
}

/* Real trusted mouse input - Chrome synthesises the pointer events from it,
   which is the whole reason for driving the browser instead of calling the
   handlers directly. */
export async function mouse(c, type, x, y, button = 'left') {
  await c.send('Input.dispatchMouseEvent', {
    type, x, y, button,
    clickCount: type === 'mousePressed' || type === 'mouseReleased' ? 1 : 0,
    buttons: type === 'mouseMoved' ? 1 : (type === 'mousePressed' ? 1 : 0)
  });
}

export async function clickAt(c, x, y) {
  await mouse(c, 'mouseMoved', x, y);
  await mouse(c, 'mousePressed', x, y);
  await mouse(c, 'mouseReleased', x, y);
}

/* Click a css selector by its real on screen box.

   Scroll it into view FIRST and measure afterwards. The nav buttons sit at the
   bottom of a tall panel, so an unscrolled getBoundingClientRect hands back a y
   below the viewport and the click lands on nothing - which looks exactly like
   a missing element and wastes an hour. */
export async function click(c, sel) {
  const box = await evalIn(c, `
    var n = document.querySelector(${JSON.stringify(sel)});
    if (!n) return null;
    n.scrollIntoView({block: 'center', inline: 'center'});
    return 1;
  `);
  if (!box) throw new Error('no element for ' + sel);
  await sleep(60);
  const at = await evalIn(c, `
    var n = document.querySelector(${JSON.stringify(sel)});
    if (!n) return null;
    var r = n.getBoundingClientRect();
    if (r.width === 0 && r.height === 0) return null;
    return {x: r.left + r.width/2, y: r.top + r.height/2};
  `);
  if (!at) throw new Error('element not visible: ' + sel);
  await clickAt(c, at.x, at.y);
}

export async function type(c, sel, text) {
  await click(c, sel);
  await evalIn(c, `document.querySelector(${JSON.stringify(sel)}).value='';`);
  for (const ch of text) {
    await c.send('Input.dispatchKeyEvent', { type: 'keyDown', text: ch });
    await c.send('Input.dispatchKeyEvent', { type: 'keyUp' });
  }
  await evalIn(c, `
    var n=document.querySelector(${JSON.stringify(sel)});
    n.dispatchEvent(new Event('input',{bubbles:true}));
  `);
}

export async function text(c, sel) {
  return evalIn(c, `
    var n=document.querySelector(${JSON.stringify(sel)});
    return n ? n.textContent.trim() : null;
  `);
}
