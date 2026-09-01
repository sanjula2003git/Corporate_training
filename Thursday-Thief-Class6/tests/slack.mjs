/* How much unused vertical space is left on the story screen, at each size.
   Feeds the --stage-chrome number in index.html: slack here is picture the
   students are not getting.   node tests/slack.mjs [url]                  */
import { launch, attach, evalIn, click, type, sleep } from './cdp.mjs';

const URL = process.argv[2] || 'http://127.0.0.1:8899/index.html';
const SIZES = [[1366, 768], [1280, 720], [1920, 1080], [1024, 640]];

const { proc, port } = await launch(9225);
const c = await attach(port);

for (const [w, h] of SIZES) {
  await c.send('Emulation.setDeviceMetricsOverride',
    { width: w, height: h, deviceScaleFactor: 1, mobile: false });
  await evalIn(c, `location.href = ${JSON.stringify(URL)}`);
  await sleep(700);
  await evalIn(c, `localStorage.clear(); location.reload();`);
  await sleep(700);
  await type(c, '#f-name', 'Aarav Sharma');
  await click(c, '#b-start');
  await sleep(600);

  const m = await evalIn(c, `
    var b = document.querySelector('.body');
    var st = document.getElementById('stage').getBoundingClientRect();
    var ct = document.querySelector('.controls').getBoundingClientRect();
    var nav = document.querySelector('.navrow').getBoundingClientRect();
    return {
      stage: Math.round(st.width) + 'x' + Math.round(st.height),
      ratio: +(st.width / st.height).toFixed(3),
      bodyFree: Math.round(b.clientHeight - b.scrollHeight),
      gapBelowNav: Math.round(window.innerHeight - nav.bottom),
      stageWidthVsPanel: Math.round(
        document.querySelector('.panel').clientWidth - st.width)
    };
  `);
  console.log('  ' + (w + 'x' + h).padEnd(11) +
    'stage ' + m.stage.padEnd(10) + 'ratio ' + m.ratio +
    '   unused inside body ' + String(m.bodyFree).padStart(4) + 'px' +
    '   below nav ' + String(m.gapBelowNav).padStart(3) + 'px' +
    '   side margin ' + String(m.stageWidthVsPanel).padStart(4) + 'px');
}
proc.kill();
process.exit(0);
