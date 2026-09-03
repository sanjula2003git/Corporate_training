# Tests for The Thursday Thief

No npm install. Node 22 has a global `WebSocket`, so `cdp.mjs` drives a
headless Chrome over the DevTools Protocol directly.

Start the static server once, then run whichever check you need:

```
node tests/serve.mjs . 8899
```

| | |
|---|---|
| `node tests/fit.mjs` | every screen at 1366x768, 1280x720 and 1920x1080 — fails if the **page** scrolls. Internal scrolling in the results review is allowed and reported |
| `node tests/e2e.mjs [url] [w] [h]` | a whole student run with real mouse input. Also asserts no button, card, option or slot is ever off screen |
| `node tests/slack.mjs` | how much vertical space the story screen is wasting — feeds `--stage-chrome` in `index.html` |
| `node tests/shots.mjs [url] [outdir] [w] [h]` | screenshots every screen, and fails if the stage is no longer 16:9 |
| `node tests/story.mjs [url] [outdir]` | the story picture: every art beat is checked against the caption line behind it, the camera is driven for real and measured, every label is checked against the frame of its own shot, the children are checked to be actually acting, and all 51 shots are rendered to `shots-story/` |

`Thursday-Thief-Assessment.html` is the file students actually get, so run the
e2e against it too after `python -X utf8 bundle.py`:

```
node tests/e2e.mjs http://127.0.0.1:8899/Thursday-Thief-Assessment.html
```

Chrome path is hard-coded at the top of `cdp.mjs`.
