# This script is run **after** metadata has been added / corrected by some music tagger like Picard
# it traverses a given directory and for each .flac file:
# 1. reads the file
# 2. extracts the length from metadat
# 3. cuts the song to length given this metadata
# 4. saves it again, easy 

# |--- external imports 
import os 
from pydub import AudioSegment
from mutagen import flac,mp3,wave
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

def receive_metadata_from_flac(audio_ref:flac.FLAC) -> song_metadata|None:
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

def receive_metadata_from_mp3(audio_ref:mp3.MP3) -> song_metadata|None:
    '''
    requires MP3-File; obtains song-metadata:
    title, artist, album, track_id and song-length
    may return None if no information could be obtained
    '''
    # MP3 files use ID3 tags
    tags = audio_ref.tags
    if tags is None:
        print_warning("MP3 file does not contain any tags")
        return None
    
    # Extract metadata from ID3 tags
    maybe_title = None
    maybe_artist = None
    maybe_album = None
    maybe_track_id = None
    maybe_song_length = audio_ref.info.length  # Length in seconds
    
    # Get title (TIT2)
    if 'TIT2' in tags:
        maybe_title = [str(tags['TIT2'])]
    
    # Get artist (TPE1)
    if 'TPE1' in tags:
        maybe_artist = [str(tags['TPE1'])]
    
    # Get album (TALB)
    if 'TALB' in tags:
        maybe_album = [str(tags['TALB'])]
    
    # Get MusicBrainz track ID (UFID:http://musicbrainz.org)
    if 'UFID:http://musicbrainz.org' in tags:
        maybe_track_id = [tags['UFID:http://musicbrainz.org'].data.decode('utf-8')]
    elif 'TXXX:MusicBrainz Release Track Id' in tags:
        maybe_track_id = [str(tags['TXXX:MusicBrainz Release Track Id'])]
    
    print_info(f"found artist in metadata:: {maybe_artist}")
    
    if (maybe_title is None) and (maybe_artist is None): 
        print_warning("MP3 file does not contain artist or title")
        return None
    
    track_id = None
    if maybe_track_id is not None:
        track_id = maybe_track_id[0]
    
    return song_metadata(
        title=maybe_title[0] if maybe_title else "Unknown Title",
        artist=maybe_artist[0] if maybe_artist else "Unknown Artist",
        track_id=track_id,
        song_length_in_ms=maybe_song_length * 1000,  # Convert seconds to milliseconds
        album=maybe_album[0] if maybe_album else None,
        source=None
    )

def receive_metadata_from_wav(audio_ref:wave.WAVE) -> song_metadata|None:
    '''
    requires WAV-File; obtains song-metadata:
    WAV files typically don't contain extensive metadata
    but we can extract what's available and the length
    '''
    # WAV files have limited metadata capabilities
    # Most WAV files don't have embedded tags like MP3 or FLAC
    # We'll extract what we can, mainly the length
    
    # Try to get basic info from INFO chunk if available
    info_tags = {}
    if hasattr(audio_ref, 'tags'):
        info_tags = audio_ref.tags
    
    maybe_title = info_tags.get('INAM', ['Unknown Title'])
    maybe_artist = info_tags.get('IART', ['Unknown Artist'])
    maybe_album = info_tags.get('IPRD', ['Unknown Album'])
    maybe_track_id = None  # WAV files typically don't have MusicBrainz IDs
    maybe_song_length = audio_ref.info.length  # Length in seconds
    
    print_info(f"found artist in metadata:: {maybe_artist}")
    
    # WAV files often don't have metadata, so we'll be more lenient
    # and return what we can extract
    
    return song_metadata(
        title=maybe_title[0] if isinstance(maybe_title, list) else maybe_title,
        artist=maybe_artist[0] if isinstance(maybe_artist, list) else maybe_artist,
        track_id=None,
        song_length_in_ms=maybe_song_length * 1000,  # Convert seconds to milliseconds
        album=maybe_album[0] if isinstance(maybe_album, list) and maybe_album else None,
        source=None
    )



def get_metadata_from_file(audio_path: str) -> song_metadata | None:
    """
    Detects the file type and uses the appropriate function to extract metadata.
    Supports FLAC, MP3, and WAV files.
    
    Args:
        audio_path: Path to the audio file
        
    Returns:
        song_metadata object or None if metadata couldn't be extracted
    """
    file_ext = os.path.splitext(audio_path)[1].lower()
    
    try:
        if file_ext == '.flac':
            audio_file = flac.Open(audio_path)
            return receive_metadata_from_flac(audio_file)
        elif file_ext == '.mp3':
            audio_file = mp3.MP3(audio_path)
            return receive_metadata_from_mp3(audio_file)
        elif file_ext == '.wav':
            audio_file = wave.WAVE(audio_path)
            return receive_metadata_from_wav(audio_file)
        else:
            print_warning(f"Unsupported file format: {file_ext}")
            return None
    except Exception as e:
        print_warning(f"Error reading metadata from {audio_path}: {str(e)}")
        return None

def open_and_shorten_song(audio_path:str):
    if not os.path.isfile(audio_path):
        raise Exception(f"no valid file given {audio_path}")
    if os.path.basename(audio_path).startswith(unchecked_file_prefix):
        print_warning("found file that has been processed already, skipping")
        return 
    
    # Get metadata based on file type
    song_info = get_metadata_from_file(audio_path)

    if song_info is None:
        return

    # decide whether to query with trackid or artist/title
    track_length = None
    # try:
    if song_info.track_id is not None: 
        track_length = song_track_length_by_id(song_info.track_id)
    else: 
        track_length = song_track_length_by_artist(song_info)
    
    if True:
    #if track_length is None:
        # saving the file again, but with different name -> indicating unchecked state of length etc.
        target_dir = os.path.dirname(audio_path)
        file_name  = os.path.basename(audio_path)
        # print(f"basepath:{target_dir}\nbasename:{file_name}")
        new_name:str = f"{unchecked_file_prefix}{file_name}"
        new_path:str= os.path.join(target_dir,new_name)
        # print(f"new path: {new_path}")
        print_info("No track length found, saving unchecked")
        # print_info(f"Saving To {new_path}")
        shutil.move(src=audio_path,dst=new_path)
        return
    
    # if track_length == song_info.song_length_in_ms:
        # print_info("Track Length already Correct")
        # return
    
    # assumes actual track length was found and does not match the given length
    # cuts and overwrites file accordingly
    print_info(f"Found length of {track_length} ms, original length is {song_info.song_length_in_ms}")
    print_info(f"received_metadata:{song_info}")
    metadata_as_dict:dict[str,str] = {
        "artist":song_info.artist,
        "title":song_info.title,
        "album":song_info.album if song_info.album is not None else "",
        "source":song_info.source if song_info.source is not None else ""
    }
    # print_info("Cutting to length")
    as_segment = AudioSegment.from_file(audio_path)
    cut_down_version = as_segment[:track_length]
    cut_down_version.export(audio_path, format="flac",tags=metadata_as_dict)

def print_info(content:str):
    print(f"| - [Info]: {content}")

def print_warning(content:str):
    print(f"| - [Warning]: {content}")


if __name__ == "__main__":
    print("Testing PostProcessing-Tool")
    song_unprocessed:str = "/home/evelyn/Nextcloud/tech-cluster/Programming/projects/SpotRec-Fork/tstfile.flac"
    unp_as_audio = flac.Open(song_unprocessed)
    print(unp_as_audio.pprint())
    print("------------")
    # print("new values")
    metadata = receive_metadata_from_flac(unp_as_audio)
    # print(track_length)
    # length = song_track_length_by_id(track_id)
    # length = song_track_length_by_artist(track_artist,track_title)
    # print(f"obtained length: {length}")
    # read metadata from song and gather duration of song 
    open_and_shorten_song(song_unprocessed)