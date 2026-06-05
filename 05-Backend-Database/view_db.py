# =====================================================================
# view_db.py  —  a simple viewer that prints everything in the database.
#
# WHY: lets you (and students) SEE the saved records as plain tables,
#   proving the data really lives inside training.db.
#
# RUN:  python view_db.py
# =====================================================================
import sqlite3

DB = "training.db"

def show(cursor, table):
    print(f"\n=== {table.upper()} " + "=" * (40 - len(table)))
    rows = cursor.execute(f"SELECT * FROM {table}").fetchall()
    if not rows:
        print("(empty)")
        return
    columns = [d[0] for d in cursor.description]
    print(" | ".join(columns))
    print("-" * 60)
    for row in rows:
        # Hide the long password hash so the output stays readable.
        printable = [("<hashed>" if columns[i] == "password_hash" else str(v))
                     for i, v in enumerate(row)]
        print(" | ".join(printable))

def main():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    # List every table the database contains, then print each one.
    tables = [r[0] for r in cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()]
    print(f"Database file: {DB}")
    print(f"Tables found: {tables}")
    for t in tables:
        show(cur, t)
    conn.close()

if __name__ == "__main__":
    main()
