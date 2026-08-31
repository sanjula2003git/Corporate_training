/* scenes.js - the narrated story "The Leaf Machine".

   Every scene is one <svg class="scene"> stacked inside the stage; app.js turns
   exactly one of them "live" at a time. Pure SVG + CSS. No image files.

   FOUR RULES if you touch anything in here.

     1. Never put an animation class on a <g> that also carries a transform
        attribute. A CSS transform REPLACES the attribute and the artwork snaps
        to the top-left corner. Position on an outer <g>, animate on an inner one.

     2. Nothing readable goes below about y=560. The caption band covers it.

     3. No teaching words anywhere - not in the narration, not painted into the
        artwork. The story must never say data, input, output, pattern, model,
        training, prediction, domain, feedback, vision, automation or password.
        Those are the answers. If they appear before Round 1 the assessment
        stops measuring anything and becomes a memory test of the video.

     4. ICONS is the single source of truth for the machine's 64-dot screen.
        The same eight strings are drawn on screen here AND used as the
        right answers in Round 1. Change a pattern and the answer changes with
        it - which is the point. Never hard-code a Round 1 answer in app.js.  */

window.STORY = (function () {
  var W = 1280, H = 720;
  var INK = '#12142a';

  /* ------------------------------------------------------------------ the
     sixty-four dots. Eight rows of eight characters; '#' is a lit dot.
     These are what the child reproduces in Round 1.                      */
  var ICONS = {
    /* the first thing it ever showed: it knew nothing yet */
    q: [
      '..####..',
      '.#....#.',
      '......#.',
      '.....#..',
      '....#...',
      '....#...',
      '........',
      '....#...'
    ],
    /* the narrow pointed leaf. It showed this for the neem - and then for
       the tulsi, the chair, the shoe and the umbrella as well.
       Pointed at BOTH ends with a short stem. An earlier version had a long
       two-wide stem and read as a dagger, not a leaf, which made nonsense of
       the caption calling it a narrow pointed shape. */
    neem: [
      '...#....',
      '..###...',
      '.#####..',
      '.#####..',
      '.#####..',
      '..###...',
      '...#....',
      '...#....'
    ],
    /* the wide leaf with the long drip tip. Its answer for a plastic leaf. */
    peepal: [
      '.##..##.',
      '.######.',
      '.######.',
      '..####..',
      '...##...',
      '...##...',
      '....#...',
      '....#...'
    ],
    /* what it put up on Friday when it got the curry leaf right */
    tick: [
      '........',
      '......##',
      '.....##.',
      '....##..',
      '#...##..',
      '##.##...',
      '.####...',
      '..##....'
    ],
    /* not used as an answer - just the dark screen at night */
    off: [
      '........',
      '........',
      '........',
      '........',
      '........',
      '........',
      '........',
      '........'
    ]
  };

  /* ---------------------------------------------------------------- css */
  var CSS = [
    '.scene text{font-family:"Trebuchet MS","Segoe UI",Verdana,sans-serif;font-weight:bold}',
    '@keyframes bob{0%,100%{transform:translateY(0)}50%{transform:translateY(-11px)}}',
    '@keyframes bob2{0%,100%{transform:translateY(0)}50%{transform:translateY(8px)}}',
    '@keyframes sway{0%,100%{transform:rotate(-1.6deg)}50%{transform:rotate(1.6deg)}}',
    '@keyframes tilt{0%,100%{transform:rotate(-4deg)}50%{transform:rotate(4deg)}}',
    '@keyframes pulse{0%,100%{transform:scale(1)}50%{transform:scale(1.06)}}',
    '@keyframes blink{0%,100%{opacity:1}50%{opacity:.18}}',
    '@keyframes glow{0%,100%{opacity:.35}50%{opacity:1}}',
    '@keyframes dashmove{to{stroke-dashoffset:-240}}',
    '@keyframes dust{0%{opacity:.8;transform:translate(0,0) scale(.6)}',
    '100%{opacity:0;transform:translate(-40px,-46px) scale(1.5)}}',
    '@keyframes grow{from{transform:scale(.35);opacity:0}to{transform:scale(1);opacity:1}}',
    '@keyframes shake{0%,100%{transform:translate(0,0)}25%{transform:translate(-3px,1px)}',
    '50%{transform:translate(3px,-1px)}75%{transform:translate(-2px,-2px)}}',
    '@keyframes flyin{from{transform:translate(320px,150px) scale(.3);opacity:0}',
    'to{transform:translate(0,0) scale(1);opacity:1}}',
    '.bob{animation:bob 3.4s ease-in-out infinite}',
    '.bob2{animation:bob2 4.1s ease-in-out infinite}',
    '.sway{animation:sway 4.4s ease-in-out infinite;transform-box:fill-box;transform-origin:bottom center}',
    '.tilt{animation:tilt 3.1s ease-in-out infinite;transform-box:fill-box;transform-origin:center}',
    '.pulse{animation:pulse 2.2s ease-in-out infinite;transform-box:fill-box;transform-origin:center}',
    '.blink{animation:blink 1.5s ease-in-out infinite}',
    '.glow{animation:glow 1.9s ease-in-out infinite}',
    '.shake{animation:shake .5s ease-in-out infinite}',
    '.flow{stroke-dasharray:20 15;animation:dashmove 2.6s linear infinite}',
    '.dust{animation:dust 2.6s ease-out infinite;transform-box:fill-box;transform-origin:center}',
    '.dust.d1{animation-delay:.5s}.dust.d2{animation-delay:1s}.dust.d3{animation-delay:1.6s}',
    '.scene.live .pop{animation:grow .5s cubic-bezier(.2,1.5,.4,1) both;transform-box:fill-box;transform-origin:center}',
    '.scene.live .fly{animation:flyin .8s cubic-bezier(.2,1,.4,1) both;transform-box:fill-box;transform-origin:center}',
    '.scene.live .d1{animation-delay:.35s}.scene.live .d2{animation-delay:.7s}',
    '.scene.live .d3{animation-delay:1.05s}.scene.live .d4{animation-delay:1.4s}',
    '.scene.live .d5{animation-delay:1.75s}.scene.live .d6{animation-delay:2.1s}',
    '.scene.live .d7{animation-delay:2.45s}.scene.live .d8{animation-delay:2.8s}'
  ].join('\n');

  /* ------------------------------------------------------------ helpers */

  function rr(x, y, w, h, r, fill, stroke, sw) {
    return '<rect x="' + x + '" y="' + y + '" width="' + w + '" height="' + h +
      '" rx="' + r + '" fill="' + fill + '"' +
      (stroke ? ' stroke="' + stroke + '" stroke-width="' + (sw || 4) + '"' : '') + '/>';
  }
  function circ(cx, cy, r, fill, stroke, sw) {
    return '<circle cx="' + cx + '" cy="' + cy + '" r="' + r + '" fill="' + fill + '"' +
      (stroke ? ' stroke="' + stroke + '" stroke-width="' + (sw || 4) + '"' : '') + '/>';
  }
  function P(d, fill, stroke, sw, extra) {
    return '<path d="' + d + '" fill="' + (fill || 'none') + '"' +
      (stroke ? ' stroke="' + stroke + '" stroke-width="' + (sw || 4) +
        '" stroke-linecap="round" stroke-linejoin="round"' : '') +
      (extra ? ' ' + extra : '') + '/>';
  }
  function ell(cx, cy, rx, ry, fill, stroke, sw) {
    return '<ellipse cx="' + cx + '" cy="' + cy + '" rx="' + rx + '" ry="' + ry +
      '" fill="' + fill + '"' +
      (stroke ? ' stroke="' + stroke + '" stroke-width="' + (sw || 4) + '"' : '') + '/>';
  }
  /* heavy comic lettering: the ink stroke is painted behind the fill */
  function T(x, y, s, size, fill, anchor) {
    return '<text x="' + x + '" y="' + y + '" font-size="' + size + '" fill="' + fill +
      '" text-anchor="' + (anchor || 'middle') + '" stroke="' + INK + '" stroke-width="' +
      Math.max(3, size / 7) + '" paint-order="stroke">' + s + '</text>';
  }
  function Tp(x, y, s, size, fill, anchor) {
    return '<text x="' + x + '" y="' + y + '" font-size="' + size + '" fill="' + fill +
      '" text-anchor="' + (anchor || 'middle') + '">' + s + '</text>';
  }
  /* outer positioning group. Animations must go on a group INSIDE this one. */
  function g(x, y, s, inner) {
    return '<g transform="translate(' + x + ',' + y + ') scale(' + (s === undefined ? 1 : s) + ')">' +
      inner + '</g>';
  }
  /* the same, with a rotation - for the scattered leaves */
  function gr(x, y, s, deg, inner) {
    return '<g transform="translate(' + x + ',' + y + ') rotate(' + deg + ') scale(' +
      (s === undefined ? 1 : s) + ')">' + inner + '</g>';
  }

  /* -------------------------------------------------- the 64-dot screen */
  /* Drawn at 0,0 in local coordinates, 8 cells of `cell` px with `gap` between.
     `key` is a name in ICONS. Lit dots glow, dark dots stay sunk. */
  function dots(key, cell, gap, litClass) {
    var pat = ICONS[key] || ICONS.off, out = '', r, c, x, y, on;
    gap = gap === undefined ? 3 : gap;
    for (r = 0; r < 8; r++) {
      for (c = 0; c < 8; c++) {
        on = pat[r].charAt(c) === '#';
        x = c * (cell + gap);
        y = r * (cell + gap);
        out += '<rect x="' + x + '" y="' + y + '" width="' + cell + '" height="' + cell +
          '" rx="' + Math.max(2, cell * 0.18) + '" fill="' + (on ? '#5ee27a' : '#204029') +
          '"' + (on && litClass ? ' class="' + litClass + '"' : '') + '/>';
      }
    }
    return out;
  }
  function screenSize(cell, gap) { return 8 * cell + 7 * (gap === undefined ? 3 : gap); }

  /* ------------------------------------------------------- the machine */
  /* Local box is 300 wide x 372 tall, origin top-left.
     opts: {icon, label, eye:'off'|'on', dim:true}                          */
  function machine(opts) {
    opts = opts || {};
    var icon = opts.icon || 'off';
    var eyeOn = opts.eye !== 'off';
    var cell = 20, gap = 3, sw = screenSize(cell, gap);   /* 181 */
    var sx = (300 - sw) / 2, sy = 122;
    var body = opts.dim ? '#5b6070' : '#9aa0b0';
    var out = '';

    /* body + a lighter face plate */
    out += rr(0, 0, 300, 372, 26, body, INK, 6);
    out += rr(14, 14, 272, 344, 18, opts.dim ? '#6a7080' : '#b5bac8', INK, 4);

    /* the one glass eye */
    out += circ(150, 70, 44, '#2b3040', INK, 6);
    out += circ(150, 70, 31, eyeOn ? '#1c7ed6' : '#3b4152', INK, 4);
    if (eyeOn) {
      out += '<g class="glow">' + circ(150, 70, 17, '#d0ebff', '', 0) + '</g>';
      out += circ(141, 61, 7, '#ffffff', '', 0);
    } else {
      out += circ(150, 70, 15, '#4a5164', '', 0);
    }

    /* the screen, sunk into the face */
    out += rr(sx - 12, sy - 12, sw + 24, sw + 24, 12, '#14261a', INK, 5);
    out += g(sx, sy, 1, dots(icon, cell, gap, opts.dim ? '' : 'glow'));

    /* a scratched name plate, low enough to stay clear of nothing readable */
    out += rr(58, 322, 184, 34, 8, '#e9ecf2', INK, 4);
    out += Tp(150, 346, 'LEAF READER', 19, '#3a3f66');
    return out;
  }

  /* ----------------------------------------------------------- children */
  /* Feet land at y=182 in local coordinates, body is about 70 wide.
     opts: {shirt, skin, hair, arms:'up'|'out'|'down', hairStyle:'plait'|'short'} */
  function kid(opts) {
    opts = opts || {};
    var shirt = opts.shirt || '#1c7ed6';
    var skin = opts.skin || '#e0ac69';
    var hair = opts.hair || '#241a12';
    var arms = opts.arms || 'down';
    var out = '';

    /* legs first so the shirt overlaps them */
    out += rr(17, 126, 16, 48, 7, '#39415c', INK, 4);
    out += rr(38, 126, 16, 48, 7, '#39415c', INK, 4);
    out += rr(12, 168, 26, 14, 6, '#2b3040', INK, 4);
    out += rr(34, 168, 26, 14, 6, '#2b3040', INK, 4);

    /* arms */
    if (arms === 'up') {
      out += P('M14 76 L-4 24', '', skin, 15);
      out += P('M56 76 L74 24', '', skin, 15);
    } else if (arms === 'out') {
      out += P('M14 78 L-14 96', '', skin, 15);
      out += P('M56 78 L84 96', '', skin, 15);
    } else {
      out += P('M14 78 L6 122', '', skin, 15);
      out += P('M56 78 L64 122', '', skin, 15);
    }

    /* torso */
    out += rr(9, 62, 52, 70, 15, shirt, INK, 4);
    out += P('M26 62 L35 80 L44 62', '', '#ffffff', 5);

    /* head */
    out += circ(35, 34, 27, skin, INK, 4);
    if (opts.hairStyle === 'plait') {
      out += P('M8 30 Q10 -2 35 -2 Q60 -2 62 30 Q56 12 35 12 Q14 12 8 30 Z', hair, INK, 3);
      out += P('M62 30 Q74 52 68 78', '', hair, 9);
    } else {
      out += P('M8 30 Q10 -2 35 -2 Q60 -2 62 30 Q52 14 35 14 Q18 14 8 30 Z', hair, INK, 3);
    }
    out += circ(26, 34, 3.4, INK, '', 0);
    out += circ(44, 34, 3.4, INK, '', 0);
    out += P('M26 45 Q35 52 44 45', '', INK, 3.4);
    return out;
  }

  /* an adult - taller, sari or jacket, used for the judge and the teacher */
  function grown(opts) {
    opts = opts || {};
    var coat = opts.coat || '#c2255c';
    var skin = opts.skin || '#d9975a';
    var hair = opts.hair || '#1d1710';
    var out = '';
    out += rr(20, 150, 18, 52, 8, '#39415c', INK, 4);
    out += rr(46, 150, 18, 52, 8, '#39415c', INK, 4);
    out += rr(14, 196, 30, 14, 6, '#2b3040', INK, 4);
    out += rr(42, 196, 30, 14, 6, '#2b3040', INK, 4);
    if (opts.arms === 'out') {
      out += P('M16 84 L-18 106', '', skin, 16);
      out += P('M68 84 L100 104', '', skin, 16);
    } else {
      out += P('M16 84 L8 140', '', skin, 16);
      out += P('M68 84 L78 140', '', skin, 16);
    }
    out += P('M10 66 L74 66 L84 168 L0 168 Z', coat, INK, 4);
    out += circ(42, 36, 29, skin, INK, 4);
    out += P('M12 32 Q14 -2 42 -2 Q70 -2 72 32 Q62 14 42 14 Q22 14 12 32 Z', hair, INK, 3);
    out += P('M12 30 Q4 60 8 88', '', hair, 10);
    out += circ(33, 36, 3.4, INK, '', 0);
    out += circ(51, 36, 3.4, INK, '', 0);
    out += P('M33 47 Q42 54 51 47', '', INK, 3.4);
    return out;
  }

  /* -------------------------------------------------------- other props */

  function tree(scale) {
    var out = '';
    out += P('M92 300 L92 150 M92 210 L52 168 M92 236 L134 194', '', '#7a5230', 17);
    out += circ(92, 118, 74, '#2f9e44', INK, 5);
    out += circ(36, 152, 46, '#37b24d', INK, 5);
    out += circ(150, 152, 46, '#37b24d', INK, 5);
    out += circ(92, 176, 44, '#2b8a3e', INK, 5);
    return g(0, 0, scale === undefined ? 1 : scale, out);
  }

  /* a single leaf, used loose on tables and in the spread */
  function leafShape(w, h, fill, tip) {
    /* pointed both ends, stem hanging down */
    var d = 'M0 0 Q' + (w / 2) + ' ' + (-h / 2) + ' 0 ' + (-h) +
      ' Q' + (-w / 2) + ' ' + (-h / 2) + ' 0 0 Z';
    return P(d, fill, INK, 3.5) + (tip ? P('M0 0 L0 ' + (h * 0.3), '', '#7a5230', 4) : '');
  }

  /* The tulsi. Round 1 question 2 sends the child back to this plant, so it
     has to be plainly a leafy plant in a red pot, not a few green specks. */
  function pot(scale, plant) {
    var out = '';
    if (plant !== false) {
      out += P('M60 96 L60 6 M60 62 L28 40 M60 48 L92 28', '', '#2b8a3e', 8);
      out += gr(60, 10, 1.5, 0, leafShape(30, 40, '#40c057'));
      out += gr(28, 44, 1.4, -32, leafShape(28, 38, '#37b24d'));
      out += gr(92, 32, 1.4, 30, leafShape(28, 38, '#37b24d'));
      out += gr(60, 52, 1.3, 0, leafShape(26, 34, '#2f9e44'));
      out += gr(30, 82, 1.3, -48, leafShape(26, 34, '#40c057'));
      out += gr(92, 76, 1.3, 44, leafShape(26, 34, '#40c057'));
      out += gr(60, 92, 1.2, 0, leafShape(24, 30, '#37b24d'));
    }
    out += P('M24 96 L96 96 L86 158 L34 158 Z', '#c9522b', INK, 5);
    out += rr(18, 86, 84, 20, 7, '#e0603a', INK, 5);
    return g(0, 0, scale === undefined ? 1 : scale, out);
  }

  function crate(scale) {
    var out = '';
    out += rr(0, 0, 260, 190, 8, '#b5813f', INK, 6);
    out += P('M0 46 L260 46 M0 144 L260 144 M0 0 L260 190 M260 0 L0 190', '', '#8a6130', 5);
    out += rr(0, 0, 260, 190, 8, 'none', INK, 6);
    return g(0, 0, scale === undefined ? 1 : scale, out);
  }

  function photo(w, h, fill) {
    return rr(0, 0, w, h, 5, '#ffffff', INK, 4) +
      rr(6, 6, w - 12, h - 22, 3, fill || '#8ce99a', INK, 3);
  }

  function phone(scale) {
    var out = rr(0, 0, 92, 168, 12, '#2b3040', INK, 5) + rr(7, 14, 78, 132, 5, '#dfe6f0', INK, 3);
    var i, x, y, cols = ['#8ce99a', '#69db7c', '#b2f2bb', '#40c057', '#d8f5a2', '#94d82d'];
    for (i = 0; i < 12; i++) {
      x = 11 + (i % 3) * 26; y = 18 + Math.floor(i / 3) * 32;
      out += rr(x, y, 22, 28, 3, cols[i % 6], INK, 2);
    }
    return g(0, 0, scale === undefined ? 1 : scale, out);
  }

  /* ------------------------------------------------------- backgrounds */

  function room(opts) {
    opts = opts || {};
    var wall = opts.night ? '#1c2340' : '#f7e9cb';
    var floor = opts.night ? '#141a30' : '#c9a97a';
    var out = rr(0, 0, W, 520, 0, wall) + rr(0, 500, W, 220, 0, floor) +
      rr(0, 494, W, 14, 0, opts.night ? '#0f1424' : '#a2814f');
    if (opts.window) {
      out += rr(940, 60, 250, 200, 10, opts.night ? '#0b1024' : '#a5d8ff', INK, 6);
      out += P('M1065 60 L1065 260 M940 160 L1190 160', '', INK, 5);
      if (opts.night) out += circ(1130, 106, 26, '#ffe066', '', 0);
    }
    if (opts.board) {
      out += rr(70, 66, 430, 250, 10, opts.night ? '#16241a' : '#22492e', INK, 6);
      out += rr(70, 306, 430, 18, 5, '#a2814f', INK, 4);
    }
    return out;
  }

  function outdoors(opts) {
    opts = opts || {};
    var out = '<defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">' +
      '<stop offset="0" stop-color="' + (opts.evening ? '#ff922b' : '#a5d8ff') + '"/>' +
      '<stop offset="1" stop-color="' + (opts.evening ? '#ffd8a8' : '#e7f5ff') + '"/>' +
      '</linearGradient></defs>';
    out += rr(0, 0, W, 540, 0, 'url(#sky)');
    out += circ(opts.evening ? 1090 : 1120, 108, 46, opts.evening ? '#fd7e14' : '#ffd43b', INK, 5);
    out += rr(0, 500, W, 220, 0, '#69db7c');
    out += rr(0, 494, W, 16, 0, '#40c057');
    return out;
  }

  function hall() {
    var out = rr(0, 0, W, 520, 0, '#efe3f7') + rr(0, 500, W, 220, 0, '#b197c4') +
      rr(0, 494, W, 14, 0, '#8f76a3');
    /* bunting, well above the caption band */
    var i, x;
    out += P('M0 34 Q640 96 1280 34', '', INK, 4);
    for (i = 0; i < 13; i++) {
      x = 44 + i * 98;
      out += P('M' + x + ' ' + (36 + Math.sin(i / 12 * Math.PI) * 26) +
        ' l22 0 l-11 34 Z', ['#e03131', '#ffd43b', '#1c7ed6', '#2f9e44'][i % 4], INK, 3);
    }
    return out;
  }

  /* a table the props stand on */
  function table(x, y, w) {
    return rr(x, y, w, 20, 6, '#a2814f', INK, 5) +
      rr(x + 18, y + 20, 18, 96, 5, '#8a6130', INK, 4) +
      rr(x + w - 36, y + 20, 18, 96, 5, '#8a6130', INK, 4);
  }

  /* a speech card the machine "says" - big block letters on the screen side */
  function shout(x, y, s, size, fill) {
    return T(x, y, s, size || 62, fill || '#ffd43b');
  }

  /* =====================================================================
     THE SCENES
     Each is {line: what is spoken and captioned, art: svg, dur: fallback ms}
     `dur` is only used when the browser has no speech voice; app.js drives
     the timing off real speech events whenever it can.
     ===================================================================== */

  var S = [];

  /* 1 - the school, four days out */
  S.push({
    line: 'Ganga Vidyalaya. Four days before the science exhibition.',
    dur: 3600,
    art:
      outdoors() +
      /* school block */
      rr(150, 190, 620, 320, 14, '#ffe8cc', INK, 6) +
      rr(150, 150, 620, 60, 10, '#e8590c', INK, 6) +
      rr(232, 268, 92, 92, 8, '#a5d8ff', INK, 5) +
      rr(392, 268, 92, 92, 8, '#a5d8ff', INK, 5) +
      rr(552, 268, 92, 92, 8, '#a5d8ff', INK, 5) +
      rr(400, 400, 120, 110, 8, '#7a5230', INK, 5) +
      g(0, 0, 1, tree(1.15)) +
      g(830, 210, 1.25, tree(1)) +
      /* gate sign */
      rr(150, 96, 620, 54, 10, '#ffd43b', INK, 6) +
      Tp(460, 134, 'GANGA VIDYALAYA', 34, INK) +
      T(1060, 350, '4 DAYS', 46, '#e03131') +
      T(1060, 400, 'TO GO', 46, '#e03131')
  });

  /* 2 - the crate */
  S.push({
    line: 'A crate came for Class Six. No letter with it. Just a name scratched into the wood. ' +
      'LEAF READER. And a great deal of dust.',
    dur: 7200,
    art:
      room({ window: true }) +
      /* the crate is the subject, so it gets the middle and the name goes
         ON it. Everyone else stands clear of the lettering. */
      g(390, 268, 1.2, crate(1)) +
      Tp(546, 400, 'LEAF  READER', 40, '#5c3d18') +
      /* dust puffs - the animation class sits on an inner group */
      g(720, 258, 1, '<g class="dust">' + circ(0, 0, 16, '#e9d9b8', '', 0) + '</g>') +
      g(766, 296, 1, '<g class="dust d1">' + circ(0, 0, 12, '#e9d9b8', '', 0) + '</g>') +
      g(704, 322, 1, '<g class="dust d2">' + circ(0, 0, 19, '#e9d9b8', '', 0) + '</g>') +
      g(786, 244, 1, '<g class="dust d3">' + circ(0, 0, 10, '#e9d9b8', '', 0) + '</g>') +
      g(120, 330, 1, kid({ shirt: '#e03131', hairStyle: 'plait', arms: 'out' })) +
      g(232, 330, 1, kid({ shirt: '#1c7ed6', skin: '#c68642' })) +
      g(1040, 330, 1, kid({ shirt: '#2f9e44', skin: '#8d5524', hair: '#100c08' }))
  });

  /* 3 - unboxed */
  S.push({
    line: 'Inside was a grey box with one glass eye, and a little screen made of dots. ' +
      'Sixty-four dots. That was everything it had to speak with.',
    dur: 7600,
    art:
      /* no blackboard here - the "64 DOTS" callout was being written on it in
         dark blue on dark green and could not be read at all */
      room({ window: true }) +
      table(440, 452, 420) +
      g(500, 84, 1, machine({ icon: 'off', eye: 'off' })) +
      /* the callout, on its own card where it is actually legible */
      g(96, 150, 1, rr(0, 0, 232, 168, 16, '#ffd43b', INK, 6) +
        Tp(116, 92, '64', 76, INK) + Tp(116, 138, 'DOTS', 32, '#5c3d18')) +
      g(200, 330, 1, kid({ shirt: '#e03131', hairStyle: 'plait', arms: 'out' })) +
      g(940, 330, 1, kid({ shirt: '#1c7ed6', skin: '#c68642', arms: 'out' }))
  });

  /* 4 - switched on: the question mark. ROUND 1 ANSWER. */
  S.push({
    line: 'Meher switched it on. The eye lit up. On the sixty-four dots came a crooked ' +
      'question mark, and nothing else at all.',
    dur: 7400,
    art:
      room({ board: true }) +
      /* big, centred, unmistakable - the child has to redraw this later */
      g(408, 40, 1.32, machine({ icon: 'q', eye: 'on' })) +
      g(120, 320, 1, kid({ shirt: '#e03131', hairStyle: 'plait', arms: 'up' })) +
      g(1080, 320, 1, kid({ shirt: '#1c7ed6', skin: '#c68642' })) +
      '<g class="pop d3">' + T(1050, 190, 'CLICK', 44, '#ffd43b') + '</g>'
  });

  /* 5 - fifty photographs of one tree */
  S.push({
    line: 'So Arjun went out and photographed the neem tree by the gate. Fifty photographs. ' +
      'The same tree, from the same bench, in the same four o\'clock light. Fifty times.',
    dur: 9400,
    art:
      outdoors({ evening: false }) +
      g(120, 130, 1.6, tree(1)) +
      /* the bench he photographs from, every single time */
      rr(620, 448, 220, 16, 5, '#a2814f', INK, 5) +
      rr(620, 400, 220, 14, 5, '#a2814f', INK, 5) +
      rr(632, 464, 14, 48, 4, '#8a6130', INK, 4) +
      rr(814, 464, 14, 48, 4, '#8a6130', INK, 4) +
      /* Arjun standing beside it, camera IN his hand, not floating near it */
      g(700, 300, 1, kid({ shirt: '#1c7ed6', skin: '#c68642', arms: 'out' })) +
      g(760, 372, 1, rr(0, 0, 74, 52, 9, '#2b3040', INK, 5) +
        circ(37, 26, 16, '#a5d8ff', INK, 4) + rr(52, 8, 14, 8, 3, '#e03131', INK, 3)) +
      T(1090, 250, '50', 88, '#e03131') +
      Tp(1090, 300, 'PHOTOS', 30, INK) +
      Tp(1090, 344, 'ONE TREE', 26, '#5c3d18') +
      /* the same clock every time */
      g(500, 118, 1, circ(0, 0, 46, '#ffffff', INK, 5) + P('M0 0 L0 -28 M0 0 L20 6', '', INK, 5)) +
      Tp(500, 198, '4 O\'CLOCK', 24, INK)
  });

  /* 6 - feeding them in */
  S.push({
    line: 'They poured all fifty into the box, and went home for the night.',
    dur: 4400,
    art:
      room({}) +
      table(620, 452, 380) +
      g(690, 84, 1, machine({ icon: 'off', eye: 'on' })) +
      /* a stream of identical photographs going in - big enough to see that
         every one of them is the same picture */
      g(70, 130, 1, '<g class="fly d1">' + photo(120, 142, '#69db7c') + '</g>') +
      g(70, 310, 1, '<g class="fly d2">' + photo(120, 142, '#69db7c') + '</g>') +
      g(230, 220, 1, '<g class="fly d3">' + photo(120, 142, '#69db7c') + '</g>') +
      g(390, 130, 1, '<g class="fly d4">' + photo(120, 142, '#69db7c') + '</g>') +
      g(390, 310, 1, '<g class="fly d5">' + photo(120, 142, '#69db7c') + '</g>') +
      P('M520 250 Q610 250 676 250', '', '#1c7ed6', 7, 'class="flow"') +
      Tp(300, 106, 'ALL FIFTY THE SAME', 26, '#5c3d18')
  });

  /* 7 - Tuesday, it works */
  S.push({
    line: 'On Tuesday it woke up clever. Arjun held the eye towards the neem, and before he ' +
      'could blink, a narrow pointed shape lit up on the dots. NEEM. Faster than any of them ' +
      'could have looked it up.',
    dur: 10200,
    art:
      outdoors() +
      g(60, 170, 1.4, tree(1)) +
      g(700, 150, 0.86, machine({ icon: 'neem', eye: 'on' })) +
      P('M690 300 L470 300', '', '#e03131', 7, 'class="flow"') +
      '<g class="pop d3">' + shout(1080, 250, 'NEEM', 66) + '</g>' +
      g(590, 330, 0.82, kid({ shirt: '#1c7ed6', skin: '#c68642', arms: 'out' }))
  });

  /* 8 - they shout */
  S.push({
    line: 'They shouted. Devu, who never shouted at anything, shouted.',
    dur: 4200,
    art:
      room({ board: true, window: true }) +
      g(200, 300, 1.1, kid({ shirt: '#e03131', hairStyle: 'plait', arms: 'up' })) +
      g(520, 290, 1.15, kid({ shirt: '#1c7ed6', skin: '#c68642', arms: 'up' })) +
      g(860, 300, 1.1, kid({ shirt: '#2f9e44', skin: '#8d5524', hair: '#100c08', arms: 'up' })) +
      '<g class="pop d1">' + T(250, 150, 'YESSS', 52, '#ffd43b') + '</g>' +
      '<g class="pop d2">' + T(640, 118, 'IT WORKS', 52, '#ffd43b') + '</g>' +
      '<g class="pop d3">' + T(980, 158, 'WHOOO', 52, '#ffd43b') + '</g>'
  });

  /* 9 - Wednesday, the judge and her tulsi */
  S.push({
    line: 'On Wednesday the head judge came early to see how they were getting on. ' +
      'She set her own plant on the table. A tulsi, in a red clay pot.',
    dur: 8200,
    art:
      room({ window: true }) +
      table(300, 452, 520) +
      /* the tulsi big and clear - Round 1 question 2 sends them back here */
      g(360, 200, 1.6, pot(1)) +
      g(660, 200, 0.62, machine({ icon: 'off', eye: 'on' })) +
      g(1010, 250, 1.06, grown({ coat: '#c2255c', arms: 'out' })) +
      g(120, 320, 1, kid({ shirt: '#e03131', hairStyle: 'plait' })) +
      '<g class="pop d3">' + T(452, 168, 'TULSI', 40, '#ffd43b') + '</g>'
  });

  /* 10 - it says NEEM. ROUND 1 ANSWER (the same pointed shape). */
  S.push({
    line: 'The eye looked. The dots lit up. The very same narrow pointed shape. NEEM. ' +
      'It was not even a little bit unsure.',
    dur: 7400,
    art:
      room({ board: true }) +
      g(408, 40, 1.32, machine({ icon: 'neem', eye: 'on' })) +
      g(70, 300, 0.95, pot(1)) +
      P('M210 330 L400 330', '', '#e03131', 7, 'class="flow"') +
      '<g class="pop d3">' + shout(1080, 250, 'NEEM', 62) + '</g>' +
      '<g class="pop d4">' + Tp(1080, 320, 'not even a little unsure', 24, '#3a3f66') + '</g>'
  });

  /* 11 - a chair, a shoe, an umbrella */
  S.push({
    line: 'Arjun turned it towards a chair. NEEM. A shoe. NEEM. The headmaster\'s green ' +
      'umbrella going past the window. NEEM, NEEM, NEEM.',
    dur: 8600,
    art:
      room({}) +
      /* three little panels, each with the same answer under it */
      g(80, 120, 1, rr(0, 0, 340, 340, 16, '#ffffff', INK, 6) +
        /* a chair, seen from the side. The earlier version was two uprights
           and a rail and read as a capital H. */
        rr(206, 44, 24, 210, 7, '#7a5230', INK, 4) +   /* the back */
        rr(212, 62, 12, 44, 4, '#a2814f', INK, 3) +
        rr(212, 118, 12, 44, 4, '#a2814f', INK, 3) +
        rr(88, 168, 146, 22, 7, '#a2814f', INK, 4) +   /* the seat */
        rr(94, 190, 20, 74, 6, '#7a5230', INK, 4) +    /* front leg */
        rr(208, 190, 20, 74, 6, '#7a5230', INK, 4) +   /* back leg */
        T(170, 316, 'NEEM', 40, '#e03131')) +
      g(470, 120, 1, rr(0, 0, 340, 340, 16, '#ffffff', INK, 6) +
        /* a shoe, seen from the side, with a sole and laces so it is a shoe
           and not a blue blob */
        P('M52 236 L52 186 Q52 160 88 160 L128 160 Q150 160 164 180 L200 214 ' +
          'Q222 232 268 234 L288 236 Z', '#1c7ed6', INK, 5) +
        P('M44 236 L294 236 L294 252 Q294 264 278 264 L60 264 Q44 264 44 252 Z',
          '#2b3040', INK, 5) +
        P('M74 190 L114 190 M74 208 L118 208', '', '#ffffff', 5) +
        T(170, 316, 'NEEM', 40, '#e03131')) +
      g(860, 120, 1, rr(0, 0, 340, 340, 16, '#ffffff', INK, 6) +
        /* umbrella */
        P('M40 190 Q170 60 300 190 Z', '#2f9e44', INK, 5) +
        P('M170 190 L170 268 Q170 288 148 288', '', '#7a5230', 8) +
        T(170, 316, 'NEEM', 40, '#e03131'))
  });

  /* 12 - the judge writes something down */
  S.push({
    line: 'The judge wrote something on her pad, and did not tell them what it was.',
    dur: 5000,
    art:
      room({ board: true, window: true }) +
      g(780, 240, 1.15, grown({ coat: '#c2255c', arms: 'out' })) +
      /* the pad sits in her left hand, which lands at about (759,362) */
      g(688, 330, 1, rr(0, 0, 116, 146, 8, '#ffffff', INK, 5) +
        P('M20 36 L92 36 M20 66 L98 66 M20 96 L76 96', '', '#adb5bd', 5)) +
      g(240, 320, 1, kid({ shirt: '#e03131', hairStyle: 'plait' })) +
      g(400, 320, 1, kid({ shirt: '#1c7ed6', skin: '#c68642' })) +
      '<g class="pop d3">' + T(320, 170, '. . . ?', 56, '#ffd43b') + '</g>'
  });

  /* 13 - Devu's phone */
  S.push({
    line: 'That evening Devu did a thing he had never done. He took out his phone. ' +
      'Two hundred and forty pictures. A whole year of them.',
    dur: 8000,
    art:
      outdoors({ evening: true }) +
      g(400, 240, 1.2, kid({ shirt: '#2f9e44', skin: '#8d5524', hair: '#100c08', arms: 'out' })) +
      /* the phone in his hand - his right hand lands at about (501,355) */
      g(486, 288, 1.15, phone(1)) +
      T(1010, 240, '240', 92, '#ffffff') +
      Tp(1010, 296, 'PICTURES', 30, INK) +
      Tp(1010, 340, 'ONE WHOLE YEAR', 24, '#5c3d18') +
      g(110, 200, 1.25, tree(0.85))
  });

  /* 14 - and they are all different */
  S.push({
    line: 'Wet leaves. Yellow ones. Torn ones. One as small as a fingernail. ' +
      'Leaves from his grandmother\'s roof in Kanpur. He had never shown them to anybody.',
    dur: 9600,
    art:
      room({}) +
      /* a spread of leaves, deliberately all different - different widths,
         different lengths, different colours and all lying at odd angles,
         because "all the same" was the whole problem in the first place */
      gr(140, 230, 1, -18, leafShape(74, 130, '#2f9e44', true)) +
      gr(300, 210, 1, 12, leafShape(96, 96, '#ffd43b', true)) +
      gr(452, 240, 1, -6, leafShape(50, 150, '#40c057', true)) +
      gr(600, 216, 1, 24, leafShape(110, 110, '#8a6130', true)) +
      gr(762, 232, 1, -30, leafShape(60, 128, '#94d82d', true)) +
      gr(892, 210, 1, 8, leafShape(84, 84, '#e8590c', true)) +
      gr(1012, 232, 1, -14, leafShape(30, 60, '#69db7c', true)) +
      gr(1120, 218, 1, 19, leafShape(90, 122, '#2b8a3e', true)) +
      gr(210, 396, 1, 27, leafShape(64, 104, '#d8f5a2', true)) +
      gr(360, 402, 1, -22, leafShape(46, 116, '#37b24d', true)) +
      gr(524, 388, 1, 6, leafShape(102, 78, '#a9e34b', true)) +
      gr(702, 398, 1, -35, leafShape(56, 110, '#66a80f', true)) +
      gr(862, 392, 1, 16, leafShape(78, 96, '#c0eb75', true)) +
      gr(1042, 400, 1, -10, leafShape(42, 126, '#5c940d', true)) +
      T(640, 108, 'ALL DIFFERENT', 46, '#ffd43b')
  });

  /* 15 - overnight */
  S.push({
    line: 'They gave the box all two hundred and forty, and left it humming in the dark.',
    dur: 5200,
    art:
      room({ night: true, window: true }) +
      table(470, 452, 380) +
      g(540, 84, 1, machine({ icon: 'off', eye: 'on', dim: true })) +
      /* sound coming off it, as three widening arcs each side */
      P('M492 214 A56 56 0 0 0 492 306', '', '#5ee27a', 5, 'class="glow"') +
      P('M462 190 A86 86 0 0 0 462 330', '', '#5ee27a', 5, 'class="glow"') +
      P('M432 166 A116 116 0 0 0 432 354', '', '#5ee27a', 5, 'class="glow"') +
      P('M888 214 A56 56 0 0 1 888 306', '', '#5ee27a', 5, 'class="glow"') +
      P('M918 190 A86 86 0 0 1 918 330', '', '#5ee27a', 5, 'class="glow"') +
      P('M948 166 A116 116 0 0 1 948 354', '', '#5ee27a', 5, 'class="glow"') +
      Tp(196, 220, 'THURSDAY', 36, '#91a7ff') +
      Tp(196, 272, 'NIGHT', 36, '#91a7ff')
  });

  /* 16 - Friday, it gets them right. ROUND 1 ANSWER (the tick). */
  S.push({
    line: 'Friday. The tulsi. TULSI. The mango. MANGO. The curry leaf, which even Meher had ' +
      'to check twice, and the dots put up a tick.',
    dur: 9000,
    art:
      hall() +
      table(120, 452, 400) +
      g(160, 292, 1, pot(1)) +
      /* the two loose leaves LIE on the table top. Standing them upright made
         them read as two more potted plants. */
      gr(300, 442, 1, 76, leafShape(70, 140, '#2b8a3e', true)) +
      gr(470, 446, 1, -68, leafShape(48, 120, '#40c057', true)) +
      g(660, 80, 1.16, machine({ icon: 'tick', eye: 'on' })) +
      '<g class="pop d3">' + T(1120, 250, 'TULSI', 34, '#ffd43b') + '</g>' +
      '<g class="pop d4">' + T(1120, 306, 'MANGO', 34, '#ffd43b') + '</g>' +
      '<g class="pop d5">' + T(1120, 362, 'CURRY', 34, '#ffd43b') + '</g>'
  });

  /* 17 - the plastic leaf */
  S.push({
    line: 'Then the head judge reached into her bag and held up a leaf she had bought in a ' +
      'shop. Plastic. Bright green. Made in a factory.',
    dur: 8200,
    art:
      hall() +
      g(820, 230, 1.2, grown({ coat: '#c2255c', arms: 'out' })) +
      /* the plastic leaf held IN her left hand, which lands at about
         (798,357). Tilted away from her so it does not cover her face, and
         kept small enough that the shine on it still reads as plastic. */
      gr(792, 357, 1.15, -22, leafShape(80, 150, '#51cf66', true) +
        P('M-14 -104 Q0 -74 -10 -44', '', '#ffffff', 6)) +
      '<g class="pop d3">' + T(280, 210, 'PLASTIC', 48, '#ffd43b') + '</g>' +
      '<g class="pop d4">' + Tp(280, 268, 'bought in a shop', 26, INK) + '</g>' +
      g(120, 330, 0.9, kid({ shirt: '#e03131', hairStyle: 'plait' }))
  });

  /* 18 - PEEPAL. ROUND 1 ANSWER. */
  S.push({
    line: 'The eye looked at it for less than a second. PEEPAL, said the dots. ' +
      'Very proudly indeed.',
    dur: 6200,
    art:
      hall() +
      g(408, 40, 1.32, machine({ icon: 'peepal', eye: 'on' })) +
      g(120, 240, 1.3, leafShape(70, 130, '#51cf66', true)) +
      P('M240 300 L400 300', '', '#e03131', 7, 'class="flow"') +
      '<g class="pop d2">' + shout(1080, 250, 'PEEPAL', 52) + '</g>' +
      '<g class="pop d3">' + Tp(1080, 316, 'very proudly indeed', 24, INK) + '</g>'
  });

  /* 19 - the card */
  S.push({
    line: 'Nobody laughed. Meher took a card, wrote four words on it, and stuck it to the glass.',
    dur: 5800,
    art:
      hall() +
      g(470, 96, 1.1, machine({ icon: 'peepal', eye: 'on' })) +
      g(150, 300, 1.1, kid({ shirt: '#e03131', hairStyle: 'plait', arms: 'out' })) +
      /* the card, tilted, going on */
      g(760, 170, 1, '<g class="tilt">' + rr(0, 0, 300, 120, 10, '#ffd43b', INK, 6) +
        Tp(150, 52, 'ASK  A  PERSON', 30, INK) + Tp(150, 94, 'TOO', 30, INK) + '</g>')
  });

  /* 20 - and afterwards */
  S.push({
    line: 'ASK A PERSON TOO. The box won third prize. And the card is still there.',
    dur: 5600,
    art:
      hall() +
      table(440, 452, 400) +
      g(490, 84, 1, machine({ icon: 'off', eye: 'on' })) +
      /* the card stuck across the face */
      g(516, 196, 1, rr(0, 0, 248, 96, 10, '#ffd43b', INK, 6) +
        Tp(124, 42, 'ASK  A  PERSON', 25, INK) + Tp(124, 78, 'TOO', 25, INK)) +
      /* third prize rosette */
      g(1010, 210, 1, '<g class="bob">' + circ(0, 0, 58, '#e8590c', INK, 6) +
        Tp(0, 12, '3rd', 40, '#ffffff') +
        P('M-24 50 L-34 120 L0 100 L34 120 L24 50 Z', '#e8590c', INK, 5) + '</g>') +
      T(230, 220, 'THE END', 54, '#ffd43b')
  });

  return { css: CSS, scenes: S, icons: ICONS, w: W, h: H };
})();
