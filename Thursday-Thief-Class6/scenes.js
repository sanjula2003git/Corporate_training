/* scenes.js - hand-drawn comic scenes for "The Thursday Thief".
   Every scene is one <svg class="scene"> stacked in the stage; app.js turns
   exactly one of them "live" as the story plays. Pure SVG + CSS, no images.

   Three rules if you touch the artwork:
     1. Never put an animation class on a <g> that also has a transform
        attribute. A CSS transform replaces the attribute and the art snaps to
        the top-left corner. Position on an outer <g>, animate on an inner one.
     2. Nothing readable goes below about y=560. The caption band covers it.
     3. No teaching words in the pictures. The scenes say "MISSING" and
        "THURSDAY", never "observation", "pattern" or "memory". If the
        vocabulary appears before Part 1, the assessment stops measuring
        anything. */
(function () {
  var W = 1280, H = 720;
  var INK = '#12142a';

  /* ---------------------------------------------------------------- css */
  var CSS = [
    '.scene text{font-family:"Trebuchet MS","Segoe UI",Verdana,sans-serif;font-weight:bold}',

    /* -------------------------------------------------------- the camera
       The move runs on the <svg class="scene"> element itself, never on a
       group inside the art, so it can never collide with a transform
       attribute (rule 1 at the top of this file). build() picks --cam per
       scene; app.js sets --hold to the seconds that scene is really on
       screen, and --tin to how far into it we already are (a negative
       number), so dragging the bar lands in the middle of a move instead of
       starting it again. Scale never drops to 1 and no pan is larger than
       (scale-1)/2, or the edge of the picture walks into frame. */
    '@keyframes campush{from{transform:scale(1.03)}to{transform:scale(1.17)}}',
    '@keyframes campull{from{transform:scale(1.19)}to{transform:scale(1.04)}}',
    '@keyframes campanr{from{transform:scale(1.13) translateX(2.8%)}',
    'to{transform:scale(1.13) translateX(-2.8%)}}',
    '@keyframes campanl{from{transform:scale(1.13) translateX(-2.8%)}',
    'to{transform:scale(1.13) translateX(2.8%)}}',
    '@keyframes camtiltup{from{transform:scale(1.15) translateY(-3.2%)}',
    'to{transform:scale(1.15) translateY(3.2%)}}',
    '@keyframes camtiltdn{from{transform:scale(1.15) translateY(3.2%)}',
    'to{transform:scale(1.15) translateY(-3.2%)}}',
    '@keyframes camdrift{from{transform:scale(1.05) translate(1.2%,0.7%)}',
    'to{transform:scale(1.15) translate(-1.2%,-0.7%)}}',
    '.scene{transform:scale(1.08)}',
    '.scene.live{animation-name:var(--cam,camdrift);animation-duration:var(--hold,14s);' +
      'animation-delay:var(--tin,0s);animation-timing-function:cubic-bezier(.35,0,.25,1);' +
      'animation-fill-mode:both}',

    /* ----------------------------------------------------- idle movement
       Every looping animation is gated on .live, so a scene that is not on
       screen animates nothing and eighteen idle SVGs stay off the CPU. The
       stage loses its .playing class whenever the story is paused, and
       everything inside it holds still with it - otherwise the pictures keep
       moving under a frozen caption, which is worse than not moving at all. */
    '@keyframes bob{0%,100%{transform:translateY(0)}50%{transform:translateY(-12px)}}',
    '@keyframes bob2{0%,100%{transform:translateY(0)}50%{transform:translateY(9px)}}',
    '@keyframes hop{0%,100%{transform:translate(0,0)}30%{transform:translate(26px,-22px)}',
    '60%{transform:translate(52px,0)}80%{transform:translate(52px,-6px)}}',
    '@keyframes flap{0%,100%{transform:scaleY(1)}50%{transform:scaleY(.35)}}',
    '@keyframes glint{0%,100%{opacity:.15;transform:scale(.7)}50%{opacity:1;transform:scale(1.15)}}',
    '@keyframes tick{0%,100%{transform:rotate(0deg)}50%{transform:rotate(6deg)}}',
    '@keyframes tilt{0%,100%{transform:rotate(-3deg)}50%{transform:rotate(3deg)}}',
    '@keyframes pulse{0%,100%{transform:scale(1)}50%{transform:scale(1.07)}}',
    '@keyframes blink{0%,100%{opacity:1}50%{opacity:.15}}',
    '@keyframes dashmove{to{stroke-dashoffset:-200}}',
    '@keyframes fly{from{transform:translate(0,0)}to{transform:translate(430px,-250px)}}',
    '@keyframes grow{from{transform:scale(.4);opacity:0}to{transform:scale(1);opacity:1}}',
    '@keyframes sway{0%,100%{transform:rotate(-1.5deg)}50%{transform:rotate(1.5deg)}}',
    /* a blink is one fast frame of shut eye in every six seconds */
    '@keyframes lid{0%,93%,100%{transform:scaleY(1)}96.5%{transform:scaleY(.06)}}',
    /* dust in a sunbeam: up and across, fading in and out at the ends */
    '@keyframes mote{0%{opacity:0;transform:translate(0,0)}',
    '14%{opacity:.85}82%{opacity:.6}100%{opacity:0;transform:translate(46px,-104px)}}',
    '@keyframes shimmer{0%,100%{opacity:.10}50%{opacity:.26}}',
    '@keyframes sweep{to{transform:rotate(360deg)}}',
    '@keyframes swingopen{0%{transform:rotate(-52deg)}70%{transform:rotate(6deg)}',
    '100%{transform:rotate(0deg)}}',
    '@keyframes peck{0%,72%,100%{transform:rotate(0deg)}84%{transform:rotate(22deg)}}',
    '@keyframes breathe{0%,100%{transform:scale(1)}50%{transform:scale(1.014)}}',

    '.scene.live .bob{animation:bob 3.4s ease-in-out infinite}',
    '.scene.live .bob2{animation:bob2 4.1s ease-in-out infinite}',
    '.scene.live .hop{animation:hop 3.6s ease-in-out infinite}',
    '.scene.live .flap{animation:flap .32s ease-in-out infinite}',
    '.flap{transform-box:fill-box;transform-origin:top center}',
    '.scene.live .glint{animation:glint 2.1s ease-in-out infinite}',
    '.glint{transform-box:fill-box;transform-origin:center}',
    '.glint.g1{animation-delay:.35s}.glint.g2{animation-delay:.7s}',
    '.glint.g3{animation-delay:1.05s}.glint.g4{animation-delay:1.4s}',
    '.scene.live .tick{animation:tick 2.4s ease-in-out infinite}',
    '.tick{transform-box:fill-box;transform-origin:bottom center}',
    '.scene.live .tilt{animation:tilt 3s ease-in-out infinite}',
    '.tilt{transform-box:fill-box;transform-origin:center}',
    '.scene.live .pulse{animation:pulse 2.2s ease-in-out infinite}',
    '.pulse{transform-box:fill-box;transform-origin:center}',
    '.scene.live .blink{animation:blink 1.6s ease-in-out infinite}',
    '.scene.live .sway{animation:sway 4.5s ease-in-out infinite}',
    '.sway{transform-box:fill-box;transform-origin:bottom center}',
    '.flow{stroke-dasharray:22 16}',
    '.scene.live .flow{animation:dashmove 2.4s linear infinite}',
    '.scene.live .lid{animation:lid 6.4s ease-in-out infinite}',
    '.lid{transform-box:fill-box;transform-origin:center}',
    '.scene.live .mote{animation:mote 13s linear infinite}',
    '.scene.live .shimmer{animation:shimmer 6s ease-in-out infinite}',
    '.scene.live .sechand{animation:sweep 60s steps(60,end) infinite}',
    '.sechand{transform-box:fill-box;transform-origin:center bottom}',
    '.scene.live .peck{animation:peck 4.4s ease-in-out infinite}',
    '.peck{transform-box:fill-box;transform-origin:right bottom}',
    '.scene.live .breathe{animation:breathe 5.6s ease-in-out infinite}',
    '.breathe{transform-box:fill-box;transform-origin:center bottom}',

    /* ------------------------------------------------------------- beats
       .pop reveals a thing once. Which second it arrives is set by a beat
       class - b0 is the moment the scene opens, b1 the second caption line
       of that scene, b2 the third, and bNxM steps between them - and the
       real delays are written by app.js out of the caption track, so a
       label always lands on the sentence that says it. d1..d5 stay for
       quick decorative staggers that belong to no line. */
    '.scene.live .pop{animation:grow .55s cubic-bezier(.2,1.5,.4,1) both}',
    '.pop{transform-box:fill-box;transform-origin:center}',
    '.scene.live .pop.d1{animation-delay:.5s}.scene.live .pop.d2{animation-delay:1s}',
    '.scene.live .pop.d3{animation-delay:1.5s}.scene.live .pop.d4{animation-delay:2s}',
    '.scene.live .pop.d5{animation-delay:2.5s}',
    '.scene.live .fly{animation:fly 3.4s ease-in both}',
    '.scene.live .swing{animation:swingopen 1.1s cubic-bezier(.3,1.4,.5,1) both}',
    '.swing{transform-box:fill-box;transform-origin:left center}',

    /* pause the whole picture with the story */
    '.stage.started:not(.playing) .scene,' +
      '.stage.started:not(.playing) .scene *{animation-play-state:paused}'
  ].join('\n');

  /* ------------------------------------------------------------ helpers */

  /* big comic lettering: fill with a heavy ink stroke painted behind it */
  function T(x, y, s, size, fill, anchor) {
    return '<text x="' + x + '" y="' + y + '" font-size="' + size + '" fill="' + fill +
      '" text-anchor="' + (anchor || 'middle') + '" stroke="' + INK + '" stroke-width="' +
      Math.max(3, size / 7) + '" paint-order="stroke">' + s + '</text>';
  }
  function Tp(x, y, s, size, fill, anchor) {
    return '<text x="' + x + '" y="' + y + '" font-size="' + size + '" fill="' + fill +
      '" text-anchor="' + (anchor || 'middle') + '">' + s + '</text>';
  }

  /* ---- room shell: back wall, blackboard, floor ----
     Pass noBoard for the scenes whose subject sits in the middle of the wall
     (the cupboard, the window, the notebook). Drawing the blackboard behind
     those just puts two big rectangles on top of each other. */
  function room(u, mood, noBoard) {
    var wall = mood === 'dim' ? '#c9b48f' : mood === 'warm' ? '#f6e6c6' : '#efdcb8';
    var floor = mood === 'dim' ? '#6b4f36' : '#8a6a49';
    var s = '<defs><linearGradient id="w' + u + '" x1="0" y1="0" x2="0" y2="1">' +
      '<stop offset="0" stop-color="' + wall + '"/>' +
      '<stop offset="1" stop-color="' + shade(wall, -18) + '"/></linearGradient></defs>' +
      '<rect width="' + W + '" height="' + H + '" fill="url(#w' + u + ')"/>' +
      /* skirting + floor */
      '<rect x="0" y="500" width="' + W + '" height="' + (H - 500) + '" fill="' + floor + '"/>' +
      '<rect x="0" y="492" width="' + W + '" height="16" fill="#5b4130"/>';
    if (!noBoard) {
      s += '<g><rect x="120" y="90" width="560" height="270" rx="10" fill="#24402f" stroke="' + INK +
        '" stroke-width="9"/>' +
        '<rect x="120" y="352" width="560" height="26" rx="6" fill="#8a6a49" stroke="' + INK +
        '" stroke-width="7"/></g>';
    }
    return s;
  }

  /* lighten / darken a #rrggbb by a percentage of full scale */
  function shade(hex, pct) {
    var n = parseInt(hex.slice(1), 16);
    var r = (n >> 16) & 255, g = (n >> 8) & 255, b = n & 255;
    function c(v) { return Math.max(0, Math.min(255, Math.round(v + 255 * pct / 100))); }
    return '#' + ((1 << 24) + (c(r) << 16) + (c(g) << 8) + c(b)).toString(16).slice(1);
  }

  /* ---- one child, drawn from the waist up unless sitting ---- */
  var LOOK = {
    tanvi:  { skin: '#c98a5b', hair: '#1a1520', top: '#fdf7ea', low: '#1c4f8c', plait: true },
    imran:  { skin: '#a9713f', hair: '#161219', top: '#fdf7ea', low: '#1c4f8c' },
    yash:   { skin: '#e0a878', hair: '#2a1f18', top: '#fdf7ea', low: '#1c4f8c' },
    kid1:   { skin: '#8d5c31', hair: '#1a1520', top: '#fdf7ea', low: '#1c4f8c', plait: true },
    kid2:   { skin: '#d99a68', hair: '#241a14', top: '#fdf7ea', low: '#1c4f8c' },
    rao:    { skin: '#c08050', hair: '#1a1520', top: '#c2255c', low: '#7a1740', adult: true },
    ramesh: { skin: '#9a6538', hair: '#3a3a3a', top: '#3f8f5f', low: '#33502f', adult: true }
  };

  /* who: key into LOOK. anim: a class name put on an INNER group (never on the
     positioned one - see rule 1 at the top of this file). */
  function kid(who, x, y, s, anim, opts) {
    opts = opts || {};
    var L = LOOK[who] || LOOK.kid2;
    var g = '';
    var headY = opts.down ? -118 : -128;      /* head hangs a little when down */

    /* body */
    g += '<path d="M -46 0 L -40 -86 Q 0 -104 40 -86 L 46 0 Z" fill="' + L.top +
      '" stroke="' + INK + '" stroke-width="7"/>';
    if (!L.adult) {
      /* school tie */
      g += '<path d="M 0 -92 L -11 -78 L 0 -66 L 11 -78 Z" fill="#c92a2a" stroke="' + INK +
        '" stroke-width="5"/>' +
        '<path d="M 0 -66 L -8 -22 L 0 -12 L 8 -22 Z" fill="#c92a2a" stroke="' + INK +
        '" stroke-width="5"/>';
    } else {
      g += '<path d="M -30 -88 Q 0 -50 30 -88" fill="none" stroke="' + shade(L.top, -14) +
        '" stroke-width="10"/>';
    }
    /* arms */
    if (opts.point) {
      g += '<path d="M 40 -80 L 118 -104" fill="none" stroke="' + L.skin +
        '" stroke-width="17" stroke-linecap="round"/>' +
        '<circle cx="124" cy="-106" r="12" fill="' + L.skin + '" stroke="' + INK + '" stroke-width="5"/>';
      g += '<path d="M -40 -80 L -56 -18" fill="none" stroke="' + L.skin +
        '" stroke-width="17" stroke-linecap="round"/>';
    } else if (opts.up) {
      g += '<path d="M 40 -80 L 66 -150" fill="none" stroke="' + L.skin +
        '" stroke-width="17" stroke-linecap="round"/>' +
        '<path d="M -40 -80 L -58 -20" fill="none" stroke="' + L.skin +
        '" stroke-width="17" stroke-linecap="round"/>';
    } else {
      g += '<path d="M 40 -80 L 54 -16" fill="none" stroke="' + L.skin +
        '" stroke-width="17" stroke-linecap="round"/>' +
        '<path d="M -40 -80 L -54 -16" fill="none" stroke="' + L.skin +
        '" stroke-width="17" stroke-linecap="round"/>';
    }
    /* head */
    g += '<circle cx="0" cy="' + headY + '" r="40" fill="' + L.skin + '" stroke="' + INK +
      '" stroke-width="7"/>';
    /* hair */
    g += '<path d="M -41 ' + (headY - 4) + ' Q -36 ' + (headY - 52) + ' 0 ' + (headY - 46) +
      ' Q 36 ' + (headY - 52) + ' 41 ' + (headY - 4) + ' Q 22 ' + (headY - 30) + ' 0 ' +
      (headY - 26) + ' Q -22 ' + (headY - 30) + ' -41 ' + (headY - 4) + ' Z" fill="' + L.hair +
      '" stroke="' + INK + '" stroke-width="5"/>';
    if (L.plait) {
      g += '<path d="M -40 ' + (headY - 2) + ' Q -62 ' + (headY + 40) + ' -50 ' + (headY + 74) +
        '" fill="none" stroke="' + L.hair + '" stroke-width="15" stroke-linecap="round"/>' +
        '<path d="M 40 ' + (headY - 2) + ' Q 62 ' + (headY + 40) + ' 50 ' + (headY + 74) +
        '" fill="none" stroke="' + L.hair + '" stroke-width="15" stroke-linecap="round"/>';
    }
    /* face */
    var ey = headY - 4;
    if (opts.shut) {
      g += '<path d="M -20 ' + ey + ' q 8 7 16 0" fill="none" stroke="' + INK + '" stroke-width="5"/>' +
        '<path d="M 4 ' + ey + ' q 8 7 16 0" fill="none" stroke="' + INK + '" stroke-width="5"/>';
    } else {
      /* open eyes blink. The lid class scales the pair down for one frame, so
         it goes on a group of its own - never on anything carrying a
         transform attribute. The offset keeps a room full of children from
         blinking in unison, which reads as a machine, not a class. */
      g += '<g class="lid" style="animation-delay:' + (x % 11 * 0.53).toFixed(2) + 's">' +
        '<circle cx="-13" cy="' + ey + '" r="5.5" fill="' + INK + '"/>' +
        '<circle cx="13" cy="' + ey + '" r="5.5" fill="' + INK + '"/></g>';
    }
    var my = headY + 18;
    if (opts.mouth === 'sad') {
      g += '<path d="M -13 ' + (my + 5) + ' q 13 -12 26 0" fill="none" stroke="' + INK +
        '" stroke-width="5" stroke-linecap="round" transform="translate(-13,0)"/>';
    } else if (opts.mouth === 'open') {
      g += '<ellipse cx="0" cy="' + my + '" rx="11" ry="13" fill="#7a2b2b" stroke="' + INK +
        '" stroke-width="4"/>';
    } else if (opts.mouth === 'flat') {
      g += '<line x1="-12" y1="' + my + '" x2="12" y2="' + my + '" stroke="' + INK +
        '" stroke-width="5" stroke-linecap="round"/>';
    } else {
      g += '<path d="M -13 ' + (my - 4) + ' q 13 14 26 0" fill="none" stroke="' + INK +
        '" stroke-width="5" stroke-linecap="round"/>';
    }

    /* Everyone breathes, and whoever has an idle loop starts it part-way
       through, at a slightly different speed. Identical loops running in step
       is most of what makes a drawn crowd look mechanical. The offsets come
       from x, so they are the same on every run and screenshots stay stable. */
    var off = (x % 13 * 0.41).toFixed(2), dur = (3.1 + (x % 7) * 0.24).toFixed(2);
    var inner = anim
      ? '<g class="' + anim + '" style="animation-delay:-' + off + 's;animation-duration:' +
        dur + 's">' + g + '</g>'
      : '<g class="breathe" style="animation-delay:-' + off + 's">' + g + '</g>';
    return '<g transform="translate(' + x + ',' + y + ') scale(' + s + ')">' + inner + '</g>';
  }

  /* ---- dust hanging in the light. Positions come off a fixed stride rather
     than Math.random, so two runs of the same scene are identical and a
     screenshot means something. ---- */
  function motes(n, x, y, w, h, tone) {
    var out = '', i, px, py;
    for (i = 0; i < n; i++) {
      px = x + ((i * 137) % 100) / 100 * w;
      py = y + ((i * 71) % 100) / 100 * h;
      out += '<circle class="mote" cx="' + px.toFixed(0) + '" cy="' + py.toFixed(0) +
        '" r="' + (2.2 + (i % 4) * 0.9).toFixed(1) + '" fill="' + (tone || '#fff4d2') +
        '" opacity="0" style="animation-delay:-' + (i * 1.7).toFixed(1) +
        's;animation-duration:' + (11 + (i % 5) * 1.6).toFixed(1) + 's"/>';
    }
    return '<g>' + out + '</g>';
  }

  /* ---- a shaft of light falling into the room from off to one side ---- */
  function shaft(xTop, wTop, xBot, wBot, tone) {
    return '<polygon class="shimmer" points="' + xTop + ',0 ' + (xTop + wTop) + ',0 ' +
      (xBot + wBot) + ',720 ' + xBot + ',720" fill="' + (tone || '#fff2c0') + '" opacity=".14"/>';
  }

  /* ---- a school desk seen from the front ---- */
  function desk(x, y, s, tone) {
    tone = tone || '#b98a52';
    return '<g transform="translate(' + x + ',' + y + ') scale(' + s + ')">' +
      '<rect x="-78" y="-14" width="156" height="20" rx="5" fill="' + tone + '" stroke="' + INK +
      '" stroke-width="7"/>' +
      '<rect x="-70" y="6" width="14" height="66" fill="' + shade(tone, -14) + '" stroke="' + INK +
      '" stroke-width="6"/>' +
      '<rect x="56" y="6" width="14" height="66" fill="' + shade(tone, -14) + '" stroke="' + INK +
      '" stroke-width="6"/></g>';
  }

  /* ---- the crow ---- */
  function crow(x, y, s, opts) {
    opts = opts || {};
    var g = '<ellipse cx="0" cy="0" rx="52" ry="34" fill="#15161f" stroke="' + INK +
      '" stroke-width="6"/>' +
      /* tail */
      '<path d="M 44 -6 L 104 -26 L 100 6 Z" fill="#15161f" stroke="' + INK + '" stroke-width="6"/>' +
      /* wing */
      '<g class="' + (opts.flap ? 'flap' : '') + '">' +
      '<path d="M 6 -12 Q -22 -40 -46 -10 Q -18 6 6 -12 Z" fill="#22232f" stroke="' + INK +
      '" stroke-width="5"/></g>' +
      /* legs */
      '<path d="M -12 30 L -14 54 M 12 30 L 16 54" stroke="' + INK +
      '" stroke-width="6" stroke-linecap="round"/>' +
      /* head, tilted the way a crow does when it is deciding. The peck
         class lives on an inner group; the rotate attribute stays outside. */
      '<g transform="rotate(' + (opts.tilt ? -18 : 0) + ',-46,-30)">' +
      '<g class="' + (opts.peck ? 'peck' : '') + '">' +
      '<circle cx="-46" cy="-30" r="27" fill="#15161f" stroke="' + INK + '" stroke-width="6"/>' +
      '<path d="M -70 -32 L -104 -24 L -70 -18 Z" fill="#6a6a72" stroke="' + INK +
      '" stroke-width="5"/>' +
      '<circle cx="-52" cy="-36" r="8" fill="#ffd43b" stroke="' + INK + '" stroke-width="4"/>' +
      '<circle cx="-52" cy="-36" r="3.4" fill="' + INK + '"/>' +
      (opts.foil
        ? '<g class="glint"><rect x="-126" y="-34" width="26" height="20" rx="4" fill="#dfe4ee" ' +
        'stroke="' + INK + '" stroke-width="4"/></g>'
        : '') +
      '</g></g>';
    return '<g transform="translate(' + x + ',' + y + ') scale(' + s + ')">' +
      (opts.anim ? '<g class="' + opts.anim + '">' + g + '</g>' : g) + '</g>';
  }

  /* ---- the shiny things that keep disappearing ---- */
  function compass(x, y, s) {
    return '<g transform="translate(' + x + ',' + y + ') scale(' + s + ')">' +
      '<path d="M 0 -46 L -26 40" stroke="#c8ccd6" stroke-width="13" stroke-linecap="round"/>' +
      '<path d="M 0 -46 L 26 40" stroke="#c8ccd6" stroke-width="13" stroke-linecap="round"/>' +
      '<circle cx="0" cy="-46" r="11" fill="#8f97a8" stroke="' + INK + '" stroke-width="5"/>' +
      '<path d="M 26 40 L 34 52" stroke="#5c6373" stroke-width="9" stroke-linecap="round"/></g>';
  }
  function whistle(x, y, s) {
    return '<g transform="translate(' + x + ',' + y + ') scale(' + s + ')">' +
      '<rect x="-40" y="-20" width="66" height="40" rx="12" fill="#cfd4de" stroke="' + INK +
      '" stroke-width="6"/>' +
      '<path d="M 26 -8 L 54 -16 L 54 8 L 26 8 Z" fill="#aeb5c2" stroke="' + INK + '" stroke-width="6"/>' +
      '<circle cx="-40" cy="-16" r="10" fill="none" stroke="' + INK + '" stroke-width="6"/></g>';
  }
  function keyring(x, y, s) {
    return '<g transform="translate(' + x + ',' + y + ') scale(' + s + ')">' +
      '<circle cx="-14" cy="-14" r="22" fill="none" stroke="#c8ccd6" stroke-width="9"/>' +
      '<path d="M 4 0 L 40 34 L 30 44 L 24 38 L 16 46 L 8 38" fill="#c8ccd6" stroke="' + INK +
      '" stroke-width="5" stroke-linejoin="round"/></g>';
  }
  function mirror(x, y, s) {
    return '<g transform="translate(' + x + ',' + y + ') scale(' + s + ')">' +
      '<circle cx="0" cy="0" r="38" fill="#dbe6f2" stroke="' + INK + '" stroke-width="7"/>' +
      '<path d="M -20 12 Q -6 -22 20 -18" fill="none" stroke="#fff" stroke-width="9" stroke-linecap="round"/></g>';
  }
  function pen(x, y, s) {
    return '<g transform="translate(' + x + ',' + y + ') scale(' + s + ') rotate(-24)">' +
      '<rect x="-10" y="-48" width="20" height="76" rx="6" fill="#cfd4de" stroke="' + INK +
      '" stroke-width="6"/>' +
      '<path d="M -10 28 L 0 52 L 10 28 Z" fill="#8f97a8" stroke="' + INK + '" stroke-width="5"/>' +
      '<rect x="-11" y="-48" width="22" height="14" rx="4" fill="#1c4f8c" stroke="' + INK +
      '" stroke-width="5"/></g>';
  }
  /* The animated class goes on an INNER group every time. Putting it on the
     group that carries the transform attribute is the trap in rule 1: the CSS
     transform replaces the attribute and the art lands at 0,0. */
  function foil(x, y, s, cls) {
    return '<g transform="translate(' + x + ',' + y + ') scale(' + s + ')">' +
      '<g class="' + (cls || '') + '">' +
      '<path d="M -30 -18 L 26 -24 L 34 16 L -22 22 Z" fill="#e6ebf5" stroke="' + INK +
      '" stroke-width="5"/>' +
      '<path d="M -14 -20 L -6 20 M 6 -22 L 14 18" stroke="#a9b0be" stroke-width="4"/></g></g>';
  }

  /* a four-pointed comic sparkle */
  function spark(x, y, r, cls) {
    return '<g transform="translate(' + x + ',' + y + ')">' +
      '<g class="glint ' + (cls || '') + '">' +
      '<path d="M 0 ' + (-r) + ' L ' + (r * 0.26) + ' ' + (-r * 0.26) + ' L ' + r + ' 0 L ' +
      (r * 0.26) + ' ' + (r * 0.26) + ' L 0 ' + r + ' L ' + (-r * 0.26) + ' ' + (r * 0.26) +
      ' L ' + (-r) + ' 0 L ' + (-r * 0.26) + ' ' + (-r * 0.26) + ' Z" fill="#ffd43b" stroke="' +
      INK + '" stroke-width="3"/></g></g>';
  }

  /* a speech bubble with its tail on the left or the right */
  function bubble(x, y, w, h, side, lines, size, beat) {
    var s = '<g transform="translate(' + x + ',' + y + ')"><g class="pop ' + (beat || '') + '">' +
      '<rect x="' + (-w / 2) + '" y="' + (-h / 2) + '" width="' + w + '" height="' + h +
      '" rx="22" fill="#fdf7ea" stroke="' + INK + '" stroke-width="8"/>';
    var tx = side === 'left' ? -w / 2 + 34 : w / 2 - 34;
    var dir = side === 'left' ? -1 : 1;
    s += '<path d="M ' + tx + ' ' + (h / 2 - 4) + ' L ' + (tx + dir * 12) + ' ' + (h / 2 + 40) +
      ' L ' + (tx + dir * 46) + ' ' + (h / 2 - 4) + ' Z" fill="#fdf7ea" stroke="' + INK +
      '" stroke-width="8"/>';
    s += '<rect x="' + (-w / 2 + 6) + '" y="' + (h / 2 - 12) + '" width="' + (w - 12) +
      '" height="10" fill="#fdf7ea"/>';
    size = size || 30;
    lines.forEach(function (ln, i) {
      s += Tp(0, -h / 2 + 46 + i * (size + 10), ln, size, INK);
    });
    return s + '</g></g>';
  }

  /* the classroom window: the latch is bent outward in every scene but the
     first, because that is the point of the story */
  function windowFrame(x, y, s, opts) {
    opts = opts || {};
    var g = '<rect x="-150" y="-116" width="300" height="232" rx="8" fill="#8fc3e8" stroke="' +
      INK + '" stroke-width="9"/>' +
      '<path d="M -150 40 L 150 -10" fill="none" stroke="#b9dcf3" stroke-width="16" opacity=".55"/>' +
      '<line x1="0" y1="-116" x2="0" y2="116" stroke="' + INK + '" stroke-width="9"/>' +
      '<line x1="-150" y1="0" x2="150" y2="0" stroke="' + INK + '" stroke-width="9"/>' +
      /* sill */
      '<rect x="-172" y="112" width="344" height="26" rx="6" fill="#d9c39a" stroke="' + INK +
      '" stroke-width="8"/>';
    /* The latch. opts.swing plays it falling open once as the scene starts,
       which is the moment the whole story turns on. The rotate attribute has
       to stay on the outer group and the animation on the inner one. */
    var rot = opts.bent ? 52 : 0;
    g += '<g transform="rotate(' + rot + ',6,26)">' +
      '<g class="' + (opts.swing ? 'swing ' + (opts.swing === true ? '' : opts.swing) : '') + '">' +
      '<rect x="-2" y="18" width="54" height="16" rx="6" fill="#9aa2b1" stroke="' + INK +
      '" stroke-width="6"/></g></g>';
    if (opts.feather) g += feather(-92, 118, 0.85, -14);
    return '<g transform="translate(' + x + ',' + y + ') scale(' + s + ')">' + g + '</g>';
  }

  function feather(x, y, s, rot) {
    return '<g transform="translate(' + x + ',' + y + ') scale(' + s + ') rotate(' + (rot || 0) + ')">' +
      '<path d="M 0 0 Q 26 -44 6 -84 Q -18 -46 0 0 Z" fill="#1c1d28" stroke="' + INK +
      '" stroke-width="5"/>' +
      '<line x1="2" y1="-4" x2="6" y2="-78" stroke="#4a4d5e" stroke-width="4"/></g>';
  }

  /* a wall clock; hh:mm drawn by rotating two hands */
  function clock(x, y, s, hh, mm) {
    var ma = mm * 6, ha = (hh % 12) * 30 + mm * 0.5;
    return '<g transform="translate(' + x + ',' + y + ') scale(' + s + ')">' +
      '<circle cx="0" cy="0" r="60" fill="#fdf7ea" stroke="' + INK + '" stroke-width="9"/>' +
      '<circle cx="0" cy="0" r="48" fill="none" stroke="#b8b2a0" stroke-width="3"/>' +
      '<line x1="0" y1="0" x2="0" y2="-32" stroke="' + INK + '" stroke-width="9" ' +
      'stroke-linecap="round" transform="rotate(' + ha + ')"/>' +
      '<line x1="0" y1="0" x2="0" y2="-46" stroke="#c92a2a" stroke-width="6" ' +
      'stroke-linecap="round" transform="rotate(' + ma + ')"/>' +
      /* a second hand that actually goes round, one step at a time. In a room
         where nothing else moves it is the only proof time is passing. */
      /* drawn as a symmetric sliver rather than a line, so that its own
         bounding box has a real width and transform-origin:center bottom
         lands exactly on the spindle */
      '<path class="sechand" d="M -2.4 0 L 2.4 0 L 1.1 -50 L -1.1 -50 Z" fill="#8a8fa3"/>' +
      '<circle cx="0" cy="0" r="6" fill="' + INK + '"/></g>';
  }

  /* --------------------------------------------------------- the scenes */
  var S = {};

  /* 1. establishing: Room 6B on a Thursday morning */
  S.room = function (u) {
    return room(u) +
      shaft(720, 130, 880, 210) +
      '<g class="pop d1">' + Tp(400, 200, '6 B', 92, '#e8f3ec') +
      Tp(400, 268, 'THURSDAY', 46, '#a9d5bd') + '</g>' +
      clock(950, 180, 1.15, 11, 20) +
      motes(16, 660, 100, 520, 340) +
      /* door with the class plate */
      '<g><rect x="790" y="300" width="180" height="200" rx="6" fill="#a4763f" stroke="' + INK +
      '" stroke-width="8"/>' +
      '<circle cx="820" cy="410" r="9" fill="#e8c15a" stroke="' + INK + '" stroke-width="4"/></g>' +
      desk(250, 470, 1) + desk(560, 470, 1) + desk(870, 470, 0.9) +
      kid('kid1', 250, 462, 0.72, 'bob') +
      kid('yash', 560, 462, 0.72, 'bob2') +
      '<g class="pop d2">' + T(640, 96, 'ROOM 6B', 62, '#ffd43b') + '</g>';
  };

  /* 2. the steel cupboard, doors open, one gap on the shelf */
  S.cupboard = function (u) {
    return room(u, 'dim', true) +
      '<g transform="translate(520,300)">' +
      '<rect x="-250" y="-230" width="500" height="450" rx="10" fill="#9aa6b4" stroke="' + INK +
      '" stroke-width="10"/>' +
      '<rect x="-232" y="-212" width="464" height="414" rx="6" fill="#5f6b7a"/>' +
      /* shelves */
      '<rect x="-232" y="-70" width="464" height="16" fill="#8d99a8"/>' +
      '<rect x="-232" y="76" width="464" height="16" fill="#8d99a8"/>' +
      /* things still there */
      '<rect x="-196" y="-176" width="120" height="102" rx="6" fill="#c25b4a" stroke="' + INK +
      '" stroke-width="6"/>' +
      '<rect x="-58" y="-150" width="86" height="76" rx="6" fill="#3f7f5f" stroke="' + INK +
      '" stroke-width="6"/>' +
      /* the gaps: dust outlines where the things used to be. They arrive on
         the line that names each one, not all at once when the scene opens. */
      '<g class="pop b0"><rect x="66" y="-158" width="140" height="84" rx="6" fill="none" ' +
      'stroke="#e8eaf0" stroke-width="7" stroke-dasharray="16 12"/></g>' +
      '<rect x="-190" y="10" width="150" height="60" rx="6" fill="#3b6ea5" stroke="' + INK +
      '" stroke-width="6"/>' +
      '<g class="pop b1"><rect x="30" y="4" width="120" height="66" rx="6" fill="none" ' +
      'stroke="#e8eaf0" stroke-width="7" stroke-dasharray="16 12"/></g>' +
      '</g>' +
      '<g class="pop b0">' + T(940, 250, '?', 150, '#e03131') + '</g>' +
      '<g class="pop b1">' + T(1090, 360, '?', 96, '#e03131') + '</g>' +
      '<g class="pop b1x2">' + T(1010, 440, '?', 74, '#e03131') + '</g>' +
      '<g class="pop b2">' + T(930, 120, 'MISSING. AGAIN.', 52, '#ffd43b') + '</g>';
  };

  /* 3. Yash points at the back of the room */
  S.accuse = function (u) {
    return room(u) +
      desk(210, 480, 0.92) + desk(470, 480, 0.92) +
      kid('yash', 250, 470, 0.94, null, { point: true, mouth: 'open' }) +
      kid('kid1', 470, 476, 0.8, 'bob2', { mouth: 'flat' }) +
      kid('kid2', 700, 480, 0.78, 'bob', { mouth: 'flat' }) +
      kid('imran', 1130, 500, 0.8, null, { down: true, mouth: 'flat', shut: true }) +
      bubble(760, 180, 470, 130, 'right', ['IT IS IMRAN.', 'HE SITS NEAREST.'], 38, 'b1') +
      '<g class="pop b2">' +
      '<path d="M 420 300 L 1040 340" stroke="#e03131" stroke-width="7" class="flow" fill="none"/>' +
      '</g>';
  };

  /* 4. Imran at the back desk, saying nothing */
  S.imran = function (u) {
    return room(u, 'dim') +
      /* the rest of the class, small and turned away */
      kid('kid1', 170, 430, 0.5, null, { shut: true, mouth: 'flat' }) +
      kid('kid2', 320, 430, 0.5, null, { shut: true, mouth: 'flat' }) +
      kid('yash', 470, 430, 0.5, null, { shut: true, mouth: 'flat' }) +
      desk(900, 500, 1.15) +
      kid('imran', 900, 486, 1.05, 'bob2', { down: true, mouth: 'flat' }) +
      '<g class="pop b0">' + T(1040, 150, 'SAID NOTHING', 42, '#ffd43b') + '</g>' +
      /* every face in the room aimed at one desk */
      '<g class="pop b1"><path d="M 560 360 L 800 400" stroke="#e03131" stroke-width="7" ' +
      'class="flow" fill="none"/></g>';
  };

  /* 5. lunch: Imran at one end, Tanvi three tables away */
  S.lunch = function (u) {
    return room(u, 'warm') +
      /* two long tables */
      '<rect x="60" y="430" width="470" height="26" rx="8" fill="#b98a52" stroke="' + INK +
      '" stroke-width="8"/>' +
      '<rect x="740" y="430" width="470" height="26" rx="8" fill="#b98a52" stroke="' + INK +
      '" stroke-width="8"/>' +
      kid('imran', 950, 424, 0.92, null, { down: true, mouth: 'flat', shut: true }) +
      /* his tiffin */
      '<rect x="1060" y="398" width="86" height="30" rx="8" fill="#cfd4de" stroke="' + INK +
      '" stroke-width="6"/>' +
      kid('tanvi', 250, 424, 0.92, 'bob2', { mouth: 'sad' }) +
      kid('kid2', 420, 428, 0.8, null, { mouth: 'smile' }) +
      '<g class="pop b1"><path d="M 330 300 Q 640 240 880 310" fill="none" stroke="#1c7ed6" ' +
      'stroke-width="7" class="flow"/></g>' +
      /* she is not innocent in this, and the picture says so on the line that
         says so */
      bubble(300, 190, 330, 130, 'left', ['I THOUGHT', 'SO TOO.'], 34, 'b2') +
      '<g class="pop b0">' + T(640, 120, 'ALL WEEK, BY HIMSELF', 44, '#ffd43b') + '</g>';
  };

  /* 6. the list: five shiny things and nothing else */
  S.list = function (u) {
    return room(u, 'dim', true) +
      '<g transform="translate(640,300)">' +
      '<rect x="-470" y="-210" width="940" height="450" rx="16" fill="#fdf7ea" stroke="' + INK +
      '" stroke-width="10" class="sway"/>' +
      '<line x1="-380" y1="-210" x2="-380" y2="240" stroke="#e0574f" stroke-width="4"/>' +
      '</g>' +
      /* the five things land one at a time, in the order she says them */
      '<g class="pop b1">' + compass(280, 250, 0.82) + spark(330, 190, 20, 'g1') + '</g>' +
      '<g class="pop b1x1">' + whistle(460, 250, 0.82) + spark(505, 196, 17, 'g2') + '</g>' +
      '<g class="pop b1x2">' + keyring(640, 240, 0.86) + spark(690, 190, 19, 'g3') + '</g>' +
      '<g class="pop b1x3">' + mirror(820, 250, 0.86) + spark(862, 196, 17, 'g4') + '</g>' +
      '<g class="pop b1x4">' + pen(990, 246, 0.86) + spark(1035, 190, 20) + '</g>' +
      '<g class="pop b3">' + T(640, 140, 'EVERY ONE OF THEM SHINY', 46, '#e03131') + '</g>' +
      '<g class="pop b2">' + Tp(640, 400, 'no books. no pencils. no money.', 34, '#3a3f66') + '</g>';
  };

  /* 7. the window: a latch that does not shut, and one black feather */
  S.window = function (u) {
    return room(u, 'warm', true) +
      windowFrame(500, 250, 1.3, { bent: true, feather: true }) +
      motes(12, 300, 120, 420, 300) +
      /* a lens over the feather on the sill */
      '<g class="pop b2">' +
      '<circle cx="380" cy="405" r="76" fill="none" stroke="#e03131" stroke-width="9"/>' +
      '<path d="M 434 459 L 486 511" stroke="#e03131" stroke-width="10" stroke-linecap="round"/>' +
      '</g>' +
      '<g class="pop b1">' + T(940, 200, 'ONE BENT', 54, '#e03131') + '</g>' +
      '<g class="pop b1x2">' + T(940, 268, 'LATCH', 54, '#e03131') + '</g>' +
      '<g class="pop b2x2">' + T(940, 360, 'ONE BLACK FEATHER', 34, '#3a3f66') + '</g>' +
      kid('tanvi', 1050, 520, 0.78, 'bob2', { mouth: 'flat' });
  };

  /* 8. the calendar: four circles, all in the same column */
  S.calendar = function (u) {
    /* the paper starts at y=150 so the heading has clear wall above it */
    var g = room(u, 'dim', true) + '<g transform="translate(640,320)">' +
      '<rect x="-390" y="-185" width="780" height="424" rx="14" fill="#fdf7ea" stroke="' + INK +
      '" stroke-width="10"/>';
    var days = ['M', 'T', 'W', 'T', 'F', 'S'];
    var i, r, c, x, y;
    for (c = 0; c < 6; c++) {
      x = -350 + c * 140;
      g += Tp(x, -145, days[c], 40, c === 3 ? '#e03131' : '#3a3f66');
    }
    /* the Thursday column is the fourth, and every circle lands in it */
    for (r = 0; r < 4; r++) {
      for (c = 0; c < 6; c++) {
        x = -350 + c * 140; y = -84 + r * 82;
        g += Tp(x, y, String(3 + r * 7 + c), 34, '#5a5f7d');
      }
    }
    /* the four rings come down the Thursday column one at a time, while she
       is saying she checked the dates */
    for (i = 0; i < 4; i++) {
      g += '<g class="pop b0x' + (i + 1) + '"><circle cx="' + (-350 + 3 * 140) + '" cy="' +
        (-96 + i * 82) + '" r="34" fill="none" stroke="#e03131" stroke-width="8"/></g>';
    }
    g += '<g class="pop b1">' +
      Tp(0, 210, 'THURSDAY IS GAMES. FORTY MINUTES.', 30, '#3a3f66') + '</g>';
    g += '</g>' + '<g class="pop b0x4">' + T(640, 108, 'ALL FOUR. SAME DAY.', 50, '#ffd43b') + '</g>';
    return g;
  };

  /* 9. June, remembered: a whistle up on the roof */
  S.memory = function (u) {
    return '<defs><linearGradient id="mem' + u + '" x1="0" y1="0" x2="0" y2="1">' +
      '<stop offset="0" stop-color="#6a5a3a"/><stop offset="1" stop-color="#9a8355"/>' +
      '</linearGradient></defs>' +
      '<rect width="' + W + '" height="' + H + '" fill="url(#mem' + u + ')"/>' +
      /* faded, because it is being remembered */
      '<g opacity=".82">' +
      '<rect x="180" y="300" width="920" height="260" fill="#b9a173" stroke="' + INK +
      '" stroke-width="9"/>' +
      '<rect x="180" y="272" width="920" height="34" fill="#8d7850" stroke="' + INK +
      '" stroke-width="8"/>' +
      /* the sun of a June morning */
      '<circle cx="1080" cy="150" r="66" fill="#ffd43b" stroke="' + INK + '" stroke-width="8" class="pulse"/>' +
      '<g class="pop b1">' + whistle(560, 236, 1.0) + spark(628, 186, 22) + '</g>' +
      '</g>' +
      '<g class="pop b0">' + T(340, 160, 'JUNE', 78, '#ffd43b') + '</g>' +
      '<g class="pop b1">' + T(830, 200, 'ON THE ROOF', 44, '#fdf7ea') + '</g>' +
      '<g class="pop b1x2">' + T(830, 260, 'A WEEK LATER', 34, '#e8dcc0') + '</g>' +
      '<g class="pop b2">' + T(640, 372, 'AND NOBODY ASKED HOW', 38, '#fdf7ea') + '</g>';
  };

  /* 10. asking Miss Rao to miss games, just once */
  S.ask = function (u) {
    return room(u, 'warm') +
      desk(880, 470, 1.25, '#a4763f') +
      kid('rao', 880, 452, 1.0, 'bob2', { mouth: 'smile' }) +
      kid('tanvi', 420, 470, 0.95, null, { up: true, mouth: 'open' }) +
      bubble(430, 170, 520, 130, 'right', ['MAY I STAY BACK', 'ON THURSDAY?'], 38, 'b0') +
      bubble(1010, 212, 250, 96, 'left', ['YES.'], 40, 'b1');
  };

  /* 11. an empty room and one girl who does not move */
  S.wait = function (u) {
    var g = room(u, 'dim');
    var i;
    for (i = 0; i < 4; i++) g += desk(150 + i * 250, 500, 0.9);
    g += desk(1100, 500, 0.9);
    g += kid('tanvi', 400, 486, 0.95, null, { shut: true, mouth: 'flat' });
    g += clock(1050, 190, 1.1, 11, 19);
    /* an empty room is the one place the dust should be visible */
    g += motes(18, 420, 110, 560, 340, '#e9dfc4');
    g += '<g class="pop b1">' + T(760, 150, 'NINETEEN MINUTES', 46, '#ffd43b') + '</g>';
    g += '<g class="pop b1x2">' + T(760, 226, 'WITHOUT MOVING', 38, '#a5d8ff') + '</g>';
    return g;
  };

  /* 12. the latch swings, and something black looks in */
  S.crow = function (u) {
    return room(u, 'dim', true) +
      /* the latch falls open as the scene opens - the hinge the whole story
         turns on, so it happens on screen instead of being already done */
      windowFrame(690, 250, 1.3, { bent: true, swing: 'b0' }) +
      /* and only then does something come in and hop along the sill */
      '<g class="pop b1">' + crow(600, 378, 0.95, { tilt: true, anim: 'hop', peck: true }) + '</g>' +
      '<g class="pop b2">' + T(1090, 210, 'ONE BRIGHT', 40, '#ffd43b') + '</g>' +
      '<g class="pop b2x2">' + T(1090, 272, 'YELLOW EYE', 44, '#ffd43b') + '</g>' +
      kid('tanvi', 170, 470, 0.85, null, { mouth: 'open' });
  };

  /* 13. it takes the foil and goes */
  S.steal = function (u) {
    return room(u, 'warm', true) +
      windowFrame(880, 240, 1.2, { bent: true }) +
      foil(300, 430, 1.1, 'glint') +
      /* it takes the foil, waits on the line that says so, and leaves once -
         a crow flying out of the window on a loop is a screensaver */
      '<g class="fly b1">' + crow(380, 470, 0.95, { flap: true, foil: true }) + '</g>' +
      '<g class="pop b1">' + T(300, 150, 'STRAIGHT', 50, '#e03131') + '</g>' +
      '<g class="pop b1x2">' + T(300, 216, 'BACK OUT', 50, '#e03131') + '</g>';
  };

  /* 14. three metres up, on the ledge under the water tank */
  S.ledge = function (u) {
    return '<defs><linearGradient id="sky' + u + '" x1="0" y1="0" x2="0" y2="1">' +
      '<stop offset="0" stop-color="#7fb8de"/><stop offset="1" stop-color="#cfe4f2"/>' +
      '</linearGradient></defs>' +
      '<rect width="' + W + '" height="' + H + '" fill="url(#sky' + u + ')"/>' +
      /* the school wall, wet and green at the bottom */
      '<rect x="240" y="180" width="800" height="540" fill="#d8c69f" stroke="' + INK +
      '" stroke-width="9"/>' +
      '<rect x="240" y="430" width="800" height="290" fill="#7f9a72" opacity=".7"/>' +
      /* the ledge */
      '<rect x="240" y="380" width="800" height="34" fill="#c0ab84" stroke="' + INK +
      '" stroke-width="8"/>' +
      /* water tank on top */
      '<rect x="560" y="60" width="280" height="126" rx="16" fill="#3f7f9f" stroke="' + INK +
      '" stroke-width="9"/>' +
      '<rect x="600" y="186" width="34" height="70" fill="#5a5f6d" stroke="' + INK + '" stroke-width="7"/>' +
      '<rect x="766" y="186" width="34" height="70" fill="#5a5f6d" stroke="' + INK + '" stroke-width="7"/>' +
      /* the nest */
      '<ellipse cx="700" cy="366" rx="86" ry="26" fill="#8a6a49" stroke="' + INK + '" stroke-width="7"/>' +
      spark(672, 350, 17, 'g1') + spark(716, 344, 15, 'g2') +
      crow(900, 340, 0.72, { tilt: true, peck: true, anim: 'bob2' }) +
      /* labels sit on the wall itself, which runs x=240..1040 */
      '<g class="pop b1">' + T(420, 296, '3 METRES UP', 44, '#ffd43b') + '</g>' +
      '<g class="pop b2">' + T(420, 490, 'WET WALL', 44, '#ff8787') + '</g>' +
      '<g class="pop b2x2">' + T(420, 542, 'NOTHING TO HOLD ON TO', 28, '#ffe3e3') + '</g>';
  };

  /* 15. the gardener, the long ladder, and everything on the ledge */
  S.ladder = function (u) {
    var g = '<rect width="' + W + '" height="' + H + '" fill="#a7cde6"/>' +
      '<rect x="200" y="150" width="880" height="570" fill="#d8c69f" stroke="' + INK +
      '" stroke-width="9"/>' +
      '<rect x="200" y="330" width="880" height="34" fill="#c0ab84" stroke="' + INK +
      '" stroke-width="8"/>';
    /* ladder */
    g += '<g><line x1="420" y1="700" x2="560" y2="300" stroke="#b98a52" stroke-width="16"/>' +
      '<line x1="500" y1="700" x2="640" y2="300" stroke="#b98a52" stroke-width="16"/>';
    var i;
    for (i = 0; i < 6; i++) {
      var t = i / 5;
      g += '<line x1="' + (420 + 140 * t + 0) + '" y1="' + (700 - 400 * t) + '" x2="' +
        (500 + 140 * t) + '" y2="' + (700 - 400 * t) + '" stroke="#a4763f" stroke-width="12"/>';
    }
    g += '</g>';
    g += kid('ramesh', 620, 330, 0.8, 'bob2', { up: true, mouth: 'open' });
    /* the haul, uncovered a piece at a time as he reads it out */
    g += '<g class="pop b1"><ellipse cx="820" cy="316" rx="120" ry="34" fill="#8a6a49" stroke="' +
      INK + '" stroke-width="7"/></g>';
    g += '<g class="pop b1x2">' + compass(770, 268, 0.5) + spark(800, 236, 16, 'g1') + '</g>' +
      '<g class="pop b1x4">' + whistle(850, 280, 0.5) + '</g>' +
      '<g class="pop b2">' + mirror(900, 276, 0.5) + spark(884, 232, 14, 'g3') + '</g>';
    /* the watchers stay above y=560 so the caption band does not eat them */
    g += kid('tanvi', 200, 550, 0.62, 'bob', { up: true, mouth: 'open' }) +
      kid('rao', 1110, 550, 0.64, 'bob2', { mouth: 'open' });
    g += '<g class="pop b3">' + T(640, 130, 'AND FORTY PIECES OF FOIL', 44, '#ffd43b') + '</g>';
    return g;
  };

  /* 16. the water cooler, before assembly */
  S.sorry = function (u) {
    return room(u, 'warm', true) +
      /* the cooler */
      '<g transform="translate(640,380)">' +
      '<rect x="-90" y="-150" width="180" height="300" rx="12" fill="#9aa6b4" stroke="' + INK +
      '" stroke-width="9"/>' +
      '<rect x="-60" y="-120" width="120" height="70" rx="8" fill="#5f6b7a"/>' +
      '<rect x="-16" y="-40" width="32" height="26" fill="#5f6b7a" stroke="' + INK +
      '" stroke-width="5"/></g>' +
      kid('tanvi', 330, 500, 0.95, null, { mouth: 'flat' }) +
      kid('imran', 960, 500, 0.95, 'bob2', { mouth: 'smile' }) +
      bubble(330, 160, 470, 120, 'left', ['I THOUGHT IT', 'WAS YOU TOO.'], 36, 'b1') +
      /* he says nothing back. He moves over, and her bottle goes under the
         tap - which is the whole of his answer */
      '<g class="pop b2"><rect x="608" y="392" width="64" height="128" rx="14" fill="#cfe8f5" ' +
      'stroke="' + INK + '" stroke-width="7"/>' +
      '<rect x="622" y="368" width="36" height="30" rx="8" fill="#4dabf7" stroke="' + INK +
      '" stroke-width="6"/></g>';
  };

  /* 17. assembly */
  S.assembly = function (u) {
    var g = '<defs><linearGradient id="as' + u + '" x1="0" y1="0" x2="0" y2="1">' +
      '<stop offset="0" stop-color="#8fbfe0"/><stop offset="1" stop-color="#e2d6b6"/>' +
      '</linearGradient></defs>' +
      '<rect width="' + W + '" height="' + H + '" fill="url(#as' + u + ')"/>' +
      '<rect x="0" y="470" width="' + W + '" height="250" fill="#b8a97e"/>';
    var i, names = ['kid1', 'kid2', 'yash', 'imran', 'kid2', 'kid1'];
    /* the seated rows stop at y=550, above the caption band */
    for (i = 0; i < 6; i++) {
      g += kid(names[i], 120 + i * 180, 550, 0.5, i % 2 ? 'bob' : 'bob2', { mouth: 'flat' });
    }
    g += kid('tanvi', 640, 430, 0.8, null, { mouth: 'flat' });
    g += kid('rao', 1130, 430, 0.72, 'bob2', { mouth: 'open' });
    g += '<g class="pop b0">' + T(340, 120, 'HOW DID YOU', 46, '#ffd43b') + '</g>';
    g += '<g class="pop b0x2">' + T(340, 180, 'KNOW?', 46, '#ffd43b') + '</g>';
    return g;
  };

  /* 18. the line. Two ways of looking, side by side. */
  S.finale = function (u) {
    return '<rect width="' + W + '" height="' + H + '" fill="#12142a"/>' +
      /* left panel: the whole class, aimed at one boy */
      '<g><rect x="60" y="70" width="520" height="420" rx="14" fill="#2a2140" stroke="#ffd43b" ' +
      'stroke-width="8"/>' +
      kid('kid1', 170, 400, 0.52, null, { mouth: 'flat' }) +
      kid('yash', 300, 400, 0.52, null, { mouth: 'flat' }) +
      kid('kid2', 430, 400, 0.52, null, { mouth: 'flat' }) +
      '<path d="M 170 300 L 470 220 M 300 300 L 480 230 M 430 300 L 490 240" stroke="#e03131" ' +
      'stroke-width="6" class="flow" fill="none"/>' +
      kid('imran', 500, 430, 0.5, null, { down: true, mouth: 'flat' }) +
      '</g>' +
      /* right panel: one girl, aimed at a window */
      '<g><rect x="700" y="70" width="520" height="420" rx="14" fill="#1d3350" stroke="#ffd43b" ' +
      'stroke-width="8"/>' +
      kid('tanvi', 800, 420, 0.62, null, { mouth: 'flat' }) +
      windowFrame(1080, 250, 0.62, { bent: true, feather: true }) +
      '<path d="M 850 300 L 1010 260" stroke="#4dabf7" stroke-width="7" class="flow" fill="none"/>' +
      '</g>' +
      '<g class="pop b0">' + T(320, 140, 'EVERYONE', 50, '#ff8787') + '</g>' +
      '<g class="pop b1">' + T(960, 140, 'ONE OF THEM', 50, '#74c0fc') + '</g>';
  };

  /* 19. the crow still comes, and it has a name now */
  S.crowend = function (u) {
    return room(u, 'warm', true) +
      windowFrame(470, 250, 1.3, { bent: true }) +
      /* foil laid out on the sill, on purpose this time */
      '<g class="pop b0">' + foil(360, 400, 0.85, 'glint') + '</g>' +
      '<g class="pop b0x1">' + foil(470, 404, 0.85, 'glint g2') + '</g>' +
      '<g class="pop b0x2">' + foil(580, 400, 0.85, 'glint g3') + '</g>' +
      '<g class="pop b0x3">' + crow(760, 372, 0.9, { tilt: true, anim: 'bob2', peck: true }) + '</g>' +
      '<g class="pop b1">' + T(1040, 200, 'THEY NAMED IT', 34, '#3a3f66') + '</g>' +
      '<g class="pop b1x2">' + T(1040, 272, 'THURSDAY', 58, '#e03131') + '</g>';
  };

  /* ------------------------------------------------------- caption track
     Times are the second each caption appears. They were written for a spoken
     reading of about 225 seconds; app.js scales them to the real length if a
     narration.mp3 is dropped in beside this file, and drives them off a plain
     clock if there is no audio at all. */
  var LINES = [
    ['room', 'Room 6B, Nandini Public School, twenty minutes past eleven on a Thursday.', 0.00],
    ['room', 'Miss Rao opened the cupboard, and stopped.', 5.60],

    ['cupboard', 'The steel compass was gone.', 9.10],
    ['cupboard', 'So was the silver whistle, and the little round mirror from the science box.', 11.70],
    ['cupboard', 'That made four Thursdays in a row.', 16.40],

    ['accuse', 'Yash did not wait for Miss Rao to ask.', 19.60],
    ['accuse', '"It is Imran," he said. "He sits nearest the cupboard. He only joined in July."', 22.80],
    ['accuse', 'Twenty-six heads turned to the back of the room.', 29.00],

    ['imran', 'Imran did not say anything.', 32.60],
    ['imran', 'He was new, and he had already learned that saying anything only made it longer.', 35.20],

    ['lunch', 'At lunch he sat by himself, the way he had all week.', 41.00],
    ['lunch', 'Three tables away, Tanvi felt something go cold.', 45.30],
    ['lunch', 'Because she had thought it was him too. On Tuesday. Without checking.', 49.20],

    ['list', 'That evening she wrote down everything that had gone missing.', 54.60],
    ['list', 'A compass. A whistle. A key ring. A mirror. Miss Rao’s steel pen.', 58.90],
    ['list', 'Not one storybook. Not one pencil. Not one rupee from anybody’s bag.', 64.60],
    ['list', 'Every single thing on that list was shiny.', 69.70],

    ['window', 'The next morning she came in early and stood at the cupboard.', 73.40],
    ['window', 'The window beside it did not shut properly. The latch was bent outward.', 77.70],
    ['window', 'And on the sill, stuck in the paint, there was one black feather.', 82.80],

    ['calendar', 'She checked the dates. All four of them were Thursdays.', 87.80],
    ['calendar', 'Thursday was games. The room stood empty for forty minutes.', 92.40],

    ['memory', 'And then she remembered something from June.', 97.30],
    ['memory', 'A whistle had gone missing that month too, and turned up a week later on the roof.', 100.90],
    ['memory', 'Nobody had ever asked how it got up there.', 107.00],

    ['ask', 'On Thursday morning, Tanvi asked Miss Rao if she could miss games. Just once.', 110.70],
    ['ask', 'Miss Rao looked at her for a moment, and said yes.', 116.50],

    ['wait', 'So Tanvi sat alone in an empty classroom with her hands in her lap,', 120.70],
    ['wait', 'and did not move for nineteen minutes.', 125.60],

    ['crow', 'At twenty past eleven, the bent latch swung open.', 128.80],
    ['crow', 'Something black came in off the water tank and hopped along the sill,', 133.00],
    ['crow', 'put its head on one side, and looked at the room with a bright yellow eye.', 138.10],

    ['steal', 'It took the silver foil off somebody’s leftover chocolate,', 143.80],
    ['steal', 'and went straight back out of the window.', 148.00],

    ['ledge', 'Tanvi stood on her chair to see where it went.', 151.40],
    ['ledge', 'Three metres up, on the ledge under the water tank.', 154.90],
    ['ledge', 'The wall below it was wet and green, with nothing to hold on to.', 159.10],
    ['ledge', 'She got down off the chair and went to find Miss Rao.', 164.20],

    ['ladder', 'Ramesh the gardener brought the long ladder.', 168.40],
    ['ladder', 'On the ledge, in a nest of wire and string, they found the compass, the whistle,', 172.00],
    ['ladder', 'two keys, a round mirror, and one steel pen with Miss Rao’s name on it.', 178.10],
    ['ladder', 'And about forty pieces of silver foil.', 183.90],

    ['sorry', 'Before assembly on Monday, Tanvi found Imran at the water cooler.', 187.50],
    ['sorry', '"I thought it was you as well," she said. "On Tuesday. I am sorry."', 192.20],
    ['sorry', 'Imran shrugged, and moved over so she could fill her bottle.', 197.80],

    ['assembly', 'In assembly, Miss Rao asked her how she had worked it out.', 202.40],
    ['assembly', 'Tanvi stood up. She did not say anything clever.', 207.00],

    ['finale', '"Everyone was looking at Imran.', 211.20],
    ['finale', 'I was the only one looking at the window."', 214.10],

    ['crowend', 'The crow still comes. 6B leave the foil out for it now, on the sill.', 218.40],
    ['crowend', 'They named it Thursday.', 224.00]
  ];

  var RUNTIME = 228;   /* seconds the story lasts when there is no audio file */

  /* -------------------------------------------------------- the camera map
     Which way the camera moves in each scene. A film where every shot pushes
     in the same way is as flat as one where nothing moves at all, so each
     move is picked for what the sentence is doing: in on a discovery, out on
     a memory, across the room on an accusation, up the wall on a climb. */
  var CAM = {
    room: 'campush', cupboard: 'campush', accuse: 'campanr', imran: 'campush',
    lunch: 'campanl', list: 'campush', window: 'campush', calendar: 'campush',
    memory: 'campull', ask: 'camdrift', wait: 'campush', crow: 'campush',
    steal: 'campanr', ledge: 'camtiltup', ladder: 'camtiltup', sorry: 'camdrift',
    assembly: 'campull', finale: 'campush', crowend: 'camdrift'
  };

  /* Where each scene starts, how long it holds, and the second every caption
     line inside it lands. All of it comes out of LINES, so retiming the story
     retimes the artwork with it and there is no second list to keep in step. */
  function timing(duration) {
    var k = (duration && duration > 1) ? duration / RUNTIME : 1;
    var last = (duration && duration > 1) ? duration : RUNTIME;
    var out = [], seen = {}, i, key, at;
    for (i = 0; i < LINES.length; i++) {
      key = LINES[i][0]; at = LINES[i][2] * k;
      if (!seen[key]) { seen[key] = { scene: key, at: at, beats: [] }; out.push(seen[key]); }
      seen[key].beats.push(at - seen[key].at);
    }
    for (i = 0; i < out.length; i++) {
      out[i].hold = (i + 1 < out.length ? out[i + 1].at : last) - out[i].at;
    }
    return out;
  }

  /* The beat delays, as a stylesheet. b0 is the second the scene opens, b1 the
     next caption line of that scene, and bNxM four steps in between - so a
     label can be hung on a sentence instead of on a stopwatch. --tin is how
     far into the scene we already are, as a negative number, so a scene
     entered by dragging the bar shows what it should already have revealed
     rather than playing the whole reveal again. */
  function beatCSS(duration) {
    var t = timing(duration), css = [], i, j, m, sel, b, next, step;
    for (i = 0; i < t.length; i++) {
      sel = '.scene[data-scene="' + t[i].scene + '"].live ';
      for (j = 0; j < t[i].beats.length; j++) {
        b = t[i].beats[j];
        next = (j + 1 < t[i].beats.length) ? t[i].beats[j + 1] : t[i].hold;
        step = (next - b) / 5;
        css.push(sel + '.b' + j + '{animation-delay:calc(' + b.toFixed(2) + 's + var(--tin,0s))}');
        for (m = 1; m <= 4; m++) {
          css.push(sel + '.b' + j + 'x' + m + '{animation-delay:calc(' +
            (b + step * m).toFixed(2) + 's + var(--tin,0s))}');
        }
      }
    }
    return css.join('\n');
  }

  /* build the stage markup once; scene svgs are reused across repeated lines */
  function build() {
    var t = timing(0), i, k;
    var html = '<style>' + CSS + '</style>' + '<style id="beats">' + beatCSS(0) + '</style>';
    for (i = 0; i < t.length; i++) {
      k = t[i].scene;
      html += '<svg class="scene" data-scene="' + k + '" viewBox="0 0 ' + W + ' ' + H +
        '" preserveAspectRatio="xMidYMid slice" style="--cam:' + (CAM[k] || 'camdrift') +
        ';--hold:' + t[i].hold.toFixed(2) + 's">' + S[k](i) + '</svg>';
    }
    return html;
  }

  /* If a narration.mp3 is added later, its real duration is passed in here and
     every caption time scales to it, so a fresh recording still lines up
     roughly. Re-measure the pauses for a tight fit. */
  function track(duration) {
    var k = (duration && duration > 1) ? duration / RUNTIME : 1;
    return LINES.map(function (l) {
      return { at: l[2] * k, scene: l[0], text: l[1] };
    });
  }

  window.STORY = {
    build: build, track: track, timing: timing, beatCSS: beatCSS,
    lines: LINES, runtime: RUNTIME
  };
})();
