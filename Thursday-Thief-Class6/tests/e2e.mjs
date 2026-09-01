/* A student run through "The Thursday Thief", driven with real mouse input
   over CDP. Guards the layout rework: everything below is done by clicking
   what is on screen, so anything that ends up off screen fails here.

     node tests/e2e.mjs [url] [w] [h]                                      */
import { launch, attach, evalIn, click, clickAt, mouse, type, text, sleep } from './cdp.mjs';

const URL = process.argv[2] || 'http://127.0.0.1:8899/index.html';
const W = Number(process.argv[3] || 1366);
const H = Number(process.argv[4] || 768);
const KEY = 'thursday-thief-class6-v1';

let pass = 0, fail = 0;
const bad = [];
function ok(name, cond, extra) {
  if (cond) { pass++; console.log('  ok   ' + name); }
  else { fail++; bad.push(name); console.log('  FAIL ' + name + (extra ? '  <- ' + extra : '')); }
}

/* nothing may sit outside the panel: that is the whole point of the rework */
async function assertOnScreen(c, label) {
  const off = await evalIn(c, `
    var out = [];
    document.querySelectorAll('.btn, .card, .opt, .slot, .qdot').forEach(function (el) {
      var b = el.getBoundingClientRect();
      if (b.height === 0) return;
      if (b.bottom > window.innerHeight + 1 || b.top < -1)
        out.push((el.id || el.className.split(' ')[0]) + '@' + Math.round(b.top) + '-' + Math.round(b.bottom));
    });
    return out;
  `);
  ok(label + ': every control on screen', off.length === 0, off.join(', '));
}

async function centreOf(c, sel, nth) {
  return evalIn(c, `
    var n = document.querySelectorAll(${JSON.stringify(sel)})[${nth || 0}];
    if (!n) return null;
    var b = n.getBoundingClientRect();
    return { x: Math.round(b.left + b.width / 2), y: Math.round(b.top + b.height / 2) };
  `);
}

const { proc, port } = await launch(9226);
const c = await attach(port);
await c.send('Emulation.setDeviceMetricsOverride',
  { width: W, height: H, deviceScaleFactor: 1, mobile: false });

console.log('\n  ' + W + 'x' + H + '\n');

await evalIn(c, `location.href = ${JSON.stringify(URL)}`);
await sleep(900);
await evalIn(c, `localStorage.clear(); location.reload();`);
await sleep(900);

/* ---- welcome ---- */
ok('welcome renders', (await text(c, '.title-main')).indexOf('Thursday') >= 0);
await assertOnScreen(c, 'welcome');
await click(c, '#b-start');
await sleep(300);
ok('name is required', !!(await text(c, '#f-warn')).trim());

await type(c, '#f-name', 'Aarav Sharma');
await type(c, '#f-cls', '6 B');
await click(c, '#b-start');
await sleep(500);

/* ---- story ---- */
ok('story screen', !!(await evalIn(c, 'return !!document.getElementById("stage")')));
await assertOnScreen(c, 'story');
ok('questions locked before the end',
  await evalIn(c, 'return document.getElementById("b-quiz").disabled === true'));

/* jump to the end rather than sitting through 228 seconds, then play: the
   unlock happens in the run loop's end check, not on the seek itself */
const bar = await centreOf(c, '#bar', 0);
const barRight = await evalIn(c,
  'var r = document.getElementById("bar").getBoundingClientRect(); return Math.round(r.right - 3);');
await clickAt(c, barRight, bar.y);
await sleep(200);
await click(c, '#b-play');
/* poll rather than sleep a fixed time: with no narration.mp3 the story runs
   off a wall clock, so the last couple of seconds really do take seconds */
for (let i = 0; i < 60; i++) {
  if (await evalIn(c, 'return document.getElementById("b-quiz").disabled === false')) break;
  await sleep(200);
}
ok('questions unlock at the end',
  await evalIn(c, 'return document.getElementById("b-quiz").disabled === false'));
await click(c, '#b-quiz');
await sleep(400);

/* ---- part 1 intro + drag and drop ---- */
ok('part 1 intro', (await text(c, '.parttitle')).indexOf('Drag') >= 0);
await assertOnScreen(c, 'intro 1');
await click(c, '#b-begin');
await sleep(400);
await assertOnScreen(c, 'quiz part 1');

/* drag the first tray card into the first empty slot with real mouse input */
const card = await centreOf(c, '.cards .card', 0);
const slot = await centreOf(c, '.slot.drop', 0);
ok('a card and a drop slot are both visible', !!card && !!slot);
await mouse(c, 'mousePressed', card.x, card.y);
await mouse(c, 'mouseMoved', (card.x + slot.x) / 2, (card.y + slot.y) / 2);
await mouse(c, 'mouseMoved', slot.x, slot.y);
await mouse(c, 'mouseReleased', slot.x, slot.y);
await sleep(300);
ok('the card lands in the slot',
  await evalIn(c, 'return !!document.querySelector(".slot.drop.full")'));

/* ---- part 2: multiple choice ---- */
await evalIn(c, `
  var o = JSON.parse(localStorage.getItem(${JSON.stringify(KEY)}));
  o.screen = 'quiz'; o.part = 1; o.current = 0; o.watched = true;
  localStorage.setItem(${JSON.stringify(KEY)}, JSON.stringify(o)); location.reload();
`);
await sleep(500);
await assertOnScreen(c, 'quiz part 2');
const opt = await centreOf(c, '.opt', 1);
await clickAt(c, opt.x, opt.y);
await sleep(250);
ok('an option can be chosen',
  await evalIn(c, 'return !!document.querySelector(".opt.chosen")'));

/* ---- part 3: guessing game ---- */
await evalIn(c, `
  var o = JSON.parse(localStorage.getItem(${JSON.stringify(KEY)}));
  o.screen = 'quiz'; o.part = 2; o.current = 0;
  localStorage.setItem(${JSON.stringify(KEY)}, JSON.stringify(o)); location.reload();
`);
await sleep(500);
await assertOnScreen(c, 'quiz part 3');
ok('the blanks are drawn', await evalIn(c, 'return document.querySelectorAll(".blank").length > 0'));

/* ---- results ---- */
await evalIn(c, `
  var o = JSON.parse(localStorage.getItem(${JSON.stringify(KEY)}));
  o.screen = 'done';
  localStorage.setItem(${JSON.stringify(KEY)}, JSON.stringify(o)); location.reload();
`);
await sleep(600);
await assertOnScreen(c, 'results');
ok('the score is on screen without scrolling', await evalIn(c, `
  var b = document.querySelector('.scorebox').getBoundingClientRect();
  return b.top >= 0 && b.bottom <= window.innerHeight;
`));
ok('the answer review scrolls inside the panel, not the page', await evalIn(c, `
  var b = document.querySelector('.body');
  return b.scrollHeight > b.clientHeight &&
         document.documentElement.scrollHeight <= window.innerHeight + 1;
`));
ok('every review row is reachable by scrolling', await evalIn(c, `
  var b = document.querySelector('.body');
  b.scrollTop = b.scrollHeight;
  var rows = document.querySelectorAll('.rev');
  var last = rows[rows.length - 1].getBoundingClientRect();
  return rows.length > 0 && last.bottom <= window.innerHeight + 1;
`));

console.log('\n  ' + pass + ' passed, ' + fail + ' failed' +
  (bad.length ? '\n  failed: ' + bad.join(', ') : '') + '\n');
proc.kill();
process.exit(fail ? 1 : 0);
