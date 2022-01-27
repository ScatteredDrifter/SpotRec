#!/bin/sh
./spotrec.py -o ./spotify --skip-intro -m -a -ac mp3 --filename-pattern "{artist}/{album}/{artist} - {title}"
