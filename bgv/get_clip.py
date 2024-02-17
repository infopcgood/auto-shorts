import random
import os 
from moviepy.editor import *

def get_clip(duration):
    current_duration = 0
    cliparr = []
    video_list = list(os.listdir('bgv/mp4/')) * 50
    random.shuffle(video_list)
    for video in video_list:
        clip = VideoFileClip('bgv/mp4/'+video, target_resolution=(1080, 1920), audio=False)
        current_duration += clip.duration
        cliparr.append(clip)
        if current_duration > duration + 1:
            break
    return concatenate_videoclips(cliparr).set_duration(duration + 1)