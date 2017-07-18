#!/usr/bin/python3
from __future__ import absolute_import, division, print_function
from audioclipextractor import AudioClipExtractor, SpecsParser
import glob
import datetime
from os import listdir
import os
from os.path import isfile, join
import subprocess
import re
import json
from webvtt import WebVTT
import sys
import io
import youtube_dl
from multiprocessing import Process, Queue, Pool

# SETUP

DEFAULT_SPLIT_INTERVAL = "00:00:05.000"
CHAN_ID = "UCHugE6eRhqB9_AZQh4DDbIw"
YT_CHANNEL = "https://www.youtube.com/channel/" + CHAN_ID  # jupiter
FFMPEG_PATH = subprocess.getoutput("which ffmpeg")
YDL_OPTS_AUDIO = {
    'format': 'bestaudio/best',
    'extractaudio': True,
}

# END SETUP


def timecode_to_seconds(tc):
    t = datetime.datetime.strptime(tc, "%H:%M:%S.%f")
    seconds = (3600 * t.hour) + (60 * t.minute) + t.second
    return str(seconds) + "." + str(t.microsecond)


def clip_audio(src, destdir, start, end):
    ext = AudioClipExtractor(src, FFMPEG_PATH)
    specs = timecode_to_seconds(start) + ' ' + timecode_to_seconds(end)
    ext.extractClips(specs, destdir, zipOutput=False)


def download_audio(vidid):
    with youtube_dl.YoutubeDL(YDL_OPTS_AUDIO) as ydl:
        ydl.download(['http://www.youtube.com/watch?v=' + vidid])
    filelist = glob.glob(sys.path[0] + '/*' + vidid + '*webm')
    if len(filelist) == 0:
        print("failed getting audio file for " + vidid)
        return


def download_and_extract(fileresults):
    for cc_clip_key in fileresults.keys():
        download_audio(fileresults[cc_clip_key][2])
        specs = ""
        dirname = sys.path[0] + '/' + cc_clip_key.strip().replace(" ", "_") + '/'
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        filelist = glob.glob(sys.path[0] + '/*' + fileresults[cc_clip_key][2] + '*webm')
        filelist.append(glob.glob(sys.path[0] + '/*' + fileresults[cc_clip_key][2] + '*m4a'))
        if filelist.__len__ == 0:
            print("Failed no webm file")
            return
        clip_audio(filelist[0], dirname, fileresults[cc_clip_key][0], fileresults[cc_clip_key][1])
        print("Wrote " + cc_clip_key)


def extract_from_results(results):
    for fileresults in results:
        download_and_extract(fileresults)


def read_subs_tostring(sub_file, strlen):
    webvtt = WebVTT().read(sub_file)
    pred = re.compile('>([a-zA-Z]| ){1,' + str(strlen) + '}<')
    mutstring = io.StringIO()
    removechars = ['>', '<']
    for caption in webvtt:
        iterator = pred.finditer(caption.text)
        mutstring.write(caption.start + ' ')  # start timestamp in text format
        if iterator is not None:
            for x in iterator:
                mutstring.write(x.group().translate({ord(c): '' for c in removechars}).strip() + ' ')
        print(caption.end)  # end timestamp in text format
        mutstring.write('\n')
    return mutstring.getvalue()


def get_video_subs(vidid, strlen):
    ydl_opts = {"writeautomaticsub": True, "skip_download": True}
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download(['http://www.youtube.com/watch?v=' + vidid])
    filelist = glob.glob(sys.path[0] + '/*' + vidid + '*vtt')
    if len(filelist) == 0:
        print("failed getting WebVTT file for " + vidid)
        return
    sub_file = filelist[0]
    subtitle_string = read_subs_tostring(sub_file, strlen)
    output = open(vidid + '.txt', "w")
    output.write(subtitle_string)


def download_all_subs_threaded(threads):
    pool = Pool(processes=threads)
    ytoutput = subprocess.getoutput("youtube-dl -cj --flat-playlist --skip-download " + YT_CHANNEL)
    for line in ytoutput.split("\n"):
        obj = json.loads(line)
        result = pool.apply_async(get_video_subs, [obj["id"], 30])
    pool.close()
    pool.join()
res_threaded_list = []


def res_threaded_list_save_cb(result):
    if result:
        res_threaded_list.append(result)


def search_subs(rootpath, substr, threads):
    findpool = Pool(processes=threads)
    subFiles = [f for f in glob.glob('*.txt')]
    print(len(subFiles))
    for subfileindex in subFiles:
        x = findpool.apply_async(search_file, [rootpath + subfileindex, substr], callback=res_threaded_list_save_cb)
    findpool.close()
    findpool.join()


def search_file(fname, substr):
    results = {}
    temp_arr = []
    counter = 0
    with open(fname, 'r') as subfile:
        for line in subfile:
            temp_arr.append(line)
    for line in temp_arr:
        if substr in line:
            timecodespl = line.split(' ', 1)
            results[timecodespl[1]] = (timecodespl[0], (DEFAULT_SPLIT_INTERVAL if (len(temp_arr) - 2 == counter) else temp_arr[counter + 1].split(' ', 1)[0]), subfile.name.replace(".txt", "").split('/')[-1],)
        # prepare index for getting ending timecode
        counter += 1
    return results

# search the python file's directory for subtitle files
path = sys.path[0] + '/'
print("searching " + path)
results = search_subs(path, " ".join(sys.argv[2:]), int(sys.argv[1]))
#print(json.dumps(res_threaded_list, indent=2))
extract_from_results(res_threaded_list)
