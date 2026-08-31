# Verifying the assessment

No npm install. Node 22 has a global `WebSocket`, so the CDP driver is
hand-rolled and needs nothing.

```
node serve.mjs "../"  8899          # serve the project folder
node e2e.mjs http://127.0.0.1:8899/index.html
node shots.mjs http://127.0.0.1:8899/index.html ./shots
```

`e2e.mjs` runs 76 checks: the content checks (every picture's first letter
really does build its word, the narration leaks none of the answer vocabulary,
Round 2's words are not Round 3's answers, "date" is not accepted for "data"),
then a whole student run driven with **real mouse input** — including painting
each 8x8 answer by pressing and dragging across the squares.

Synthetic PointerEvents do not reproduce a drag. Driving Chrome with
`Input.dispatchMouseEvent` is the only way the paint-and-rub-out path is
actually exercised, and it is what caught the click-swallowing bug.

The expected total is **37/40, not 40** — the run deliberately takes a
different marking path on each Round 1 question (wrong-then-right = 2, right
first time = 3, hint used = 1) so all three are covered.

`shots.mjs` screenshots every screen and all 20 scenes, plus a sheet of all 19
rebus pictures at a readable size. Look at that sheet after touching
`pictures.js` — a yak that reads as a caterpillar breaks Round 2, and only a
picture of it tells you.
