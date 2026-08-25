/* app.js - The Sentinels of Nova City: AI input & output assessment (Class 6).
   Four screens: welcome -> story -> questions -> result.
   Nothing leaves the browser; the answer file is saved to the student's own disk. */
(function () {
  'use strict';

  var app = document.getElementById('app');
  var audio = document.getElementById('narration');

  /* ------------------------------------------------------------ questions */
  var IN = 'in', OUT = 'out', MACH = 'machine';

  var QUESTIONS = [
    {
      type: 'sort', tag: 'Sort it', hero: 'Captain Echo',
      q: 'Captain Echo hears a shout, and words appear on her visor.',
      hint: 'Tap a card, then tap the box it belongs in. Careful — one card is not an input OR an output.',
      cards: [
        { id: 'a', t: 'The shout from the street', bin: IN },
        { id: 'b', t: 'The words that appear on her visor', bin: OUT },
        { id: 'c', t: 'Her helmet', bin: MACH }
      ]
    },
    {
      type: 'sort', tag: 'Sort it', hero: 'Iris',
      q: 'Iris takes a photo of the dam wall, and says the word CRACK.',
      hint: 'Tap a card, then tap the box it belongs in.',
      cards: [
        { id: 'a', t: 'The photo of the dam wall', bin: IN },
        { id: 'b', t: 'The word CRACK', bin: OUT },
        { id: 'c', t: 'Iris’s camera eye', bin: MACH }
      ]
    },
    {
      type: 'sort', tag: 'Sort it', hero: 'Nova',
      q: 'Nova reads tonight’s rainfall and river level, then warns the city.',
      hint: 'Tap a card, then tap the box it belongs in.',
      cards: [
        { id: 'a', t: 'Rainfall 92 mm, river level 7.4 m', bin: IN },
        { id: 'b', t: 'The warning “FLOOD IN TWO HOURS”', bin: OUT },
        { id: 'c', t: 'Nova herself', bin: MACH }
      ]
    },
    {
      type: 'sort', tag: 'Sort it', hero: 'Rex',
      q: 'You type a question to Rex, and Rex speaks the answer out loud.',
      hint: 'Tap a card, then tap the box it belongs in.',
      cards: [
        { id: 'a', t: 'The question you type', bin: IN },
        { id: 'b', t: 'The answer Rex speaks out loud', bin: OUT },
        { id: 'c', t: 'The robot dog’s body', bin: MACH }
      ]
    },

    {
      type: 'mcq', tag: 'From the story',
      q: 'Why did Iris say “ZEBRA” when she looked at the dam?',
      opts: [
        'Iris was broken and needed repair',
        'The Static had painted stripes on the wall, so her picture had stripes in it',
        'A real zebra was standing on the dam',
        'Iris was making a joke'
      ], ans: 1,
      why: 'Iris was working perfectly. She was given a picture with stripes in it, so stripes are what she answered about.'
    },
    {
      type: 'mcq', tag: 'From the story',
      q: 'What did the Static attack?',
      opts: [
        'The heroes’ bodies',
        'The city’s electricity',
        'The inputs the heroes were given',
        'The dam wall itself'
      ], ans: 2,
      why: 'He never touched the heroes. He changed what went IN — the picture, the voice and the numbers.'
    },
    {
      type: 'mcq', tag: 'From the story',
      q: 'How did the Sentinels finally get the right answers?',
      opts: [
        'They fought the Static on the bridge',
        'They switched their machines off and on again',
        'They gave their machines fresh, correct inputs',
        'They asked the mayor what to do'
      ], ans: 2,
      why: 'They did not fight at all. They fixed what went IN, and the right answers came OUT.'
    },
    {
      type: 'mcq', tag: 'The big rule',
      q: 'Meera said, “Bad input, bad output.” What does that mean?',
      opts: [
        'AI machines tell lies on purpose',
        'An AI’s answer can only be as good as what it is given',
        'Bad machines should be thrown away',
        'The output matters more than the input'
      ], ans: 1,
      why: 'The machine is not lying. It can only work with what you hand it.'
    },

    {
      type: 'mcq', tag: 'New machine',
      q: 'A school gate has a camera. When it sees a student in uniform, the gate opens. What is the INPUT?',
      opts: [
        'The gate',
        'The camera',
        'The picture of the person standing at the gate',
        'The gate opening'
      ], ans: 2,
      why: 'The camera is the machine, not the input. The input is the picture the camera takes.'
    },
    {
      type: 'mcq', tag: 'New machine',
      q: 'Same school gate. What is the OUTPUT?',
      opts: [
        'The picture of the person',
        'The camera lens',
        'The decision to open the gate',
        'The student’s uniform'
      ], ans: 2,
      why: 'The output is what comes out at the end — here, the decision that opens the gate.'
    },
    {
      type: 'mcq', tag: 'Odd one out',
      q: 'Which one of these is NOT an input?',
      opts: [
        'A photo you upload to an app',
        'The question you type to a chatbot',
        'The answer that appears on your screen',
        'Your voice when you speak to a smart speaker'
      ], ans: 2,
      why: 'The answer on the screen is what comes OUT. The other three are things you put IN.'
    },

    {
      type: 'pair', tag: 'Write it yourself', marks: 2,
      q: 'Bela’s grandmother uses an app. She holds a photo of her medicine strip in front of it, and the app says the name of the medicine out loud.',
      hint: 'Write in your own words. Your teacher will mark this one.',
      fields: [
        { k: 'input', label: 'The INPUT is…' },
        { k: 'output', label: 'The OUTPUT is…' }
      ]
    }
  ];

  var BIN_LABEL = {};
  BIN_LABEL[IN] = 'INPUT';
  BIN_LABEL[OUT] = 'OUTPUT';
  BIN_LABEL[MACH] = 'THE MACHINE';

  var AUTO_TOTAL = QUESTIONS.reduce(function (n, q) {
    return n + (q.type === 'sort' ? q.cards.length : q.type === 'mcq' ? 1 : 0);
  }, 0);
  var TEACHER_TOTAL = QUESTIONS.reduce(function (n, q) {
    return n + (q.type === 'pair' ? q.marks : 0);
  }, 0);

  /* ---------------------------------------------------------------- state */
  var S = {
    screen: 'welcome',
    name: '', cls: '', roll: '',
    watched: false,
    current: 0,
    answers: QUESTIONS.map(function (q) {
      return q.type === 'sort' ? {} : q.type === 'pair' ? { input: '', output: '' } : null;
    }),
    startedAt: null,
    finishedAt: null,
    picked: null   /* card id currently lifted in a sorting question */
  };

  var SAVE_KEY = 'sentinels-class6-v1';
  function save() {
    try { localStorage.setItem(SAVE_KEY, JSON.stringify(S)); } catch (e) { }
  }
  function restore() {
    try {
      var raw = localStorage.getItem(SAVE_KEY);
      if (!raw) return;
      var o = JSON.parse(raw);
      if (o && o.answers && o.answers.length === QUESTIONS.length && o.name) {
        Object.keys(o).forEach(function (k) { S[k] = o[k]; });
        S.picked = null;
        if (S.screen === 'story') S.screen = 'welcome';
      }
    } catch (e) { }
  }

  function esc(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
  function go(screen) { S.screen = screen; save(); render(); window.scrollTo(0, 0); }

  /* -------------------------------------------------------------- welcome */
  function welcomeHTML() {
    return '' +
      '<div class="panel">' +
      '<div class="hero-title">' +
      '<span class="kicker">Class 6 &middot; Artificial Intelligence</span>' +
      '<div class="title-main">The Sentinels<br>of Nova City</div>' +
      '<div class="subtitle">Input and Output</div>' +
      '</div>' +
      '<div class="steps">' +
      '<div class="step"><div class="n">1</div><b>Watch the story</b><p style="margin:6px 0 0;font-size:15px">' +
      'A 3 minute comic about four heroes and one very sneaky villain.</p></div>' +
      '<div class="step"><div class="n">2</div><b>Answer 12 questions</b><p style="margin:6px 0 0;font-size:15px">' +
      'Sort cards, choose answers, and write two lines of your own.</p></div>' +
      '<div class="step"><div class="n">3</div><b>See your score</b><p style="margin:6px 0 0;font-size:15px">' +
      'You may watch the story again at any time. There is no time limit.</p></div>' +
      '</div>' +
      '<div class="row">' +
      '<div class="grow"><label for="f-name">Your name</label>' +
      '<input id="f-name" type="text" value="' + esc(S.name) + '" placeholder="e.g. Aarav Sharma" autocomplete="off"></div>' +
      '<div style="flex:0 1 180px"><label for="f-cls">Class &amp; section</label>' +
      '<input id="f-cls" type="text" value="' + esc(S.cls) + '" placeholder="6 B" autocomplete="off"></div>' +
      '<div style="flex:0 1 150px"><label for="f-roll">Roll number</label>' +
      '<input id="f-roll" type="text" value="' + esc(S.roll) + '" placeholder="17" autocomplete="off"></div>' +
      '</div>' +
      '<p id="f-warn" style="color:var(--red);font-weight:bold;min-height:22px;margin:10px 0 0"></p>' +
      '<div class="navrow"><span></span>' +
      '<button class="btn go" id="b-start">Start the story</button></div>' +
      '</div>';
  }

  function wireWelcome() {
    document.getElementById('b-start').onclick = function () {
      S.name = document.getElementById('f-name').value.trim();
      S.cls = document.getElementById('f-cls').value.trim();
      S.roll = document.getElementById('f-roll').value.trim();
      if (!S.name) {
        document.getElementById('f-warn').textContent = 'Please write your name first.';
        document.getElementById('f-name').focus();
        return;
      }
      if (!S.startedAt) S.startedAt = new Date().toISOString();
      go('story');
    };
  }

  /* ---------------------------------------------------------------- story */
  var cues = null, rafId = 0, liveScene = null, liveCue = -1;

  function storyHTML() {
    return '' +
      '<div class="panel">' +
      '<div class="row spread" style="margin-bottom:12px">' +
      '<h2 style="margin:0">The Sentinels of Nova City</h2>' +
      '<span class="muted" style="font-weight:bold">Watch it right through. You can replay it later.</span>' +
      '</div>' +
      '<div class="stage" id="stage">' + window.STORY.build() +
      '<div class="caption" id="cap">Press play to begin.</div></div>' +
      '<div class="controls">' +
      '<button class="btn" id="b-play">Play</button>' +
      '<button class="btn plain sm" id="b-restart">Start again</button>' +
      '<div class="bar" id="bar" title="Jump to a moment"><i id="barfill"></i></div>' +
      '<span class="time" id="clock">0:00 / 2:58</span>' +
      '</div>' +
      '<div class="navrow">' +
      '<button class="btn plain" id="b-back">Back</button>' +
      '<button class="btn go" id="b-quiz"' + (S.watched ? '' : ' disabled') + '>' +
      (S.watched ? 'Go to the questions' : 'Questions unlock when the story ends') + '</button>' +
      '</div></div>';
  }

  function mmss(t) {
    t = Math.max(0, Math.floor(t || 0));
    return Math.floor(t / 60) + ':' + ('0' + (t % 60)).slice(-2);
  }

  function showScene(name) {
    if (name === liveScene) return;
    liveScene = name;
    var all = document.querySelectorAll('#stage .scene'), i;
    for (i = 0; i < all.length; i++) {
      all[i].classList.toggle('live', all[i].getAttribute('data-scene') === name);
    }
  }

  /* paint() does the work; loop() keeps it smooth while playing. The audio's own
     timeupdate event is wired to paint() as well, so captions keep moving even
     when the browser throttles animation frames (a backgrounded tab). */
  function paint() {
    var t = audio.currentTime, d = audio.duration || 178;
    if (!cues) cues = window.STORY.track(d);
    var i, k = 0;
    for (i = 0; i < cues.length; i++) if (cues[i].at <= t + 0.02) k = i;
    if (k !== liveCue) {
      liveCue = k;
      showScene(cues[k].scene);
      var cap = document.getElementById('cap');
      if (cap) cap.textContent = cues[k].text;
    }
    var fill = document.getElementById('barfill');
    if (fill) fill.style.width = (t / d * 100).toFixed(2) + '%';
    var clock = document.getElementById('clock');
    if (clock) clock.textContent = mmss(t) + ' / ' + mmss(d);
  }

  function loop() {
    paint();
    if (!audio.paused) rafId = requestAnimationFrame(loop);
  }

  function wireStory() {
    cues = null; liveScene = null; liveCue = -1;
    var play = document.getElementById('b-play');

    function sync() { play.textContent = audio.paused ? 'Play' : 'Pause'; }

    play.onclick = function () {
      if (audio.paused) {
        audio.play().then(sync).catch(function () {
          document.getElementById('cap').textContent =
            'The sound file could not be played. Keep narration.mp3 next to this page.';
        });
        cancelAnimationFrame(rafId); rafId = requestAnimationFrame(loop);
      } else { audio.pause(); }
      sync();
    };
    document.getElementById('b-restart').onclick = function () {
      audio.currentTime = 0; liveCue = -1; audio.play(); sync();
      cancelAnimationFrame(rafId); rafId = requestAnimationFrame(loop);
    };
    document.getElementById('bar').onclick = function (e) {
      var r = this.getBoundingClientRect();
      audio.currentTime = Math.max(0, Math.min(1, (e.clientX - r.left) / r.width)) * (audio.duration || 178);
      liveCue = -1; paint();
    };
    document.getElementById('b-back').onclick = function () { audio.pause(); go('welcome'); };
    document.getElementById('b-quiz').onclick = function () { audio.pause(); go('quiz'); };

    audio.onended = function () {
      S.watched = true; save();
      play.textContent = 'Play';
      var b = document.getElementById('b-quiz');
      if (b) { b.disabled = false; b.textContent = 'Go to the questions'; }
      var cap = document.getElementById('cap');
      if (cap) cap.textContent = 'The end. Now answer the questions.';
    };
    audio.onpause = sync;
    audio.onplay = sync;
    audio.ontimeupdate = paint;
    sync();
    paint();
  }

  /* --------------------------------------------------------------- quiz */
  function answered(i) {
    var q = QUESTIONS[i], a = S.answers[i];
    if (q.type === 'sort') return Object.keys(a || {}).length === q.cards.length;
    if (q.type === 'mcq') return a !== null && a !== undefined;
    if (q.type === 'pair') return q.fields.every(function (f) { return (a[f.k] || '').trim().length > 0; });
    return false;
  }

  function dotsHTML() {
    var s = '<div class="qdots">';
    QUESTIONS.forEach(function (q, i) {
      s += '<button class="qdot' + (answered(i) ? ' done' : '') + (i === S.current ? ' here' : '') +
        '" data-jump="' + i + '" title="Question ' + (i + 1) + '">' + (i + 1) + '</button>';
    });
    return s + '</div>';
  }

  function sortBodyHTML(q, i) {
    var a = S.answers[i] || {};
    var tray = q.cards.filter(function (c) { return !a[c.id]; });
    var s = '<div class="cards" id="tray">';
    if (!tray.length) s += '<span class="muted" style="font-weight:bold;padding:14px 0">' +
      'All three cards are placed. Tap a card in a box to take it back.</span>';
    tray.forEach(function (c) {
      s += '<button class="card' + (S.picked === c.id ? ' picked' : '') + '" data-card="' + c.id + '">' + esc(c.t) + '</button>';
    });
    s += '</div><div class="bins">';
    [[IN, 'in', 'what goes IN'], [OUT, 'out', 'what comes OUT'], [MACH, 'mach', 'not in, not out']].forEach(function (b) {
      s += '<div class="bin ' + b[1] + (S.picked ? ' armed' : '') + '" data-bin="' + b[0] + '">' +
        '<h3>' + BIN_LABEL[b[0]] + '</h3><p class="why">' + b[2] + '</p><div class="drop">';
      q.cards.forEach(function (c) {
        if (a[c.id] === b[0]) s += '<button class="card placed" data-card="' + c.id + '">' + esc(c.t) + '</button>';
      });
      s += '</div></div>';
    });
    return s + '</div>';
  }

  function mcqBodyHTML(q, i) {
    var a = S.answers[i], s = '<div class="opts">';
    q.opts.forEach(function (o, k) {
      s += '<button class="opt' + (a === k ? ' chosen' : '') + '" data-opt="' + k + '">' +
        '<span class="k">' + 'ABCD'[k] + '</span><span>' + esc(o) + '</span></button>';
    });
    return s + '</div>';
  }

  function pairBodyHTML(q, i) {
    var a = S.answers[i] || {};
    var s = '';
    q.fields.forEach(function (f) {
      s += '<label for="w-' + f.k + '">' + esc(f.label) + '</label>' +
        '<textarea id="w-' + f.k + '" data-field="' + f.k + '" style="min-height:80px">' + esc(a[f.k] || '') + '</textarea>';
    });
    return s;
  }

  function quizHTML() {
    var i = S.current, q = QUESTIONS[i];
    var body = q.type === 'sort' ? sortBodyHTML(q, i)
      : q.type === 'mcq' ? mcqBodyHTML(q, i) : pairBodyHTML(q, i);
    var done = QUESTIONS.filter(function (_, k) { return answered(k); }).length;
    return '' +
      '<div class="panel">' +
      '<div class="qhead">' + dotsHTML() +
      '<span style="flex:1"></span>' +
      '<span class="muted" style="font-weight:bold" id="progress">' + done + ' of ' + QUESTIONS.length + ' answered</span>' +
      '<button class="btn plain sm" id="b-rewatch">Watch the story again</button>' +
      '</div>' +
      '<span class="qtag">' + esc(q.tag) + (q.hero ? ' &middot; ' + esc(q.hero) : '') + '</span>' +
      '<p class="qtext">' + esc(q.q) + '</p>' +
      (q.hint ? '<p class="qhint">' + esc(q.hint) + '</p>' : '') +
      body +
      '<div class="navrow">' +
      '<button class="btn plain" id="b-prev"' + (i === 0 ? ' disabled' : '') + '>Previous</button>' +
      (i === QUESTIONS.length - 1
        ? '<button class="btn hot" id="b-finish">Finish and see my score</button>'
        : '<button class="btn go" id="b-next">Next question</button>') +
      '</div></div>';
  }

  function wireQuiz() {
    var i = S.current, q = QUESTIONS[i];

    Array.prototype.forEach.call(document.querySelectorAll('[data-jump]'), function (b) {
      b.onclick = function () { S.current = +b.getAttribute('data-jump'); S.picked = null; save(); render(); };
    });
    document.getElementById('b-rewatch').onclick = function () { go('story'); };

    var prev = document.getElementById('b-prev');
    if (prev) prev.onclick = function () { S.current = Math.max(0, i - 1); S.picked = null; save(); render(); };
    var next = document.getElementById('b-next');
    if (next) next.onclick = function () { S.current = Math.min(QUESTIONS.length - 1, i + 1); S.picked = null; save(); render(); };
    var fin = document.getElementById('b-finish');
    if (fin) fin.onclick = function () {
      var missing = [];
      QUESTIONS.forEach(function (_, k) { if (!answered(k)) missing.push(k + 1); });
      if (missing.length && !window.confirm(
        'Question ' + missing.join(', ') + ' still empty. Finish anyway?')) return;
      S.finishedAt = new Date().toISOString();
      go('done');
    };

    if (q.type === 'sort') {
      Array.prototype.forEach.call(document.querySelectorAll('[data-card]'), function (b) {
        b.onclick = function (ev) {
          /* a placed card sits inside its bin - without this the click bubbles
             to the bin and drops the card straight back in */
          ev.stopPropagation();
          var id = b.getAttribute('data-card');
          if (S.answers[i][id]) { delete S.answers[i][id]; S.picked = id; }
          else { S.picked = (S.picked === id) ? null : id; }
          save(); render();
        };
      });
      Array.prototype.forEach.call(document.querySelectorAll('[data-bin]'), function (b) {
        b.onclick = function () {
          if (!S.picked) return;
          S.answers[i][S.picked] = b.getAttribute('data-bin');
          S.picked = null;
          if (Object.keys(S.answers[i]).length < q.cards.length) {
            var left = q.cards.filter(function (c) { return !S.answers[i][c.id]; });
            if (left.length === 1) S.picked = left[0].id;   /* keep it moving for young hands */
          }
          save(); render();
        };
      });
    }

    if (q.type === 'mcq') {
      Array.prototype.forEach.call(document.querySelectorAll('[data-opt]'), function (b) {
        b.onclick = function () { S.answers[i] = +b.getAttribute('data-opt'); save(); render(); };
      });
    }

    if (q.type === 'pair') {
      Array.prototype.forEach.call(document.querySelectorAll('[data-field]'), function (t) {
        t.oninput = function () {
          S.answers[i][t.getAttribute('data-field')] = t.value;
          save();
          refreshProgress();   /* a full render here would steal the caret mid-word */
        };
      });
    }
  }

  /* keep the dots and the counter honest without re-rendering the question */
  function refreshProgress() {
    Array.prototype.forEach.call(document.querySelectorAll('[data-jump]'), function (b) {
      b.classList.toggle('done', answered(+b.getAttribute('data-jump')));
    });
    var n = QUESTIONS.filter(function (_, k) { return answered(k); }).length;
    var el = document.getElementById('progress');
    if (el) el.textContent = n + ' of ' + QUESTIONS.length + ' answered';
  }

  /* -------------------------------------------------------------- result */
  function grade() {
    var got = 0, rows = [];
    QUESTIONS.forEach(function (q, i) {
      var a = S.answers[i];
      if (q.type === 'sort') {
        q.cards.forEach(function (c) {
          var mine = (a || {})[c.id], ok = mine === c.bin;
          if (ok) got++;
          rows.push({
            ok: ok, q: 'Q' + (i + 1) + ' ' + q.hero + ': ' + c.t,
            said: mine ? 'You put it in ' + BIN_LABEL[mine] : 'You left it out',
            right: 'It is ' + BIN_LABEL[c.bin]
          });
        });
      } else if (q.type === 'mcq') {
        var ok = a === q.ans;
        if (ok) got++;
        rows.push({
          ok: ok, q: 'Q' + (i + 1) + '. ' + q.q,
          said: (a === null || a === undefined) ? 'You left it blank' : 'You chose: ' + q.opts[a],
          right: 'Answer: ' + q.opts[q.ans] + (q.why ? ' — ' + q.why : '')
        });
      }
    });
    return { got: got, rows: rows };
  }

  function doneHTML() {
    var g = grade(), i = QUESTIONS.length - 1, wq = QUESTIONS[i], wa = S.answers[i] || {};
    var pct = Math.round(g.got / AUTO_TOTAL * 100);
    var word = pct >= 85 ? 'Sentinel level. Excellent.' : pct >= 60 ? 'Good work. Read the red ones again.'
      : 'Watch the story once more, then look at the red ones.';
    var s = '<div class="panel">' +
      '<h1 style="text-align:center">' + esc(S.name || 'Student') + '</h1>' +
      '<p class="muted" style="text-align:center;margin-top:-4px">' +
      (S.cls ? 'Class ' + esc(S.cls) + ' &middot; ' : '') + (S.roll ? 'Roll ' + esc(S.roll) + ' &middot; ' : '') +
      'The Sentinels of Nova City &middot; AI Input and Output</p>' +
      '<div class="scorebox"><div class="num">' + g.got + ' / ' + AUTO_TOTAL + '</div>' +
      '<div style="font-weight:bold;font-size:19px;margin-top:6px">' + word + '</div>' +
      '<div style="font-size:15px;margin-top:4px">Question 12 is worth ' + TEACHER_TOTAL +
      ' more marks and is checked by your teacher.</div></div>' +
      '<div class="teacher" style="margin-bottom:18px"><b>Question 12 &mdash; for the teacher</b><br>' +
      esc(wq.q) + '<br><br>' +
      '<b>Input:</b> ' + (esc(wa.input) || '<i>left blank</i>') + '<br>' +
      '<b>Output:</b> ' + (esc(wa.output) || '<i>left blank</i>') + '<br><br>' +
      '<span class="muted">Expected: input = the photo of the medicine strip; ' +
      'output = the spoken name of the medicine.</span></div>' +
      '<h2>Every answer</h2><div class="review">';
    g.rows.forEach(function (r) {
      s += '<div class="rev ' + (r.ok ? 'ok' : 'no') + '"><span class="mark">' + (r.ok ? '✔' : '✘') + '</span>' +
        '<span><b>' + esc(r.q) + '</b><span class="said">' + esc(r.said) + '</span>' +
        (r.ok ? '' : '<span class="said" style="color:var(--green)"><b>' + esc(r.right) + '</b></span>') +
        '</span></div>';
    });
    s += '</div><div class="navrow noprint">' +
      '<button class="btn plain" id="b-again">Back to the questions</button>' +
      '<span><button class="btn" id="b-print">Print / Save as PDF</button> ' +
      '<button class="btn go" id="b-save">Save my answer file</button> ' +
      '<button class="btn hot" id="b-new">New student</button></span>' +
      '</div></div>';
    return s;
  }

  function wireDone() {
    document.getElementById('b-again').onclick = function () { go('quiz'); };
    document.getElementById('b-print').onclick = function () { window.print(); };
    document.getElementById('b-new').onclick = function () {
      if (!window.confirm('Clear this student and start fresh?')) return;
      try { localStorage.removeItem(SAVE_KEY); } catch (e) { }
      window.location.reload();
    };
    document.getElementById('b-save').onclick = function () {
      var g = grade();
      var out = {
        assessment: 'The Sentinels of Nova City - AI Input and Output (Class 6)',
        name: S.name, classSection: S.cls, roll: S.roll,
        startedAt: S.startedAt, finishedAt: S.finishedAt,
        minutesTaken: S.startedAt && S.finishedAt
          ? Math.round((new Date(S.finishedAt) - new Date(S.startedAt)) / 600) / 100 : null,
        autoScore: g.got, autoTotal: AUTO_TOTAL,
        teacherMarksAvailable: TEACHER_TOTAL, teacherMarks: null, teacherFeedback: '',
        answers: QUESTIONS.map(function (q, i) {
          var a = S.answers[i];
          if (q.type === 'sort') {
            return {
              n: i + 1, type: 'sort', question: q.q,
              placed: q.cards.map(function (c) {
                return { card: c.t, studentPut: BIN_LABEL[(a || {})[c.id]] || null, correct: BIN_LABEL[c.bin] };
              })
            };
          }
          if (q.type === 'mcq') {
            return {
              n: i + 1, type: 'mcq', question: q.q,
              chose: (a === null || a === undefined) ? null : q.opts[a],
              correct: q.opts[q.ans], right: a === q.ans
            };
          }
          return { n: i + 1, type: 'written', question: q.q, input: a.input, output: a.output };
        }),
        review: g.rows
      };
      var safe = (S.name || 'student').replace(/[^A-Za-z0-9]+/g, '-').replace(/^-|-$/g, '');
      var blob = new Blob([JSON.stringify(out, null, 2)], { type: 'application/json' });
      var url = URL.createObjectURL(blob);
      var a2 = document.createElement('a');
      a2.href = url;
      a2.download = 'sentinels-' + safe + '.json';
      document.body.appendChild(a2); a2.click(); a2.remove();
      setTimeout(function () { URL.revokeObjectURL(url); }, 4000);
    };
  }

  /* -------------------------------------------------------------- render */
  function render() {
    if (S.screen !== 'story') { audio.pause(); cancelAnimationFrame(rafId); }
    if (S.screen === 'welcome') { app.innerHTML = welcomeHTML(); wireWelcome(); }
    else if (S.screen === 'story') { app.innerHTML = storyHTML(); wireStory(); }
    else if (S.screen === 'quiz') { app.innerHTML = quizHTML(); wireQuiz(); }
    else { app.innerHTML = doneHTML(); wireDone(); }
  }

  restore();

  render();
})();
