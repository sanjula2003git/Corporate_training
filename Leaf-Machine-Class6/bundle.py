"""Fold index.html + scenes.js + pictures.js + app.js into ONE html file.

    python -X utf8 bundle.py

The -X utf8 is not optional on Windows. Without it the em-dashes and the
curly quotes in the story come out as mojibake inside the captions.

Writes Leaf-Machine-Assessment.html, which can be emailed, dropped on a USB
stick, or opened straight off a desktop with nothing else beside it. Re-run
this after editing ANY of the source files.

One thing does not survive being opened from a desktop: the microphone in
Round 3. Browsers only hand over a microphone on a secure page, and a file on
a disk is not one. The typed answer beside it is worth the same marks, and the
page says so itself when it detects the problem. Serve the folder over http,
or use the GitHub Pages copy, if you want the speaking round to speak.
"""
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "Leaf-Machine-Assessment.html")

PARTS = ["scenes.js", "pictures.js", "app.js"]


def read(name):
    with io.open(os.path.join(HERE, name), encoding="utf-8") as f:
        return f.read()


def main():
    html = read("index.html")

    for name in PARTS:
        tag = '<script src="%s"></script>' % name
        if tag not in html:
            sys.exit("index.html no longer contains:\n  " + tag)
        html = html.replace(tag, "<script>\n" + read(name) + "\n</script>")

    # the bundled copy says so in its title bar, so nobody edits the wrong file
    html = html.replace("</title>", " (single file)</title>", 1)

    with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)

    kb = os.path.getsize(OUT) / 1024.0
    print("wrote %s  (%.0f KB)" % (os.path.basename(OUT), kb))


if __name__ == "__main__":
    main()
