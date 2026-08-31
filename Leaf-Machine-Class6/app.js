/* app.js - "The Leaf Machine", a Class 6 assessment on Unit 2 (What is AI?).

   Shape:  welcome -> the story -> Round 1 (draw) -> Round 2 (picture word)
           -> Round 3 (say it) -> result.

   Everything runs in the browser. Nothing is uploaded anywhere. Answers live in
   localStorage under one key, so the SAME BROWSER PROFILE resumes the SAME
   child - there is a "New student" button, and a fresh profile per child is
   safer in a shared lab.

   Marks: Round 1  4 x 3 = 12
          Round 2  6 x 2 = 12
          Round 3  8 x 2 = 16
          total          = 40

   The Round 1 answers are NOT written here. They are read out of STORY.icons,
   the same eight-row strings the machine's screen draws in the video. One
   source of truth: change the artwork and the answer changes with it.        */

(function () {
  'use strict';

  var KEY = 'leafmachine.class6.v1';
  var app = document.getElementById('app');

  /* ===================================================================
     QUESTIONS
     =================================================================== */

  /* Round 1 - reproduce the sixty-four dots.
     Two of these are plain recall. Two (d2 and d3) can only be answered by
     a child who understood WHY the box was wrong, which is the whole point
     of the story - so they are the ones worth the argument. */
  var R1 = [
    {
      id: 'd1', icon: 'q',
      ask: 'Meher switched the box on for the very first time, before it had seen a single ' +
        'photograph. One shape came up on the sixty-four dots. Draw that shape.'
    },
    {
      id: 'd2', icon: 'neem',
      ask: 'On Wednesday the head judge put her own tulsi plant, in a red clay pot, in front ' +
        'of the glass eye. Draw the shape the dots showed.'
    },
    {
      id: 'd3', icon: 'peepal',
      ask: 'On Friday the judge held up a plastic leaf she had bought in a shop. Draw the ' +
        'shape the dots showed for it.'
    },
    {
      id: 'd4', icon: 'tick',
      ask: 'On Friday, after Devu\'s two hundred and forty pictures had gone in, the box got ' +
        'the curry leaf right. Draw what the dots put up.'
    }
  ];

  /* Round 3 - say the answer out loud.
     `accept` is matched against the transcript. Keep every accepted phrase
     something an eleven year old would actually say. */
  var R3 = [
    {
      q: 'What do we call the information that an AI system learns from?',
      accept: ['data'],
      hint: 'It begins with D. The box learned from photographs - photographs were its what?'
    },
    {
      q: 'AI looks for something that repeats in the information. What is that called?',
      accept: ['pattern', 'patterns'],
      hint: 'It begins with P.'
    },
    {
      q: 'A smart guess that AI makes from data is called a what?',
      accept: ['prediction', 'predictions'],
      hint: 'It begins with P and it is a guess, not a certainty.'
    },
    {
      q: 'Which AI domain works with images and videos?',
      accept: ['computer vision', 'vision'],
      hint: 'Two words. The first one is "computer".'
    },
    {
      q: 'Which AI domain works with human language - chat messages, questions and voice commands?',
      accept: ['natural language processing', 'nlp', 'n l p', 'natural language'],
      hint: 'Three words. People usually shorten it to N L P.'
    },
    {
      q: 'A washing machine runs a fixed thirty minute wash after you choose a mode. ' +
        'Is that AI, or is that automation?',
      accept: ['automation', 'automatic'],
      hint: 'It only follows fixed instructions. It never learns anything.'
    },
    {
      q: 'Name one thing you should never share with an app you do not know.',
      accept: ['password', 'phone number', 'home address', 'address', 'otp',
        'one time password', 'bank', 'location', 'school id', 'date of birth',
        'personal photo', 'personal photos'],
      hint: 'Think of anything that could identify you, reach you, or open something of yours.'
    },
    {
      q: 'An AI app gives you medical advice about a fever. Should you trust it straight away, ' +
        'or should you check it with a doctor?',
      accept: ['check', 'checked', 'doctor', 'verify', 'ask a doctor', 'ask an adult'],
      hint: 'Remember the four words Meher wrote on the card.'
    }
  ];

  var WORDS = window.PICTURES.words;
  var PICS = window.PICTURES.pics;

  var MAX1 = R1.length * 3, MAX2 = WORDS.length * 2, MAX3 = R3.length * 2;
  var MAXALL = MAX1 + MAX2 + MAX3;

  /* ===================================================================
     STATE
     =================================================================== */

  function fresh() {
    return {
      name: '',
      started: '',
      watched: false,
      screen: 'welcome',
      idx: 0,
      draw: {},   /* id -> {cells:[64 bools], done, checks, hinted, mark} */
      word: {},   /* i  -> {done, hints, mark, tries} */
      say: {}     /* i  -> {done, heard, mark, mode, tries} */
    };
  }

  var S = load() || fresh();

  function load() {
    try {
      var raw = localStorage.getItem(KEY);
      if (!raw) return null;
      var o = JSON.parse(raw);
      return (o && typeof o === 'object' && o.draw && o.word && o.say) ? o : null;
    } catch (e) { return null; }
  }
  function save() {
    try { localStorage.setItem(KEY, JSON.stringify(S)); } catch (e) { /* private mode */ }
  }

  /* ===================================================================
     SMALL HELPERS
     =================================================================== */

  function esc(s) {
    return String(s === undefined || s === null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }
  function $(id) { return document.getElementById(id); }
  function on(id, ev, fn) { var n = $(id); if (n) n.addEventListener(ev, fn); }

  /* the eight strings of an icon -> a flat array of 64 booleans */
  function patCells(key) {
    var pat = window.STORY.icons[key], out = [], r, c;
    for (r = 0; r < 8; r++) for (c = 0; c < 8; c++) out.push(pat[r].charAt(c) === '#');
    return out;
  }
  function blankCells() {
    var a = [], i; for (i = 0; i < 64; i++) a.push(false); return a;
  }
  function cellsWrong(mine, target) {
    var n = 0, i; for (i = 0; i < 64; i++) if (!!mine[i] !== !!target[i]) n++; return n;
  }

  /* normalise a spoken or typed answer down to bare words */
  function norm(s) {
    return (' ' + String(s || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ') + ' ')
      .replace(/\s+/g, ' ');
  }
  function lev(a, b) {
    var m = a.length, n = b.length, i, j, prev, tmp, row = [];
    for (j = 0; j <= n; j++) row[j] = j;
    for (i = 1; i <= m; i++) {
      prev = row[0]; row[0] = i;
      for (j = 1; j <= n; j++) {
        tmp = row[j];
        row[j] = Math.min(row[j] + 1, row[j - 1] + 1,
          prev + (a.charAt(i - 1) === b.charAt(j - 1) ? 0 : 1));
        prev = tmp;
      }
    }
    return row[n];
  }
  /* Contains-match first. Then a near-miss allowance for LONG single words
     only - the recogniser mangles "prediction" far more often than "data",
     and a loose match on a four letter word would accept "date" for "data". */
  function answered(said, accepts) {
    var n = norm(said), i, j, a, toks;
    for (i = 0; i < accepts.length; i++) {
      a = norm(accepts[i]).trim();
      if (a && n.indexOf(' ' + a + ' ') >= 0) return true;
    }
    toks = n.trim().split(' ');
    for (i = 0; i < accepts.length; i++) {
      a = norm(accepts[i]).trim();
      if (!a || a.indexOf(' ') >= 0 || a.length < 5) continue;
      for (j = 0; j < toks.length; j++) {
        if (toks[j].length >= 4 && lev(toks[j], a) <= (a.length >= 8 ? 2 : 1)) return true;
      }
    }
    return false;
  }

  /* ===================================================================
     VOICE (out) - the narrator, and reading a question aloud
     =================================================================== */

  var VOICE = {
    ok: typeof window.speechSynthesis !== 'undefined' &&
      typeof window.SpeechSynthesisUtterance !== 'undefined',
    on: true,
    voice: null,
    keep: null
  };

  function pickVoice() {
    if (!VOICE.ok) return null;
    var vs = window.speechSynthesis.getVoices() || [], i, v;
    /* prefer an Indian English voice, then any English one, then anything */
    for (i = 0; i < vs.length; i++) if (/en[-_]IN/i.test(vs[i].lang)) return vs[i];
    for (i = 0; i < vs.length; i++) if (/en[-_]GB/i.test(vs[i].lang)) return vs[i];
    for (i = 0; i < vs.length; i++) if (/^en/i.test(vs[i].lang)) return vs[i];
    v = vs[0]; return v || null;
  }
  if (VOICE.ok) {
    VOICE.voice = pickVoice();
    window.speechSynthesis.onvoiceschanged = function () {
      if (!VOICE.voice) VOICE.voice = pickVoice();
    };
  }

  function speak(text, done) {
    if (!VOICE.ok || !VOICE.on) { if (done) setTimeout(done, 60); return null; }
    stopSpeaking();
    var u = new window.SpeechSynthesisUtterance(text);
    if (VOICE.voice) u.voice = VOICE.voice;
    u.rate = 0.94; u.pitch = 1.0; u.volume = 1;
    var finished = false;
    function end() { if (finished) return; finished = true; clearKeep(); if (done) done(); }
    u.onend = end;
    u.onerror = end;
    window.speechSynthesis.speak(u);
    /* Chrome stops speaking after about fifteen seconds unless it is poked. */
    clearKeep();
    VOICE.keep = setInterval(function () {
      if (!window.speechSynthesis.speaking) { clearKeep(); return; }
      window.speechSynthesis.pause(); window.speechSynthesis.resume();
    }, 5000);
    return u;
  }
  function clearKeep() { if (VOICE.keep) { clearInterval(VOICE.keep); VOICE.keep = null; } }
  function stopSpeaking() {
    clearKeep();
    if (VOICE.ok) { try { window.speechSynthesis.cancel(); } catch (e) { } }
  }

  /* ===================================================================
     VOICE (in) - the microphone for Round 3
     =================================================================== */

  var SR = window.SpeechRecognition || window.webkitSpeechRecognition || null;
  var MIC_OK = !!SR && (window.isSecureContext !== false);

  /* Chrome reports a file:// page as a SECURE CONTEXT - isSecureContext is
     true there - so a secure-context test alone will happily show the
     microphone button on a copy opened off a desktop, where the permission
     prompt is usually refused and the recogniser cannot reach the network.
     Test the protocol itself. We still do not hide the button, because on
     some machines it does work; we warn instead, and the typed answer beside
     it is worth exactly the same marks. */
  var FILE_MODE = (window.location.protocol === 'file:');
  var rec = null, recLive = false;

  function micReason() {
    if (!SR) return 'This browser does not have speech recognition. Chrome or Edge does.';
    return '';
  }
  function micCaution() {
    if (!MIC_OK) return '';
    if (FILE_MODE) {
      return 'This page was opened straight from a file on the computer. The microphone ' +
        'often will not work that way. If it fails, just type your answer - it is worth ' +
        'the same 2 marks.';
    }
    return '';
  }

  /* ===================================================================
     SCREENS
     =================================================================== */

  function go(screen, idx) {
    stopSpeaking();
    stopMic();
    S.screen = screen;
    if (idx !== undefined) S.idx = idx;
    save();
    render();
    window.scrollTo(0, 0);
  }

  function render() {
    switch (S.screen) {
      case 'story': return viewStory();
      case 'r1intro': return viewIntro(1);
      case 'r1': return viewDraw();
      case 'r2intro': return viewIntro(2);
      case 'r2': return viewWord();
      case 'r3intro': return viewIntro(3);
      case 'r3': return viewSay();
      case 'result': return viewResult();
      default: return viewWelcome();
    }
  }

  /* ------------------------------------------------------------ welcome */
  function viewWelcome() {
    app.innerHTML =
      '<div class="panel">' +
      '<div class="hero-title">' +
      '<span class="kicker">Class 6 &middot; Unit 2 &middot; What is AI?</span>' +
      '<div class="title-main">The Leaf<br>Machine</div>' +
      '<div class="subtitle">A story, and then three rounds</div>' +
      '</div>' +
      '<div class="steps">' +
      '<div class="step"><div class="n">1</div><h3>Watch</h3>' +
      '<p>A three minute story about a box with one glass eye. Watch it right to the end. ' +
      'You can watch it again as many times as you like.</p></div>' +
      '<div class="step"><div class="n">2</div><h3>Draw</h3>' +
      '<p>The box speaks with sixty-four dots. You will be asked to draw exactly what its ' +
      'screen showed.</p></div>' +
      '<div class="step"><div class="n">3</div><h3>Guess</h3>' +
      '<p>Six words hidden in pictures. Take the first letter of each picture.</p></div>' +
      '<div class="step"><div class="n">4</div><h3>Speak</h3>' +
      '<p>Eight questions. Turn your microphone on and say the answer out loud.</p></div>' +
      '</div>' +
      '<label for="nm">Write your name</label>' +
      '<input type="text" id="nm" maxlength="60" placeholder="Your name and section" value="' +
      esc(S.name) + '">' +
      '<p class="warn" id="warn"></p>' +
      '<p class="muted" style="font-size:15px">Your answers stay on this computer. Nothing is ' +
      'sent anywhere. If two children share this computer, press <b>New student</b> on the ' +
      'last page before the next one starts.</p>' +
      '<div class="navrow">' +
      '<button class="btn plain" id="reset">New student</button>' +
      '<button class="btn go" id="start">Start the story</button>' +
      '</div></div>';

    on('start', 'click', function () {
      var v = $('nm').value.trim();
      if (v.length < 2) { $('warn').textContent = 'Please write your name first.'; return; }
      S.name = v;
      if (!S.started) S.started = new Date().toISOString();
      go('story');
    });
    on('reset', 'click', function () {
      if (window.confirm('Clear this student\'s answers and start again?')) {
        S = fresh(); save(); render();
      }
    });
    var nm = $('nm');
    if (nm) nm.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') { e.preventDefault(); $('start').click(); }
    });
  }

  /* -------------------------------------------------------------- story */
  var play = { i: 0, running: false, timer: null, ended: false };

  function viewStory() {
    var sc = window.STORY.scenes, i, svgs = '';
    for (i = 0; i < sc.length; i++) {
      svgs += '<svg class="scene" viewBox="0 0 ' + window.STORY.w + ' ' + window.STORY.h +
        '" preserveAspectRatio="xMidYMid slice"><style>' + window.STORY.css + '</style>' +
        sc[i].art + '</svg>';
    }
    app.innerHTML =
      '<div class="panel">' +
      '<div class="row spread" style="margin-bottom:14px">' +
      '<h2 style="margin:0">The Leaf Machine</h2>' +
      '<span class="qtag">' + esc(S.name) + '</span>' +
      '</div>' +
      '<div class="stage" id="stage">' + svgs +
      '<div class="caption" id="cap"></div></div>' +
      '<div class="controls noprint">' +
      '<button class="btn sm go" id="pp">Play</button>' +
      '<button class="btn sm plain" id="back">Back</button>' +
      '<button class="btn sm plain" id="fwd">Next</button>' +
      '<div class="bar"><i id="fill"></i></div>' +
      '<span class="time" id="tno">1 / ' + sc.length + '</span>' +
      '<button class="btn sm plain" id="vox">' + (VOICE.on ? 'Voice on' : 'Voice off') +
      '</button>' +
      '</div>' +
      (VOICE.ok ? '' : '<p class="muted" style="font-size:15px;margin-top:10px">This browser ' +
        'has no speaking voice, so read the words under the picture.</p>') +
      '<p class="okline" id="doneline">' +
      (S.watched ? 'You have watched the whole story. You can start the rounds.' : '') + '</p>' +
      '<div class="navrow">' +
      '<button class="btn plain" id="home">Back to the start</button>' +
      '<button class="btn go" id="next" ' + (S.watched ? '' : 'disabled') +
      '>Go to Round 1</button>' +
      '</div></div>';

    play.i = 0; play.running = false; play.ended = false;
    showScene(0);

    on('pp', 'click', function () { play.running ? pauseStory() : playStory(); });
    on('back', 'click', function () { stepTo(play.i - 1); });
    on('fwd', 'click', function () { stepTo(play.i + 1); });
    on('vox', 'click', function () {
      VOICE.on = !VOICE.on;
      $('vox').textContent = VOICE.on ? 'Voice on' : 'Voice off';
      stopSpeaking();
      if (play.running) { pauseStory(); playStory(); }
    });
    on('home', 'click', function () { stopStory(); go('welcome'); });
    on('next', 'click', function () { stopStory(); go('r1intro'); });

    /* start it straight away - the click on "Start the story" was the gesture
       browsers want before they will let a page speak */
    playStory();
  }

  function showScene(i) {
    var sc = window.STORY.scenes, nodes = app.querySelectorAll('.scene'), k;
    play.i = Math.max(0, Math.min(sc.length - 1, i));
    for (k = 0; k < nodes.length; k++) nodes[k].classList.toggle('live', k === play.i);
    if ($('cap')) $('cap').textContent = sc[play.i].line;
    if ($('tno')) $('tno').textContent = (play.i + 1) + ' / ' + sc.length;
    if ($('fill')) $('fill').style.width = ((play.i + 1) / sc.length * 100) + '%';
  }

  function clearTimer() { if (play.timer) { clearTimeout(play.timer); play.timer = null; } }

  function playStory() {
    play.running = true;
    if ($('pp')) $('pp').textContent = 'Pause';
    runScene();
  }
  function pauseStory() {
    play.running = false;
    clearTimer(); stopSpeaking();
    if ($('pp')) $('pp').textContent = 'Play';
  }
  function stopStory() { play.running = false; clearTimer(); stopSpeaking(); }

  function stepTo(i) {
    var sc = window.STORY.scenes;
    if (i < 0 || i >= sc.length) return;
    clearTimer(); stopSpeaking();
    showScene(i);
    if (play.running) runScene();
  }

  /* Speak the line, and move on when the SPEECH ends - not when a stopwatch
     says so. That is what keeps the captions and the voice together however
     fast or slow the browser's voice happens to be. */
  function runScene() {
    var sc = window.STORY.scenes, line = sc[play.i], mine = play.i;
    clearTimer();
    function advance() {
      if (!play.running || play.i !== mine) return;
      if (play.i >= sc.length - 1) { finishStory(); return; }
      showScene(play.i + 1);
      runScene();
    }
    if (VOICE.ok && VOICE.on) {
      speak(line.line, function () {
        if (!play.running || play.i !== mine) return;
        play.timer = setTimeout(advance, 520);
      });
      /* a safety net: if the voice never fires onend, do not hang forever */
      play.timer = setTimeout(function () {
        if (play.running && play.i === mine) { stopSpeaking(); advance(); }
      }, line.dur + 9000);
    } else {
      play.timer = setTimeout(advance, line.dur);
    }
  }

  function finishStory() {
    play.running = false;
    play.ended = true;
    if ($('pp')) $('pp').textContent = 'Play';
    if (!S.watched) { S.watched = true; save(); }
    if ($('next')) $('next').disabled = false;
    if ($('doneline')) {
      $('doneline').textContent = 'You have watched the whole story. You can start the rounds.';
    }
  }

  /* --------------------------------------------------------- round intro */
  function viewIntro(n) {
    var body, demo = '';
    if (n === 1) {
      body = '<p class="big">The box only had <b>sixty-four dots</b> to speak with. ' +
        'In this round you draw exactly what its screen showed.</p>' +
        '<p class="big">Drag across the squares to fill them in. Drag across a filled ' +
        'square to rub it out. Press <b>Check</b> when you think it is right. ' +
        'You can check as many times as you like.</p>' +
        '<p class="big"><b>Every square must match.</b> Get it right the first time you ' +
        'check for 3 marks, right after more tries for 2. If you ask for the hint you ' +
        'can still score 1.</p>';
      demo = '<div class="demo"><p class="democap">This is the screen you will draw on.</p>' +
        '<div class="screenbox" style="display:inline-block">' +
        gridHTML('demo', blankCells(), null) + '</div></div>';
    } else if (n === 2) {
      body = '<p class="big">Each picture gives you <b>one letter</b> - the letter its name ' +
        'starts with.</p>' +
        '<p class="big">A picture of a <b>D</b>og, an <b>A</b>pple, a <b>T</b>ap and an ' +
        '<b>A</b>xe spells <b>DATA</b>.</p>' +
        '<p class="big">Type the whole word. 2 marks each. If you ask for a hint - which ' +
        'tells you what one picture is - the word is worth 1.</p>';
    } else {
      body = '<p class="big">Eight questions about everything in Unit 2. ' +
        'Press the button, let the browser use your microphone, and <b>say the answer out ' +
        'loud</b>.</p>' +
        '<p class="big">2 marks each. There is no penalty for trying again.</p>' +
        (MIC_OK
          ? '<p class="big">Your browser will ask permission for the microphone the first ' +
          'time. Say <b>Allow</b>.</p>'
          : '<p class="warn" style="font-size:19px">' + esc(micReason()) + '</p>') +
        (micCaution() ? '<p class="warn" style="font-size:18px">' + esc(micCaution()) + '</p>' : '') +
        '<p class="muted">You can always type an answer instead - it is worth the same.</p>';
    }
    app.innerHTML =
      '<div class="panel">' +
      '<span class="partbadge">Round ' + n + ' of 3</span>' +
      '<h1 class="parttitle">' +
      (n === 1 ? 'Draw the dots' : n === 2 ? 'The picture word' : 'Say it out loud') +
      '</h1>' + body + demo +
      '<div class="navrow">' +
      '<button class="btn plain" id="bk">' + (n === 1 ? 'Watch the story again' : 'Back') +
      '</button>' +
      '<button class="btn go" id="fw">Start Round ' + n + '</button>' +
      '</div></div>';

    on('fw', 'click', function () { go(n === 1 ? 'r1' : n === 2 ? 'r2' : 'r3', 0); });
    on('bk', 'click', function () {
      go(n === 1 ? 'story' : n === 2 ? 'r1' : 'r2', n === 1 ? undefined : 0);
    });
  }

  /* ------------------------------------------------------------- chrome */
  function head(part, total, idx, doneFn, jump) {
    var i, dots = '';
    for (i = 0; i < total; i++) {
      dots += '<button class="qdot' + (doneFn(i) === 2 ? ' done' : doneFn(i) === 1 ? ' part' : '') +
        (i === idx ? ' here' : '') + '" data-j="' + i + '">' + (i + 1) + '</button>';
    }
    setTimeout(function () {
      var ns = app.querySelectorAll('.qdot'), k;
      for (k = 0; k < ns.length; k++) {
        ns[k].addEventListener('click', function (e) {
          jump(parseInt(e.currentTarget.getAttribute('data-j'), 10));
        });
      }
    }, 0);
    return '<div class="qhead"><span class="partchip">Round ' + part + '</span>' +
      '<div class="qdots">' + dots + '</div></div>';
  }

  function gridHTML(id, cells, ghost) {
    var out = '<div class="pxgrid" id="' + id + '">', i;
    for (i = 0; i < 64; i++) {
      out += '<button type="button" class="pxcell' + (cells[i] ? ' on' : '') +
        (ghost && ghost[i] && !cells[i] ? ' ghost' : '') +
        '" data-i="' + i + '" aria-label="square ' + (i + 1) + '"></button>';
    }
    return out + '</div>';
  }

  /* ------------------------------------------------------ round 1: draw */
  function drawRec(id) {
    if (!S.draw[id]) S.draw[id] = { cells: blankCells(), done: false, checks: 0, hinted: false, mark: 0 };
    if (!S.draw[id].cells || S.draw[id].cells.length !== 64) S.draw[id].cells = blankCells();
    return S.draw[id];
  }

  function viewDraw() {
    var i = Math.max(0, Math.min(R1.length - 1, S.idx));
    var q = R1[i], rec2 = drawRec(q.id);
    var target = patCells(q.icon);

    app.innerHTML =
      '<div class="panel">' +
      head(1, R1.length, i, function (k) {
        var r = S.draw[R1[k].id]; return r && r.done ? 2 : (r && r.checks ? 1 : 0);
      }, function (k) { go('r1', k); }) +
      '<span class="qtag">Question ' + (i + 1) + ' of ' + R1.length + ' &middot; 3 marks</span>' +
      '<p class="qtext">' + esc(q.ask) + '</p>' +
      '<div class="drawwrap">' +
      '<div class="screenbox">' + gridHTML('grid', rec2.cells, rec2.hinted ? target : null) + '</div>' +
      '<div class="drawside">' +
      '<p class="countline" id="cl">' +
      (rec2.done ? 'Correct. ' + rec2.mark + ' out of 3.'
        : rec2.checks ? 'Not yet - press Check again when you have changed it.'
          : 'Drag across the squares to fill them in.') + '</p>' +
      '<div class="drawtools">' +
      '<button class="btn sm go" id="chk">Check</button>' +
      '<button class="btn sm plain" id="clr">Clear</button>' +
      '<button class="btn sm cool" id="hint"' + (rec2.hinted || rec2.done ? ' disabled' : '') +
      '>Show me a hint</button>' +
      '</div>' +
      '<p class="muted" style="font-size:15px">' +
      (rec2.hinted ? 'The hint is showing behind your squares. This one is now worth 1 mark.'
        : 'A hint puts the right shape faintly behind the screen. The question drops to 1 mark.') +
      '</p>' +
      '<button class="btn sm plain" id="rewatch">Watch the story again</button>' +
      '</div></div>' +
      '<div class="navrow">' +
      '<button class="btn plain" id="prev">' + (i === 0 ? 'Round 1 rules' : 'Previous') + '</button>' +
      '<button class="btn go" id="nxt">' +
      (i === R1.length - 1 ? 'Finish Round 1' : 'Next question') + '</button>' +
      '</div></div>';

    wireGrid('grid', rec2, rec2.hinted ? target : null, function () { save(); });

    on('chk', 'click', function () {
      var wrong = cellsWrong(rec2.cells, target);
      rec2.checks++;
      if (wrong === 0) {
        rec2.done = true;
        rec2.mark = rec2.hinted ? 1 : (rec2.checks <= 1 ? 3 : 2);
        $('cl').textContent = 'Exactly right. ' + rec2.mark + ' out of 3.';
        $('cl').style.color = '#2f9e44';
        $('hint').disabled = true;
      } else {
        rec2.done = false; rec2.mark = 0;
        $('cl').textContent = wrong === 1
          ? 'One square is still wrong.'
          : wrong + ' squares are still wrong.';
        $('cl').style.color = '#e03131';
      }
      save();
      refreshDots(1);
    });
    on('clr', 'click', function () {
      rec2.cells = blankCells();
      rec2.done = false; rec2.mark = 0;
      save(); go('r1', i);
    });
    on('hint', 'click', function () {
      rec2.hinted = true; save(); go('r1', i);
    });
    on('rewatch', 'click', function () { go('story'); });
    on('prev', 'click', function () { i === 0 ? go('r1intro') : go('r1', i - 1); });
    on('nxt', 'click', function () {
      i === R1.length - 1 ? go('r2intro') : go('r1', i + 1);
    });
  }

  /* pointer painting: press decides paint-or-rub, then drag carries it along */
  function wireGrid(id, rec2, ghost, changed) {
    var grid = $(id);
    if (!grid) return;
    var painting = false, paintTo = true, suppressClick = false;

    function cellAt(x, y) {
      var n = document.elementFromPoint(x, y);
      if (!n || !n.classList || !n.classList.contains('pxcell')) return null;
      return grid.contains(n) ? n : null;
    }
    function apply(n) {
      if (!n) return;
      var k = parseInt(n.getAttribute('data-i'), 10);
      if (!!rec2.cells[k] === paintTo) return;
      rec2.cells[k] = paintTo;
      n.classList.toggle('on', paintTo);
      if (paintTo) n.classList.remove('ghost');
      else if (ghost) {
        /* put the faint hint back underneath, but only where the hint
           actually has a lit square - not under every square rubbed out */
        n.classList.toggle('ghost', !!ghost[k]);
      }
      if (changed) changed();
    }

    grid.addEventListener('pointerdown', function (e) {
      var n = cellAt(e.clientX, e.clientY);
      if (!n) return;
      e.preventDefault();
      suppressClick = true;
      painting = true;
      paintTo = !rec2.cells[parseInt(n.getAttribute('data-i'), 10)];
      try { grid.setPointerCapture(e.pointerId); } catch (err) { }
      apply(n);
    });
    grid.addEventListener('pointermove', function (e) {
      if (!painting) return;
      apply(cellAt(e.clientX, e.clientY));
    });
    function stop() { painting = false; }
    grid.addEventListener('pointerup', stop);
    grid.addEventListener('pointercancel', stop);
    window.addEventListener('pointerup', stop);

    /* keyboard: Enter or Space on a focused square. The pointer path fires a
       click too, so the first one after a press is swallowed. */
    grid.addEventListener('click', function (e) {
      /* Clear the flag FIRST, whatever the target is. A drag that starts on
         one square and ends on another fires its click on the grid itself,
         not on a square - and leaving the flag standing would swallow the
         next real keyboard press instead. */
      var swallow = suppressClick;
      suppressClick = false;
      if (swallow) return;
      var n = e.target;
      if (!n.classList || !n.classList.contains('pxcell')) return;
      var k = parseInt(n.getAttribute('data-i'), 10);
      paintTo = !rec2.cells[k];
      apply(n);
    });
  }

  function refreshDots(part) {
    var ns = app.querySelectorAll('.qdot'), k, r;
    for (k = 0; k < ns.length; k++) {
      if (part === 1) r = S.draw[R1[k].id];
      else if (part === 2) r = S.word[k];
      else r = S.say[k];
      ns[k].classList.toggle('done', !!(r && r.done));
      ns[k].classList.toggle('part', !!(r && !r.done && (r.checks || r.tries)));
    }
  }

  /* ----------------------------------------------- round 2: picture word */
  function wordRec(i) {
    if (!S.word[i]) S.word[i] = { done: false, hints: 0, mark: 0, tries: 0, said: '' };
    return S.word[i];
  }

  function viewWord() {
    var i = Math.max(0, Math.min(WORDS.length - 1, S.idx));
    var w = WORDS[i], rec2 = wordRec(i), k, pic;

    var strip = '<div class="rebus">';
    for (k = 0; k < w.pics.length; k++) {
      pic = PICS[w.pics[k]];
      strip += '<div class="pic"><span class="pn">' + (k + 1) + '</span>' + pic.svg +
        (k < rec2.hints ? '<span class="named">' + esc(pic.name) + '</span>' : '') + '</div>';
    }
    strip += '</div>';

    var blanks = '<div class="blanks">';
    for (k = 0; k < w.word.length; k++) {
      blanks += '<div class="blank' + (rec2.done ? ' got' : '') + '">' +
        (rec2.done ? esc(w.word.charAt(k)) : '') + '</div>';
    }
    blanks += '</div>';

    app.innerHTML =
      '<div class="panel">' +
      head(2, WORDS.length, i, function (j) {
        var r = S.word[j]; return r && r.done ? 2 : (r && r.tries ? 1 : 0);
      }, function (j) { go('r2', j); }) +
      '<span class="qtag">Word ' + (i + 1) + ' of ' + WORDS.length + ' &middot; 2 marks</span>' +
      '<p class="qtext">Take the first letter of each picture. What word do they spell?</p>' +
      strip + blanks +
      (rec2.done
        ? '<p class="gotit">' + esc(w.word) + '. Correct - ' + rec2.mark + ' out of 2.</p>'
        : '<div class="guessrow">' +
        '<input type="text" id="gw" maxlength="20" autocomplete="off" spellcheck="false" ' +
        'placeholder="Type the word" value="' + esc(rec2.said) + '">' +
        '<button class="btn go" id="gchk">Check</button>' +
        '<button class="btn cool" id="ghint"' +
        (rec2.hints >= w.pics.length ? ' disabled' : '') + '>Hint</button>' +
        '</div>' +
        '<p class="warn" id="gmsg"></p>' +
        '<p class="muted" style="font-size:15px">' +
        (rec2.hints ? 'You have used ' + rec2.hints + ' hint' + (rec2.hints > 1 ? 's' : '') +
          '. This word is now worth 1 mark.'
          : 'A hint tells you the name of one picture, and drops this word to 1 mark.') +
        '</p>') +
      '<div class="navrow">' +
      '<button class="btn plain" id="prev">' + (i === 0 ? 'Round 2 rules' : 'Previous') + '</button>' +
      '<button class="btn go" id="nxt">' +
      (i === WORDS.length - 1 ? 'Finish Round 2' : 'Next word') + '</button>' +
      '</div></div>';

    function check() {
      var v = $('gw').value.trim();
      rec2.said = v;
      rec2.tries++;
      if (v.replace(/[^a-z]/gi, '').toUpperCase() === w.word) {
        rec2.done = true;
        rec2.mark = rec2.hints > 0 ? 1 : 2;
        save(); go('r2', i);
      } else {
        $('gmsg').textContent = v ? 'Not that word. Look at the first letters again.'
          : 'Type your answer first.';
        save(); refreshDots(2);
      }
    }
    on('gchk', 'click', check);
    on('ghint', 'click', function () {
      rec2.hints++; save(); go('r2', i);
    });
    var gw = $('gw');
    if (gw) {
      gw.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') { e.preventDefault(); check(); }
      });
      gw.focus();
    }
    on('prev', 'click', function () { i === 0 ? go('r2intro') : go('r2', i - 1); });
    on('nxt', 'click', function () {
      i === WORDS.length - 1 ? go('r3intro') : go('r2', i + 1);
    });
  }

  /* ------------------------------------------------------- round 3: say */
  function sayRec(i) {
    if (!S.say[i]) S.say[i] = { done: false, heard: '', mark: 0, mode: '', tries: 0, hinted: false };
    return S.say[i];
  }

  function stopMic() {
    recLive = false;
    if (rec) { try { rec.abort(); } catch (e) { } rec = null; }
  }

  function viewSay() {
    var i = Math.max(0, Math.min(R3.length - 1, S.idx));
    var q = R3[i], rec2 = sayRec(i);

    app.innerHTML =
      '<div class="panel">' +
      head(3, R3.length, i, function (j) {
        var r = S.say[j]; return r && r.done ? 2 : (r && r.tries ? 1 : 0);
      }, function (j) { go('r3', j); }) +
      '<span class="qtag">Question ' + (i + 1) + ' of ' + R3.length + ' &middot; 2 marks</span>' +
      '<p class="qtext">' + esc(q.q) + '</p>' +
      '<div class="micpanel">' +
      (MIC_OK
        ? '<div class="row">' +
        '<button class="micbtn" id="mic"' + (rec2.done ? ' disabled' : '') + '>' +
        '<span class="micdot"></span><span id="miclab">Unmute and answer</span></button>' +
        '<button class="btn sm plain" id="hear">Read the question to me</button>' +
        '</div>'
        : '<p class="warn" style="margin-top:0">' + esc(micReason()) + '</p>' +
        '<div class="row"><button class="btn sm plain" id="hear">Read the question to me</button></div>') +
      (micCaution()
        ? '<p class="muted" style="font-size:15px;margin:10px 0 0"><b>Note:</b> ' +
        esc(micCaution()) + '</p>' : '') +
      '<div class="heard" id="heard"><span class="lab">What I heard</span>' +
      '<span class="txt' + (rec2.done ? '' : ' no') + '" id="htxt">' +
      (rec2.heard ? esc(rec2.heard) : '&mdash;') + '</span></div>' +
      '<div class="typefall">' +
      '<div class="guessrow">' +
      '<input type="text" id="ty" maxlength="120" autocomplete="off" placeholder="' +
      (MIC_OK ? 'or type your answer here' : 'type your answer here') + '" value="' +
      (rec2.mode === 'typed' ? esc(rec2.heard) : '') + '"' + (rec2.done ? ' disabled' : '') + '>' +
      '<button class="btn go" id="tchk"' + (rec2.done ? ' disabled' : '') + '>Check</button>' +
      '<button class="btn cool" id="shint"' + (rec2.done ? ' disabled' : '') + '>Hint</button>' +
      '</div>' +
      (rec2.hinted ? '<p class="muted" style="font-size:16px;margin-bottom:0"><b>Hint:</b> ' +
        esc(q.hint) + '</p>' : '') +
      '</div></div>' +
      '<p class="' + (rec2.done ? 'okline' : 'warn') + '" id="smsg">' +
      (rec2.done ? 'Correct - 2 out of 2.' : '') + '</p>' +
      '<div class="navrow">' +
      '<button class="btn plain" id="prev">' + (i === 0 ? 'Round 3 rules' : 'Previous') + '</button>' +
      '<button class="btn go" id="nxt">' +
      (i === R3.length - 1 ? 'See my result' : 'Next question') + '</button>' +
      '</div></div>';

    function accept(text, mode) {
      var r = sayRec(i);
      r.tries++;
      r.heard = text;
      r.mode = mode;
      if (answered(text, q.accept)) {
        r.done = true; r.mark = 2;
        save(); go('r3', i);
      } else {
        r.done = false; r.mark = 0;
        $('htxt').textContent = text || '—';
        $('htxt').className = 'txt no';
        $('smsg').textContent = text
          ? 'That is not the answer we are looking for. Try again, or press Hint.'
          : 'Nothing was heard. Try once more.';
        $('smsg').className = 'warn';
        save(); refreshDots(3);
      }
    }

    on('hear', 'click', function () { stopMic(); speak(q.q); });
    on('shint', 'click', function () { rec2.hinted = true; save(); go('r3', i); });
    on('tchk', 'click', function () { accept($('ty').value.trim(), 'typed'); });
    var ty = $('ty');
    if (ty) ty.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') { e.preventDefault(); accept(ty.value.trim(), 'typed'); }
    });

    if (MIC_OK) {
      on('mic', 'click', function () {
        if (recLive) { stopMic(); setMicLabel(false); return; }
        stopSpeaking();
        try {
          rec = new SR();
        } catch (err) {
          $('smsg').textContent = 'The microphone could not be started. Type the answer instead.';
          return;
        }
        rec.lang = 'en-IN';
        rec.interimResults = true;
        rec.maxAlternatives = 3;
        rec.continuous = false;
        var best = '';
        rec.onstart = function () { recLive = true; setMicLabel(true); $('smsg').textContent = ''; };
        rec.onresult = function (ev) {
          var k, j, txt = '', alts = [];
          for (k = ev.resultIndex; k < ev.results.length; k++) {
            txt += ev.results[k][0].transcript;
            if (ev.results[k].isFinal) {
              for (j = 0; j < ev.results[k].length; j++) alts.push(ev.results[k][j].transcript);
            }
          }
          best = txt;
          $('htxt').textContent = txt || '—';
          if (alts.length) {
            /* if any alternative the recogniser offered is right, take it -
               it mishears children far more often than it mishears adults */
            for (j = 0; j < alts.length; j++) {
              if (answered(alts[j], q.accept)) { best = alts[j]; break; }
            }
          }
        };
        rec.onerror = function (ev) {
          recLive = false; setMicLabel(false);
          var m = 'The microphone did not work. Type the answer instead.';
          if (ev && ev.error === 'not-allowed') {
            m = 'The microphone was blocked. Allow it in the address bar, or type the answer.';
          } else if (ev && ev.error === 'no-speech') {
            m = 'Nothing was heard. Press the button and speak clearly.';
          } else if (ev && ev.error === 'network') {
            m = 'Speech needs the internet and it is not reachable. Type the answer instead.';
          }
          $('smsg').textContent = m;
          $('smsg').className = 'warn';
        };
        rec.onend = function () {
          recLive = false; setMicLabel(false);
          if (best) accept(best.trim(), 'mic');
        };
        try { rec.start(); } catch (err) {
          $('smsg').textContent = 'The microphone is already listening. Wait a moment.';
        }
      });
    }
    function setMicLabel(live) {
      var b = $('mic'), l = $('miclab');
      if (!b || !l) return;
      b.classList.toggle('live', live);
      l.textContent = live ? 'Listening - say it now' : 'Unmute and answer';
    }

    on('prev', 'click', function () { i === 0 ? go('r3intro') : go('r3', i - 1); });
    on('nxt', 'click', function () {
      i === R3.length - 1 ? go('result') : go('r3', i + 1);
    });
  }

  /* ------------------------------------------------------------ result */
  function totals() {
    var a = 0, b = 0, c = 0, i;
    for (i = 0; i < R1.length; i++) a += (S.draw[R1[i].id] && S.draw[R1[i].id].mark) || 0;
    for (i = 0; i < WORDS.length; i++) b += (S.word[i] && S.word[i].mark) || 0;
    for (i = 0; i < R3.length; i++) c += (S.say[i] && S.say[i].mark) || 0;
    return { r1: a, r2: b, r3: c, all: a + b + c };
  }

  function miniGrid(cells) {
    var out = '<div class="minigrid">', i;
    for (i = 0; i < 64; i++) out += '<i' + (cells[i] ? ' class="on"' : '') + '></i>';
    return out + '</div>';
  }

  function viewResult() {
    var t = totals(), i, rows = '', r, q;

    rows += '<h3 class="revhead">Round 1 &middot; Draw the dots</h3><div class="review">';
    for (i = 0; i < R1.length; i++) {
      q = R1[i]; r = S.draw[q.id];
      rows += '<div class="rev ' + (r && r.done ? (r.mark === 3 ? 'ok' : 'half') : 'no') + '">' +
        '<span class="mark">' + ((r && r.mark) || 0) + '/3</span><div>' +
        '<b>Question ' + (i + 1) + '</b>' +
        '<span class="said">' + esc(q.ask) + '</span>' +
        '<div class="revgrid">' +
        '<div><div class="minilab">yours</div>' + miniGrid((r && r.cells) || blankCells()) + '</div>' +
        '<div><div class="minilab">right</div>' + miniGrid(patCells(q.icon)) + '</div>' +
        '</div></div></div>';
    }
    rows += '</div>';

    rows += '<h3 class="revhead">Round 2 &middot; The picture word</h3><div class="review">';
    for (i = 0; i < WORDS.length; i++) {
      r = S.word[i];
      rows += '<div class="rev ' + (r && r.done ? (r.mark === 2 ? 'ok' : 'half') : 'no') + '">' +
        '<span class="mark">' + ((r && r.mark) || 0) + '/2</span><div>' +
        '<b>' + esc(WORDS[i].word) + '</b>' +
        '<span class="said">' +
        (r && r.done ? 'Correct' + (r.hints ? ' after ' + r.hints + ' hint' +
          (r.hints > 1 ? 's' : '') : '') : 'Wrote: ' + esc((r && r.said) || 'nothing')) +
        '</span></div></div>';
    }
    rows += '</div>';

    rows += '<h3 class="revhead">Round 3 &middot; Say it out loud</h3><div class="review">';
    for (i = 0; i < R3.length; i++) {
      r = S.say[i];
      rows += '<div class="rev ' + (r && r.done ? 'ok' : 'no') + '">' +
        '<span class="mark">' + ((r && r.mark) || 0) + '/2</span><div>' +
        '<b>' + esc(R3[i].q) + '</b>' +
        '<span class="said">' +
        (r && r.heard ? (r.mode === 'typed' ? 'Typed: ' : 'Said: ') + esc(r.heard)
          : 'No answer given') +
        (r && r.hinted ? ' &middot; used the hint' : '') +
        '</span></div></div>';
    }
    rows += '</div>';

    app.innerHTML =
      '<div class="panel">' +
      '<div class="row spread"><h1>Result</h1><span class="qtag">' + esc(S.name) + '</span></div>' +
      '<div class="scorebox"><div class="num">' + t.all + ' / ' + MAXALL + '</div>' +
      '<div class="big">' + esc(S.name) + '</div></div>' +
      '<div class="partscores">' +
      '<div class="ps">Round 1 &middot; Draw <span>' + t.r1 + '/' + MAX1 + '</span></div>' +
      '<div class="ps">Round 2 &middot; Words <span>' + t.r2 + '/' + MAX2 + '</span></div>' +
      '<div class="ps">Round 3 &middot; Speaking <span>' + t.r3 + '/' + MAX3 + '</span></div>' +
      '</div>' + rows +
      '<div class="navrow noprint">' +
      '<button class="btn plain" id="reset">New student</button>' +
      '<div class="row">' +
      '<button class="btn plain" id="back3">Back to Round 3</button>' +
      '<button class="btn cool" id="prn">Print / Save as PDF</button>' +
      '<button class="btn go" id="dl">Download my answers</button>' +
      '</div></div></div>';

    on('prn', 'click', function () { window.print(); });
    on('back3', 'click', function () { go('r3', R3.length - 1); });
    on('reset', 'click', function () {
      if (window.confirm('Clear this student\'s answers so the next one can start?')) {
        S = fresh(); save(); go('welcome');
      }
    });
    on('dl', 'click', downloadJSON);
  }

  function downloadJSON() {
    var t = totals(), out = {
      assessment: 'The Leaf Machine - Class 6, Unit 2 (What is AI?)',
      student: S.name,
      started: S.started,
      finished: new Date().toISOString(),
      total: t.all, outOf: MAXALL,
      rounds: { draw: t.r1, words: t.r2, speaking: t.r3 },
      answers: { draw: {}, words: {}, speaking: {} }
    }, i, r;
    for (i = 0; i < R1.length; i++) {
      r = S.draw[R1[i].id] || {};
      out.answers.draw[R1[i].id] = {
        correct: !!r.done, mark: r.mark || 0, checks: r.checks || 0,
        usedHint: !!r.hinted, drew: (r.cells || blankCells()).map(function (b) { return b ? 1 : 0; }).join('')
      };
    }
    for (i = 0; i < WORDS.length; i++) {
      r = S.word[i] || {};
      out.answers.words[WORDS[i].word] = {
        correct: !!r.done, mark: r.mark || 0, hints: r.hints || 0, wrote: r.said || ''
      };
    }
    for (i = 0; i < R3.length; i++) {
      r = S.say[i] || {};
      out.answers.speaking['q' + (i + 1)] = {
        question: R3[i].q, correct: !!r.done, mark: r.mark || 0,
        answer: r.heard || '', how: r.mode || '', usedHint: !!r.hinted
      };
    }
    var blob = new Blob([JSON.stringify(out, null, 2)], { type: 'application/json' });
    var a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'leaf-machine-' +
      S.name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') + '.json';
    document.body.appendChild(a); a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); document.body.removeChild(a); }, 400);
  }

  /* ===================================================================
     GO
     =================================================================== */
  window.addEventListener('beforeunload', function () { stopSpeaking(); stopMic(); });
  render();

  /* exposed only so the smoke test can drive it */
  window.__leaf = {
    state: function () { return S; },
    go: go,
    totals: totals,
    answered: answered,
    patCells: patCells,
    R1: R1, R3: R3, WORDS: WORDS
  };
})();
