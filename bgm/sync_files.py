import yt_dlp
from yt_dlp.utils import download_range_func
import os

def sync_files():
    # get working directory
    CWD = os.getcwd()

    # get bgm list file and read lines from it
    bgm_list_file = open(CWD + '/bgm/bgm_list.txt', 'r')
    lines = bgm_list_file.readlines()

    # sync individual line
    for line in lines:
        data = line.strip().split(' ')
        if len(data) == 1: # no starting timestamp
            ydl_opt = {
                'outtmpl': f"{CWD}/bgm/mp3/{data[0][32:]}",
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }, {'key': 'FFmpegMetadata'},],
            }
        else: # starting timestamp
            ydl_opt = {
                'outtmpl': f"{CWD}/bgm/mp3/{data[0][32:]}",
                'format': 'bestaudio/best',
                'download_ranges': download_range_func(None, [(int(data[1]), int(data[1]) + 60)]),
                'force_keyframes_at_cuts': True,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }, {'key': 'FFmpegMetadata'},],
            }
        ydl = yt_dlp.YoutubeDL(ydl_opt)
        ydl.download(data[0])

if __name__ == '__main__':
    sync_files()
