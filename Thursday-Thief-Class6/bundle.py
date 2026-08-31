"""Fold index.html + scenes.js + app.js (+ narration.mp3, if there is one)
into ONE html file.

    python -X utf8 bundle.py

Writes Thursday-Thief-Assessment.html, which can be emailed, dropped on a USB
stick or opened straight off the desktop with no other file beside it.
Re-run it after editing any of the source files.

narration.mp3 is optional. Without it the story runs off a plain clock and the
child reads the captions; drop an mp3 in beside this script and re-run, and the
same story plays with a voice.
"""
import base64
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "Thursday-Thief-Assessment.html")

AUDIO_TAG = '<audio id="narration" preload="auto" src="narration.mp3"></audio>'


def read(name):
    with io.open(os.path.join(HERE, name), encoding="utf-8") as f:
        return f.read()


def main():
    html = read("index.html")
    scenes = read("scenes.js")
    app = read("app.js")

    mp3_path = os.path.join(HERE, "narration.mp3")
    if os.path.exists(mp3_path):
        with open(mp3_path, "rb") as f:
            mp3 = base64.b64encode(f.read()).decode("ascii")
        audio = ('<audio id="narration" preload="auto" '
                 'src="data:audio/mpeg;base64,' + mp3 + '"></audio>')
        print("narration.mp3 found - folding it in")
    else:
        # No mp3: leave an audio element with no source at all. app.js reads
        # that as "no audio" and drives the story off its own clock instead.
        audio = '<audio id="narration"></audio>'
        print("no narration.mp3 - building the read-along version")

    swaps = [
        (AUDIO_TAG, audio),
        ('<script src="scenes.js"></script>', '<script>\n' + scenes + '\n</script>'),
        ('<script src="app.js"></script>', '<script>\n' + app + '\n</script>'),
    ]
    for old, new in swaps:
        if old not in html:
            sys.exit("index.html no longer contains:\n  " + old[:60])
        html = html.replace(old, new)

    # the bundled copy says so in its title bar, so nobody edits the wrong file
    html = html.replace("</title>", " (single file)</title>", 1)

    with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)

    mb = os.path.getsize(OUT) / 1048576.0
    print("wrote %s  (%.1f MB)" % (os.path.basename(OUT), mb))
    if mb > 20:
        print("WARNING: that is large for an email attachment.")


if __name__ == "__main__":
    main()
