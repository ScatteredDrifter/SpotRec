# This script is run **after** metadata has been added / corrected by some music tagger like Picard
# it traverses a given directory and for each .flac file:
# 1. reads the file
# 2. extracts the length from metadat
# 3. cuts the song to length given this metadata
# 4. saves it again, easy 

# |--- external imports 
import os 
from pydub import AudioSegment
from mutagen import flac 
import shutil
import pprint
import musicbrainzngs

# |--- internal imports 
from mod_data_representation import song_metadata

# variables
user_mail:str = "yourmail"

unchecked_file_prefix:str="[UNCHECKED]_"


def song_track_length_by_id(track_id) -> int | None:
    '''
    utilize the track-ids used by Musicbrainz
    to find the appropriate track-length
    '''
    musicbrainzngs.set_useragent("QueryForCorrectTrackLength", "1.0", user_mail)
    result = musicbrainzngs.get_recording_by_id(track_id)
    pprint.pprint(result)
    # result = musicbrainzngs.search_recordings(artist=artist, recording=title, limit=1)
    recording = result.get('recording', [])
    if recording:
        print(recording)
        length_ms = int(recording.get('length'))
        print(f"length from id {length_ms}")
        return length_ms
    return None

def song_track_length_by_artist(song_info:song_metadata) -> int | None:
    '''
    from song-information query musicbrainz
    to find a matching track and obtain its track length

    (warning: is not guaranteed to find a match)
    '''
    musicbrainzngs.set_useragent("QueryForCorrectTrackLength", "1.0", user_mail)
    # result = musicbrainzngs.get_recording_by_id(track_id)
    query = {
        "artist":song_info.artist,
        "recording":song_info.title,
        "release":song_info.album,
        "limit":10,
    }
    result = musicbrainzngs.search_recordings(**query)
    # pprint.pprint(result)
    # print(f"searching with the following attributes {song_info}")
    recordings = result.get('recording-list', [])
    for rec in recordings:
        rec_title = rec.get('title', '').strip().lower()
        # Extract artist name for comparison
        rec_artist = ''
        if 'artist-credit' in rec and rec['artist-credit']:
            rec_artist = rec['artist-credit'][0].get('name', '').strip().lower()
        # Extract album name if available
        rec_album = None
        if 'release-list' in rec and rec['release-list']:
            rec_album = rec['release-list'][0].get('title', '').strip().lower()
        print(f"|-[release-List]\n|-- title: {rec_title}\n|-- artist: {rec_artist}\n|-- album: {rec_album}\n|----------")
        # classify as match if song-title and album match 
        # (I would argue that this is a good indicator whether the correct track was found) 
        # Not using artist because: the original metadata may not contain the full list of artists --> hence it would be a mismatch
        # yet cases exist where the artist is relevant
        if rec_artist == song_info.artist.strip().lower() and rec_title == song_info.title.strip().lower():
            # highest priority match
            return int(rec.get('length',0))
        elif rec_title == song_info.title.strip().lower() and rec_album == song_info.album.strip().lower():
            return int(rec.get('length', 0))
    return None

def receive_metadata_from_song(audio_ref:flac.FLAC) -> song_metadata|None:
    '''
    requires FLAC-File; obtains song-metadata:
    title,artist,album,track_id and song-length
    may return nothing, if no information could be obtained
    '''
    maybe_title = audio_ref.get("title")
    maybe_artist = audio_ref.get("artist")
    maybe_album = audio_ref.get("album")
    maybe_track_id = audio_ref.get("musicbrainz_trackid")
    maybe_song_length = audio_ref.info.length
    print_info(f"found artist in metadata:: {maybe_artist}")
    # print(audio_ref.info.length)
    if (maybe_title is None)  and (maybe_artist is None): 
        # raise Exception("found invalid file, no artist, title available")
        print_warning("File does not contain artist or title")
        return None
    track_id  = None 
    if maybe_track_id is not None:
        track_id = maybe_track_id[0]

    return song_metadata(
        title=maybe_title[0],
        artist=maybe_artist[0],
        track_id=track_id,
        song_length_in_ms=maybe_song_length*1000,
        album=maybe_album[0],
        source=None
    )

def open_and_shorten_song(audio_path:str):
    if not os.path.isfile(audio_path):
        raise Exception(f"no valid file given {audio_path}")
    if os.path.basename(audio_path).startswith(unchecked_file_prefix):
        print_warning("found file that has been processed already, skipping")
        return 
    
    as_audio = flac.Open(audio_path)

    # receive its metadata
    song_info = receive_metadata_from_song(as_audio)

    if song_info is None:
        return

    # decide whether to query with trackid or artist/title
    track_length = None
    # try:
    if song_info.track_id is not None: 
        track_length = song_track_length_by_id(song_info.track_id)
    else: 
        track_length = song_track_length_by_artist(song_info)
    
    if track_length is None:
        # saving the file again, but with different name -> indicating unchecked state of length etc.
        target_dir = os.path.dirname(audio_path)
        file_name  = os.path.basename(audio_path)
        # print(f"basepath:{target_dir}\nbasename:{file_name}")
        new_name:str = f"{unchecked_file_prefix}{file_name}"
        new_path:str= os.path.join(target_dir,new_name)
        # print(f"new path: {new_path}")
        print_info("No track length found, saving unchecked")
        print_info(f"Saving To {new_path}")
        shutil.move(src=audio_path,dst=new_path)
        return
    
    if track_length == song_info.song_length_in_ms:
        print_info("Track Length already Correct")
        return
    
    # assumes actual track length was found and does not match the given length
    # cuts and overwrites file accordingly
    print_info(f"Found length of {track_length} ms, original length is {song_info.song_length_in_ms}")
    print_info("Cutting to length")
    as_segment = AudioSegment.from_file(audio_path)
    cut_down_version = as_segment[:track_length]
    cut_down_version.export(audio_path, format="flac")

def print_info(content:str):
    print(f"| - [Info]: {content}")

def print_warning(content:str):
    print(f"| - [Warning]: {content}")


if __name__ == "__main__":
    print("Testing PostProcessing-Tool")
    song_unprocessed:str = "/home/evelyn/Nextcloud/tech-cluster/Programming/projects/SpotRec-Fork/spotify/Oaring.flac"
    unp_as_audio = flac.Open(song_unprocessed)
    print(unp_as_audio.pprint())
    print("------------")
    # print("new values")
    metadata = receive_metadata_from_song(unp_as_audio)
    # print(track_length)
    # length = song_track_length_by_id(track_id)
    # length = song_track_length_by_artist(track_artist,track_title)
    # print(f"obtained length: {length}")
    # read metadata from song and gather duration of song 
    open_and_shorten_song(song_unprocessed)