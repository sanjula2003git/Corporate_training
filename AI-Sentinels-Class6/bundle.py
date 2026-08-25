"""Fold index.html + scenes.js + app.js + narration.mp3 into ONE html file.

    python -X utf8 bundle.py

Writes AI-Sentinels-Assessment.html, which can be emailed, dropped on a USB
stick or opened straight off the desktop with no other file beside it.
Re-run it after editing any of the four source files.
"""
import base64
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "AI-Sentinels-Assessment.html")


def read(name):
    with io.open(os.path.join(HERE, name), encoding="utf-8") as f:
        return f.read()


def main():
    html = read("index.html")
    scenes = read("scenes.js")
    app = read("app.js")

    with open(os.path.join(HERE, "narration.mp3"), "rb") as f:
        mp3 = base64.b64encode(f.read()).decode("ascii")

    swaps = [
        ('<audio id="narration" preload="auto" src="narration.mp3"></audio>',
         '<audio id="narration" preload="auto" src="data:audio/mpeg;base64,' + mp3 + '"></audio>'),
        ('<script src="scenes.js"></script>',
         '<script>\n' + scenes + '\n</script>'),
        ('<script src="app.js"></script>',
         '<script>\n' + app + '\n</script>'),
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
