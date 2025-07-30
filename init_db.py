import sqlite3

conn = sqlite3.connect('gallery.db')
c = conn.cursor()

# Proje tablosu
c.execute('''
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
)
''')

# Medya tablosu
c.execute('''
CREATE TABLE IF NOT EXISTS media (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    filename TEXT NOT NULL,
    filetype TEXT CHECK(filetype IN ('image', 'video')),
    FOREIGN KEY(project_id) REFERENCES projects(id)
)
''')

conn.commit()
conn.close()

print("Veritabanı oluşturuldu.")
