#!/usr/bin/env python
# coding: utf-8

#./spotrec.py -o ./spotify --skip-intro -a -ac mp3 --filename-pattern "{artist}/{album}/{artist} - {title}"')

import subprocess
import os
from pathlib import Path
import shlex
import multiprocessing
import eyed3
import shutil

def getFiles(rootDir):
    gottenFiles = []
    for item in os.scandir(rootDir):
        if item.is_file():
            gottenFiles.append(item.path)
        else:
            gottenFiles = gottenFiles + getFiles(item)
    return gottenFiles

def getTrimmedMp3(mp3):
    fileLocation, fileName = os.path.split(mp3)
    trimmedLocation = os.path.join(fileLocation, "Trimmed")
    Path(trimmedLocation).mkdir(parents = False, exist_ok = True)
    return os.path.join(trimmedLocation, fileName)

class WithTryCatch:
    def __init__(self, func):
        self.func = func

    def __call__(self, *args, **kwargs):
        try:
            return self.func(*args, **kwargs)
        except Exception as e:
            return e

def run_pooled(func, args):
    with multiprocessing.Pool(multiprocessing.cpu_count()) as p:
        results = p.map(WithTryCatch(func), args)
    failureList = list()
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            failureList.append((i, result))
    return results, failureList

def trimSilence(mp3):
    print("Trimming silence on", mp3)
    encoding = "utf-8"
    trimmedMp3 = getTrimmedMp3(mp3)
    cmd = "sox {} {} silence " \
            "1 0.1 0.1% " \
            "reverse silence 1 0.1 0.% " \
            "reverse".format(
                shlex.quote(mp3),
                shlex.quote(trimmedMp3)
            )
    with open("/dev/null", "w") as devnull:
        subprocess.run(cmd.encode(encoding),
                       stdin=None,
                       stdout=devnull,
                       stderr=devnull,
                       shell=True,
                       encoding=encoding)
    return trimmedMp3

def copyOverArtwork(mp3):
    print("Copying artwork from", mp3)
    trimmedMp3 = getTrimmedMp3(mp3)
    original = eyed3.load(mp3)
    trimmed  = eyed3.load(trimmedMp3)
    if len(original.tag._images) == 0:
        return
    original_dict = original.tag._images[0].__dict__.copy()
    trimmed.tag.images.set(type_ = original_dict['_pic_type'],
                            img_data = original_dict['image_data'],
                            mime_type = original_dict['_mime_type'])
    trimmed.tag.save()

def cleanUp(mp3):
    print("Cleaning up", mp3)
    trimmedMp3 = getTrimmedMp3(mp3)
    if os.path.exists(trimmedMp3):
        shutil.move(trimmedMp3, mp3)
    trimmedLocation, _ = os.path.split(trimmedMp3)
    try:
        os.rmdir(trimmedLocation)
    except OSError:
        pass

def createArtworkFiles(mp3):
    fileLocation, fileName = os.path.split(mp3)
    fileNameNoExt, _ = fileName.rsplit('.mp3', 1)
    jpegFile = os.path.join(fileLocation, fileNameNoExt + '.jpeg')
    jpgFile = os.path.join(fileLocation, fileNameNoExt + '.jpg')
    if os.path.exists(jpegFile):
        shutil.move(jpegFile, jpgFile)
    for fileName in ['folder', 'poster', 'cover', 'default', 'clearart', 'backdrop', 'fanart', 'background'] +                     ['art', 'extrafanart', 'banner', 'disc', 'cdart', 'logo', 'thumb', 'landscape']:
        newFile = os.path.join(fileLocation, fileName + '.jpg')
        if not os.path.exists(newFile):
            os.link(jpgFile, newFile)

def run_multiple_pooled(funcs, strings, mp3s):
    for func, string in zip(funcs, strings):
        results, failureList = run_pooled(func, mp3s)
        if len(failureList) > 0:
            for (i, e) in failureList:
                print("Failure {} " \
                        "on #{} for mp3 " \
                        "{} because {}".format(
                            string,
                            i,
                            mp3s[i],
                            e
                        )
                    )
            return False
    return True


def main():
    rootDir = './spotify'
    mp3s = [ i for i in getFiles(rootDir) if i.endswith('.mp3') and '/Trimmed/' not in i ]
    if not run_multiple_pooled([trimSilence, copyOverArtwork, cleanUp, createArtworkFiles],
                            ["trimming silence", "copying artwork", "cleaning up", "creating artwork files"],
                            mp3s):
        return 1
    else:
        return 0

if __name__ == "__main__":
    main()
