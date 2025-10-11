# SpotRec

Python script to record the audio of the Spotify desktop client using FFmpeg
and PulseAudio
and saving song-data to database.



## Things To Improve
- [ ] add querying information from Spotify instead of musicbrainz - cus its more up to date usually
- [ ] add interface to clear out certain entries from db ( either because of wrong download or similar)
- [ ] improve logging information
- [ ] maybe add timestamps to db?


## Usage

```
python3 spotrec.py
```
or when using the start-script ( that makes use of some parameters one can set)

```
sh start.sh
```

---
### Requirements | Example
- For making use of this tool you need a spotify client.

Then you can run the python script which will record the music:

```
./spotrec.py -o ./my_song_dir --skip-intro
```
By default spotrec will output `*.flac` files. If you want to change the file type to `*.mp3` use the `--audio-codec` flag:

```bash
./spotrec.py -o ./my_song_dir --skip-intro --audio-codec mp3
```

Check the  pulseaudio configuration:

```
pavucontrol
```

Pay attention to the red circles, everything else is muted and with volume set
to 0%

![playback tab](https://github.com/Bleuzen/SpotRec/raw/master/img/pavucontrol_playback_tab.jpeg)

Note: actually "Lavf..." will appear after you start playing a song

![recording tab](https://github.com/Bleuzen/SpotRec/raw/master/img/pavucontrol_recording_tab.jpeg)

![output devices tab](https://github.com/Bleuzen/SpotRec/raw/master/img/pavucontrol_output_devices_tab.jpeg)

![input devices tab](https://github.com/Bleuzen/SpotRec/raw/master/img/pavucontrol_input_devices_tab.jpeg)

![configuration tab](https://github.com/Bleuzen/SpotRec/raw/master/img/pavucontrol_configuration_tab.jpeg)

Finally start playing whatever you want


## Hints

- Disable volume normalization in the Spotify Client

- Do not change the volume during recording

- Use Audacity for post processing

  * because SpotRec records a little longer at the end to ensure that nothing is missing of the song. But sometimes this also includes the beginning of the next song. So you should use Audacity to cut the audio to what you want. From Audacity you can also export it to the format you like (ogg/mp3/...).

> This has been worked on in this fork. It attempts to query information about length of the song and, if received, cuts it down to that size. Further an offset helps, possibly, avoiding recording the next song.
> - If for a song no track length could be determined from external source, it is saved with the prefix `_[UNCHECKED]_`

---

## Troubleshooting

Start the script with the debug flag:

```
./spotrec.py --debug
```

If one of the following scenarios happens:

* you do not see something like the ffmpeg output, which should appear right
  few seconds after the song start

```
# what you should see when ffmpeg is recording ...
size=56400kB time=00:00:04.15 bitrate= 130.7kbits/s speed=1x
```

* you do not see any "Lavf..." in the pavucontrol
  [recording tab](https://github.com/Bleuzen/SpotRec/raw/master/img/pavucontrol_recording_tab.jpeg)
* you get a stacktrace ending with:

```
ValueError: invalid literal for int() with base 10: 'nput'
```

I would suggest you to:

* quickly press the "next song button" and then the "previous song button" in
  the spotify client
* stop everything and start over, after some tries it usually works :)


**Note: sometimes spotify detects when the user does not interact with the
application for a long time (more or less an hour) and starts looping over a
song, to avoid this scenario I would suggest to keep interacting with the
spotify client.**


---
### Ideas for improvement: 

For better tracking of the current state we could introduce a _state\_machine_ denoting the state of a song. 

```

INITIAL --Skip--> Song Records  --Pause Triggered--> Redo Recording
                           \
                            Song Change
                             \
                              > New Song, Stop Recording
```