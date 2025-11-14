# Tool To add / import new songs from directory given

# |--- internal imports
from mod_db_interface import initialize_database,query_song_id,query_artist_id,insert_new_song,insert_new_artist
from mod_data_representation import song_metadata
from mod_post_process_picard import receive_metadata_from_flac,get_metadata_from_file

# |--- external imports
import os
import pathlib
from mutagen import flac,wave,mp3


# |----
def extract_from_flac(path:str) -> song_metadata|None:
    as_flac_file = flac.Open(path)
    return receive_metadata_from_flac(as_flac_file)
def extract_from_mp3(path:str) -> song_metadata|None:
    return None
def extract_from_wav(path:str) -> song_metadata|None:
    return None

# |-- Variables
ALLOWED_FILES_SUFFIXES = [".mp3",".wav","flac"]

if __name__ == "__main__":
    print("|---[Running Tool To Parse Songs From Directory]")
    db_path = "/home/evelyn/Nextcloud/tech-cluster/Programming/projects/SpotRec-Fork/recording.db"
    dir_to_traverse ="/home/evelyn/Music_Collection/"

    if not os.path.isdir(dir_to_traverse):
        print("|- invalid path to traverse")
        exit()
    
    if not os.path.isfile(db_path):
        print("|- invalid path to DB")
        exit()

    # |--- ---|
    connection = initialize_database(db_path)

    new_songs:list[song_metadata] = []
    for base_path,subdirs,files in os.walk(dir_to_traverse):
        absolute_path = os.path.join(dir_to_traverse,base_path)
        # print(f"|-----[{absolute_path}]--|")
        for subdir in subdirs:
            # print(f"|---<{subdir}>")
            #run this code again
            continue
        
        # files 
        for file in files:
            filepath = os.path.join(absolute_path,file)
            # print(f"|-- {filepath}")
            if pathlib.Path(filepath).suffix in ALLOWED_FILES_SUFFIXES:
                continue
            maybe_info = get_metadata_from_file(filepath)
            if maybe_info:
                new_songs.append(maybe_info)
    # print(new_songs)
    # print(len(new_songs))


