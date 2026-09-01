/* Screenshots every screen at a given viewport, and checks that the story
   stage is still a true 16:9 box (a squashed stage means the SVG art is being
   cropped by preserveAspectRatio="slice").

     node tests/shots.mjs [url] [outdir] [w] [h]                            */
import { launch, attach, evalIn, click, type, sleep } from './cdp.mjs';
import { writeFileSync, mkdirSync } from 'node:fs';
import { join } from 'node:path';

const URL = process.argv[2] || 'http://127.0.0.1:8899/index.html';
const OUT = process.argv[3] || './shots';
const W = Number(process.argv[4] || 1366);
const H = Number(process.argv[5] || 768);
const KEY = 'thursday-thief-class6-v1';
mkdirSync(OUT, { recursive: true });

const { proc, port } = await launch(9224);
const c = await attach(port);
await c.send('Page.enable');
await c.send('Emulation.setDeviceMetricsOverride',
  { width: W, height: H, deviceScaleFactor: 1, mobile: false });

async function shot(name) {
  const res = await c.send('Page.captureScreenshot', { format: 'png' });
  writeFileSync(join(OUT, name + '.png'), Buffer.from(res.data, 'base64'));
  console.log('  ' + name);
}

async function goTo(screen, part) {
  await evalIn(c, `
    var o = JSON.parse(localStorage.getItem(${JSON.stringify(KEY)}));
    o.screen = ${JSON.stringify(screen)}; o.part = ${part || 0};
    o.current = 0; o.watched = true;
    localStorage.setItem(${JSON.stringify(KEY)}, JSON.stringify(o));
    location.reload();
  `);
  await sleep(500);
}

await c.send('Page.navigate', { url: URL });
await sleep(1200);
await evalIn(c, `localStorage.clear(); location.reload();`);
await sleep(900);

console.log('\n  ' + W + 'x' + H);
await shot('01-welcome');

await type(c, '#f-name', 'Aarav Sharma');
await click(c, '#b-start');
await sleep(600);
await shot('02-story');

/* the stage must stay 16:9, or the artwork gets sliced */
const st = await evalIn(c, `
  var b = document.getElementById('stage').getBoundingClientRect();
  var p = document.querySelector('.panel').getBoundingClientRect();
  return { w: Math.round(b.width), h: Math.round(b.height),
           ratio: +(b.width / b.height).toFixed(3),
           bottom: Math.round(b.bottom), panelBottom: Math.round(p.bottom) };
`);
const ratioOk = Math.abs(st.ratio - 16 / 9) < 0.02;
console.log('\n  stage ' + st.w + 'x' + st.h + '  ratio ' + st.ratio +
  (ratioOk ? '  (16:9 held)' : '  <- NOT 16:9, art will be cropped'));

for (let p = 0; p < 3; p++) {
  await goTo('intro', p);
  await shot('0' + (3 + p * 2) + '-intro-part' + (p + 1));
  await goTo('quiz', p);
  await shot('0' + (4 + p * 2) + '-quiz-part' + (p + 1));
}
await goTo('done', 2);
await shot('09-results');

proc.kill();
process.exit(ratioOk ? 0 : 1);
