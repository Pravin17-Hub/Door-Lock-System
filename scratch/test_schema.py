import sqlite3

db_path = 'database/web_facesecure.db'
conn = sqlite3.connect(db_path)
row = conn.execute("SELECT sql FROM sqlite_master WHERE name='RegisteredFaces';").fetchone()
print("SQL SCHEMA:", row[0] if row else "Table Not Found")
conn.close()
