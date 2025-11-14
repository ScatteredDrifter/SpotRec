# This tool is aimed at being an option to recover lost databases from files.

# internal imports
import sqlite3
import os
import argparse
# external imports
from mod_db_interface import song_is_in_db,initialize_database,insert_new_song
from mod_data_representation import song_metadata
from mod_post_process_picard import get_metadata_from_file

# -----
    # parsing and traversing collection
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Union

def collect_songs_to_parse(dir_path:str, ignore_paths: list[str] | None) -> list[str]:
    """
    Traverse dir_path and collect .flac/.mp3 files while skipping hidden paths
    and any folder names contained in ignore_paths.

    ignore_paths: list of folder names (not full paths). Matching is case-insensitive
    against any path component under the base directory.
    """
    collected_songs:list[str] = []

    # traversing files 
    p = Path(dir_path)
    if not p.is_dir():
        raise NotADirectoryError(f"{dir_path!r} is not a directory")

    for f in p.rglob("*"):
        if not f.is_file():
            continue
        if f.suffix.lower() not in (".flac", ".mp3"):
            continue
        # skip hidden files and directories
        try:
            rel_parts = f.relative_to(p).parts
        except Exception:
            rel_parts = f.parts
        if any(part.startswith('.') for part in rel_parts):
            continue
        # skip any paths that contain a component listed in ignore_paths
        if ignore_paths:
            # compare case-insensitive
            ignore_set = {s.lower().strip() for s in ignore_paths}
            if any(part.lower() in ignore_set for part in rel_parts):
                continue
        collected_songs.append(str(f.resolve()))

    # sort for deterministic order
    collected_songs.sort()

    return collected_songs 

def collect_metadata_from_songs(list_of_songs:list[str]) -> list[song_metadata]:
    retrieved_metadata:list[song_metadata] = []

    for entry in list_of_songs:
        maybe_metadata = get_metadata_from_file(entry)
        if maybe_metadata:
            retrieved_metadata.append(maybe_metadata)
    return retrieved_metadata

if __name__ == "__main__":
    print("|- recoverying database from collection")
    parser = argparse.ArgumentParser(prog="Recording-DB-From-Collection",
                                     usage="construct database from Collection",
                                     formatter_class=argparse.RawTextHelpFormatter
                                     )
    parser.add_argument("-db","--database",
                        help="name of resulting database",
                        required=True
                        )
    parser.add_argument("-dir","--directory",
                        help="receive path to collection",
                        required=True)
    parser.add_argument("-s","--source",
                        help="Set source of music to Spotify,None otherwise",
                        action="store_true",default=False,
                        required=False)
    parser.add_argument("-ignore","--ignore_folders",
                        help="write liste of folders to ignore; divided by ;",
                        required=False
                        )
    
    arguments = parser.parse_args()

    db_path    = arguments.database
    collection_path = arguments.directory
    ignore_folders:str|None = arguments.ignore_folders
    add_spotify_as_source = arguments.source

    if not os.path.isdir(collection_path):
        print("|-[Warning] - path to collection invalid")
        exit()
    
    # traversing collection
    if ignore_folders: 
        ignore_as_list = ignore_folders.split(";")
        print(ignore_as_list)
        songs = collect_songs_to_parse(collection_path,ignore_as_list)
    else:
        songs = collect_songs_to_parse(collection_path,None)

    metadata = collect_metadata_from_songs(songs)

    if add_spotify_as_source:
        # new instances with the updated `source` field instead of attempting
        # to assign to the field which raises an error.
        metadata = [entry._replace(source="Spotify") for entry in metadata]

    # adding to db
    db_connection = initialize_database(f"{db_path}.db")
    for entry in metadata:
        insert_new_song(db_connection,entry)




    
