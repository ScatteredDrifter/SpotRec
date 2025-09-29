# |-- Holds Several Data Representations + possible helper functions

# External Imports
from typing import NamedTuple


class song_metadata(NamedTuple):
    artist:str
    title:str
    track_id:str|None
    album:str
    song_length_in_ms:int
    source:str|None
