import yt_dlp
from yt_dlp.utils import download_range_func

def sync_files():
    # get bgm list file and read lines from it
    bgm_list_file = open('bgv/bgv_list.txt', 'r')
    lines = bgm_list_file.readlines()

    # sync individual line
    for line in lines:
        data = line.strip().split(' ')
        if len(data) == 1: # no starting timestamp
            ydl_opt = {
                'outtmpl': f"bgv/mp4/{data[0][31:]}.mp4",
                'format': 'mp4'
            }
        else: # starting timestamp
            ydl_opt = {
                'outtmpl': f"bgv/mp4/{data[0][31:]}.mp4",
                'format': 'mp4',
                'download_ranges': download_range_func(None, [(int(data[1]), int(data[1]) + 60)]),
            }
        ydl = yt_dlp.YoutubeDL(ydl_opt)
        ydl.download(data[0])

if __name__ == '__main__':
    sync_files()
