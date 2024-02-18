import random
import os 
from moviepy.editor import *
from moviepy.video.fx.resize import resize

def get_clip(duration):
    current_duration = 0
    cliparr = []
    video_list = list(os.listdir('bgv/mp4/')) * 50
    random.shuffle(video_list)
    for video in video_list:
        clip = resize(VideoFileClip('bgv/mp4/'+video, audio=False), width=720, height=1280)
        current_duration += clip.duration
        cliparr.append(clip)
        if current_duration > duration + 1:
            break
    return concatenate_videoclips(cliparr)