/* A whole student run through "The Leaf Machine", driven with real mouse
   input over CDP.  node e2e.mjs <url>                                     */
import { launch, attach, evalIn, click, clickAt, mouse, type, text, sleep } from './cdp.mjs';

const URL = process.argv[2] || 'http://127.0.0.1:8899/index.html';
let pass = 0, fail = 0;
const bad = [];

function ok(name, cond, extra) {
  if (cond) { pass++; console.log('  ok   ' + name); }
  else { fail++; bad.push(name + (extra ? '  <- ' + extra : '')); console.log('  FAIL ' + name + (extra ? '  <- ' + extra : '')); }
}

const { proc, port } = await launch(9222);
const c = await attach(port);
await c.ready;
await c.send('Runtime.enable');
await c.send('Page.enable');

const errors = [];
c.on(m => {
  if (m.method === 'Runtime.exceptionThrown') {
    errors.push(m.params.exceptionDetails?.exception?.description ||
      m.params.exceptionDetails?.text || 'unknown');
  }
});

await c.send('Page.navigate', { url: URL });
await sleep(1400);

/* ==================================================================
   A. content checks - these do not touch the UI at all
   ================================================================== */
console.log('\nA. content');

const content = await evalIn(c, `
  var out = {};
  var W = window.PICTURES.words, P = window.PICTURES.pics;
  var L = window.__leaf;

  // every picture's first letter must build its word
  out.spell = W.map(function(w){
    var got = w.pics.map(function(k){ return P[k] ? P[k].name.charAt(0) : '?'; }).join('');
    return {word: w.word, got: got, ok: got === w.word};
  });

  // every referenced picture exists
  out.missing = [];
  W.forEach(function(w){ w.pics.forEach(function(k){ if(!P[k]) out.missing.push(k); }); });

  // the narration must never use the words that are the answers
  var banned = ['data','input','output','pattern','model','training','prediction',
                'domain','feedback','vision','automation','password','artificial',
                'intelligence','algorithm'];
  out.leaks = [];
  window.STORY.scenes.forEach(function(s, i){
    var t = ' ' + s.line.toLowerCase().replace(/[^a-z]+/g,' ') + ' ';
    banned.forEach(function(b){
      if (t.indexOf(' '+b+' ') >= 0) out.leaks.push('scene '+(i+1)+': '+b);
    });
  });

  // no two scenes may share a caption
  var seen = {}; out.dupes = [];
  window.STORY.scenes.forEach(function(s,i){
    if (seen[s.line]) out.dupes.push(i+1); seen[s.line] = 1;
  });

  // every icon is 8 rows of 8, and every round 1 answer names a real icon
  out.iconShape = [];
  Object.keys(window.STORY.icons).forEach(function(k){
    var p = window.STORY.icons[k];
    if (p.length !== 8 || p.some(function(r){ return r.length !== 8; })) out.iconShape.push(k);
  });
  out.badIcon = L.R1.filter(function(q){ return !window.STORY.icons[q.icon]; }).map(function(q){return q.id;});

  // round 2 must not hand over a round 3 answer
  out.collide = [];
  W.forEach(function(w){
    L.R3.forEach(function(q, i){
      q.accept.forEach(function(a){
        if (a.toUpperCase() === w.word) out.collide.push(w.word + ' = answer to q' + (i+1));
      });
    });
  });

  // the accept lists must actually accept their own answers
  out.selfAccept = [];
  L.R3.forEach(function(q,i){
    q.accept.forEach(function(a){
      if (!L.answered(a, q.accept)) out.selfAccept.push('q'+(i+1)+' "'+a+'"');
    });
  });

  // and must NOT accept an obviously wrong one
  out.falsePos = [];
  L.R3.forEach(function(q,i){
    if (L.answered('i do not know', q.accept)) out.falsePos.push('q'+(i+1));
  });
  // the classic near miss: "date" must not pass for "data"
  out.dateForData = L.answered('date', L.R3[0].accept);

  out.marks = {r1: L.R1.length*3, r2: W.length*2, r3: L.R3.length*2};
  return out;
`);

content.spell.forEach(s => ok('pictures spell ' + s.word, s.ok, 'got ' + s.got));
ok('every picture referenced exists', content.missing.length === 0, content.missing.join(','));
ok('narration leaks no answer word', content.leaks.length === 0, content.leaks.join('; '));
ok('no two scenes share a caption', content.dupes.length === 0, content.dupes.join(','));
ok('every icon is 8x8', content.iconShape.length === 0, content.iconShape.join(','));
ok('every round 1 answer names a real icon', content.badIcon.length === 0, content.badIcon.join(','));
ok('round 2 words are not round 3 answers', content.collide.length === 0, content.collide.join('; '));
ok('accept lists accept themselves', content.selfAccept.length === 0, content.selfAccept.join('; '));
ok('accept lists reject "i do not know"', content.falsePos.length === 0, content.falsePos.join(','));
ok('"date" is not accepted for "data"', content.dateForData === false);
ok('marks add to 40', content.marks.r1 + content.marks.r2 + content.marks.r3 === 40,
  JSON.stringify(content.marks));

/* ==================================================================
   B. the journey
   ================================================================== */
console.log('\nB. welcome and story');

await evalIn(c, `localStorage.clear(); return 1;`);
await c.send('Page.reload');
await sleep(1000);

await type(c, '#nm', 'Test Student 6B');
await click(c, '#start');
await sleep(500);

ok('story screen opened', await evalIn(c, `return !!document.getElementById('stage');`));
ok('exactly one scene is live at a time',
  await evalIn(c, `return document.querySelectorAll('.scene.live').length === 1;`));

// turn the voice off and make the scenes fly past, so the test is not a
// three minute wait
await evalIn(c, `window.STORY.scenes.forEach(function(s){ s.dur = 45; }); return 1;`);
await click(c, '#vox');
ok('continue is locked before the story ends',
  await evalIn(c, `return document.getElementById('next').disabled === true;`));

await sleep(2600);
ok('story reached the end', await evalIn(c, `return window.__leaf.state().watched === true;`));
ok('continue unlocked after watching',
  await evalIn(c, `return document.getElementById('next').disabled === false;`));
ok('last scene is the live one',
  await evalIn(c, `
    var n = document.querySelectorAll('.scene');
    return n[n.length-1].classList.contains('live');`));

await click(c, '#next');
await sleep(350);
await click(c, '#fw');           // round 1 intro -> start
await sleep(350);

/* ---------------------------------------------------------- round 1 */
console.log('\nC. round 1 - drawing on the dots');

async function cellBoxes() {
  await evalIn(c, `document.getElementById('grid').scrollIntoView({block:'center'}); return 1;`);
  await sleep(120);
  return evalIn(c, `
    return Array.prototype.map.call(
      document.querySelectorAll('#grid .pxcell'),
      function(n){ var r = n.getBoundingClientRect();
        return {x: r.left + r.width/2, y: r.top + r.height/2}; });
  `);
}

/* paint a whole row run with ONE press-drag-release, which is the path that
   a child on a tablet actually takes */
async function dragRun(boxes, from, to) {
  await mouse(c, 'mouseMoved', boxes[from].x, boxes[from].y);
  await mouse(c, 'mousePressed', boxes[from].x, boxes[from].y);
  for (let i = from; i <= to; i++) {
    await mouse(c, 'mouseMoved', boxes[i].x, boxes[i].y);
  }
  await mouse(c, 'mouseReleased', boxes[to].x, boxes[to].y);
}

async function paintTarget(iconKey) {
  const pat = await evalIn(c, `return window.STORY.icons[${JSON.stringify(iconKey)}];`);
  const boxes = await cellBoxes();
  for (let r = 0; r < 8; r++) {
    let c0 = 0;
    while (c0 < 8) {
      if (pat[r][c0] !== '#') { c0++; continue; }
      let c1 = c0;
      while (c1 + 1 < 8 && pat[r][c1 + 1] === '#') c1++;
      await dragRun(boxes, r * 8 + c0, r * 8 + c1);
      c0 = c1 + 1;
    }
  }
}

// question 1: paint it wrong first, so the miscount is exercised too
{
  const boxes = await cellBoxes();
  await dragRun(boxes, 0, 3);
  await click(c, '#chk');
  await sleep(200);
  const msg = await text(c, '#cl');
  ok('a wrong grid reports how many squares are wrong', /squares are still wrong/.test(msg), msg);
  await click(c, '#clr');
  await sleep(250);
  ok('clear empties the grid',
    await evalIn(c, `return document.querySelectorAll('#grid .pxcell.on').length === 0;`));
}

/* Each of the four questions exercises a different marking path, so the
   expected round total is deliberately NOT full marks:
     q1  wrong once, then right   -> 2
     q2  right first time         -> 3
     q3  hint asked for           -> 1
     q4  right first time         -> 3                       total 9      */
const EXPECT = [2, 3, 1, 3];

for (let q = 0; q < 4; q++) {
  const icon = await evalIn(c, `return window.__leaf.R1[${q}].icon;`);

  if (q === 2) {
    // ask for the hint before drawing anything
    await click(c, '#hint');
    await sleep(300);
    const ghosts = await evalIn(c, `
      return {
        ghost: document.querySelectorAll('#grid .pxcell.ghost').length,
        want: window.STORY.icons[window.__leaf.R1[2].icon].join('').split('#').length - 1
      };`);
    ok('the hint faintly shows every square of the answer',
      ghosts.ghost === ghosts.want, ghosts.ghost + ' of ' + ghosts.want);
    ok('asking for the hint disables the hint button',
      await evalIn(c, `return document.getElementById('hint').disabled === true;`));
  }

  await paintTarget(icon);
  const litOk = await evalIn(c, `
    var pat = window.STORY.icons[${JSON.stringify(icon)}].join('');
    var on = Array.prototype.map.call(document.querySelectorAll('#grid .pxcell'),
      function(n){ return n.classList.contains('on') ? '#' : '.'; }).join('');
    return on === pat;
  `);
  ok('q' + (q + 1) + ' drag painted exactly the right squares', litOk);
  await click(c, '#chk');
  await sleep(220);
  const msg = await text(c, '#cl');
  ok('q' + (q + 1) + ' marked exactly right', /Exactly right/.test(msg), msg);

  const mark = await evalIn(c, `
    return window.__leaf.state().draw[window.__leaf.R1[${q}].id].mark;`);
  ok('q' + (q + 1) + ' scored ' + EXPECT[q], mark === EXPECT[q], 'got ' + mark);

  if (q < 3) { await click(c, '#nxt'); await sleep(300); }
}

const r1total = await evalIn(c, `return window.__leaf.totals().r1;`);
ok('round 1 scored 9 (2+3+1+3, one of each marking path)', r1total === 9, 'got ' + r1total);

// the erase path: drag back across a filled run and it should empty
{
  const boxes = await cellBoxes();
  const before = await evalIn(c, `return document.querySelectorAll('#grid .pxcell.on').length;`);
  // find a lit run in the current (tick) icon and drag over it
  const run = await evalIn(c, `
    var pat = window.STORY.icons[window.__leaf.R1[3].icon];
    for (var r=0;r<8;r++){ for(var c=0;c<7;c++){
      if (pat[r][c]==='#' && pat[r][c+1]==='#') return {a:r*8+c, b:r*8+c+1};
    }}
    return null;`);
  await dragRun(boxes, run.a, run.b);
  const after = await evalIn(c, `return document.querySelectorAll('#grid .pxcell.on').length;`);
  ok('dragging over lit squares rubs them out', after === before - 2, before + ' -> ' + after);
  await dragRun(boxes, run.a, run.b);   // put them back
  ok('and dragging again puts them back',
    await evalIn(c, `return document.querySelectorAll('#grid .pxcell.on').length === ${before};`));
}

await click(c, '#nxt');
await sleep(300);
await click(c, '#fw');    // round 2 intro -> start
await sleep(300);

/* ---------------------------------------------------------- round 2 */
console.log('\nD. round 2 - the picture word');

ok('the first word shows its pictures',
  await evalIn(c, `return document.querySelectorAll('.pic').length > 0;`));
ok('a blank is drawn for every letter',
  await evalIn(c, `
    return document.querySelectorAll('.blank').length ===
      window.__leaf.WORDS[0].word.length;`));
ok('no picture is labelled before a hint is asked for',
  await evalIn(c, `return document.querySelectorAll('.pic .named').length === 0;`));

// a wrong guess first
await type(c, '#gw', 'MOTH');
await click(c, '#gchk');
await sleep(220);
ok('a wrong word is refused', /Not that word/.test(await text(c, '#gmsg')));
ok('and is not marked done',
  await evalIn(c, `return window.__leaf.state().word[0].done !== true;`));

for (let i = 0; i < 6; i++) {
  const w = await evalIn(c, `return window.__leaf.WORDS[${i}].word;`);
  await type(c, '#gw', w);
  await click(c, '#gchk');
  await sleep(280);
  ok('word ' + w + ' accepted',
    await evalIn(c, `return window.__leaf.state().word[${i}].done === true;`));
  if (i < 5) { await click(c, '#nxt'); await sleep(280); }
}
const r2total = await evalIn(c, `return window.__leaf.totals().r2;`);
ok('round 2 scored 12 out of 12', r2total === 12, 'got ' + r2total);

await click(c, '#nxt');
await sleep(300);
await click(c, '#fw');   // round 3 intro -> start
await sleep(300);

/* ---------------------------------------------------------- round 3 */
console.log('\nE. round 3 - say it');

ok('round 3 shows a question',
  await evalIn(c, `return /\\?/.test(document.querySelector('.qtext').textContent);`));
ok('a typed answer box is always there',
  await evalIn(c, `return !!document.getElementById('ty');`));

// wrong answer first
await type(c, '#ty', 'bananas');
await click(c, '#tchk');
await sleep(220);
ok('a wrong spoken answer is refused',
  await evalIn(c, `return window.__leaf.state().say[0].done !== true;`));
ok('and it shows what was heard',
  /bananas/.test(await text(c, '#htxt')));

// hint
await click(c, '#shint');
await sleep(260);
ok('the hint appears when asked for',
  await evalIn(c, `return /Hint:/.test(document.querySelector('.typefall').textContent);`));

for (let i = 0; i < 8; i++) {
  const a = await evalIn(c, `return window.__leaf.R3[${i}].accept[0];`);
  await type(c, '#ty', a);
  await click(c, '#tchk');
  await sleep(280);
  ok('spoken q' + (i + 1) + ' accepted ("' + a + '")',
    await evalIn(c, `return window.__leaf.state().say[${i}].done === true;`));
  if (i < 7) { await click(c, '#nxt'); await sleep(280); }
}
const r3total = await evalIn(c, `return window.__leaf.totals().r3;`);
ok('round 3 scored 16 out of 16', r3total === 16, 'got ' + r3total);

/* ---------------------------------------------------------- result */
console.log('\nF. result and persistence');

await click(c, '#nxt');
await sleep(400);

const shown = await text(c, '.scorebox .num');
ok('the result reads 37 / 40', shown === '37 / 40', shown);
ok('the review lists every question',
  await evalIn(c, `return document.querySelectorAll('.rev').length === 18;`),
  String(await evalIn(c, `return document.querySelectorAll('.rev').length;`)));
ok('round 1 review shows both grids',
  await evalIn(c, `return document.querySelectorAll('.minigrid').length === 8;`));
ok('the student name is on the sheet',
  /Test Student 6B/.test(await evalIn(c, `return document.body.textContent;`)));

await c.send('Page.reload');
await sleep(1100);
ok('answers survive a reload',
  await evalIn(c, `return window.__leaf.totals().all === 37;`));
ok('and it comes back on the result screen',
  await evalIn(c, `return window.__leaf.state().screen === 'result';`));

/* new student wipes it */
await evalIn(c, `
  var b = document.getElementById('reset');
  window.confirm = function(){ return true; };
  b.click(); return 1;`);
await sleep(400);
ok('new student clears the answers',
  await evalIn(c, `return window.__leaf.totals().all === 0;`));
ok('and returns to the welcome screen',
  await evalIn(c, `return !!document.getElementById('nm');`));

/* ------------------------------------------------------------------ */
ok('no uncaught page errors', errors.length === 0, errors.slice(0, 3).join(' | '));

console.log('\n' + '='.repeat(56));
console.log(pass + ' passed, ' + fail + ' failed');
if (fail) { console.log('\nfailures:'); bad.forEach(b => console.log('  - ' + b)); }
console.log('='.repeat(56));

c.close();
proc.kill();
process.exit(fail ? 1 : 0);
