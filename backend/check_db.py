import sqlite3

conn = sqlite3.connect("./data/metadata.db")
cur = conn.cursor()

cur.execute("SELECT * FROM gmail_tokens")

rows = cur.fetchall()

print("Gmail tokens in DB:")
print(rows)

conn.close()