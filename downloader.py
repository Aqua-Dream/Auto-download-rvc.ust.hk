# -*- coding: utf-8 -*-

import config
import time
import requests
from urllib.request import urlopen
import os
import copy
import sys
import threading
import platform

# load config file
url = config.url
save_dir = config.save_dir
if not save_dir.endswith('/'):
    save_dir += '/'
threads = config.threads


def GetVideoList(PlaylistUrl):
    r = requests.get(PlaylistUrl).text.encode('ascii', 'ignore').decode()
    prefix = PlaylistUrl[:PlaylistUrl.index('playlist')]
    Chunklist_idx = r.index('chunk')
    ChunklistUrl = prefix + r[Chunklist_idx:]
    print( 'Get chunk list url:', ChunklistUrl)
    Chunklist = requests.get(ChunklistUrl).text.encode('ascii', 'ignore').decode()
    Videolist = []
    while 'media' in Chunklist:
        idx = Chunklist.index('media')
        i = idx
        while Chunklist[i] is not '#':
            i += 1
        video = prefix + Chunklist[idx:i-1]
        Videolist.append(video)
        Chunklist = Chunklist[i:]
    print( 'Get video list success!')
    print( 'There are %d chunks' % (len(Videolist)))
    return(Videolist)


def GetVideo(Videolist):
    if not os.path.exists(save_dir):
        os.mkdir(save_dir)
    VideoName = []
    for i in range(len(Videolist)):
        idx = GetCurrentFileIdx(Videolist[i])
        try:
            r = urlopen(Videolist[i])
            if idx==-1:
                print( Videolist[i]," failed")
                continue
            filename = save_dir + str(idx) + '.ts'
            if os.path.isfile(filename):
                filesize = os.path.getsize(filename)
                if filesize==int(r.headers["content-length"]):
                    print( idx,", it has been downloaded")
                    continue
            print( '%d' % (idx),)
            content = r.read()
            VideoName.append(str(i) + '.ts')
            with open(filename, 'wb') as f:
                f.write(content)
        except Exception as e:
            print( Videolist[i],",failed")
            print( e)
            
def Merge_TS(VideoName, dir):

    templist = copy.copy(VideoName)
    
    if len(templist) <= 1:
        return True
    os.chdir(dir)
    print( 'Merging videos ......')
    sys = platform.system()
    if "Windows" in sys:
        src = '+'.join(VideoName)
        cmd = 'copy /b %s %s' %(src, "merged.ts")
    elif "Linux" in sys:
        src = ' '.join(VideoName)
        cmd = 'cat %s > %s' %(src, "merged.ts")
    else:
        raise ValueError("Unrecognized platform system!")
    os.system(cmd)
    for file in VideoName:
        os.remove(file)
   

def GetCurrentFileIdx(VideoUrl):
    idx=-1
    try:
        ts = VideoUrl.split('.')[-2]
    except:
        pass
    try:
        idx = int(ts.split('_')[-1])
    except:
        pass
    return(idx)
    
def getsortedlist():
    # sort the VideoName according to the number not the ascii code
    VideoName = os.listdir(save_dir)
    for i in range(len(VideoName)):
        VideoName[i] = int(VideoName[i].split('.')[0])
    VideoName = sorted(VideoName)
    for i in range(len(VideoName)):
        VideoName[i] = str(VideoName[i]) + '.ts'
    return VideoName
    
if __name__ == '__main__':
    if len(sys.argv)==1: # no argument
        PlaylistUrl = url
        Videolist = GetVideoList(PlaylistUrl)

        # assign each threads' workload
        if threads > len(Videolist):
            threads = len(Videolist)
        num = len(Videolist) // threads
        mod = len(Videolist) % threads
        thrVideolist = [[]]*threads
        x = 0
        for i in range(threads):
            thrVideolist[i] = Videolist[x:x+num]
            x += num
            if i < mod:
                thrVideolist[i].append(Videolist[x])
                x += 1
        # establish threads
        thr = []
        for i in range(threads):
            t = threading.Thread(target=GetVideo, args=(thrVideolist[i],))
            thr.append(t)
            t.start()

        # wait every threads to complete tasks
        for i in range(threads):
            thr[i].join()
        VideoName = getsortedlist()
        # merge the videos downloaded into one file
        Merge_TS(VideoName, save_dir)
    else:
        VideoName = getsortedlist()
        Merge_TS(VideoName, save_dir)
