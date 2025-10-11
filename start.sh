#!/bin/sh
./spotrec.py -o ~/SpotRecTesting --skip-intro -u -a -ac flac -db recording.db --filename-pattern "{artist}/{album}:{title}"
