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

/* The children have to be doing something other than bobbing. Checking the
   markup would only prove the classes are spelled right; the computed
   animation name proves a rule actually reached the element, which is where
   an SVG transform-origin or a gating selector usually goes wrong. */
const acting = await evalIn(c, `return (() => {
  const sv = document.querySelector('#stage .scene[data-scene="accuse"]');
  const live = sv.classList.contains('live');
  sv.classList.add('live');
  const run = sel => [...sv.querySelectorAll(sel)]
    .filter(el => getComputedStyle(el).animationName !== 'none').length;
  const out = {
    heads: run('.head'), arms: run('.armrd, .armld, .armru'),
    pointing: run('.jab'), mouths: run('.talk'), eyes: run('.lid'),
    /* the pivot has to land on the shoulder, not the middle of the arm */
    armOrigin: (() => {
      const a = sv.querySelector('.armrd');
      return a ? getComputedStyle(a).transformOrigin : null;
    })()
  };
  if (!live) sv.classList.remove('live');
  return out;
})()`);

ok(acting.heads > 0 && acting.arms > 0,
  acting.heads + ' heads turn on the neck and ' + acting.arms + ' arms hinge at the shoulder');
ok(acting.pointing === 1, 'the boy doing the accusing is the one whose arm jabs');
ok(acting.mouths > 0, acting.mouths + ' mouth is actually saying something');
ok(acting.eyes > 0, acting.eyes + ' pairs of eyes blink');
ok(/px 0px$|px 0px /.test(acting.armOrigin) || /0px$/.test(acting.armOrigin),
  'and an arm swings from its top corner, not its middle (' + acting.armOrigin + ')');

/* ------------------------------------------------ 3. every label is in shot
   The camera now cuts between framings inside a scene, so a label being out
   of frame is normal - the wide shot's title has no business being visible
   during a close-up of a latch. What is NOT allowed is a label being out of
   frame during the shot it was written for, which is a thing you cannot see
   in a still and will not notice while watching unless you already know it
   is missing. So: drive each scene to both ends of each of its shots, and
   measure the text that belongs to that shot against the stage. */
console.log('\n  every label is inside the shot it belongs to');

const framing = await evalIn(c, `return (() => {
  const stage = document.getElementById('stage');
  const sb = stage.getBoundingClientRect();
  const bad = [];
  let checked = 0;
  window.STORY.timing(0).forEach(sc => {
    const sv = document.querySelector('#stage .scene[data-scene="' + sc.scene + '"]');
    const live = sv.classList.contains('live');
    sv.classList.add('live');
    sv.style.animationPlayState = 'paused';

    const beatOf = el => {
      for (let n = el; n && n !== sv; n = n.parentElement) {
        const c = [...(n.classList || [])].find(x => /^b\\d+(x\\d)?$/.test(x));
        if (c) return parseInt(c.slice(1), 10);
      }
      return 0;                       /* no beat class means the opening shot */
    };
    const texts = [...sv.querySelectorAll('text')];

    sc.beats.forEach((b, j) => {
      const till = (j + 1 < sc.beats.length) ? sc.beats[j + 1] : sc.hold;
      const mine = texts.filter(el => beatOf(el) === j);
      [['start', b + 0.05], ['end', till - 0.05]].forEach(([when, at]) => {
        sv.style.animationDelay = '-' + at.toFixed(3) + 's';
        sv.getBoundingClientRect();
        mine.forEach(el => {
          const r = el.getBoundingClientRect();
          if (!r.width) return;
          checked++;
          const out = Math.max(sb.left - r.left, r.right - sb.right,
                               sb.top - r.top, r.bottom - sb.bottom);
          if (out > 3) bad.push(sc.scene + ' shot ' + j + ' "' +
            el.textContent.slice(0, 22) + '" out of frame at the ' + when +
            ' by ' + Math.round(out) + 'px');
        });
      });
    });

    sv.style.animationDelay = '';
    sv.style.animationPlayState = '';
    if (!live) sv.classList.remove('live');
  });
  return { bad, checked };
})()`);

ok(framing.checked > 60, framing.checked + ' label positions measured across the shot list');
ok(framing.bad.length === 0, 'every label is in frame for its own shot' +
  (framing.bad.length ? ':\n        ' + framing.bad.join('\n        ') : ''));

/* and the shots must actually be different from one another, or this is all
   an expensive way of doing nothing */
const cuts = await evalIn(c, `return (() => {
  const t = window.STORY.timing(0);
  let shots = 0, moved = 0;
  t.forEach(sc => {
    const list = window.STORY.shots[sc.scene] || [];
    shots += Math.min(list.length, sc.beats.length);
    for (let j = 1; j < Math.min(list.length, sc.beats.length); j++) {
      const a = window.STORY.frame(list[j-1].z, list[j-1].x, list[j-1].y);
      const b = window.STORY.frame(list[j].z, list[j].x, list[j].y);
      if (a !== b) moved++;
    }
  });
  return { shots, moved };
})()`);
ok(cuts.shots >= 40, 'the nineteen scenes are cut into ' + cuts.shots + ' shots');
ok(cuts.moved === cuts.shots - 19, 'and every cut lands the camera somewhere new');

/* ---------------------------------------------------- 4. a picture of each shot
   Not each scene - each shot. A wide drawing can be perfectly composed and
   still fall apart in the close-up the camera actually cuts to, and the
   close-up is what a child sees. */
console.log('\n  rendering every shot');

/* Stop the story first. Rendering while it plays leaves the caption band and
   the progress bar wandering through the shots, so every frame looks like it
   belongs to a different moment than it does. */
await evalIn(c, `(() => {
  const b = document.getElementById('b-play');
  if (b.textContent === 'Pause') b.click();
})()`);
await sleep(300);

/* freeze the animation but keep the camera, which is set per shot below */
await evalIn(c, `(() => {
  const st = document.createElement('style');
  st.id = 'freeze';
  /* transform:none may only ever go on the <svg> itself. Putting it on the
     children overrides their transform ATTRIBUTES and collapses the whole
     drawing into the top-left corner - the trap named at the top of
     scenes.js, which this test walked straight into the first time. */
  /* index.html has .stage svg{display:block}, which is MORE specific than a
     bare .scene - so hiding the other scenes needs !important or the paused
     live scene simply paints over the shot we asked for */
  st.textContent = '.scene{animation:none!important;transition:none!important;' +
    'display:none!important;opacity:0!important}' +
    '.scene.shot{display:block!important;opacity:1!important}' +
    '.scene *{animation:none!important}' +
    '.mote{opacity:.6!important}';
  document.head.appendChild(st);
})()`);

const shotList = await evalIn(c, `return window.STORY.timing(0).map(sc => ({
  scene: sc.scene, lines: sc.beats.length,
  shots: (window.STORY.shots[sc.scene] || []).length
}))`);

let n = 0;
for (const sc of shotList) {
  for (let j = 0; j < Math.min(sc.lines, sc.shots); j++) {
    await evalIn(c, `(() => {
      const want = ${JSON.stringify(sc.scene)};
      document.querySelectorAll('#stage .scene').forEach(sv => {
        const on = sv.getAttribute('data-scene') === want;
        sv.classList.toggle('shot', on);
        if (!on) return;
        /* Only what has been revealed by this line. Without this the sheet
           shows every label at once, including ones that belong to a later
           shot, and half of them read as bugs when they are simply not on
           screen yet. */
        sv.querySelectorAll('*').forEach(el => {
          /* Double the backslash: this regex is inside a JS template literal,
             where an unrecognised escape quietly loses it - \d arrives in the
             browser as plain d, and the pattern stops matching anything at
             all, with no error. */
          const cls = [...(el.classList || [])].find(x => /^b\\d+(x\\d)?$/.test(x));
          if (cls) el.style.visibility = parseInt(cls.slice(1), 10) <= ${j} ? '' : 'hidden';
        });
        const sh = window.STORY.shots[want][${j}];
        const to = sh.to || {};
        /* the framing halfway through the shot, which is what it mostly looks like */
        sv.style.transform = window.STORY.frame(
          (sh.z + (to.z || sh.z * 1.05)) / 2,
          (sh.x + (to.x || sh.x)) / 2,
          (sh.y + (to.y || sh.y)) / 2);
      });
    })()`);
    /* put that shot's own caption up, so the frame explains itself */
    await evalIn(c, `(() => {
      const t = window.STORY.timing(0).find(x => x.scene === ${JSON.stringify(sc.scene)});
      const cue = window.STORY.track(0).filter(q => q.scene === ${JSON.stringify(sc.scene)})[${j}];
      if (cue) document.getElementById('cap').textContent = cue.text;
    })()`);
    await sleep(110);
    const res = await Promise.race([
      c.send('Page.captureScreenshot', { format: 'png' }),
      sleep(8000).then(() => null)        /* captureScreenshot can hang forever */
    ]);
    n++;
    if (!res) { console.log('   (screenshot timed out) ' + sc.scene + ' ' + j); continue; }
    const name = String(n).padStart(2, '0') + '-' + sc.scene + '-shot' + j;
    writeFileSync(join(OUT, name + '.png'), Buffer.from(res.data, 'base64'));
  }
}
console.log('   ' + n + ' shots written to ' + OUT);

await evalIn(c, `document.querySelectorAll('#stage .scene').forEach(sv => {
  sv.style.transform = '';
  sv.querySelectorAll('*').forEach(el => { el.style.visibility = ''; });
})`);

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
