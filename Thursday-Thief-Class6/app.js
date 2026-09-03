/* app.js - The Thursday Thief (Class 6, AI Unit 1: What is Intelligence?).
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
      blurb: 'Every smart move in this story follows the same three steps. Drag the ' +
        'missing pieces into the empty boxes to complete it.'
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

  /* The three steps are deliberately identical every time: the situation you
     are in, the thinking you do about it, and the action that follows.
     Repeating it is what teaches it. */
  var SLOT_LABEL = {
    sit: 'THE SITUATION',
    skill: 'THE THINKING SKILL',
    act: 'THE SMART ACTION'
  };

  var QUESTIONS = [
    /* ------------------------------------------------------ part 1: drag
       Four different thinking skills from Unit 1 - comparing, patterns,
       memory, and safe decisions - poured into one unchanging shape. Every
       tray carries two decoys: one thing that is not a thinking skill at all,
       and one guess made without checking. */
    {
      part: 'drag', hero: 'TANVI &middot; THE LIST',
      q: 'Tanvi wrote down all five missing things and read the list again.',
      slots: [
        { role: 'sit', answer: 'shiny' },
        { role: 'skill', fixed: 'FINDING WHAT THEY ALL HAD IN COMMON' },
        { role: 'act', answer: 'window' }
      ],
      tray: [
        { id: 'shiny', t: 'every missing thing was small and shiny' },
        { id: 'window', t: 'she stopped looking at people and looked at the window' },
        { id: 'new', t: 'Imran was new, so it was probably him' },
        { id: 'box', t: 'the red pencil box still sitting on the shelf' }
      ]
    },
    {
      part: 'drag', hero: 'TANVI &middot; THE DATES',
      q: 'Tanvi checked the date of every single thing that had gone missing.',
      slots: [
        { role: 'sit', answer: 'thurs' },
        { role: 'skill', fixed: 'SPOTTING THE DAY THAT KEPT REPEATING' },
        { role: 'act', answer: 'stay' }
      ],
      tray: [
        { id: 'thurs', t: 'all four of them happened on a Thursday' },
        { id: 'stay', t: 'she asked to stay back in the room next Thursday' },
        { id: 'lucky', t: 'she hoped she would be lucky and pick the right day' },
        { id: 'clock', t: 'the clock on the classroom wall' }
      ]
    },
    {
      part: 'drag', hero: 'TANVI &middot; JUNE',
      q: 'Something about a missing whistle felt familiar to Tanvi.',
      slots: [
        { role: 'sit', fixed: 'a whistle went missing in June and turned up on the roof' },
        { role: 'skill', answer: 'remem' },
        { role: 'act', answer: 'up' }
      ],
      tray: [
        { id: 'remem', t: 'using something she had learned before' },
        { id: 'up', t: 'she looked upward, at the ledge under the water tank' },
        { id: 'sure', t: 'she felt sure about it without checking anything' },
        { id: 'ladder', t: 'the long ladder in the garden shed' }
      ]
    },
    {
      part: 'drag', hero: 'TANVI &middot; THE WET WALL',
      q: 'The nest was three metres up, and the wall below it was wet and green.',
      slots: [
        { role: 'sit', answer: 'wet' },
        { role: 'skill', fixed: 'THINKING ABOUT WHAT IS SAFE' },
        { role: 'act', answer: 'tell' }
      ],
      tray: [
        { id: 'wet', t: 'the ledge was high up with nothing safe to hold on to' },
        { id: 'tell', t: 'she got down off the chair and went to find Miss Rao' },
        { id: 'climb', t: 'she climbed the wall quickly before anyone could see' },
        { id: 'tank', t: 'the water tank on top of the building' }
      ]
    },

    /* ------------------------------------------------------- part 2: mcq
       Three about the story, three about situations that never appear in it,
       so the second half is transfer rather than recall. */
    {
      part: 'mcq',
      q: 'Not one person had seen Imran take anything. So why did the class decide it was him?',
      opts: [
        'Somebody had watched him open the cupboard',
        'He sat nearest the cupboard and he was new, so they decided it without checking',
        'Miss Rao told them it was him',
        'He said that he had done it'
      ], ans: 1,
      why: 'They started from what they thought, not from what anybody had actually noticed. That is a guess wearing the clothes of an answer.'
    },
    {
      part: 'mcq',
      q: 'Tanvi chose to stay back on a Thursday, not on a Monday. What made that a smart choice rather than a lucky one?',
      opts: [
        'Thursday is her favourite day of the week',
        'She had a strong feeling about Thursday',
        'All four of the thefts had already happened on Thursdays',
        'Games period is the nicest lesson to miss'
      ], ans: 2,
      why: 'A smart guess is built on something real. Four Thursdays in a row is a real clue. A feeling is not.'
    },
    {
      part: 'mcq',
      q: 'Tanvi could see the nest from her chair. Why was going to find Miss Rao the intelligent thing to do?',
      opts: [
        'Because teachers like being told things',
        'Because the wall was three metres high and wet, so climbing it was not safe',
        'Because she was not tall enough to reach',
        'Because she wanted somebody else to get the credit'
      ], ans: 1,
      why: 'Working out the answer is only half of it. A choice is only really intelligent when it is also a safe and responsible one.'
    },
    {
      part: 'mcq',
      q: 'You learned to ride a bicycle when you were seven, and you can still ride one today. What kind of memory is that?',
      opts: [
        'Short-term memory, because learning it happened quickly',
        'Long-term memory, because the skill has stayed with you for years',
        'It is not memory at all, it is only your legs',
        'Short-term memory, because you were young at the time'
      ], ans: 1,
      why: 'A page number you hold in your head for ten seconds is short-term. A skill that stays with you for years is long-term.'
    },
    {
      part: 'mcq',
      q: 'A phone can unlock by recognising your face, and a map app can find the fastest route. Which of these can a machine NOT truly do?',
      opts: [
        'Turn a sentence from Hindi into English',
        'Find a pattern hidden in a lot of numbers',
        'Truly understand how a friend who is sad is feeling',
        'Repeat the same task all day without getting tired'
      ], ans: 2,
      why: 'Machines are very good with data, rules and patterns. Understanding what another person actually feels is still a human thing.'
    },
    {
      part: 'mcq',
      q: 'You want to know whether the ground will be too wet for games this evening. Which information actually helps?',
      opts: [
        'Your friend’s favourite colour',
        'How much rain fell this afternoon',
        'Yesterday’s lunch menu',
        'How many books there are in the library'
      ], ans: 1,
      why: 'Useful information is joined to the question. The other three are perfectly true, and completely unconnected to a wet field.'
    },

    /* ----------------------------------------------------- part 3: guess
       Four words from the Unit 1 vocabulary board, one from each corner of
       the unit: noticing, patterns, memory, and giving a reason. */
    {
      part: 'guess', answer: 'OBSERVATION',
      accept: ['observation', 'observations', 'observe', 'observing'],
      clues: [
        'I am what you actually notice — not what you think might be true.',
        'A bent latch. A black feather stuck in the paint. Five missing things that were all shiny. Every one of those was me.',
        'Eleven letters, starting with O. I am what your eyes and ears do before you decide anything.'
      ]
    },
    {
      part: 'guess', answer: 'PATTERN',
      accept: ['pattern', 'patterns', 'the pattern'],
      clues: [
        'I happen again and again in the same way, so anyone who spots me can work out what comes next.',
        'Four Thursdays in a row. I had been sitting in those dates the whole time.',
        'Seven letters, starting with P. 2, 4, 6, 8 is one of me.'
      ]
    },
    {
      part: 'guess', answer: 'MEMORY',
      accept: ['memory', 'memories'],
      clues: [
        'I keep what you learned before, so that you can use it again today.',
        'Tanvi used me when a missing whistle reminded her of a June morning and a school roof.',
        'Six letters, starting with M. Some of me lasts ten seconds. Some of me lasts your whole life.'
      ]
    },
    {
      part: 'guess', answer: 'REASON',
      accept: ['reason', 'reasons', 'reasoning'],
      clues: [
        'An answer is only half an answer until it has me. I am the “because” part.',
        'In assembly, Miss Rao asked Tanvi how she had worked it out. What Tanvi gave her was me.',
        'Six letters, starting with R. “The soil is dry, so the plant needs water” — the second half is me.'
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

  var SAVE_KEY = 'thursday-thief-class6-v1';
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

  /* ------------------------------------------------------- the story clock
     The story runs off narration.mp3 when a readable one is sitting beside
     this file, and off a plain clock when there is not — so the folder works
     either way and a voiceover can be dropped in later without touching a
     line of this. Which one is in charge is settled at the first press of
     Play and then left alone, so the timing never changes mid-story. */
  var media = (function () {
    var useAudio = false, decided = false;
    var playing = false, clockAt = 0, stamp = 0, endedCb = null;

    function audible() { return !audio.error && audio.readyState >= 2; }
    function decide() {
      if (!decided) { useAudio = audible(); decided = true; }
      return useAudio;
    }
    function duration() {
      return (useAudio && audio.duration > 1) ? audio.duration : window.STORY.runtime;
    }
    function time() {
      if (useAudio) return audio.currentTime;
      if (!playing) return clockAt;
      return Math.min(duration(), clockAt + (Date.now() - stamp) / 1000);
    }

    audio.addEventListener('ended', function () { if (endedCb) endedCb(); });

    return {
      audible: audible,
      usingAudio: function () { return decided ? useAudio : audible(); },
      duration: duration,
      time: time,
      paused: function () { return useAudio ? audio.paused : !playing; },
      play: function () {
        decide();
        if (useAudio) return audio.play();
        clockAt = time(); stamp = Date.now(); playing = true;
        return Promise.resolve();
      },
      pause: function () {
        if (useAudio) { audio.pause(); return; }
        clockAt = time(); playing = false;
      },
      seek: function (t) {
        t = Math.max(0, Math.min(duration(), t));
        if (useAudio) { audio.currentTime = t; return; }
        clockAt = t; stamp = Date.now();
      },
      onended: function (fn) { endedCb = fn; },
      /* the clock has no 'ended' event of its own, so the frame loop asks */
      checkEnd: function () {
        if (useAudio || !playing) return;
        if (time() >= duration() - 0.02) {
          clockAt = duration(); playing = false;
          if (endedCb) endedCb();
        }
      }
    };
  })();

  /* -------------------------------------------------------------- welcome */
  function welcomeHTML() {
    return '<div class="panel">' +
      '<div class="body">' +
      '<div class="hero-title">' +
      '<span class="kicker">Class 6 &middot; Unit 1 &middot; What is Intelligence?</span>' +
      '<div class="title-main">The Thursday<br>Thief</div>' +
      '<div class="subtitle">Watch. Then work it out.</div>' +
      '</div>' +
      '<div class="steps">' +
      '<div class="step"><div class="n">1</div><b>Watch the story</b>' +
      '<p>Four minutes. Four Thursdays, one empty cupboard, and a boy everybody blamed.</p></div>' +
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
      '</div>' +
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
  var cues = null, tim = null, startOf = null, rafId = 0, liveScene = null, liveCue = -1;

  function storyHTML() {
    return '<div class="panel">' +
      '<div class="body">' +
      '<div class="row spread" style="margin-bottom:10px;flex:0 0 auto">' +
      '<h2 style="margin:0">The Thursday Thief</h2>' +
      '<span class="muted" style="font-weight:bold" id="mode">Watch it right through. You can replay it later.</span>' +
      '</div>' +
      '<div class="stage" id="stage">' + window.STORY.build() +
      '<div class="caption" id="cap">Press play to begin.</div></div>' +
      '<div class="controls">' +
      '<button class="btn" id="b-play">Play</button>' +
      '<button class="btn plain sm" id="b-restart">Start again</button>' +
      '<div class="bar" id="bar" title="Jump to a moment"><i id="barfill"></i></div>' +
      '<span class="time" id="clock">0:00</span>' +
      '</div>' +
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

  /* The caption track, the scene timing, and the stylesheet of beat delays
     all come from the same LINES, and all three are rebuilt here whenever the
     story screen is opened - because a narration.mp3 dropped in beside this
     file changes the length of everything at once. */
  function buildTiming() {
    var d = media.usingAudio() ? audio.duration : 0;
    cues = window.STORY.track(d);
    tim = window.STORY.timing(d);
    startOf = {};
    var st = document.getElementById('beats'), i, el;
    if (st) st.textContent = window.STORY.timingCSS(d);
    for (i = 0; i < tim.length; i++) {
      startOf[tim[i].scene] = tim[i].at;
      el = document.querySelector('#stage .scene[data-scene="' + tim[i].scene + '"]');
      if (el) el.style.setProperty('--hold', tim[i].hold.toFixed(2) + 's');
    }
  }

  /* tin is how far into this scene the story already is. It is zero when the
     scene arrives in its own time, and some way in when a child has dragged
     the bar - and passing it down as a negative delay is what makes a dragged
     scene look like it was always running instead of starting over. */
  function showScene(name, tin) {
    if (name === liveScene) return;
    liveScene = name;
    var all = document.querySelectorAll('#stage .scene'), i, el, on;
    for (i = 0; i < all.length; i++) {
      el = all[i];
      on = el.getAttribute('data-scene') === name;
      el.classList.remove('live');
      if (on) {
        el.style.setProperty('--tin', '-' + Math.max(0, tin || 0).toFixed(2) + 's');
        void el.getBoundingClientRect();   /* forces the camera move to restart */
        el.classList.add('live');
      }
    }
  }

  /* A caption arrives a word at a time, fast, the way a line is spoken. A
     whole sentence appearing at once is the single most mechanical thing a
     read-along does. textContent still reads back as the plain sentence. */
  function setCaption(text) {
    var cap = document.getElementById('cap');
    if (!cap) return;
    var words = String(text).split(' '), out = '', i;
    var step = Math.min(0.05, 0.5 / Math.max(1, words.length));
    for (i = 0; i < words.length; i++) {
      out += '<span class="w" style="animation-delay:' + (i * step).toFixed(3) + 's">' +
        esc(words[i]) + '</span>' + (i < words.length - 1 ? ' ' : '');
    }
    cap.innerHTML = out;
  }

  /* paint() does the work; loop() keeps it smooth while playing. timeupdate is
     wired to paint() too, so captions keep moving if frames are throttled. */
  function paint() {
    var t = media.time(), d = media.duration();
    if (!cues) buildTiming();
    var i, k = 0;
    for (i = 0; i < cues.length; i++) if (cues[i].at <= t + 0.02) k = i;
    if (k !== liveCue) {
      liveCue = k;
      showScene(cues[k].scene, t - (startOf[cues[k].scene] || 0));
      setCaption(cues[k].text);
    }
    var fill = document.getElementById('barfill');
    if (fill) fill.style.width = (t / d * 100).toFixed(2) + '%';
    var clock = document.getElementById('clock');
    if (clock) clock.textContent = mmss(t) + ' / ' + mmss(d);
  }

  function loop() {
    media.checkEnd();
    paint();
    if (!media.paused()) rafId = requestAnimationFrame(loop);
  }

  function wireStory() {
    cues = null; tim = null; liveScene = null; liveCue = -1;
    var play = document.getElementById('b-play');
    /* Pausing has to stop the pictures too. A paused story whose art keeps
       drifting under a frozen caption looks broken, not alive. */
    function sync() {
      play.textContent = media.paused() ? 'Play' : 'Pause';
      var stage = document.getElementById('stage');
      if (stage) stage.classList.toggle('playing', !media.paused());
    }

    /* tell the child whether to expect a voice or to read along */
    var mode = document.getElementById('mode');
    if (mode && !media.audible()) {
      mode.textContent = 'Read the words as they appear. There is no sound in this one.';
    }

    play.onclick = function () {
      var st = document.getElementById('stage');
      if (st) st.classList.add('started');
      if (media.paused()) {
        media.play().then(sync).catch(function () {
          document.getElementById('cap').textContent =
            'The sound could not be played. Keep narration.mp3 next to this page.';
        });
        cancelAnimationFrame(rafId); rafId = requestAnimationFrame(loop);
      } else { media.pause(); }
      sync();
    };
    document.getElementById('b-restart').onclick = function () {
      media.seek(0); liveCue = -1; liveScene = null; media.play();
      cancelAnimationFrame(rafId); rafId = requestAnimationFrame(loop);
      sync();
    };
    document.getElementById('bar').onclick = function (e) {
      var r = this.getBoundingClientRect();
      media.seek(Math.max(0, Math.min(1, (e.clientX - r.left) / r.width)) * media.duration());
      liveCue = -1; liveScene = null; paint();
    };
    document.getElementById('b-back').onclick = function () { media.pause(); go('welcome'); };
    document.getElementById('b-quiz').onclick = function () {
      media.pause(); S.part = 0; S.current = 0; go('intro');
    };

    media.onended(function () {
      S.watched = true; save();
      play.textContent = 'Play';
      var b = document.getElementById('b-quiz');
      if (b) { b.disabled = false; b.textContent = 'Go to the questions'; }
      setCaption('The end. Now the questions.');
      var stage = document.getElementById('stage');
      if (stage) stage.classList.remove('playing');
    });
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
      demo = '<div class="demo"><p class="democap">This is the shape. It is the same every time.</p>' +
        patternHTML([
          { role: 'sit', fixed: 'the bus reaches the stop at 7:30 every single day, and it is 7:25 now' },
          { role: 'skill', fixed: 'SPOTTING WHAT KEEPS REPEATING' },
          { role: 'act', fixed: 'wait at the stop — it should be here in a few minutes' }
        ], {}, -1) + '</div>';
    }
    return '<div class="panel">' +
      '<div class="body">' +
      '<div class="partbadge">' + p.n + ' of 3</div>' +
      '<h1 class="parttitle">' + p.title + '</h1>' +
      '<p class="big" style="max-width:760px">' + p.blurb + '</p>' +
      demo +
      '<p class="muted big"><b>' + qs.length + ' question' + (qs.length > 1 ? 's' : '') +
      '</b> &middot; ' + marks + ' mark' + (marks > 1 ? 's' : '') + '</p>' +
      '</div>' +
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
        (slot.role === 'skill' && slot.fixed ? ' think' : '') + '"' +
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
    s += '<p class="traylab">Drag a card into an empty box. On a tablet, tap the card then tap the box. ' +
      'Two of these four cards do not belong anywhere — leave them where they are.</p>';
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
      '<div class="body">' +
      '<div class="qhead">' +
      '<span class="partchip">' + p.n + ' &middot; ' + p.title + '</span>' + dots +
      '<span style="flex:1"></span>' +
      '<span class="muted" style="font-weight:bold" id="progress">' + done + ' of ' + qs.length + ' answered</span>' +
      '<button class="btn plain sm" id="b-rewatch">Watch the story again</button>' +
      '</div>' +
      (q.hero ? '<span class="qtag">' + q.hero + '</span>' : '') +
      '<p class="qtext">' + esc(q.q || 'What is the word?') + '</p>' +
      body +
      '</div>' +
      '<div class="navrow">' +
      '<button class="btn plain" id="b-prev"' + (local === 0 ? ' disabled' : '') + '>Previous</button>' +
      (last
        ? '<button class="btn ' + (lastPart ? 'hot' : 'go') + '" id="b-nextpart">' +
        (lastPart ? 'Finish and see my score' : 'On to ' + PARTS[S.part + 1].title) + '</button>'
        : '<button class="btn go" id="b-next">Next question</button>') +
      '</div></div>';
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
  function plain(s) { return String(s).replace(/&middot;/g, '-').replace(/&amp;/g, '&'); }

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
            q: plain(q.hero) + ' — ' + SLOT_LABEL[slot.role],
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
    var word = pct >= 85 ? 'Detective level. Excellent.'
      : pct >= 60 ? 'Good work. Read the red ones again.'
        : 'Watch the story once more, then look at the red ones.';
    var s = '<div class="panel">' +
      '<h1 style="text-align:center">' + esc(S.name || 'Student') + '</h1>' +
      '<p class="muted" style="text-align:center;margin-top:-4px">' +
      (S.cls ? 'Class ' + esc(S.cls) + ' &middot; ' : '') + (S.roll ? 'Roll ' + esc(S.roll) + ' &middot; ' : '') +
      'The Thursday Thief</p>' +
      '<div class="scorebox"><div class="num">' + g.got + ' / ' + TOTAL + '</div>' +
      '<div style="font-weight:bold;font-size:19px;margin-top:6px">' + word + '</div></div>' +
      '<div class="partscores">';
    PARTS.forEach(function (p) {
      var b = g.byPart[p.key];
      s += '<div class="ps"><b>' + p.title + '</b><span>' + b.got + ' / ' + b.total + '</span></div>';
    });
    s += '</div><div class="body">' +
      '<div class="revtop"><h2 style="margin:0">Every answer</h2>' +
      '<span class="muted scrollhint">' + g.rows.length +
      ' answers &middot; scroll this list</span></div>' +
      '<div class="review">';
    PARTS.forEach(function (p) {
      s += '<h3 class="revhead">' + p.title + '</h3>';
      g.rows.filter(function (r) { return r.part === p.key; }).forEach(function (r) {
        s += '<div class="rev ' + (r.ok ? 'ok' : 'no') + '"><span class="mark">' + (r.ok ? '✔' : '✘') + '</span>' +
          '<span><b>' + esc(r.q) + '</b><span class="said">' + esc(r.said) + '</span>' +
          (r.ok ? '' : '<span class="said" style="color:var(--green)"><b>' + esc(r.right) + '</b></span>') +
          '</span></div>';
      });
    });
    s += '</div></div><div class="navrow noprint">' +
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
        assessment: 'The Thursday Thief - Class 6 - Unit 1: What is Intelligence?',
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
      a2.href = url; a2.download = 'thursday-thief-' + safe + '.json';
      document.body.appendChild(a2); a2.click(); a2.remove();
      setTimeout(function () { URL.revokeObjectURL(url); }, 4000);
    };
  }

  /* -------------------------------------------------------------- render */
  function render() {
    if (S.screen !== 'story') { media.pause(); cancelAnimationFrame(rafId); }
    if (S.screen === 'welcome') { app.innerHTML = welcomeHTML(); wireWelcome(); }
    else if (S.screen === 'story') { app.innerHTML = storyHTML(); wireStory(); }
    else if (S.screen === 'intro') { app.innerHTML = introHTML(); wireIntro(); }
    else if (S.screen === 'quiz') { app.innerHTML = quizHTML(); wireQuiz(); }
    else { app.innerHTML = doneHTML(); wireDone(); }
  }

  restore();
  render();
})();
