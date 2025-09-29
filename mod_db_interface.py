# Database Management for tracking songs that were recorded.

# |--- Internal Imports
from mod_data_representation import song_metadata

# |--- External Imports
import sqlite3
import os

# |--- Variables
SOURCES:list[str] = [
    "Bandcamp",
    "YouTube",
    "Spotify",
    "Soundcloud"
]

def initialize_database(path_to_db:str) -> sqlite3.Connection:
    init_db = False 
    if not os.path.isfile(path_to_db):
        # creating new db at given location
        print(f"|- [DB Initialization] No Db found, creating new at {path_to_db}")
    
    connection = sqlite3.connect(path_to_db)
    create_tables(connection)
    
    return connection

        
def insert_sources(db:sqlite3.Connection):
    cursor = db.cursor()
    for source in SOURCES:
        cursor.execute("INSERT OR IGNORE INTO sources (name) VALUES (?);",(source,))
        db.commit()
        

def create_tables(connection:sqlite3.Connection):
    cursor = connection.cursor()
    # creating table for artists 
    print("|-  [DB Initialization] adding artists")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS artists (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   name TEXT NOT NULL UNIQUE
                   );
                   """)
    
    # creating table for download-source
    print("|-  [DB Initialization] adding sources")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sources (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   name TEXT NOT NULL UNIQUE
                   );
                   """)
    insert_sources(connection)
    print("|-  [DB Initialization] adding songs")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS songs (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   artist_id INTEGER NOT NULL,
                   title TEXT NOT NULL,
                   album TEXT NOT NULL,
                   source_id INTEGER NOT NULL,
                   FOREIGN KEY(artist_id) REFERENCES artists(id),
                   FOREIGN KEY(source_id) REFERENCES source(id)
                   );
                   """)
    connection.commit()

def query_artist_id(db:sqlite3.Connection,artist:str) -> int|None:
    cursor = db.cursor()
    cursor.execute("SELECT id FROM artists WHERE name = ?;",(artist,))
    result = cursor.fetchone()
    return result[0] if result else None

def query_artist_name(db:sqlite3.Connection,id:int) -> str|None:
    cursor = db.cursor()
    cursor.execute("SELECT name FROM artists WHERE id = ?;",(id,))
    result = cursor.fetchone()
    return result[0] if result else None


def query_source_id(db:sqlite3.Connection, source_name:str) -> int|None:
    cursor = db.cursor()
    cursor.execute("SELECT id FROM sources WHERE name = ?;",(source_name,))
    result = cursor.fetchone()
    return result[0] if result else None

def query_source_name(db:sqlite3.Connection,source_id:int) -> str|None:
    cursor = db.cursor()
    cursor.execute("SELECT name FROM sources WHERE id = ?;",(source_id,))
    result = cursor.fetchone()
    return result[0] if result else None

def song_is_in_db(db:sqlite3.Connection,song:song_metadata) -> bool:
    maybe_artist_id = query_artist_id(db,song.artist)
    if maybe_artist_id is None: 
        # assumes no song has been saved then
        return False
    cursor = db.cursor()
    cursor.execute("SELECT artist_id,title,album,source_id  FROM songs WHERE title = ? AND album = ? AND artist_id = ?;",(song.title,song.album,maybe_artist_id,))
    result = cursor.fetchone()
    return True if result else False


# |----------
# |------ INSERTION 

def insert_new_artist(db:sqlite3.Connection, artist_name:str):
    cursor = db.cursor()
    cursor.execute("INSERT OR IGNORE INTO artists (name) VALUES (?);",(artist_name,))
    db.commit()

def insert_new_song(db:sqlite3.Connection,song:song_metadata):
    if song_is_in_db(db,song):
        # aborting 
        print("|- [entry, already exists, skipping]")
        return
    maybe_artist = query_artist_id(db,song.artist)
    if maybe_artist is None:
        # inserting 
        insert_new_artist(db,song.artist)
        #FIXME could be improved to remove this extra query
        maybe_artist = query_artist_id(db,song.artist)
    maybe_source = query_source_id(db,song.source)
    if maybe_source is None:
        print(f"|- [DB Insertion] WARNING: unknown Source {song.source}; defaulting to 'YouTube'")
        maybe_source = query_source_id(db,SOURCES[1])

    cursor = db.cursor()
    cursor.execute("""
    INSERT INTO songs (artist_id, title, album, source_id) VALUES (?,?,?,?);
                   """, (
                       maybe_artist,
                       song.title,
                       song.album,
                       maybe_source,
                   ))
    db.commit()


# --- EXTRACT TO MODULE 
def insert_songs_from_dir(path_to_dir:str):
    pass

if __name__ == "__main__":
    print("|--- [Test DB INterface]")
    path = "tst.db"
    connection = initialize_database(path)
    tst_song1 = song_metadata("Hehe","Haha",None,"erstes Album",10,"Spotify")
    tst_song2 = song_metadata("Hehe","Haha",None,"erstes Album",10,"Spotify")
    tst_song3 = song_metadata("Hehehe","Hoho",None,"zweites Album",11,"Spotify")
    tst_song4 = song_metadata("Aladyian","Glacier",None,"Glacier",11,"Spotify")

    # testing inserting 
    insert_new_song(connection,tst_song1)
    # should skip adding it!
    insert_new_song(connection,tst_song1)

    # testing new entries 
    insert_new_song(connection,tst_song2)
    insert_new_song(connection,tst_song3)
    insert_new_song(connection,tst_song4)

    print(song_is_in_db(connection,tst_song3))
