/* Screenshot every screen and every scene.  node shots.mjs <url> <outdir> */
import { launch, attach, evalIn, click, type, sleep } from './cdp.mjs';
import { writeFileSync, mkdirSync } from 'node:fs';
import { join } from 'node:path';

const URL = process.argv[2] || 'http://127.0.0.1:8899/index.html';
const OUT = process.argv[3] || './shots';
mkdirSync(OUT, { recursive: true });

const { proc, port } = await launch(9223);
const c = await attach(port);
await c.ready;
await c.send('Page.enable');
await c.send('Emulation.setDeviceMetricsOverride',
  { width: 1400, height: 1000, deviceScaleFactor: 1, mobile: false });

async function shot(name, sel) {
  let clip;
  if (sel) {
    const r = await evalIn(c, `
      var n = document.querySelector(${JSON.stringify(sel)});
      if (!n) return null;
      n.scrollIntoView({block:'center'});
      var b = n.getBoundingClientRect();
      return {x:b.left+window.scrollX, y:b.top+window.scrollY, width:b.width, height:b.height};
    `);
    if (r) clip = { ...r, scale: 1 };
  }
  const res = await c.send('Page.captureScreenshot',
    clip ? { format: 'png', clip, captureBeyondViewport: true } : { format: 'png' });
  writeFileSync(join(OUT, name + '.png'), Buffer.from(res.data, 'base64'));
  console.log('  ' + name);
}

await c.send('Page.navigate', { url: URL });
await sleep(1400);
await evalIn(c, `localStorage.clear(); return 1;`);
await c.send('Page.reload');
await sleep(1200);

await shot('01-welcome');

await type(c, '#nm', 'Aarti Menon 6B');
await click(c, '#start');
await sleep(600);
await click(c, '#pp');           // pause it - we step by hand
await sleep(200);

/* every scene, clipped to the stage */
const n = await evalIn(c, `return window.STORY.scenes.length;`);
for (let i = 0; i < n; i++) {
  await evalIn(c, `
    var ns = document.querySelectorAll('.scene');
    for (var k=0;k<ns.length;k++) ns[k].classList.toggle('live', k === ${i});
    document.getElementById('cap').textContent = window.STORY.scenes[${i}].line;
    return 1;
  `);
  await sleep(2900);  // every pop and fly delay must have played out first
  await shot('scene-' + String(i + 1).padStart(2, '0'), '#stage');
}

/* the rounds */
await evalIn(c, `window.__leaf.state().watched = true; window.__leaf.go('r1intro'); return 1;`);
await sleep(400); await shot('02-round1-intro');

await evalIn(c, `window.__leaf.go('r1', 0); return 1;`);
await sleep(400); await shot('03-round1-question');

/* the same question with the hint showing */
await click(c, '#hint');
await sleep(400); await shot('04-round1-hint');

await evalIn(c, `window.__leaf.go('r2intro'); return 1;`);
await sleep(400); await shot('05-round2-intro');

for (const i of [0, 3, 5]) {
  await evalIn(c, `window.__leaf.go('r2', ${i}); return 1;`);
  await sleep(400);
  await shot('06-round2-word-' + (i + 1));
}

await evalIn(c, `window.__leaf.go('r3intro'); return 1;`);
await sleep(400); await shot('07-round3-intro');
await evalIn(c, `window.__leaf.go('r3', 0); return 1;`);
await sleep(400); await shot('08-round3-question');

/* every picture at a readable size, on one sheet - the only way to be sure a
   yak reads as a yak and not as a dog */
await evalIn(c, `
  var P = window.PICTURES.pics, keys = Object.keys(P).sort(), out = '';
  keys.forEach(function(k){
    out += '<div style="display:inline-block;width:180px;margin:10px;text-align:center">' +
      '<div style="width:160px;height:160px;background:#fff;border:4px solid #12142a;' +
      'border-radius:14px;padding:10px;margin:0 auto">' + P[k].svg + '</div>' +
      '<div style="font:bold 17px Trebuchet MS;margin-top:6px;color:#12142a">' +
      P[k].name + '</div></div>';
  });
  document.body.innerHTML = '<div id="sheet" style="background:#fdf7ea;padding:20px;' +
    'width:1360px">' + out + '</div>';
  return keys.length;
`);
await sleep(400);
await shot('09-all-pictures', '#sheet');

console.log('done');
c.close(); proc.kill(); process.exit(0);
