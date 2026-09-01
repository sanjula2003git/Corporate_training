/* Measures whether each screen fits the viewport without page scrolling.
   Runs every screen at three real classroom sizes.

     node tests/fit.mjs [url]

   A screen "fits" when documentElement.scrollHeight <= innerHeight, i.e. the
   page itself has nothing to scroll. Scrolling inside a region that was built
   to scroll (the results review list) is allowed, and reported separately. */
import { launch, attach, evalIn, click, type, sleep } from './cdp.mjs';

const URL = process.argv[2] || 'http://127.0.0.1:8899/index.html';
const KEY = 'thursday-thief-class6-v1';

/* the three shapes that matter: a projector, a normal laptop, a monitor */
const SIZES = [
  { w: 1366, h: 768, name: '1366x768   laptop' },
  { w: 1280, h: 720, name: '1280x720   projector' },
  { w: 1920, h: 1080, name: '1920x1080  monitor' }
];

async function setSize(c, w, h) {
  await c.send('Emulation.setDeviceMetricsOverride',
    { width: w, height: h, deviceScaleFactor: 1, mobile: false });
}

/* patch the app's own saved state, so the answers array is always the right
   length for restore() to accept it */
async function goTo(c, screen, part) {
  await evalIn(c, `(() => {
    const o = JSON.parse(localStorage.getItem(${JSON.stringify(KEY)}));
    o.screen = ${JSON.stringify(screen)};
    o.part = ${part || 0};
    o.current = 0;
    o.watched = true;
    localStorage.setItem(${JSON.stringify(KEY)}, JSON.stringify(o));
  })()`);
  await evalIn(c, 'location.reload()');
  await sleep(400);
}

async function measure(c, label, out) {
  const m = await evalIn(c, `return (() => {
    const d = document.documentElement;
    const p = document.querySelector('.panel');
    const scrollers = [...document.querySelectorAll('.panel *')].filter(
      el => el.scrollHeight > el.clientHeight + 2 &&
            /auto|scroll/.test(getComputedStyle(el).overflowY));
    return {
      page: d.scrollHeight, view: window.innerHeight,
      panel: p ? Math.round(p.getBoundingClientRect().height) : 0,
      inner: scrollers.map(el => (el.className.split(' ')[0] || el.tagName) +
        ' +' + (el.scrollHeight - el.clientHeight))
    };
  })()`);
  const over = m.page - m.view;
  const fits = over <= 1;
  out.push(fits);
  console.log('    ' + label.padEnd(20) +
    (fits ? 'fits' : 'SCROLLS ' + over + 'px').padEnd(17) +
    'page ' + String(m.page).padStart(5) + '  view ' + m.view +
    '  panel ' + String(m.panel).padStart(5) +
    (m.inner.length ? '   [scrolls inside: ' + m.inner.join(', ') + ']' : ''));
  return fits;
}

const run = async () => {
  const { proc } = await launch(9223);
  const c = await attach(9223);
  const results = [];

  for (const s of SIZES) {
    console.log('\n  ' + s.name);
    await setSize(c, s.w, s.h);

    /* navigate first - localStorage is not readable on about:blank */
    await evalIn(c, `location.href = ${JSON.stringify(URL)}`);
    await sleep(600);
    await evalIn(c, `localStorage.removeItem(${JSON.stringify(KEY)}); location.reload()`);
    await sleep(600);
    await measure(c, 'welcome', results);

    /* the story screen is reached by actually starting: restore() deliberately
       sends a saved 'story' back to 'welcome' */
    await type(c, '#f-name', 'Aarav Sharma');
    await click(c, '#b-start');
    await sleep(500);
    await measure(c, 'story', results);

    for (let p = 0; p < 3; p++) {
      await goTo(c, 'intro', p);
      await measure(c, 'intro part ' + (p + 1), results);
      await goTo(c, 'quiz', p);
      await measure(c, 'quiz part ' + (p + 1), results);
    }

    await goTo(c, 'done', 2);
    await measure(c, 'results', results);
  }

  const bad = results.filter(r => !r).length;
  console.log('\n  ' + (bad ? bad + ' of ' + results.length + ' screens still scroll'
    : 'every screen fits (' + results.length + ' checks)') + '\n');
  proc.kill();
  process.exit(bad ? 1 : 0);
};

run().catch(e => { console.error(e); process.exit(2); });
