/* app.js - The Sentinels of Nova City (Class 6).
   Screens: welcome -> story -> [part intro -> questions] x3 -> result.
   The story only tells the story. All of the teaching happens here, in three
   parts: Drag & Drop (complete the pattern), Multiple Choice, Guessing Game.
   Nothing leaves the browser. */
(function () {
  'use strict';

  var app = document.getElementById('app');
  var audio = document.getElementById('narration');

  /* ------------------------------------------------------------- the parts */
  var PARTS = [
    {
      key: 'drag', n: 'Part 1', title: 'Drag &amp; Drop',
      blurb: 'Every machine in Nova City follows the same pattern. Drag the missing ' +
        'pieces into the empty boxes to complete it.'
    },
    {
      key: 'mcq', n: 'Part 2', title: 'Multiple Choice',
      blurb: 'Four answers, one is best. Tap the one you think is right.'
    },
    {
      key: 'guess', n: 'Part 3', title: 'Guessing Game',
      blurb: 'Read the clue and work out the word. Stuck? Ask for another clue — ' +
        'it costs you nothing.'
    }
  ];

  /* The pattern is deliberately identical every time: what goes IN, the machine
     in the middle, what comes OUT. Repeating it is what teaches it. */
  var SLOT_LABEL = { in: 'WHAT GOES IN', machine: 'THE MACHINE', out: 'WHAT COMES OUT' };

  var QUESTIONS = [
    /* ------------------------------------------------------ part 1: drag */
    {
      part: 'drag', hero: 'IRIS',
      q: 'Iris looked past the paint and said the word CRACK.',
      slots: [
        { role: 'in', answer: 'photo' },
        { role: 'machine', fixed: 'IRIS' },
        { role: 'out', answer: 'crack' }
      ],
      tray: [
        { id: 'photo', t: 'the photo of the dam wall' },
        { id: 'crack', t: 'the word “CRACK”' },
        { id: 'eye', t: 'Iris’s camera eye' },
        { id: 'cape', t: 'Iris’s purple cape' }
      ]
    },
    {
      part: 'drag', hero: 'NOVA',
      q: 'Nova threw away the old page and read tonight’s gauges.',
      slots: [
        { role: 'in', answer: 'nums' },
        { role: 'machine', fixed: 'NOVA' },
        { role: 'out', answer: 'flood' }
      ],
      tray: [
        { id: 'nums', t: 'tonight’s rain and river numbers' },
        { id: 'flood', t: '“Flood. Two hours.”' },
        { id: 'nova', t: 'Nova herself' },
        { id: 'storm', t: 'the storm clouds' }
      ]
    },
    {
      part: 'drag', hero: 'REX',
      q: 'You ask Rex a question and he answers out loud.',
      slots: [
        { role: 'in', fixed: 'the question you type' },
        { role: 'machine', answer: 'rex' },
        { role: 'out', answer: 'said' }
      ],
      tray: [
        { id: 'rex', t: 'REX the robot dog' },
        { id: 'said', t: 'the answer he says out loud' },
        { id: 'tail', t: 'his antenna tail' },
        { id: 'kettle', t: 'a voice like a kettle' }
      ]
    },
    {
      part: 'drag', hero: 'CAPTAIN ECHO',
      q: 'Echo listened to the real mayor on the town hall steps.',
      slots: [
        { role: 'in', answer: 'voice' },
        { role: 'machine', fixed: 'CAPTAIN ECHO' },
        { role: 'out', answer: 'evac' }
      ],
      tray: [
        { id: 'voice', t: 'the mayor’s real voice' },
        { id: 'evac', t: 'the word “EVACUATE”' },
        { id: 'helmet', t: 'Echo’s helmet' },
        { id: 'steps', t: 'the town hall steps' }
      ]
    },

    /* ------------------------------------------------------- part 2: mcq */
    {
      part: 'mcq',
      q: 'Why did Iris say “zebra” when she looked at the dam?',
      opts: [
        'Iris was broken and needed repair',
        'The wall she looked at had black stripes painted across it',
        'A real zebra was standing on the dam',
        'Iris was making a joke'
      ], ans: 1,
      why: 'Iris was working perfectly. She was handed a wall covered in stripes, so stripes are what she named.'
    },
    {
      part: 'mcq',
      q: 'The Static never touched a single hero. So what did it change?',
      opts: [
        'The heroes’ powers',
        'The weather over Nova City',
        'The things the heroes were given to work from',
        'The strength of the dam wall'
      ], ans: 2,
      why: 'Nine days of painting a wall, recording a voice and swapping a page of numbers — all of it changed what went in.'
    },
    {
      part: 'mcq',
      q: 'Meera said: “They weren’t wrong. They were told wrong.” What did she mean?',
      opts: [
        'The heroes were telling lies',
        'The heroes were given the wrong things to work from',
        'The heroes should be replaced with better ones',
        'The heroes were not listening carefully'
      ], ans: 1,
      why: 'A machine can only work with what you hand it. Hand it something false and it will answer falsely, with total confidence.'
    },
    {
      part: 'mcq',
      q: 'A school gate has a camera. When it sees a student, the gate opens. What goes IN?',
      opts: [
        'The gate',
        'The camera',
        'The picture of the person standing at the gate',
        'The gate opening'
      ], ans: 2,
      why: 'The camera is the machine, not the thing going in. What goes in is the picture it takes.'
    },
    {
      part: 'mcq',
      q: 'Same school gate. What comes OUT?',
      opts: [
        'The picture of the person',
        'The camera lens',
        'The decision to open the gate',
        'The student’s uniform'
      ], ans: 2,
      why: 'What comes out is the thing the machine produces at the end — here, the decision that opens the gate.'
    },
    {
      part: 'mcq',
      q: 'Which one of these is NOT something you put IN?',
      opts: [
        'A photo you upload to an app',
        'A question you type to a chatbot',
        'The answer that appears on your screen',
        'Your voice when you talk to a smart speaker'
      ], ans: 2,
      why: 'The answer on the screen is what comes out. The other three are all things you hand over.'
    },

    /* ----------------------------------------------------- part 3: guess */
    {
      part: 'guess', answer: 'INPUT', accept: ['input', 'inputs', 'the input'],
      clues: [
        'I am the thing you hand to a machine before it can do anything at all.',
        'Iris was handed a photo. Echo was handed a sound. Nova was handed numbers. Every one of those was me.',
        'Five letters. I start with I, and I rhyme with "put".'
      ]
    },
    {
      part: 'guess', answer: 'OUTPUT', accept: ['output', 'outputs', 'the output'],
      clues: [
        'I am what the machine gives back when it has finished working.',
        '“Zebra” was me. So was “Crack”. So was “Flood. Two hours.”',
        'Six letters. I am the opposite of the last word you guessed.'
      ]
    },
    {
      part: 'guess', answer: 'MACHINE', accept: ['machine', 'the machine', 'machines'],
      clues: [
        'I sit in the middle of the pattern. I am neither the thing going in nor the thing coming out.',
        'Echo’s helmet is part of me. So is Iris’s camera eye and Rex’s whole robot body.',
        'Seven letters, starting with M. A washing one and a vending one are both me.'
      ]
    },
    {
      part: 'guess', answer: 'STATIC', accept: ['static', 'the static'],
      clues: [
        'I am the villain, and I never threw a single punch.',
        'I spent nine days of rain painting a wall, recording a voice, and swapping a page of numbers.',
        'Six letters. I am also the crackly noise a radio makes between stations.'
      ]
    }
  ];

  function inPart(key) {
    return QUESTIONS.filter(function (q) { return q.part === key; });
  }
  function gapCount(q) {
    return q.slots.filter(function (s) { return s.answer; }).length;
  }
  var TOTAL = QUESTIONS.reduce(function (n, q) {
    return n + (q.part === 'drag' ? gapCount(q) : 1);
  }, 0);

  /* ---------------------------------------------------------------- state */
  var S = {
    screen: 'welcome',
    name: '', cls: '', roll: '',
    watched: false,
    part: 0,
    current: 0,
    answers: QUESTIONS.map(function (q) {
      return q.part === 'drag' ? {}
        : q.part === 'guess' ? { tries: [], clues: 1, solved: false }
          : null;
    }),
    startedAt: null, finishedAt: null,
    picked: null
  };

  var SAVE_KEY = 'sentinels-class6-v2';
  function save() { try { localStorage.setItem(SAVE_KEY, JSON.stringify(S)); } catch (e) { } }
  function restore() {
    try {
      var o = JSON.parse(localStorage.getItem(SAVE_KEY) || 'null');
      if (o && o.answers && o.answers.length === QUESTIONS.length && o.name) {
        Object.keys(o).forEach(function (k) { S[k] = o[k]; });
        S.picked = null;
        if (S.screen === 'story') S.screen = 'welcome';
      }
    } catch (e) { }
  }

  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
  function go(screen) { S.screen = screen; save(); render(); window.scrollTo(0, 0); }

  /* index helpers: questions are stored flat but shown part by part */
  function partQs() { return inPart(PARTS[S.part].key); }
  function absIndex(local) { return QUESTIONS.indexOf(partQs()[local]); }

  /* -------------------------------------------------------------- welcome */
  function welcomeHTML() {
    return '<div class="panel">' +
      '<div class="hero-title">' +
      '<span class="kicker">Class 6 &middot; Artificial Intelligence</span>' +
      '<div class="title-main">The Sentinels<br>of Nova City</div>' +
      '<div class="subtitle">Watch. Then work it out.</div>' +
      '</div>' +
      '<div class="steps">' +
      '<div class="step"><div class="n">1</div><b>Watch the story</b>' +
      '<p>Three minutes. Four heroes, one night of rain, and a villain who never throws a punch.</p></div>' +
      '<div class="step"><div class="n">2</div><b>Three rounds of questions</b>' +
      '<p>Drag &amp; Drop, then Multiple Choice, then a Guessing Game.</p></div>' +
      '<div class="step"><div class="n">3</div><b>See how you did</b>' +
      '<p>Replay the story whenever you like. There is no time limit.</p></div>' +
      '</div>' +
      '<div class="row">' +
      '<div class="grow"><label for="f-name">Your name</label>' +
      '<input id="f-name" type="text" value="' + esc(S.name) + '" placeholder="e.g. Aarav Sharma" autocomplete="off"></div>' +
      '<div style="flex:0 1 180px"><label for="f-cls">Class &amp; section</label>' +
      '<input id="f-cls" type="text" value="' + esc(S.cls) + '" placeholder="6 B" autocomplete="off"></div>' +
      '<div style="flex:0 1 150px"><label for="f-roll">Roll number</label>' +
      '<input id="f-roll" type="text" value="' + esc(S.roll) + '" placeholder="17" autocomplete="off"></div>' +
      '</div>' +
      '<p id="f-warn" class="warn"></p>' +
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
    return '<div class="panel">' +
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
      '<span class="time" id="clock">0:00</span>' +
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

  /* paint() does the work; loop() keeps it smooth while playing. timeupdate is
     wired to paint() too, so captions keep moving if frames are throttled. */
  function paint() {
    var t = audio.currentTime, d = audio.duration || 190;
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
            'The sound could not be played. Keep narration.mp3 next to this page.';
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
      audio.currentTime = Math.max(0, Math.min(1, (e.clientX - r.left) / r.width)) * (audio.duration || 190);
      liveCue = -1; paint();
    };
    document.getElementById('b-back').onclick = function () { audio.pause(); go('welcome'); };
    document.getElementById('b-quiz').onclick = function () {
      audio.pause(); S.part = 0; S.current = 0; go('intro');
    };

    audio.onended = function () {
      S.watched = true; save();
      play.textContent = 'Play';
      var b = document.getElementById('b-quiz');
      if (b) { b.disabled = false; b.textContent = 'Go to the questions'; }
      var cap = document.getElementById('cap');
      if (cap) cap.textContent = 'The end. Now the questions.';
    };
    audio.onpause = sync;
    audio.onplay = sync;
    audio.ontimeupdate = paint;
    sync();
    paint();
  }

  /* --------------------------------------------------------- part intro */
  function introHTML() {
    var p = PARTS[S.part];
    var qs = partQs();
    var marks = qs.reduce(function (n, q) { return n + (q.part === 'drag' ? gapCount(q) : 1); }, 0);
    var demo = '';
    if (p.key === 'drag') {
      demo = '<div class="demo"><p class="democap">This is the pattern. It is the same every time.</p>' +
        patternHTML([
          { role: 'in', fixed: 'a shout in the street' },
          { role: 'machine', fixed: 'CAPTAIN ECHO' },
          { role: 'out', fixed: 'the words on her visor' }
        ], {}, -1) + '</div>';
    }
    return '<div class="panel">' +
      '<div class="partbadge">' + p.n + ' of 3</div>' +
      '<h1 class="parttitle">' + p.title + '</h1>' +
      '<p class="big" style="max-width:760px">' + p.blurb + '</p>' +
      demo +
      '<p class="muted big"><b>' + qs.length + ' question' + (qs.length > 1 ? 's' : '') +
      '</b> &middot; ' + marks + ' mark' + (marks > 1 ? 's' : '') + '</p>' +
      '<div class="navrow">' +
      '<button class="btn plain" id="b-story">Watch the story again</button>' +
      '<button class="btn go" id="b-begin">Start ' + p.title + '</button>' +
      '</div></div>';
  }

  function wireIntro() {
    document.getElementById('b-story').onclick = function () { go('story'); };
    document.getElementById('b-begin').onclick = function () { S.current = 0; go('quiz'); };
  }

  /* ----------------------------------------------------- part 1: drag&drop */
  function patternHTML(slots, placed, qi) {
    var s = '<div class="pattern">';
    slots.forEach(function (slot, k) {
      if (k) s += '<div class="arrowcell"><span class="arrowmark"></span></div>';
      var filled = slot.fixed || (slot.answer ? placed[slot.answer] : null);
      s += '<div class="slotwrap">' +
        '<div class="slotlab ' + slot.role + '">' + SLOT_LABEL[slot.role] + '</div>' +
        '<div class="slot' + (slot.fixed ? ' fixed' : ' drop') + (filled ? ' full' : '') +
        (slot.role === 'machine' ? ' mach' : '') + '"' +
        (slot.answer ? ' data-slot="' + slot.answer + '"' : '') + '>' +
        (filled ? esc(filled) : (slot.fixed ? '' : '<span class="ghosttext">drop here</span>')) +
        '</div></div>';
    });
    return s + '</div>';
  }

  function dragBodyHTML(q, qi) {
    var placed = S.answers[qi] || {};        /* slotId -> tray item text */
    var usedIds = Object.keys(placed).map(function (k) { return placed[k].id; });
    var placedText = {};
    Object.keys(placed).forEach(function (k) { placedText[k] = placed[k].t; });

    var tray = q.tray.filter(function (it) { return usedIds.indexOf(it.id) < 0; });
    var s = patternHTML(q.slots, placedText, qi);
    s += '<p class="traylab">Drag a card into an empty box. On a tablet, tap the card then tap the box.</p>';
    s += '<div class="cards" id="tray">';
    if (!tray.length) s += '<span class="muted" style="font-weight:bold;padding:12px 0">' +
      'All done. Tap a card in the pattern to take it back.</span>';
    tray.forEach(function (it) {
      s += '<button class="card' + (S.picked === it.id ? ' picked' : '') +
        '" data-card="' + it.id + '">' + esc(it.t) + '</button>';
    });
    return s + '</div>';
  }

  /* pointer dragging that also works as tap-then-tap, so it is fine with a
     mouse, a finger, and a keyboard-less tablet alike */
  function wireDrag(q, qi) {
    var ghost = null, from = null, moved = false, startX = 0, startY = 0;

    function placeInto(slotId, item) {
      var a = S.answers[qi];
      Object.keys(a).forEach(function (k) {          /* one card per slot, one slot per card */
        if (a[k].id === item.id) delete a[k];
      });
      a[slotId] = { id: item.id, t: item.t };
      S.picked = null;
      save(); render();
    }
    function itemById(id) {
      var m = q.tray.filter(function (t) { return t.id === id; });
      return m[0];
    }

    Array.prototype.forEach.call(document.querySelectorAll('[data-card]'), function (b) {
      b.onpointerdown = function (ev) {
        from = b.getAttribute('data-card'); moved = false;
        startX = ev.clientX; startY = ev.clientY;
        b.setPointerCapture(ev.pointerId);
      };
      b.onpointermove = function (ev) {
        if (from !== b.getAttribute('data-card')) return;
        if (!moved && Math.abs(ev.clientX - startX) + Math.abs(ev.clientY - startY) < 8) return;
        if (!moved) {
          moved = true;
          ghost = document.createElement('div');
          ghost.className = 'ghostcard';
          ghost.textContent = b.textContent;
          document.body.appendChild(ghost);
          b.classList.add('lifting');
        }
        ghost.style.left = ev.clientX + 'px';
        ghost.style.top = ev.clientY + 'px';
        var over = document.elementFromPoint(ev.clientX, ev.clientY);
        var slot = over && over.closest ? over.closest('[data-slot]') : null;
        Array.prototype.forEach.call(document.querySelectorAll('[data-slot]'), function (sl) {
          sl.classList.toggle('hot', sl === slot);
        });
      };
      b.onpointerup = function (ev) {
        var id = b.getAttribute('data-card');
        if (ghost) { ghost.remove(); ghost = null; }
        b.classList.remove('lifting');
        if (moved) {
          var over = document.elementFromPoint(ev.clientX, ev.clientY);
          var slot = over && over.closest ? over.closest('[data-slot]') : null;
          moved = false; from = null;
          if (slot) { placeInto(slot.getAttribute('data-slot'), itemById(id)); return; }
          render();                       /* dropped on nothing - just redraw */
          return;
        }
        from = null;
        S.picked = (S.picked === id) ? null : id;   /* a plain tap selects it */
        save(); render();
      };
      b.onpointercancel = function () {
        if (ghost) { ghost.remove(); ghost = null; }
        b.classList.remove('lifting'); moved = false; from = null;
      };
    });

    Array.prototype.forEach.call(document.querySelectorAll('[data-slot]'), function (sl) {
      sl.onclick = function () {
        if (!S.picked) return;
        placeInto(sl.getAttribute('data-slot'), itemById(S.picked));
      };
    });

    /* tapping a card already in the pattern sends it back to the tray */
    Array.prototype.forEach.call(document.querySelectorAll('.slot.full[data-slot]'), function (sl) {
      sl.onclick = function (ev) {
        if (S.picked) { placeInto(sl.getAttribute('data-slot'), itemById(S.picked)); return; }
        ev.stopPropagation();
        delete S.answers[qi][sl.getAttribute('data-slot')];
        save(); render();
      };
    });
  }

  /* ----------------------------------------------------------- part 2: mcq */
  function mcqBodyHTML(q, qi) {
    var a = S.answers[qi], s = '<div class="opts">';
    q.opts.forEach(function (o, k) {
      s += '<button class="opt' + (a === k ? ' chosen' : '') + '" data-opt="' + k + '">' +
        '<span class="k">' + 'ABCD'[k] + '</span><span>' + esc(o) + '</span></button>';
    });
    return s + '</div>';
  }

  /* --------------------------------------------------------- part 3: guess */
  function blanksHTML(word, solved) {
    return '<div class="blanks">' + word.split('').map(function (ch) {
      return '<span class="blank' + (solved ? ' got' : '') + '">' + (solved ? ch : '') + '</span>';
    }).join('') + '</div>';
  }

  function guessBodyHTML(q, qi) {
    var a = S.answers[qi];
    var s = blanksHTML(q.answer, a.solved);
    s += '<div class="clues">';
    q.clues.slice(0, a.clues).forEach(function (c, k) {
      s += '<div class="clue"><span class="cluen">Clue ' + (k + 1) + '</span>' + esc(c) + '</div>';
    });
    s += '</div>';
    if (a.solved) {
      s += '<p class="gotit">Got it — the word is <b>' + esc(q.answer) + '</b>.</p>';
    } else {
      s += '<div class="guessrow">' +
        '<input id="g-in" type="text" placeholder="Type your guess" autocomplete="off" spellcheck="false">' +
        '<button class="btn go" id="b-guess">Check</button>' +
        (a.clues < q.clues.length
          ? '<button class="btn plain sm" id="b-clue">Another clue</button>' : '') +
        '</div>';
      var bad = a.tries.length;
      if (bad) s += '<p class="warn">Not quite' + (bad > 1 ? ' — you have tried ' + bad + ' times' : '') +
        '. Try another word, or ask for a clue.</p>';
    }
    return s;
  }

  function wireGuess(q, qi) {
    var a = S.answers[qi];
    if (a.solved) return;
    var box = document.getElementById('g-in');
    function submit() {
      var v = (box.value || '').trim().toLowerCase().replace(/[^a-z ]/g, '');
      if (!v) return;
      if (q.accept.indexOf(v) >= 0) { a.solved = true; a.at = a.clues; }
      else a.tries.push(v);
      save(); render();
    }
    document.getElementById('b-guess').onclick = submit;
    box.onkeydown = function (e) { if (e.key === 'Enter') submit(); };
    var clue = document.getElementById('b-clue');
    if (clue) clue.onclick = function () { a.clues++; save(); render(); };
    box.focus();
  }

  /* ---------------------------------------------------------------- quiz */
  function answered(qi) {
    var q = QUESTIONS[qi], a = S.answers[qi];
    if (q.part === 'drag') return Object.keys(a || {}).length === gapCount(q);
    if (q.part === 'mcq') return a !== null && a !== undefined;
    if (q.part === 'guess') return !!(a && (a.solved || a.tries.length));
    return false;
  }

  function quizHTML() {
    var p = PARTS[S.part], qs = partQs(), local = S.current, qi = absIndex(local), q = QUESTIONS[qi];
    var body = p.key === 'drag' ? dragBodyHTML(q, qi)
      : p.key === 'mcq' ? mcqBodyHTML(q, qi) : guessBodyHTML(q, qi);
    var done = qs.filter(function (_, k) { return answered(absIndex(k)); }).length;

    var dots = '<div class="qdots">';
    qs.forEach(function (_, k) {
      dots += '<button class="qdot' + (answered(absIndex(k)) ? ' done' : '') +
        (k === local ? ' here' : '') + '" data-jump="' + k + '">' + (k + 1) + '</button>';
    });
    dots += '</div>';

    var last = local === qs.length - 1, lastPart = S.part === PARTS.length - 1;
    return '<div class="panel">' +
      '<div class="qhead">' +
      '<span class="partchip">' + p.n + ' &middot; ' + p.title + '</span>' + dots +
      '<span style="flex:1"></span>' +
      '<span class="muted" style="font-weight:bold" id="progress">' + done + ' of ' + qs.length + ' answered</span>' +
      '<button class="btn plain sm" id="b-rewatch">Watch the story again</button>' +
      '</div>' +
      (q.hero ? '<span class="qtag">' + esc(q.hero) + '</span>' : '') +
      '<p class="qtext">' + esc(q.q || 'What is the word?') + '</p>' +
      body +
      '<div class="navrow">' +
      '<button class="btn plain" id="b-prev"' + (local === 0 ? ' disabled' : '') + '>Previous</button>' +
      (last
        ? '<button class="btn ' + (lastPart ? 'hot' : 'go') + '" id="b-nextpart">' +
        (lastPart ? 'Finish and see my score' : 'On to ' + PARTS[S.part + 1].title) + '</button>'
        : '<button class="btn go" id="b-next">Next question</button>') +
      '</div></div>';
  }

  function refreshProgress() {
    var qs = partQs();
    Array.prototype.forEach.call(document.querySelectorAll('[data-jump]'), function (b) {
      b.classList.toggle('done', answered(absIndex(+b.getAttribute('data-jump'))));
    });
    var n = qs.filter(function (_, k) { return answered(absIndex(k)); }).length;
    var el = document.getElementById('progress');
    if (el) el.textContent = n + ' of ' + qs.length + ' answered';
  }

  function wireQuiz() {
    var p = PARTS[S.part], qs = partQs(), local = S.current, qi = absIndex(local), q = QUESTIONS[qi];

    Array.prototype.forEach.call(document.querySelectorAll('[data-jump]'), function (b) {
      b.onclick = function () { S.current = +b.getAttribute('data-jump'); S.picked = null; save(); render(); };
    });
    document.getElementById('b-rewatch').onclick = function () { go('story'); };

    var prev = document.getElementById('b-prev');
    if (prev) prev.onclick = function () { S.current = Math.max(0, local - 1); S.picked = null; save(); render(); };
    var next = document.getElementById('b-next');
    if (next) next.onclick = function () { S.current = local + 1; S.picked = null; save(); render(); };

    var np = document.getElementById('b-nextpart');
    if (np) np.onclick = function () {
      var missing = [];
      qs.forEach(function (_, k) { if (!answered(absIndex(k))) missing.push(k + 1); });
      if (missing.length && !window.confirm(
        'Question ' + missing.join(', ') + ' of this round is still empty. Move on anyway?')) return;
      if (S.part === PARTS.length - 1) { S.finishedAt = new Date().toISOString(); go('done'); }
      else { S.part++; S.current = 0; S.picked = null; go('intro'); }
    };

    if (p.key === 'drag') wireDrag(q, qi);
    if (p.key === 'mcq') {
      Array.prototype.forEach.call(document.querySelectorAll('[data-opt]'), function (b) {
        b.onclick = function () { S.answers[qi] = +b.getAttribute('data-opt'); save(); render(); };
      });
    }
    if (p.key === 'guess') wireGuess(q, qi);
  }

  /* -------------------------------------------------------------- result */
  function grade() {
    var got = 0, byPart = {}, rows = [];
    PARTS.forEach(function (p) { byPart[p.key] = { got: 0, total: 0 }; });

    QUESTIONS.forEach(function (q, i) {
      var a = S.answers[i], b = byPart[q.part];
      if (q.part === 'drag') {
        q.slots.forEach(function (slot) {
          if (!slot.answer) return;
          b.total++;
          var mine = (a || {})[slot.answer], ok = !!(mine && mine.id === slot.answer);
          if (ok) { got++; b.got++; }
          var right = q.tray.filter(function (t) { return t.id === slot.answer; })[0];
          rows.push({
            part: q.part, ok: ok,
            q: q.hero + ' — ' + SLOT_LABEL[slot.role],
            said: mine ? 'You dropped in: ' + mine.t : 'You left it empty',
            right: 'It is: ' + right.t
          });
        });
      } else if (q.part === 'mcq') {
        b.total++;
        var ok2 = a === q.ans;
        if (ok2) { got++; b.got++; }
        rows.push({
          part: q.part, ok: ok2, q: q.q,
          said: (a === null || a === undefined) ? 'You left it blank' : 'You chose: ' + q.opts[a],
          right: 'Answer: ' + q.opts[q.ans] + (q.why ? ' — ' + q.why : '')
        });
      } else {
        b.total++;
        var ok3 = !!(a && a.solved);
        if (ok3) { got++; b.got++; }
        rows.push({
          part: q.part, ok: ok3, q: 'Clue: ' + q.clues[0],
          said: ok3
            ? 'You got it' + (a.at > 1 ? ' after ' + a.at + ' clues' : ' from the first clue')
            : (a && a.tries.length ? 'You tried: ' + a.tries.join(', ') : 'You left it blank'),
          right: 'The word is ' + q.answer
        });
      }
    });
    return { got: got, rows: rows, byPart: byPart };
  }

  function doneHTML() {
    var g = grade();
    var pct = Math.round(g.got / TOTAL * 100);
    var word = pct >= 85 ? 'Sentinel level. Excellent.'
      : pct >= 60 ? 'Good work. Read the red ones again.'
        : 'Watch the story once more, then look at the red ones.';
    var s = '<div class="panel">' +
      '<h1 style="text-align:center">' + esc(S.name || 'Student') + '</h1>' +
      '<p class="muted" style="text-align:center;margin-top:-4px">' +
      (S.cls ? 'Class ' + esc(S.cls) + ' &middot; ' : '') + (S.roll ? 'Roll ' + esc(S.roll) + ' &middot; ' : '') +
      'The Sentinels of Nova City</p>' +
      '<div class="scorebox"><div class="num">' + g.got + ' / ' + TOTAL + '</div>' +
      '<div style="font-weight:bold;font-size:19px;margin-top:6px">' + word + '</div></div>' +
      '<div class="partscores">';
    PARTS.forEach(function (p) {
      var b = g.byPart[p.key];
      s += '<div class="ps"><b>' + p.title + '</b><span>' + b.got + ' / ' + b.total + '</span></div>';
    });
    s += '</div><h2>Every answer</h2><div class="review">';
    PARTS.forEach(function (p) {
      s += '<h3 class="revhead">' + p.title + '</h3>';
      g.rows.filter(function (r) { return r.part === p.key; }).forEach(function (r) {
        s += '<div class="rev ' + (r.ok ? 'ok' : 'no') + '"><span class="mark">' + (r.ok ? '✔' : '✘') + '</span>' +
          '<span><b>' + esc(r.q) + '</b><span class="said">' + esc(r.said) + '</span>' +
          (r.ok ? '' : '<span class="said" style="color:var(--green)"><b>' + esc(r.right) + '</b></span>') +
          '</span></div>';
      });
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
    document.getElementById('b-again').onclick = function () { S.part = 0; S.current = 0; go('quiz'); };
    document.getElementById('b-print').onclick = function () { window.print(); };
    document.getElementById('b-new').onclick = function () {
      if (!window.confirm('Clear this student and start fresh?')) return;
      try { localStorage.removeItem(SAVE_KEY); } catch (e) { }
      window.location.reload();
    };
    document.getElementById('b-save').onclick = function () {
      var g = grade();
      var out = {
        assessment: 'The Sentinels of Nova City - Class 6',
        name: S.name, classSection: S.cls, roll: S.roll,
        startedAt: S.startedAt, finishedAt: S.finishedAt,
        score: g.got, total: TOTAL,
        parts: PARTS.map(function (p) {
          return { part: p.title, got: g.byPart[p.key].got, total: g.byPart[p.key].total };
        }),
        answers: QUESTIONS.map(function (q, i) {
          var a = S.answers[i];
          if (q.part === 'drag') {
            return {
              n: i + 1, part: 'drag', question: q.q,
              slots: q.slots.filter(function (sl) { return sl.answer; }).map(function (sl) {
                var right = q.tray.filter(function (t) { return t.id === sl.answer; })[0];
                return {
                  box: SLOT_LABEL[sl.role],
                  studentPut: (a || {})[sl.answer] ? a[sl.answer].t : null,
                  correct: right.t
                };
              })
            };
          }
          if (q.part === 'mcq') {
            return {
              n: i + 1, part: 'mcq', question: q.q,
              chose: (a === null || a === undefined) ? null : q.opts[a],
              correct: q.opts[q.ans], right: a === q.ans
            };
          }
          return {
            n: i + 1, part: 'guess', word: q.answer,
            solved: !!(a && a.solved), cluesUsed: a ? a.clues : 0,
            wrongTries: a ? a.tries : []
          };
        }),
        review: g.rows
      };
      var safe = (S.name || 'student').replace(/[^A-Za-z0-9]+/g, '-').replace(/^-|-$/g, '');
      var blob = new Blob([JSON.stringify(out, null, 2)], { type: 'application/json' });
      var url = URL.createObjectURL(blob);
      var a2 = document.createElement('a');
      a2.href = url; a2.download = 'sentinels-' + safe + '.json';
      document.body.appendChild(a2); a2.click(); a2.remove();
      setTimeout(function () { URL.revokeObjectURL(url); }, 4000);
    };
  }

  /* -------------------------------------------------------------- render */
  function render() {
    if (S.screen !== 'story') { audio.pause(); cancelAnimationFrame(rafId); }
    if (S.screen === 'welcome') { app.innerHTML = welcomeHTML(); wireWelcome(); }
    else if (S.screen === 'story') { app.innerHTML = storyHTML(); wireStory(); }
    else if (S.screen === 'intro') { app.innerHTML = introHTML(); wireIntro(); }
    else if (S.screen === 'quiz') { app.innerHTML = quizHTML(); wireQuiz(); }
    else { app.innerHTML = doneHTML(); wireDone(); }
  }

  restore();
  render();
})();
