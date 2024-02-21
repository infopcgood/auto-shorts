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
        clip = resize(VideoFileClip('bgv/mp4/'+video, audio=False), width=1080, height=1920)
        if current_duration + clip.duration >= duration:
            start_time = random.uniform(0, clip.duration - (duration - current_duration))
            print(start_time)
            clip = clip.cutout(start_time, start_time + (duration - current_duration))
        current_duration += clip.duration
        cliparr.append(clip)
        if current_duration >= duration:
            break
    return concatenate_videoclips(cliparr)