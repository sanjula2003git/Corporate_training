/* pictures.js - the little drawings for Round 2, the picture word.

   Every picture contributes ONE letter: its first letter. Four pictures of a
   Dog, an Apple, a Tap and an Axe spell DATA.

   Two rules.

     1. A picture must have exactly one obvious name to an eleven year old.
        No "hound" for dog, no "faucet" for tap, no bird that might be a duck.
        If a picture can be named two ways it is a bad clue and the question
        stops being fair. The HINT button reveals a picture's name, which is
        the safety net, but the drawing should not need it.

     2. Never write the name into the drawing. The letter is the whole puzzle.

   All drawings are a 100x100 viewBox, flat colour, heavy ink line, so they
   still read at 118 pixels across on a projector.                          */

window.PICTURES = (function () {
  var INK = '#12142a';

  function svg(inner) {
    return '<svg viewBox="0 0 100 100" aria-hidden="true">' +
      '<g stroke="' + INK + '" stroke-width="3.4" stroke-linecap="round" ' +
      'stroke-linejoin="round">' + inner + '</g></svg>';
  }
  function P(d, fill, sw) {
    return '<path d="' + d + '" fill="' + (fill || 'none') + '"' +
      (sw ? ' stroke-width="' + sw + '"' : '') + '/>';
  }
  function C(cx, cy, r, fill, sw) {
    return '<circle cx="' + cx + '" cy="' + cy + '" r="' + r + '" fill="' + (fill || 'none') + '"' +
      (sw ? ' stroke-width="' + sw + '"' : '') + '/>';
  }
  function E(cx, cy, rx, ry, fill, sw) {
    return '<ellipse cx="' + cx + '" cy="' + cy + '" rx="' + rx + '" ry="' + ry +
      '" fill="' + (fill || 'none') + '"' + (sw ? ' stroke-width="' + sw + '"' : '') + '/>';
  }
  function R(x, y, w, h, r, fill) {
    return '<rect x="' + x + '" y="' + y + '" width="' + w + '" height="' + h +
      '" rx="' + (r || 0) + '" fill="' + (fill || 'none') + '"/>';
  }
  function dot(cx, cy, r) { return '<circle cx="' + cx + '" cy="' + cy + '" r="' + r + '" fill="' + INK + '" stroke="none"/>'; }

  var P_ = {};

  /* ---- A ------------------------------------------------------------- */
  P_.apple = {
    name: 'APPLE',
    svg: svg(
      P('M50 30 Q28 22 20 42 Q12 64 28 80 Q40 90 50 82 Q60 90 72 80 Q88 64 80 42 Q72 22 50 30 Z', '#e03131') +
      P('M50 30 L50 16', '', 4) +
      P('M50 20 Q64 8 74 16 Q66 28 50 22 Z', '#2f9e44')
    )
  };

  /* ---- B ------------------------------------------------------------- */
  /* a striped beach ball. The football version - one black pentagon on white -
     rendered as a dark dome and stopped reading as a ball at all. */
  P_.ball = {
    name: 'BALL',
    svg: svg(
      C(50, 52, 34, '#ffd43b') +
      P('M50 18 Q33 52 50 86 Q67 52 50 18 Z', '#e03131') +
      P('M26 31 Q40 52 26 73', '', 3.4) +
      P('M74 31 Q60 52 74 73', '', 3.4) +
      C(50, 52, 34, 'none')
    )
  };

  /* ---- C ------------------------------------------------------------- */
  P_.cup = {
    name: 'CUP',
    svg: svg(
      P('M24 34 L76 34 L70 68 Q68 76 58 76 L42 76 Q32 76 30 68 Z', '#ffffff') +
      P('M76 42 Q90 42 90 52 Q90 62 76 62', '', 4) +
      E(50, 84, 32, 6, '#dee2e6') +
      P('M42 22 Q46 16 42 10 M56 22 Q60 16 56 10', '', 3)
    )
  };

  /* ---- D ------------------------------------------------------------- */
  P_.drum = {
    name: 'DRUM',
    svg: svg(
      P('M24 40 L76 40 L76 72 L24 72 Z', '#e8590c') +
      E(50, 40, 26, 9, '#ffe8cc') +
      E(50, 72, 26, 9, '#c9522b') +
      P('M24 44 L40 68 M40 44 L56 68 M56 44 L72 68', '', 3) +
      P('M22 30 L34 18 M78 30 L66 18', '', 4) +
      C(34, 16, 4, '#7a5230', 3) + C(66, 16, 4, '#7a5230', 3)
    )
  };

  /* ---- E ------------------------------------------------------------- */
  /* rounded at the top, not pointed - the quadratic version came out as a
     water droplet */
  P_.egg = {
    name: 'EGG',
    svg: svg(
      P('M50 14 C66 14 74 34 74 54 C74 76 64 88 50 88 C36 88 26 76 26 54 C26 34 34 14 50 14 Z',
        '#fff9db') +
      P('M36 40 Q40 30 48 27', '', 3)
    )
  };

  /* ---- F ------------------------------------------------------------- */
  P_.fish = {
    name: 'FISH',
    svg: svg(
      P('M18 50 Q40 26 62 50 Q40 74 18 50 Z', '#1c7ed6') +
      P('M62 50 L84 34 L84 66 Z', '#1c7ed6') +
      /* the top fin has to touch the back, or it floats off on its own */
      P('M36 34 L44 22 L52 40 Z', '#1c7ed6') +
      dot(30, 46, 3.2)
    )
  };

  /* ---- H ------------------------------------------------------------- */
  P_.hat = {
    name: 'HAT',
    svg: svg(
      P('M32 62 L32 24 Q32 18 40 18 L60 18 Q68 18 68 24 L68 62 Z', '#343a40') +
      E(50, 64, 36, 9, '#212529') +
      P('M32 50 L68 50', '', 4)
    )
  };

  /* ---- I ------------------------------------------------------------- */
  P_.igloo = {
    name: 'IGLOO',
    svg: svg(
      P('M14 72 Q14 26 50 26 Q86 26 86 72 Z', '#e7f5ff') +
      P('M14 72 L86 72', '', 4) +
      P('M38 72 L38 56 Q50 46 62 56 L62 72', '#a5d8ff') +
      P('M22 52 L78 52 M30 38 L70 38 M50 26 L50 38', '', 3)
    )
  };

  /* ---- K ------------------------------------------------------------- */
  P_.kite = {
    name: 'KITE',
    svg: svg(
      P('M50 10 L78 42 L50 74 L22 42 Z', '#7048e8') +
      P('M50 10 L50 74 M22 42 L78 42', '', 3) +
      P('M50 74 Q42 84 50 90 Q58 96 50 100', '', 3)
    )
  };

  /* ---- L ------------------------------------------------------------- */
  P_.leaf = {
    name: 'LEAF',
    svg: svg(
      P('M50 16 Q80 42 50 76 Q20 42 50 16 Z', '#2f9e44') +
      P('M50 76 L50 92', '', 4) +
      P('M50 30 L50 70 M50 44 L36 38 M50 44 L64 38 M50 58 L38 52 M50 58 L62 52', '', 2.6)
    )
  };

  /* ---- M ------------------------------------------------------------- */
  P_.moon = {
    name: 'MOON',
    svg: svg(
      P('M62 12 Q26 26 26 52 Q26 80 62 90 Q34 72 34 51 Q34 30 62 12 Z', '#ffd43b') +
      dot(74, 26, 3) + dot(82, 46, 2.4) + dot(70, 68, 2.4)
    )
  };

  /* ---- N ------------------------------------------------------------- */
  /* back of the bowl, THEN the eggs, THEN the front rim over them. Drawing
     the eggs first buried them and it read as an empty basket. */
  P_.nest = {
    name: 'NEST',
    svg: svg(
      P('M14 50 Q50 38 86 50 Q84 60 50 60 Q16 60 14 50 Z', '#8a6130') +
      E(37, 52, 11, 9, '#fff9db') + E(63, 52, 11, 9, '#fff9db') + E(50, 45, 11, 9, '#fff9db') +
      P('M14 56 Q50 48 86 56 Q82 86 50 86 Q18 86 14 56 Z', '#a2814f') +
      P('M20 64 Q50 58 80 64 M18 72 Q50 66 82 72 M24 80 Q50 74 76 80', '', 2.6)
    )
  };

  /* ---- O ------------------------------------------------------------- */
  P_.owl = {
    name: 'OWL',
    svg: svg(
      P('M50 18 Q80 18 80 52 Q80 86 50 86 Q20 86 20 52 Q20 18 50 18 Z', '#8a6130') +
      P('M26 22 L36 34 M74 22 L64 34', '', 4) +
      C(38, 46, 12, '#ffffff') + C(62, 46, 12, '#ffffff') +
      dot(38, 46, 5) + dot(62, 46, 5) +
      P('M50 54 L44 62 L56 62 Z', '#e8590c') +
      P('M38 74 L44 82 M62 74 L56 82', '', 3)
    )
  };

  /* ---- P ------------------------------------------------------------- */
  P_.pen = {
    name: 'PEN',
    svg: svg(
      P('M26 82 L34 60 L74 20 L86 32 L46 72 Z', '#1c7ed6') +
      P('M74 20 L86 32', '', 3) +
      P('M34 60 L46 72', '', 3) +
      P('M26 82 L33 74', '#12142a', 3)
    )
  };

  /* ---- T ------------------------------------------------------------- */
  /* a wall tap: flange, an L-shaped body that turns down, a spout mouth, a
     handle on top and a drop falling out of it */
  P_.tap = {
    name: 'TAP',
    svg: svg(
      R(6, 24, 15, 46, 4, '#868e96') +
      P('M20 32 L60 32 L60 64 L44 64 L44 46 L20 46 Z', '#adb5bd') +
      R(40, 62, 24, 11, 4, '#868e96') +
      R(26, 15, 22, 10, 4, '#adb5bd') +
      C(37, 11, 7, '#e03131') +
      P('M52 80 Q59 89 52 96 Q45 89 52 80 Z', '#1c7ed6')
    )
  };
  P_.tent = {
    name: 'TENT',
    svg: svg(
      P('M50 16 L86 76 L14 76 Z', '#e8590c') +
      P('M50 16 L50 76', '', 3) +
      P('M50 34 L64 76 L36 76 Z', '#7a3d10') +
      P('M8 76 L92 76', '', 4)
    )
  };
  P_.tree = {
    name: 'TREE',
    svg: svg(
      R(44, 58, 12, 30, 3, '#7a5230') +
      C(50, 38, 24, '#2f9e44') +
      C(32, 50, 16, '#37b24d') +
      C(68, 50, 16, '#37b24d') +
      P('M14 88 L86 88', '', 4)
    )
  };

  /* ---- U ------------------------------------------------------------- */
  P_.umbrella = {
    name: 'UMBRELLA',
    svg: svg(
      P('M12 52 Q12 16 50 16 Q88 16 88 52 Z', '#e03131') +
      P('M12 52 Q24 40 37 52 Q50 40 63 52 Q76 40 88 52', '', 3.4) +
      P('M50 52 L50 78 Q50 90 36 90 Q26 90 26 82', '', 4.6) +
      P('M50 16 L50 8', '', 3.4)
    )
  };

  /* ---- Y ------------------------------------------------------------- */
  /* A yak has to read as a big shaggy ox, not a caterpillar - which is what
     the first attempt looked like, because the head was tiny and the fringe
     of hair was mistaken for a row of legs. Big head, big curved horns,
     four thick legs, fringe kept shallow. */
  P_.yak = {
    name: 'YAK',
    svg: svg(
      /* thick legs first, so the body overlaps their tops */
      P('M34 62 L34 86 M48 62 L48 86 M64 62 L64 86 M78 62 L78 86', '', 8) +
      /* the humped body */
      P('M26 52 Q28 30 50 30 L74 30 Q88 30 88 48 L88 64 Q88 70 80 70 L34 70 Q26 70 26 60 Z',
        '#5c3d18') +
      /* a shallow fringe of long hair along the belly */
      P('M28 66 L32 80 L38 66 L44 80 L50 66 L56 80 L62 66 L68 80 L74 66 L80 78 L84 66 Z',
        '#3d2810') +
      /* the head, large and low at the front */
      P('M30 44 Q12 42 10 58 Q9 72 24 70 Q32 68 32 58 Z', '#5c3d18') +
      E(13, 66, 7, 5, '#d3bfa6') +
      dot(20, 55, 3.4) +
      /* the horns - the single most yak thing about a yak */
      P('M18 44 Q4 36 6 24 M32 40 Q34 24 46 22', '', 5) +
      /* tufted tail */
      P('M88 44 Q97 52 94 64', '', 4) +
      C(93, 70, 6, '#3d2810')
    )
  };

  /* ------------------------------------------------------------------- */
  /* The six words. Ordered easiest to hardest by length.
     None of these is an answer in Round 3 - keep it that way, or Round 2
     hands the spoken answers over before the child is asked for them.    */
  var WORDS = [
    { word: 'MYTH', pics: ['moon', 'yak', 'tent', 'hat'] },
    { word: 'MODEL', pics: ['moon', 'owl', 'drum', 'egg', 'leaf'] },
    { word: 'INPUT', pics: ['igloo', 'nest', 'pen', 'umbrella', 'tap'] },
    { word: 'OUTPUT', pics: ['owl', 'umbrella', 'tree', 'pen', 'umbrella', 'tap'] },
    { word: 'DOMAIN', pics: ['drum', 'owl', 'moon', 'apple', 'igloo', 'nest'] },
    { word: 'FEEDBACK', pics: ['fish', 'egg', 'egg', 'drum', 'ball', 'apple', 'cup', 'kite'] }
  ];

  return { pics: P_, words: WORDS };
})();
