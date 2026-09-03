/* Checks the story picture, which is the half of this app no unit test can
   see. Two things it does that nothing else does:

     1. Screenshots all nineteen scenes with every animation switched off and
        every reveal forced on, so a label sitting on top of a face, or under
        the caption band, shows up as a picture instead of as nothing.
     2. Reads back the computed animation-delay of every beat element in the
        art. A beat class that no caption line backs - b3 in a scene with
        three lines, say - silently falls through to zero and the label pops
        up at the wrong moment. Only the computed value catches that.

     node tests/story.mjs [url] [outdir]                                    */
import { launch, attach, evalIn, click, type, sleep } from './cdp.mjs';
import { writeFileSync, mkdirSync } from 'node:fs';
import { join } from 'node:path';

const URL = process.argv[2] || 'http://127.0.0.1:8899/index.html';
const OUT = process.argv[3] || './shots-story';
mkdirSync(OUT, { recursive: true });

let pass = 0, fail = 0;
const ok = (c, m) => { c ? pass++ : fail++; console.log('   ' + (c ? 'ok  ' : 'FAIL') + '  ' + m); };
/* the caption is spans on screen; this is what it has to read back as */
const window0 = t => t.replace(/\s+/g, ' ').trim();

const { proc, port } = await launch(9227);
const c = await attach(port);
await c.send('Page.enable');
await c.send('Emulation.setDeviceMetricsOverride',
  { width: 1366, height: 768, deviceScaleFactor: 1, mobile: false });
await c.send('Page.navigate', { url: URL });
await sleep(1200);
await evalIn(c, 'localStorage.clear(); location.reload();');
await sleep(900);
await type(c, '#f-name', 'Aarav Sharma');
await click(c, '#b-start');
await sleep(700);

/* ------------------------------------------------------------ 1. the beats */
console.log('\n  beats land on the sentence that says them');

const beats = await evalIn(c, `return (() => {
  const t = window.STORY.timing(0);
  const hold = {}, lines = {};
  t.forEach(s => { hold[s.scene] = s.hold; lines[s.scene] = s.beats.length; });
  const out = [];
  document.querySelectorAll('#stage .scene').forEach(sv => {
    const scene = sv.getAttribute('data-scene');
    const was = sv.classList.contains('live');
    sv.classList.add('live');                       /* delays only apply live */
    sv.querySelectorAll('[class*="b"]').forEach(el => {
      const cls = [...el.classList].find(x => /^b\\d+(x\\d)?$/.test(x));
      if (!cls) return;
      out.push({
        scene, cls,
        delay: parseFloat(getComputedStyle(el).animationDelay) || 0,
        hold: hold[scene], lines: lines[scene],
        index: parseInt(cls.slice(1), 10)
      });
    });
    if (!was) sv.classList.remove('live');
  });
  return out;
})()`);

ok(beats.length > 40, beats.length + ' beat elements found in the artwork');

const orphans = beats.filter(b => b.index >= b.lines);
ok(orphans.length === 0, 'every beat class has a caption line behind it' +
  (orphans.length ? ' — ' + orphans.map(o => o.scene + '.' + o.cls).join(', ') : ''));

const late = beats.filter(b => b.delay > b.hold - 0.4);
ok(late.length === 0, 'no reveal is scheduled after its scene has left' +
  (late.length ? ' — ' + late.map(o => o.scene + '.' + o.cls + ' @' + o.delay.toFixed(1) +
    's of ' + o.hold.toFixed(1) + 's').join(', ') : ''));

const zeroed = beats.filter(b => b.index > 0 && b.delay === 0);
ok(zeroed.length === 0, 'no later beat collapsed to zero' +
  (zeroed.length ? ' — ' + zeroed.map(o => o.scene + '.' + o.cls).join(', ') : ''));

/* every scene must have a camera move, and it must last exactly its hold */
const cam = await evalIn(c, `return [...document.querySelectorAll('#stage .scene')].map(sv => ({
  scene: sv.getAttribute('data-scene'),
  cam: sv.style.getPropertyValue('--cam').trim(),
  hold: parseFloat(sv.style.getPropertyValue('--hold'))
}))`);
ok(cam.every(s => s.cam && s.hold > 1), 'every scene carries a camera move and a hold');
ok(new Set(cam.map(s => s.cam)).size >= 5,
  'the camera does not do the same thing every time (' +
  new Set(cam.map(s => s.cam)).size + ' different moves)');

/* ------------------------------------------------------- 2. it actually moves
   A still of a frozen scene cannot tell a camera move from a static frame, so
   this half presses Play for real and reads the live computed style back. */
console.log('\n  the picture moves, and stops when the story stops');

await click(c, '#b-play');
await sleep(700);

const playing = await evalIn(c, `return (() => {
  const sv = document.querySelector('#stage .scene.live');
  const cs = getComputedStyle(sv);
  const cap = document.getElementById('cap');
  return {
    stage: document.getElementById('stage').className,
    scene: sv.getAttribute('data-scene'),
    name: cs.animationName,
    state: cs.animationPlayState,
    transform: cs.transform,
    words: cap.querySelectorAll('.w').length,
    text: cap.textContent,
    inScript: window.STORY.lines.some(l => l[1] === cap.textContent)
  };
})()`);

ok(/started/.test(playing.stage) && /playing/.test(playing.stage),
  'the stage knows it is playing');
ok(playing.name.indexOf('cam') === 0, 'the opening scene is running a camera move (' +
  playing.name + ')');
ok(playing.transform !== 'none' && playing.transform !== 'matrix(1, 0, 0, 1, 0, 0)',
  'and the camera has actually moved the frame');
ok(playing.words > 3, 'the caption came in as ' + playing.words + ' separate words');
ok(playing.inScript, 'and still reads back as exactly the sentence in the script');

/* drag the bar into the middle of a long scene: the reveal that belongs to
   the line already spoken must be shown, not queued up to play again */
const seeked = await evalIn(c, `return (() => {
  const bar = document.getElementById('bar');
  const r = bar.getBoundingClientRect();
  bar.onclick.call(bar, { clientX: r.left + r.width * 0.30 });   /* ~68s, mid list */
  const sv = document.querySelector('#stage .scene.live');
  const first = sv.querySelector('.b1');
  return {
    scene: sv.getAttribute('data-scene'),
    tin: sv.style.getPropertyValue('--tin'),
    firstDelay: first ? getComputedStyle(first).animationDelay : null
  };
})()`);
await sleep(300);
const shown = await evalIn(c, `return (() => {
  const sv = document.querySelector('#stage .scene.live');
  const el = sv.querySelector('.b1');
  return el ? +getComputedStyle(el).opacity : null;
})()`);

ok(parseFloat(seeked.tin) < 0, 'dragging the bar drops us into the middle of ' +
  seeked.scene + ' (' + seeked.tin + ')');
ok(parseFloat(seeked.firstDelay) < 0,
  'so a reveal already spoken for is pulled back into the past (' + seeked.firstDelay + ')');
ok(shown === 1, 'and is on screen straight away rather than popping in again');

await click(c, '#b-play');                                          /* pause */
await sleep(400);
const paused = await evalIn(c, `return (() => {
  const sv = document.querySelector('#stage .scene.live');
  /* not one named child - every animating thing in the scene, because which
     children animate differs from scene to scene */
  let running = 0, animated = 0;
  sv.querySelectorAll('*').forEach(el => {
    const cs = getComputedStyle(el);
    if (cs.animationName === 'none') return;
    animated++;
    if (cs.animationPlayState === 'running') running++;
  });
  return {
    stage: document.getElementById('stage').className,
    scene: getComputedStyle(sv).animationPlayState,
    animated, running
  };
})()`);
ok(!/playing/.test(paused.stage), 'pressing pause takes the playing flag off the stage');
ok(paused.scene === 'paused', 'the camera holds still while the story is paused');
ok(paused.animated > 0 && paused.running === 0,
  'and so does all ' + paused.animated + ' of the animating parts inside it');

await click(c, '#b-play');    /* leave it running for the shots below */
await sleep(300);

/* --------------------------------------------------- 3. nothing gets cropped
   A camera that pushes in crops the frame, so a label that was comfortably
   inside the picture at the start of a scene can be outside it by the end.
   This walks every scene to both ends of its own move and measures every
   piece of text against the edge of the stage - which is the only way to
   find it, because a still of the first frame always looks fine. */
console.log('\n  the camera never cuts a word in half');

const clipped = await evalIn(c, `return (() => {
  const stage = document.getElementById('stage');
  const sb = stage.getBoundingClientRect();
  const bad = [];
  document.querySelectorAll('#stage .scene').forEach(sv => {
    const hold = parseFloat(sv.style.getPropertyValue('--hold')) || 10;
    const live = sv.classList.contains('live');
    sv.classList.add('live');
    sv.style.animationPlayState = 'paused';
    [['start', 0.001], ['end', hold - 0.001]].forEach(([when, t]) => {
      sv.style.animationDelay = '-' + t.toFixed(3) + 's';
      sv.getBoundingClientRect();                       /* settle the transform */
      sv.querySelectorAll('text').forEach(el => {
        const r = el.getBoundingClientRect();
        if (!r.width) return;
        const out = Math.max(sb.left - r.left, r.right - sb.right,
                             sb.top - r.top, r.bottom - sb.bottom);
        if (out > 2) bad.push(sv.getAttribute('data-scene') + ' "' +
          el.textContent.slice(0, 22) + '" cut at the ' + when + ' by ' +
          Math.round(out) + 'px');
      });
    });
    sv.style.animationDelay = '';
    sv.style.animationPlayState = '';
    if (!live) sv.classList.remove('live');
  });
  return bad;
})()`);

ok(clipped.length === 0, 'every word stays inside the frame for the whole move' +
  (clipped.length ? ':\n        ' + clipped.join('\n        ') : ''));

/* ------------------------------------------------- 2. a picture of each scene */
console.log('\n  rendering every scene');

/* freeze everything and force every reveal on, so a shot is the finished
   composition rather than whatever frame the animation happened to be at */
await evalIn(c, `(() => {
  const st = document.createElement('style');
  st.id = 'freeze';
  /* transform:none may only ever go on the <svg> itself. Putting it on the
     children overrides their transform ATTRIBUTES and collapses the whole
     drawing into the top-left corner - the trap named at the top of
     scenes.js, which this test walked straight into the first time. */
  st.textContent = '.scene{animation:none!important;transform:none!important;' +
    'transition:none!important;display:none}' +
    '.scene.shot{display:block;opacity:1}' +
    '.scene *{animation:none!important}' +
    '.mote{opacity:.6!important}';
  document.head.appendChild(st);
})()`);

const names = cam.map(s => s.scene);
for (let i = 0; i < names.length; i++) {
  await evalIn(c, `document.querySelectorAll('#stage .scene').forEach(s =>
    s.classList.toggle('shot', s.getAttribute('data-scene') === ${JSON.stringify(names[i])}))`);
  await sleep(120);
  const res = await Promise.race([
    c.send('Page.captureScreenshot', { format: 'png' }),
    sleep(8000).then(() => null)          /* captureScreenshot can hang forever */
  ]);
  if (!res) { console.log('   (screenshot timed out) ' + names[i]); continue; }
  const n = String(i + 1).padStart(2, '0') + '-' + names[i];
  writeFileSync(join(OUT, n + '.png'), Buffer.from(res.data, 'base64'));
  console.log('   ' + n);
}

/* nothing readable may sit under the caption band (rule 2 in scenes.js) */
const low = await evalIn(c, `return (() => {
  const bad = [];
  document.querySelectorAll('#stage .scene').forEach(sv => {
    sv.querySelectorAll('text').forEach(t => {
      const y = parseFloat(t.getAttribute('y'));
      if (y > 560) bad.push(sv.getAttribute('data-scene') + ' "' +
        t.textContent.slice(0, 24) + '" y=' + y);
    });
  });
  return bad;
})()`);
console.log('');
ok(low.length === 0, 'no text hides under the caption band' +
  (low.length ? ' — ' + low.join(' | ') : ''));

console.log('\n  ' + pass + ' passed, ' + fail + ' failed\n');
proc.kill();
process.exit(fail ? 1 : 0);
