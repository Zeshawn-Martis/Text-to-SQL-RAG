import sqlite3
import os


# DATABASE LOCATION
os.makedirs("database", exist_ok=True)

DB_PATH = "database/movies.db"


# CONNECT DATABASE
conn = sqlite3.connect(DB_PATH)

# ENABLE FOREIGN KEYS
conn.execute(
    "PRAGMA foreign_keys = ON"
)

cursor = conn.cursor()


# REMOVE OLD TABLES
cursor.execute(
    "DROP TABLE IF EXISTS movies"
)

cursor.execute(
    "DROP TABLE IF EXISTS directors"
)


# DIRECTORS TABLE
cursor.execute("""
CREATE TABLE directors(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
)
""")


# MOVIES TABLE
cursor.execute("""
CREATE TABLE movies(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    genre TEXT,
    rating REAL,
    director_id INTEGER,

    FOREIGN KEY(director_id)
    REFERENCES directors(id)
)
""")


# INSERT DIRECTORS

directors = [
    ("Christopher Nolan",),
    ("Steven Spielberg",),
    ("Quentin Tarantino",),
    ("James Cameron",),
    ("Denis Villeneuve",)
]


cursor.executemany(
    """
    INSERT INTO directors(name)
    VALUES(?)
    """,
    directors
)



# INSERT MOVIES

movies = [

    ("Inception","Sci-Fi",8.8,1),
    ("Interstellar","Sci-Fi",8.7,1),
    ("The Dark Knight","Action",9.0,1),

    ("Jurassic Park","Adventure",8.2,2),
    ("Saving Private Ryan","War",8.6,2),

    ("Pulp Fiction","Crime",8.9,3),
    ("Django Unchained","Western",8.4,3),

    ("Avatar","Fantasy",7.9,4),
    ("Titanic","Romance",7.9,4),

    ("Dune","Sci-Fi",8.0,5),
    ("Blade Runner 2049","Sci-Fi",8.0,5)

]


cursor.executemany(
    """
    INSERT INTO movies(
        title,
        genre,
        rating,
        director_id
    )

    VALUES(?,?,?,?)
    """,
    movies
)



conn.commit()
conn.close()


print("Database created successfully!")