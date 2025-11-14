# Tool to remove unwantend / false entries from database fast / easily.
# ---| Reads from file with one song per line

import sqlite3
import os
import argparse
from mod_db_interface import song_is_in_db,initialize_database,query_artist_id,query_song_id

# ---|---
def remove_song_from_db(db_connection:sqlite3.Connection,title:str,artist:str|None) -> bool:
    # does not require a specific title or artist, it should be find within the given query
    artist_id:int|None = query_artist_id(db_connection,artist) if artist is not None else None
    song_id:int|None   = query_song_id(db_connection,artist_id,title)

    if not song_id:
        return False
    # remove from db
    cursor = db_connection.cursor()
    cursor.execute("DELETE FROM songs WHERE id = ?",(song_id,))
    db_connection.commit()
    return True

def parse_from_file(path_to_file:str) -> list[tuple[str,str|None]]:
    if not os.path.isfile(path_to_file):
        raise Exception("File Not Existing")
    result:list[tuple[str,str|None]] = []
    with open(path_to_file,'r') as file:
        content = file.readlines()
        for line in content:
            # parsing each entry
            vals = line.split(",")
            if len(vals) == 0:
                continue
            artist = vals[1].strip() if len(vals) >1 else None
            title  = vals[0].strip()
            # print(f"title: {title}, artist: {artist}")
            result.append((title,artist))
    return result
    
def parse_and_remove_files(path_to_file:str,db_connection:sqlite3.Connection):
    songs = parse_from_file(path_to_file)
    for title,artist in songs:
        is_removed = remove_song_from_db(db_connection,title,artist)
        print(f"result: {is_removed} | {title} -- {artist}")

if __name__ == "__main__":
    print("|--- Deletion of Songs in DB")

    parser = argparse.ArgumentParser(prog="Recording-Song-Removal",
                                     usage="remove songs from database",
                                     formatter_class=argparse.RawTextHelpFormatter
                                     )
    parser.add_argument("-db","--database",
                        help="path to recording.db",
                        required=True
                        )
    parser.add_argument("-f","--file",
                        help="pass file containing [title],[artist] per line")
    parser.add_argument("-t","--title",
                        help="set title to remove")
    parser.add_argument("-a","--artist", 
                        help="set artist to query for")
    
    arguments = parser.parse_args()

    db_path    = arguments.database
    maybe_file = arguments.file
    maybe_title = arguments.title
    maybe_artist = arguments.artist

    if not maybe_file and not maybe_title and not maybe_artist:
        print("|-[Warning] - No File nor song info given")
        exit()
    if not os.path.isfile(db_path):
        print("|-[Warning] - database path invalid")
        exit()

    db_connection = initialize_database(db_path)
    if maybe_file:
        if not os.path.isfile(maybe_file):
            print("|-[Warning] - file path invalid")
            exit()
        parse_and_remove_files(maybe_file,db_connection)
    else:
        remove_song_from_db(db_connection,maybe_title,maybe_artist)
