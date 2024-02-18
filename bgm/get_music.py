import random
import os
from moviepy.editor import *

def get_music(duration=90):
    music_list = os.listdir("bgm/mp3")
    selected_music = "bgm/mp3/" + random.choice(music_list)
    return AudioFileClip(selected_music).set_duration(duration)
