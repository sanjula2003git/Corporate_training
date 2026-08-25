/* scenes.js - hand-drawn comic scenes for "The Sentinels of Nova City".
   Every scene is one <svg class="scene"> stacked in the stage; app.js turns
   exactly one of them "live" as the narration plays. Pure SVG + CSS, no images. */
(function () {
  var W = 1280, H = 720;
  var INK = '#12142a';

  /* ---------------------------------------------------------------- css */
  var CSS = [
    '.scene text{font-family:"Trebuchet MS","Segoe UI",Verdana,sans-serif;font-weight:bold}',
    '@keyframes bob{0%,100%{transform:translateY(0)}50%{transform:translateY(-15px)}}',
    '@keyframes bob2{0%,100%{transform:translateY(0)}50%{transform:translateY(12px)}}',
    '@keyframes rainfall{from{transform:translateY(-160px)}to{transform:translateY(260px)}}',
    '@keyframes dashmove{to{stroke-dashoffset:-200}}',
    '@keyframes pulse{0%,100%{transform:scale(1)}50%{transform:scale(1.07)}}',
    '@keyframes flick{0%,100%{opacity:1}45%{opacity:.3}}',
    '@keyframes jitter{0%,100%{transform:translate(0,0)}20%{transform:translate(7px,-5px)}',
    '40%{transform:translate(-6px,4px)}60%{transform:translate(5px,5px)}80%{transform:translate(-4px,-6px)}}',
    '@keyframes sweep{from{transform:translateX(-1500px)}to{transform:translateX(1500px)}}',
    '@keyframes blink{0%,100%{opacity:1}50%{opacity:.12}}',
    '@keyframes grow{from{transform:scale(.4);opacity:0}to{transform:scale(1);opacity:1}}',
    '@keyframes tilt{0%,100%{transform:rotate(-3deg)}50%{transform:rotate(3deg)}}',
    '.bob{animation:bob 3.4s ease-in-out infinite}',
    '.bob2{animation:bob2 4.1s ease-in-out infinite}',
    '.pulse{animation:pulse 2.2s ease-in-out infinite;transform-box:fill-box;transform-origin:center}',
    '.flick{animation:flick 1.1s steps(2,end) infinite}',
    '.jit{animation:jitter .38s steps(2,end) infinite}',
    '.blink{animation:blink 1.4s ease-in-out infinite}',
    '.tilt{animation:tilt 3s ease-in-out infinite;transform-box:fill-box;transform-origin:center}',
    '.flow{stroke-dasharray:26 20;animation:dashmove 2.2s linear infinite}',
    '.rain line{animation:rainfall 1s linear infinite}',
    '.shine{animation:sweep 3.6s linear infinite}',
    '.scene.live .pop{animation:grow .55s cubic-bezier(.2,1.5,.4,1) both;transform-box:fill-box;transform-origin:center}',
    '.scene.live .pop.d1{animation-delay:.5s}.scene.live .pop.d2{animation-delay:1s}',
    '.scene.live .pop.d3{animation-delay:1.5s}.scene.live .pop.d4{animation-delay:2s}'
  ].join('\n');

  /* ------------------------------------------------------------ helpers */
  function T(x, y, s, size, fill, extra) {
    return '<text x="' + x + '" y="' + y + '" font-size="' + size + '" fill="' + fill +
      '" text-anchor="middle" stroke="' + INK + '" stroke-width="' + Math.max(3, size / 7) +
      '" paint-order="stroke" ' + (extra || '') + '>' + s + '</text>';
  }
  function Tplain(x, y, s, size, fill, anchor) {
    return '<text x="' + x + '" y="' + y + '" font-size="' + size + '" fill="' + fill +
      '" text-anchor="' + (anchor || 'middle') + '">' + s + '</text>';
  }

  function sky(u, mood) {
    var top = mood === 'storm' ? '#2b2f52' : mood === 'dawn' ? '#3b2b52' : '#1b2050';
    var bot = mood === 'storm' ? '#4a4166' : mood === 'dawn' ? '#8a4a5e' : '#4a3f7a';
    return '<defs><linearGradient id="sk' + u + '" x1="0" y1="0" x2="0" y2="1">' +
      '<stop offset="0" stop-color="' + top + '"/><stop offset="1" stop-color="' + bot + '"/>' +
      '</linearGradient></defs><rect width="' + W + '" height="' + H + '" fill="url(#sk' + u + ')"/>';
  }

  function stars(n, seed) {
    var s = '', i, x, y, r;
    for (i = 0; i < n; i++) {
      x = ((seed * 37 + i * 91) % 127) / 127 * W;
      y = ((seed * 53 + i * 61) % 89) / 89 * 330;
      r = 1.5 + ((i * 17) % 5) / 2;
      s += '<circle cx="' + x.toFixed(0) + '" cy="' + y.toFixed(0) + '" r="' + r +
        '" fill="#fff" opacity="' + (0.25 + ((i * 13) % 7) / 12) + '"/>';
    }
    return s;
  }

  function rain(n, seed, op) {
    var s = '<g class="rain" opacity="' + op + '">', i, x, d;
    for (i = 0; i < n; i++) {
      x = ((seed * 29 + i * 83) % 151) / 151 * (W + 200) - 100;
      d = (i % 10) / 10;
      s += '<line x1="' + x.toFixed(0) + '" y1="-60" x2="' + (x - 22).toFixed(0) + '" y2="30" ' +
        'stroke="#cfe3ff" stroke-width="3" stroke-linecap="round" ' +
        'style="animation-delay:-' + d + 's"/>';
    }
    return s + '</g>';
  }

  /* city skyline, drawn deterministically so it looks the same every replay */
  function skyline(baseY, fill, seed, lit) {
    var s = '<g>', x = -40, i = 0, w, h, k, wx, wy;
    while (x < W + 40) {
      w = 70 + ((seed * 7 + i * 43) % 90);
      h = 90 + ((seed * 11 + i * 67) % 230);
      s += '<rect x="' + x + '" y="' + (baseY - h) + '" width="' + w + '" height="' + (h + 60) +
        '" fill="' + fill + '" stroke="' + INK + '" stroke-width="5"/>';
      if (lit) {
        for (k = 0; k < 6; k++) {
          wx = x + 14 + (k % 2) * (w - 46);
          wy = baseY - h + 22 + Math.floor(k / 2) * 46;
          if (wy < baseY - 20 && (i + k) % 3 !== 0) {
            s += '<rect x="' + wx + '" y="' + wy + '" width="26" height="26" rx="4" fill="#ffd43b" opacity="' +
              (0.5 + ((i + k) % 4) / 8) + '"/>';
          }
        }
      }
      x += w + 12; i++;
    }
    return s + '</g>';
  }

  /* ------------------------------------------------------------- heroes */
  function cape(color) {
    return '<path d="M-48,-34 L48,-34 L82,96 L-82,96 Z" fill="' + color +
      '" stroke="' + INK + '" stroke-width="7" stroke-linejoin="round"/>';
  }
  function torso(color) {
    return '<rect x="-42" y="-28" width="84" height="112" rx="22" fill="' + color +
      '" stroke="' + INK + '" stroke-width="7"/>';
  }
  function head() {
    return '<circle cx="0" cy="-66" r="38" fill="#f2c9a0" stroke="' + INK + '" stroke-width="7"/>';
  }
  function legs(color) {
    return '<rect x="-34" y="78" width="28" height="58" rx="12" fill="' + color + '" stroke="' + INK + '" stroke-width="6"/>' +
      '<rect x="6" y="78" width="28" height="58" rx="12" fill="' + color + '" stroke="' + INK + '" stroke-width="6"/>';
  }
  function emblem(sym, color) {
    var fs = sym.length > 2 ? 22 : 30;          /* "123" must not burst its badge */
    return '<circle cx="0" cy="14" r="26" fill="#fdf7ea" stroke="' + INK + '" stroke-width="6"/>' +
      Tplain(0, 14 + fs / 3, sym, fs, color);
  }

  var HERO = {
    echo: function () {
      return legs('#1864ab') + cape('#4dabf7') + torso('#1c7ed6') + head() +
        /* helmet with ear discs */
        '<path d="M-40,-72 a40,40 0 0 1 80,0 z" fill="#1864ab" stroke="' + INK + '" stroke-width="7"/>' +
        '<circle cx="-44" cy="-64" r="16" fill="#ffd43b" stroke="' + INK + '" stroke-width="6"/>' +
        '<circle cx="44" cy="-64" r="16" fill="#ffd43b" stroke="' + INK + '" stroke-width="6"/>' +
        '<circle cx="-8" cy="-60" r="5" fill="' + INK + '"/><circle cx="14" cy="-60" r="5" fill="' + INK + '"/>' +
        emblem('))', '#1c7ed6');
    },
    iris: function () {
      return legs('#5f3dc4') + cape('#9775fa') + torso('#7048e8') + head() +
        /* visor lens across the eyes */
        '<rect x="-42" y="-80" width="84" height="30" rx="14" fill="#12142a" stroke="' + INK + '" stroke-width="6"/>' +
        '<circle cx="16" cy="-65" r="11" fill="#69db7c" stroke="#fdf7ea" stroke-width="4" class="pulse"/>' +
        '<path d="M-40,-84 q40,-26 80,0" fill="none" stroke="' + INK + '" stroke-width="7"/>' +
        emblem('O', '#7048e8');
    },
    nova: function () {
      return legs('#2b8a3e') + cape('#8ce99a') + torso('#2f9e44') + head() +
        '<path d="M-38,-88 q38,-16 76,0 l-6,20 q-32,-12 -64,0 z" fill="#2b8a3e" stroke="' + INK + '" stroke-width="6"/>' +
        '<circle cx="-12" cy="-60" r="5" fill="' + INK + '"/><circle cx="12" cy="-60" r="5" fill="' + INK + '"/>' +
        '<path d="M-16,-42 q16,12 32,0" fill="none" stroke="' + INK + '" stroke-width="5" stroke-linecap="round"/>' +
        emblem('123', '#2f9e44');
    },
    rex: function () {
      /* robot dog: box body, four stiff legs, antenna tail */
      return '<g>' +
        '<rect x="-70" y="-16" width="140" height="76" rx="16" fill="#e8590c" stroke="' + INK + '" stroke-width="7"/>' +
        '<rect x="-58" y="60" width="24" height="52" rx="8" fill="#495057" stroke="' + INK + '" stroke-width="6"/>' +
        '<rect x="-18" y="60" width="24" height="52" rx="8" fill="#495057" stroke="' + INK + '" stroke-width="6"/>' +
        '<rect x="20" y="60" width="24" height="52" rx="8" fill="#495057" stroke="' + INK + '" stroke-width="6"/>' +
        '<rect x="44" y="60" width="24" height="52" rx="8" fill="#495057" stroke="' + INK + '" stroke-width="6"/>' +
        '<path d="M70,0 q46,-16 40,-64" fill="none" stroke="' + INK + '" stroke-width="8" stroke-linecap="round"/>' +
        '<circle cx="110" cy="-66" r="11" fill="#ffd43b" stroke="' + INK + '" stroke-width="6" class="pulse"/>' +
        '<rect x="-118" y="-58" width="70" height="66" rx="14" fill="#f76707" stroke="' + INK + '" stroke-width="7"/>' +
        '<circle cx="-100" cy="-34" r="9" fill="#fdf7ea" stroke="' + INK + '" stroke-width="5"/>' +
        '<circle cx="-70" cy="-34" r="9" fill="#fdf7ea" stroke="' + INK + '" stroke-width="5"/>' +
        '<rect x="-114" y="-12" width="52" height="12" rx="6" fill="' + INK + '"/>' +
        '<path d="M-92,-58 l-8,-34 M-70,-58 l8,-34" stroke="' + INK + '" stroke-width="7" stroke-linecap="round"/>' +
        '</g>';
    },
    meera: function () {
      /* a Class-6-sized kid, ponytail, school satchel */
      return '<g>' +
        '<rect x="-26" y="62" width="22" height="52" rx="10" fill="#364fc7" stroke="' + INK + '" stroke-width="6"/>' +
        '<rect x="6" y="62" width="22" height="52" rx="10" fill="#364fc7" stroke="' + INK + '" stroke-width="6"/>' +
        '<rect x="-34" y="-16" width="68" height="86" rx="18" fill="#f59f00" stroke="' + INK + '" stroke-width="7"/>' +
        '<rect x="24" y="-4" width="30" height="52" rx="10" fill="#c92a2a" stroke="' + INK + '" stroke-width="6"/>' +
        '<circle cx="0" cy="-52" r="32" fill="#e0a06b" stroke="' + INK + '" stroke-width="7"/>' +
        '<path d="M-32,-58 a32,32 0 0 1 64,0 q-32,-20 -64,0 z" fill="#212529" stroke="' + INK + '" stroke-width="6"/>' +
        '<path d="M30,-58 q34,10 24,54" fill="none" stroke="#212529" stroke-width="14" stroke-linecap="round"/>' +
        '<circle cx="-11" cy="-48" r="4.5" fill="' + INK + '"/><circle cx="11" cy="-48" r="4.5" fill="' + INK + '"/>' +
        '<path d="M-11,-32 q11,9 22,0" fill="none" stroke="' + INK + '" stroke-width="5" stroke-linecap="round"/>' +
        '</g>';
    },
    statik: function () {
      /* the villain: a jagged silhouette made of broken signal bars */
      return '<g class="jit">' +
        '<path d="M0,-150 L58,-70 L30,-70 L74,10 L36,10 L86,130 L-86,130 L-36,10 L-74,10 L-30,-70 L-58,-70 Z" ' +
        'fill="#1a1030" stroke="#cc5de8" stroke-width="7" stroke-linejoin="round"/>' +
        '<rect x="-52" y="-58" width="104" height="14" fill="#cc5de8" class="flick"/>' +
        '<rect x="-40" y="-20" width="80" height="10" fill="#f783ac" class="flick" style="animation-delay:-.4s"/>' +
        '<rect x="-60" y="30" width="120" height="12" fill="#cc5de8" class="flick" style="animation-delay:-.7s"/>' +
        '<circle cx="-22" cy="-92" r="9" fill="#ff8787"/><circle cx="22" cy="-92" r="9" fill="#ff8787"/>' +
        '</g>';
    }
  };

  /* NOTE: the animation class must never sit on the same <g> as the transform
     attribute - a CSS transform replaces the attribute and yanks the art to 0,0.
     Position on the outer group, animate on an inner one. */
  function heroAt(kind, x, y, scale, cls) {
    return '<g transform="translate(' + x + ',' + y + ') scale(' + scale + ')">' +
      '<g class="' + (cls || '') + '">' + HERO[kind]() + '</g></g>';
  }

  /* -------------------------------------------------- input/output chips */
  function chip(x, y, w, h, title, body, color, cls) {
    var lines = body.split('|');
    var s = '<g transform="translate(' + x + ',' + y + ')"><g class="' + (cls || '') + '">' +
      '<rect x="' + (-w / 2) + '" y="' + (-h / 2) + '" width="' + w + '" height="' + h + '" rx="18" ' +
      'fill="#fdf7ea" stroke="' + INK + '" stroke-width="7"/>' +
      '<rect x="' + (-w / 2) + '" y="' + (-h / 2) + '" width="' + w + '" height="42" rx="18" fill="' + color + '"/>' +
      '<rect x="' + (-w / 2) + '" y="' + (-h / 2 + 24) + '" width="' + w + '" height="18" fill="' + color + '"/>' +
      '<rect x="' + (-w / 2) + '" y="' + (-h / 2) + '" width="' + w + '" height="' + h + '" rx="18" ' +
      'fill="none" stroke="' + INK + '" stroke-width="7"/>' +
      Tplain(0, -h / 2 + 31, title, 25, '#fff');
    var i, n = lines.length, fs = n > 2 ? 25 : 30, y0 = 12 - (n - 1) * (fs * 0.62);
    for (i = 0; i < n; i++) s += Tplain(0, y0 + i * fs * 1.24, lines[i], fs, INK);
    return s + '</g></g>';
  }

  /* the "machine in the middle" - a friendly box with a face, labelled underneath
     so the label can be as long as it likes without spilling inside the box */
  function aiBox(x, y, label, tone) {
    var edge = tone === 'bad' ? '#e03131' : tone === 'good' ? '#69db7c' : '#ffd43b';
    var face = tone === 'bad' ? '#ff8787' : '#ffd43b';
    var mouth = tone === 'bad'
      ? '<path d="M-44,38 q44,-30 88,0" fill="none" stroke="' + face + '" stroke-width="9" stroke-linecap="round"/>'
      : '<path d="M-44,14 q44,34 88,0" fill="none" stroke="' + face + '" stroke-width="9" stroke-linecap="round"/>';
    return '<g transform="translate(' + x + ',' + y + ')">' +
      '<rect x="-92" y="-80" width="184" height="160" rx="26" fill="#232a5c" stroke="' + edge + '" stroke-width="8"/>' +
      '<rect x="-70" y="-58" width="140" height="30" rx="8" fill="#12142a"/>' +
      '<circle cx="-44" cy="-43" r="6" fill="' + face + '" class="pulse"/>' +
      '<circle cx="-16" cy="-43" r="6" fill="' + face + '" class="pulse"/>' +
      '<circle cx="12" cy="-43" r="6" fill="' + face + '" class="pulse"/>' +
      '<circle cx="40" cy="-43" r="6" fill="' + face + '" class="pulse"/>' +
      '<circle cx="-34" cy="-6" r="14" fill="' + face + '"/>' +
      '<circle cx="34" cy="-6" r="14" fill="' + face + '"/>' +
      mouth +
      T(0, 122, label || 'THE AI', 27, '#fff') +
      '</g>';
  }

  function arrow(x1, x2, y, color, flow) {
    return '<g><line x1="' + x1 + '" y1="' + y + '" x2="' + (x2 - 26) + '" y2="' + y +
      '" stroke="' + color + '" stroke-width="11" stroke-linecap="round" class="' + (flow ? 'flow' : '') + '"/>' +
      '<path d="M' + (x2 - 30) + ',' + (y - 20) + ' L' + x2 + ',' + y + ' L' + (x2 - 30) + ',' + (y + 20) + ' Z" fill="' + color + '"/></g>';
  }

  /* the middle-of-the-story diagram: what they were handed, what they said */
  function pipeline(opts) {
    var y = opts.y || 400, tone = opts.tone || '', good = tone !== 'bad';
    var arrowC = tone === 'bad' ? '#ff8787' : '#ffd43b';
    return '<g>' +
      chip(210, y, 300, 180, opts.inTitle || 'WAS HANDED', opts.inp, '#1c7ed6', 'pop') +
      arrow(370, 540, y, arrowC, true) +
      '<g class="pop d1">' + aiBox(640, y, opts.brain, tone) + '</g>' +
      arrow(742, 912, y, arrowC, true) +
      chip(1070, y, 300, 180, opts.outTitle || 'SAID', opts.outp, good ? '#2f9e44' : '#e03131', 'pop d2') +
      (tone === 'bad'
        ? '<g class="pop d3"><circle cx="1070" cy="' + (y - 128) + '" r="42" fill="#e03131" stroke="' + INK + '" stroke-width="7"/>' +
          Tplain(1070, y - 114, 'X', 46, '#fff') + '</g>'
        : '') +
      '</g>';
  }

  function banner(text, sub, color) {
    return '<g>' +
      '<rect x="60" y="52" width="1160" height="' + (sub ? 132 : 96) + '" rx="20" fill="' + (color || '#e03131') +
      '" stroke="' + INK + '" stroke-width="7"/>' +
      T(640, sub ? 122 : 120, text, 54, '#fff') +
      (sub ? Tplain(640, 164, sub, 27, '#ffe8e8') : '') +
      '</g>';
  }

  /* --------------------------------------------------------- the scenes */
  var S = {};

  S.clock = function (u) {
    return sky(u, 'storm') + rain(46, 3, .5) +
      skyline(600, '#2b2f57', 5, true) + skyline(680, '#181c3d', 9, false) +
      '<g class="pop">' +
      '<circle cx="640" cy="240" r="134" fill="#12142a" stroke="#ffd43b" stroke-width="10"/>' +
      '<circle cx="640" cy="240" r="112" fill="none" stroke="#3a3f66" stroke-width="4"/>' +
      /* 23:49 - both hands drawn pointing at twelve, then rotated into place */
      '<line x1="640" y1="240" x2="640" y2="166" stroke="#fdf7ea" stroke-width="12" ' +
      'stroke-linecap="round" transform="rotate(-4,640,240)"/>' +
      '<line x1="640" y1="240" x2="640" y2="132" stroke="#ffd43b" stroke-width="9" ' +
      'stroke-linecap="round" transform="rotate(-66,640,240)"/>' +
      '<circle cx="640" cy="240" r="12" fill="#e03131"/>' +
      T(640, 452, 'ELEVEN MINUTES TO MIDNIGHT', 46, '#ffd43b') + '</g>';
  };

  S.team = function (u) {
    return sky(u, 'night') + stars(28, 7) + skyline(660, '#20244a', 4, true) +
      heroAt('echo', 250, 470, 1.05, 'bob') +
      heroAt('iris', 500, 460, 1.05, 'bob2') +
      heroAt('nova', 760, 470, 1.05, 'bob') +
      heroAt('rex', 1040, 500, 0.95, 'bob2') +
      '<g class="pop">' + T(640, 150, 'THE SENTINELS', 76, '#ffd43b') + '</g>';
  };

  S.echo = function (u) {
    return sky(u, 'night') + stars(20, 11) + skyline(700, '#20244a', 6, true) +
      heroAt('echo', 250, 430, 1.15, 'bob') +
      '<g class="pop d1">' +
      '<path d="M420,300 q40,60 0,120" fill="none" stroke="#ffd43b" stroke-width="10" stroke-linecap="round"/>' +
      '<path d="M470,270 q56,90 0,180" fill="none" stroke="#ffd43b" stroke-width="10" stroke-linecap="round"/>' +
      '<path d="M520,240 q72,120 0,240" fill="none" stroke="#ffd43b" stroke-width="10" stroke-linecap="round"/>' +
      '</g>' +
      chip(880, 300, 460, 150, 'SHE HEARS', '"HELP!"', '#1c7ed6', 'pop d2') +
      chip(880, 540, 460, 150, 'SHE WRITES', 'A boy shouted|from Baker Street', '#2f9e44', 'pop d3');
  };

  S.iris = function (u) {
    return sky(u, 'night') + stars(24, 13) + skyline(690, '#20244a', 8, true) +
      '<g class="bob">' + heroAt('iris', 260, 330, 1.05) + '</g>' +
      '<g class="pop d1"><line x1="330" y1="380" x2="560" y2="470" stroke="#69db7c" stroke-width="8" class="flow"/>' +
      '<line x1="330" y1="420" x2="560" y2="560" stroke="#69db7c" stroke-width="8" class="flow"/></g>' +
      chip(830, 330, 400, 150, 'SHE LOOKS AT', '[ a cracked wall ]', '#1c7ed6', 'pop d2') +
      chip(830, 560, 400, 150, 'SHE NAMES IT', 'CRACK', '#2f9e44', 'pop d3');
  };

  S.nova = function (u) {
    return sky(u, 'storm') + rain(30, 5, .35) + skyline(700, '#20244a', 12, true) +
      heroAt('nova', 240, 440, 1.1, 'bob') +
      chip(760, 300, 520, 160, 'SHE READS', 'Rain 92 mm   River 7.4 m', '#1c7ed6', 'pop d1') +
      chip(760, 540, 520, 160, 'SHE SAYS', 'NOT SAFE', '#2f9e44', 'pop d2');
  };

  S.rex = function (u) {
    return sky(u, 'night') + stars(18, 17) + skyline(700, '#20244a', 14, true) +
      heroAt('rex', 300, 400, 1.05, 'bob2') +
      chip(880, 300, 470, 150, 'YOU ASK', 'Where is the dam?', '#1c7ed6', 'pop d1') +
      chip(880, 540, 470, 150, 'HE ANSWERS', 'Two miles north.', '#2f9e44', 'pop d2');
  };

  S.storm = function (u) {
    return sky(u, 'storm') + rain(70, 3, .75) + skyline(620, '#232750', 5, true) + skyline(690, '#161a3a', 9, false) +
      '<path d="M300,60 L250,220 L330,220 L270,380" fill="none" stroke="#ffd43b" stroke-width="14" ' +
      'stroke-linecap="round" class="flick"/>' +
      '<g class="pop">' + T(640, 170, 'NINE DAYS OF RAIN', 58, '#fff') + '</g>';
  };

  function damWall(striped) {
    return '<g>' +
      '<path d="M180,700 L260,240 L1020,240 L1100,700 Z" fill="#adb5bd" stroke="' + INK + '" stroke-width="9"/>' +
      '<rect x="240" y="200" width="800" height="52" rx="10" fill="#868e96" stroke="' + INK + '" stroke-width="8"/>' +
      '<path d="M300,300 L340,540 M420,290 L450,560 M640,285 L640,570 M860,290 L830,560" ' +
      'stroke="#868e96" stroke-width="6" opacity=".8"/>' +
      (striped
        ? '<g class="pop"><path d="M300,270 L360,690 M430,255 L490,690 M560,245 L620,690 M700,245 L760,690 M830,255 L890,690" ' +
          'stroke="#12142a" stroke-width="34" stroke-linecap="round" opacity=".92"/></g>'
        : '') +
      '<path d="M600,300 q18,80 -14,150 q22,60 6,130" fill="none" stroke="#e03131" stroke-width="9" stroke-linecap="round"/>' +
      '</g>';
  }

  S.dam = function (u) {
    return sky(u, 'storm') + rain(50, 7, .55) +
      '<rect y="150" width="' + W + '" height="120" fill="#3b5bdb" opacity=".7"/>' + damWall(false) +
      '<g class="pop">' + T(640, 120, 'THE OLD DAM', 58, '#ffd43b') + '</g>';
  };

  S.statik = function (u) {
    return sky(u, 'storm') + rain(40, 9, .4) + damWall(false) +
      '<rect width="' + W + '" height="' + H + '" fill="#12142a" opacity=".45"/>' +
      heroAt('statik', 880, 430, 1.25) +
      '<g class="pop">' + T(400, 200, 'THE STATIC', 66, '#cc5de8') + '</g>';
  };

  S.attack = function (u) {
    return sky(u, 'storm') + '<rect width="' + W + '" height="' + H + '" fill="#12142a" opacity=".3"/>' +
      banner('IT NEVER TOUCHED A HERO', 'nine days of paint, a recording, a swapped page', '#7048e8') +
      heroAt('statik', 250, 470, .95) +
      chip(760, 430, 340, 190, 'IT CHANGED', 'the picture|the voice|the numbers', '#1c7ed6', 'pop d1') +
      '<g class="pop d2"><path d="M470,430 q120,-70 220,-10" fill="none" stroke="#cc5de8" stroke-width="12" ' +
      'stroke-linecap="round" class="flow"/>' +
      '<path d="M960,340 l90,-60 M960,430 l110,0 M960,520 l90,60" stroke="#cc5de8" stroke-width="10" stroke-linecap="round"/>' +
      '</g>';
  };

  S.zebra = function (u) {
    return sky(u, 'storm') + damWall(true) +
      '<rect width="' + W + '" height="' + H + '" fill="#12142a" opacity=".25"/>' +
      '<g class="pop d1">' + heroAt('iris', 190, 250, .8) + '</g>' +
      chip(900, 220, 420, 160, 'IRIS SEES', 'stripes', '#1c7ed6', 'pop d2') +
      '<g class="pop d3">' + chip(900, 470, 420, 160, 'IRIS SAYS', 'ZEBRA', '#e03131') +
      '<circle cx="1110" cy="380" r="44" fill="#e03131" stroke="' + INK + '" stroke-width="7"/>' +
      Tplain(1110, 396, 'X', 48, '#fff') + '</g>';
  };

  S.fakevoice = function (u) {
    return sky(u, 'storm') + '<rect width="' + W + '" height="' + H + '" fill="#12142a" opacity=".2"/>' +
      banner('A RECORDING, NOT THE REAL MAYOR', null, '#7048e8') +
      pipeline({
        y: 440, tone: 'bad', brain: 'ECHO LISTENS',
        inTitle: 'ECHO WAS HANDED', outTitle: 'SO ECHO WROTE',
        inp: 'a RECORDING|of the mayor', outp: 'nothing to|worry about'
      });
  };

  S.oldnum = function (u) {
    return sky(u, 'storm') + '<rect width="' + W + '" height="' + H + '" fill="#12142a" opacity=".2"/>' +
      banner('THE SWAPPED PAGE', 'old numbers, not tonight’s', '#7048e8') +
      pipeline({
        y: 450, tone: 'bad', brain: 'NOVA COUNTS',
        inTitle: 'NOVA WAS HANDED', outTitle: 'SO NOVA SAID',
        inp: 'the OLD page|Rain 4 mm', outp: 'SAFE'
      });
  };

  S.allwrong = function (u) {
    var s = sky(u, 'storm') + banner('ALL FOUR OF THEM WERE WRONG', 'on the same night', '#e03131');
    var rows = [['IRIS', 'ZEBRA'], ['ECHO', 'NOTHING TO WORRY ABOUT'], ['NOVA', 'SAFE'], ['REX', 'THERE IS NO DANGER']];
    rows.forEach(function (r, i) {
      var yy = 275 + i * 98;
      s += '<g class="pop d' + (i + 1) + '">' +
        Tplain(340, yy + 12, r[0], 40, '#ffd43b', 'end') +
        arrow(380, 560, yy, '#ff8787', true) +
        chip(830, yy, 520, 76, '', r[1], '#e03131') +
        '<circle cx="1140" cy="' + yy + '" r="30" fill="#e03131" stroke="' + INK + '" stroke-width="6"/>' +
        Tplain(1140, yy + 11, 'X', 32, '#fff') + '</g>';
    });
    return s;
  };

  S.rexwrong = function (u) {
    return sky(u, 'storm') + rain(30, 21, .35) + skyline(700, '#20244a', 14, true) +
      heroAt('rex', 300, 420, 1.05, 'bob2') +
      chip(880, 300, 470, 140, 'ASKED', 'Where is the danger?', '#7048e8', 'pop d1') +
      '<g class="pop d2">' + chip(880, 500, 470, 140, 'REX SAID', 'There is no danger.', '#e03131') +
      '<circle cx="1130" cy="418" r="40" fill="#e03131" stroke="' + INK + '" stroke-width="7"/>' +
      Tplain(1130, 432, 'X', 44, '#fff') + '</g>';
  };

  S.meera = function (u) {
    return sky(u, 'storm') + rain(36, 11, .45) + skyline(560, '#20244a', 6, true) +
      /* the bridge */
      '<rect x="0" y="560" width="' + W + '" height="34" fill="#495057" stroke="' + INK + '" stroke-width="7"/>' +
      '<path d="M0,560 q320,-150 640,-10 q320,140 640,10" fill="none" stroke="#868e96" stroke-width="9"/>' +
      '<path d="M120,560 L120,470 M360,560 L360,505 M900,560 L900,505 M1150,560 L1150,470" stroke="#868e96" stroke-width="7"/>' +
      '<rect y="594" width="' + W + '" height="126" fill="#1b2050"/>' +
      heroAt('meera', 640, 448, 1.0, 'bob') +
      '<g class="pop d1">' + T(640, 180, 'MEERA UNDERSTOOD FIRST', 50, '#ffd43b') + '</g>';
  };

  /* NOTE: the caption band covers roughly y > 580 of the 720-high viewBox.
     Nothing readable goes below that line, and no scene repeats its own
     caption word for word - the art shows, the caption tells. */
  /* Iris dives past the paint and finally sees the wall itself */
  S.dive = function (u) {
    return sky(u, 'storm') + rain(40, 31, .45) +
      '<path d="M180,700 L260,200 L1020,200 L1100,700 Z" fill="#adb5bd" stroke="' + INK + '" stroke-width="9"/>' +
      '<rect x="240" y="160" width="800" height="52" rx="10" fill="#868e96" stroke="' + INK + '" stroke-width="8"/>' +
      '<path d="M660,215 q26,110 -18,205 q30,85 8,180 q-14,55 6,100" fill="none" stroke="#12142a" ' +
      'stroke-width="16" stroke-linecap="round" class="pulse"/>' +
      '<path d="M660,215 q26,110 -18,205 q30,85 8,180 q-14,55 6,100" fill="none" stroke="#e03131" ' +
      'stroke-width="7" stroke-linecap="round"/>' +
      '<g transform="translate(300,330) rotate(28)"><g class="bob">' + HERO.iris() + '</g></g>' +
      '<g class="pop d1">' + T(950, 300, 'PAST THE PAINT', 52, '#ffd43b') + '</g>';
  };

  S.clean = function (u) {
    return sky(u, 'dawn') +
      banner('THEY WENT AND GOT THE REAL THING', 'a fresh look, the real voice, tonight’s gauges', '#2f9e44') +
      /* the old card stays readable under its strike - a full X hid the words */
      '<g opacity=".62">' + chip(230, 400, 330, 150, 'THE FAKE', 'paint, a tape,|an old page', '#868e96', 'pop') + '</g>' +
      '<g class="pop d1"><line x1="80" y1="330" x2="380" y2="470" stroke="#e03131" stroke-width="13" stroke-linecap="round"/>' +
      '<circle cx="392" cy="330" r="36" fill="#e03131" stroke="' + INK + '" stroke-width="6"/>' +
      Tplain(392, 344, 'X', 40, '#fff') + '</g>' +
      arrow(450, 620, 400, '#ffd43b', true) +
      chip(880, 400, 420, 190, 'THE REAL THING', 'the wall itself|the real mayor|tonight’s gauges', '#1c7ed6', 'pop d2');
  };

  S.fixed = function (u) {
    var s = sky(u, 'storm') + banner('THIS TIME THEY WERE RIGHT', null, '#2f9e44');
    [['IRIS', 'CRACK. IT’S OPENING.'], ['ECHO', 'EVACUATE. NOW.'], ['NOVA', 'FLOOD. TWO HOURS.']].forEach(function (r, i) {
      var yy = 300 + i * 110;
      s += '<g class="pop d' + (i + 1) + '">' +
        Tplain(330, yy + 12, r[0], 40, '#ffd43b', 'end') +
        arrow(370, 560, yy, '#ffd43b', true) +
        chip(850, yy, 520, 84, '', r[1], '#2f9e44') + '</g>';
    });
    return s;
  };

  S.rescue = function (u) {
    return sky(u, 'storm') + rain(40, 13, .5) + skyline(560, '#20244a', 6, true) +
      '<rect x="0" y="560" width="' + W + '" height="34" fill="#495057" stroke="' + INK + '" stroke-width="7"/>' +
      '<rect y="594" width="' + W + '" height="126" fill="#1b2050"/>' +
      '<g class="pop">' +
      heroAt('meera', 300, 448, .8) + heroAt('meera', 460, 448, .8) + heroAt('meera', 620, 448, .8) +
      '</g>' +
      '<g class="pop d2">' + T(640, 190, 'THE BRIDGE CLEARED', 58, '#ffd43b') + '</g>';
  };

  S.dambreak = function (u) {
    return sky(u, 'storm') +
      '<path d="M180,700 L260,240 L560,240 L520,700 Z" fill="#adb5bd" stroke="' + INK + '" stroke-width="9"/>' +
      '<path d="M760,240 L1020,240 L1100,700 L800,700 Z" fill="#adb5bd" stroke="' + INK + '" stroke-width="9"/>' +
      '<path d="M540,240 q40,120 20,240 q-30,120 40,220 L790,700 q-70,-120 -30,-230 q30,-110 -10,-230 Z" ' +
      'fill="#3b5bdb" stroke="#a5d8ff" stroke-width="8" class="pulse"/>' +
      '<g class="pop">' + T(640, 130, 'NOT ONE PERSON', 62, '#ffd43b') +
      T(640, 208, 'STOOD BELOW IT', 62, '#ffd43b') + '</g>';
  };

  S.staticgone = function (u) {
    return sky(u, 'dawn') + skyline(660, '#2b2f57', 4, true) +
      '<g opacity=".35">' + heroAt('statik', 1080, 420, .8) + '</g>' +
      heroAt('meera', 380, 470, 1.15, 'bob') +
      '<g class="pop d1">' + T(700, 180, 'BUT MEERA KNEW THE RULE', 50, '#ffd43b') + '</g>';
  };

  /* morning after: the reporters, and Meera's last line */
  S.morning = function (u) {
    return sky(u, 'dawn') + skyline(620, '#2b2f57', 4, true) +
      '<circle cx="1050" cy="200" r="70" fill="#ffd43b" opacity=".85"/>' +
      heroAt('meera', 420, 470, 1.15, 'bob') +
      '<g class="pop d1">' +
      '<rect x="700" y="330" width="120" height="80" rx="12" fill="#12142a" stroke="#fdf7ea" stroke-width="6"/>' +
      '<circle cx="760" cy="370" r="24" fill="#495057" stroke="#fdf7ea" stroke-width="5"/>' +
      '<rect x="880" y="350" width="90" height="60" rx="10" fill="#12142a" stroke="#fdf7ea" stroke-width="6"/>' +
      '<circle cx="925" cy="380" r="18" fill="#495057" stroke="#fdf7ea" stroke-width="4"/>' +
      '<rect x="1020" y="336" width="110" height="72" rx="12" fill="#12142a" stroke="#fdf7ea" stroke-width="6"/>' +
      '<circle cx="1075" cy="372" r="21" fill="#495057" stroke="#fdf7ea" stroke-width="5"/>' +
      '</g>' +
      '<g class="pop d2">' + T(640, 150, 'THE NEXT MORNING', 54, '#ffd43b') + '</g>';
  };

  S.finale = function (u) {
    return '<rect width="' + W + '" height="' + H + '" fill="#12142a"/>' +
      '<g class="shine" opacity=".12"><rect x="-300" width="220" height="' + H + '" fill="#fff" transform="skewX(-18)"/></g>' +
      '<g class="pop">' + T(640, 250, '“THEY WEREN’T WRONG.', 74, '#fdf7ea') + '</g>' +
      '<g class="pop d2">' + T(640, 370, 'THEY WERE TOLD WRONG.”', 74, '#ffd43b') + '</g>' +
      '<g class="pop d3">' + Tplain(640, 480, '— Meera, aged eleven', 34, '#adb5bd') + '</g>';
  };

  /* ------------------------------------------------------- caption track
     Each line is one on-screen caption. `w` is a rough spoken-length weight
     (characters, plus a bonus where the narrator pauses between paragraphs).
     app.js turns the weights into real times using the audio's own duration,
     so the sync holds even if the mp3 is ever re-recorded slightly longer. */
  var LINES = [
    ['clock', 'Eleven minutes to midnight,', 0.00],
    ['storm', 'and the rain over Nova City had not stopped for nine days.', 1.83],

    ['dam', 'High on the ridge above the houses stood the old dam,', 6.14],
    ['dam', 'holding back a lake that had grown far too big for it.', 9.50],

    ['team', 'Four Sentinels guarded the city.', 13.47],

    ['echo', 'Captain Echo, who could hear a whisper across nine streets,', 16.26],
    ['echo', 'and write down every word of it.', 19.87],

    ['iris', 'Iris, who flew, and named whatever her camera eye landed on.', 22.59],

    ['nova', 'Nova, who read the rain gauges and the river marks,', 27.67],
    ['nova', 'and said one word. Safe. Or not safe.', 30.69],

    ['rex', 'And Rex, the robot dog, who answered any question out loud,', 35.56],
    ['rex', 'in a voice like a kettle.', 39.37],

    ['allwrong', 'That night, all four of them were wrong.', 41.74],

    ['zebra', 'At six minutes to midnight, Iris circled the dam wall,', 44.83],
    ['zebra', 'looked straight at it, and said: “Zebra.”', 48.62],

    ['fakevoice', 'Echo tilted her head towards the town hall, listened,', 52.80],
    ['fakevoice', 'and wrote: “The mayor says there is nothing to worry about.”', 55.65],

    ['oldnum', 'Nova checked her numbers twice, and said: “Safe.”', 60.95],

    ['rexwrong', 'And Rex, asked where the danger was,', 65.26],
    ['rexwrong', 'wagged his antenna and said: “There is no danger.”', 67.74],

    ['meera', 'On the bridge, a girl named Meera stopped walking.', 72.29],

    ['meera', 'Meera was eleven. No cape. No camera. No antenna.', 76.13],
    ['meera', 'What she had was a clear view of the dam wall.', 81.50],
    ['zebra', 'And the dam wall had black stripes painted across it,', 84.74],
    ['zebra', 'still wet, shining in the rain.', 87.87],

    ['meera', 'She turned round.', 90.85],
    ['statik', 'Behind the heroes, in the dark between two lamps, something flickered.', 92.50],
    ['statik', 'Not a person, exactly. A shape made of broken signal.', 97.51],
    ['statik', 'Bars, and crackle, and two red eyes.', 101.99],

    ['attack', 'It had not touched a single hero.', 105.69],

    ['attack', 'It had spent all nine days of that rain painting a wall,', 108.10],
    ['attack', 'recording a voice, and swapping one page of numbers for another.', 111.73],

    ['meera', '“Iris! Fly closer! Get past the paint!”', 117.40],

    ['dive', 'Iris dropped through the rain, so close her cape brushed the concrete,', 121.56],
    ['dive', 'and looked again. At the wall itself.', 125.81],
    ['dive', 'At the crack running down it like a black river.', 129.31],

    ['fixed', '“Crack,” said Iris. “It’s opening.”', 132.74],

    ['clean', 'Echo turned away from the recording, and found the real mayor,', 136.47],
    ['clean', 'soaked, shouting on the town hall steps.', 140.73],

    ['fixed', '“Evacuate,” wrote Echo. “Now.”', 143.54],

    ['clean', 'Nova threw the old page into the water, and read tonight’s gauges.', 147.23],

    ['fixed', '“Flood,” she said. “Two hours. Maybe less.”', 152.01],

    ['rescue', 'It took forty minutes to clear the low streets.', 156.32],
    ['staticgone', 'The Static was gone by then.', 159.31],
    ['staticgone', 'It never stays where people are looking.', 161.54],

    ['dambreak', 'At sixteen minutes past two, the dam broke.', 164.44],

    ['dambreak', 'The water came down the valley, through the empty market,', 168.21],
    ['dambreak', 'under the empty bridge, and out to the sea.', 171.64],

    ['dambreak', 'Not one person was standing below it.', 175.03],

    ['morning', 'And in the morning, when the reporters asked Meera', 179.03],
    ['morning', 'how four superheroes had all been wrong on the same night,', 182.32],
    ['morning', 'she thought about it for a moment, and said:', 184.77],

    ['finale', '“They weren’t wrong. They were told wrong.”', 187.70]
  ];

  /* build the stage markup once; scene svgs are reused across repeated lines */
  function build() {
    var order = [], seen = {}, i, k;
    for (i = 0; i < LINES.length; i++) {
      k = LINES[i][0];
      if (!seen[k]) { seen[k] = true; order.push(k); }
    }
    var html = '<style>' + CSS + '</style>';
    for (i = 0; i < order.length; i++) {
      k = order[i];
      html += '<svg class="scene" data-scene="' + k + '" viewBox="0 0 ' + W + ' ' + H +
        '" preserveAspectRatio="xMidYMid slice">' + S[k](i) + '</svg>';
    }
    return html;
  }

  /* Caption times were measured against the real narration: the silent gaps in
     narration.mp3 were located, and every line anchored to the pause in front of
     it (mean error 0.3 s). They scale if the audio is ever re-recorded at a
     different length, so a fresh voiceover still lines up roughly. */
  function track(duration) {
    var k = (duration && duration > 1) ? duration / 190.35 : 1;
    return LINES.map(function (l) {
      return { at: l[2] * k, scene: l[0], text: l[1] };
    });
  }

  window.STORY = { build: build, track: track, lines: LINES };
})();
