import sys
import os
from navertts import NaverTTS
import subprocess
import time
import re
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from moviepy.editor import *
from moviepy.config import change_settings
from moviepy.video.fx.resize import resize
from dotenv import dotenv_values

DOTENV_CONFIG = dotenv_values(".env")
change_settings({"FFMPEG_BINARY":"ffmpeg"})

CWD = os.getcwd()
sys.path.append("bgv/")
sys.path.append("libraries/")

from get_clip import get_clip

from tiktok_uploader.upload import upload_video

def get_pending_posts():
    pending_file = open('video_algorithm/reddit_stories/pending_posts.txt', "r")
    pending_posts_list = pending_file.readlines()
    pending_file.close()
    return pending_posts_list

def get_popular_reddit_post(driver):
    pending_posts_list = get_pending_posts()
    pending_file = open('video_algorithm/reddit_stories/pending_posts.txt', "a")
    driver.get('https://www.reddit.com/r/nosleep/top/?t=month')
    screen_height = 500 #driver.execute_script("return window.screen.height;")   # get the screen height of the web
    for i in range(10):
        driver.execute_script(f"window.scrollTo(0, {screen_height}*{i});")  
        i += 1
        time.sleep(1.75)
    all_posts = driver.find_elements(By.CSS_SELECTOR, "article.w-full > shreddit-post") + driver.find_elements(By.CSS_SELECTOR, "#main-content > div > faceplate-batch > article > shreddit-post")
    for post in all_posts:
        url = post.get_attribute("content-href")+"\n"
        if not (url in pending_posts_list):
            pending_file.write(url)
    pending_file.close()

def get_post_info(driver, post):
    driver.get(post)
    time.sleep(2)
    title = driver.find_element(By.XPATH, "//h1[starts-with(@id, 'post-title-')]").text
    driver.find_element(By.XPATH, "//*[contains(@id, '-read-more-button')]").click()
    time.sleep(3)
    # needs some improvements i guess
    bodies = driver.find_elements(By.XPATH, f"//div[@id='t3_{post.split('/')[6]}-post-rtjson-content']/p")
    body = []
    for p in bodies:
        text = p.text
        if text.find("Upvote") != -1:
            break
        body += re.findall('[^.…,\-~:;?!]+|.…,-~:;?!', text.replace('“', '').replace('”', ''))
    return {"title": title, "body": body}

def generate_video(driver, post):
    post_info_dict = get_post_info(driver, post)
    NaverTTS(post_info_dict["title"], lang="en", speed=-2, lang_check=False, pre_processor_funcs=[]).save("video_algorithm/reddit_stories/tmp/atitle.mp3")
    body_tts = []
    for i, line in enumerate(post_info_dict["body"]):
        print('Connecting to API', i)
        try:
            body_tts.append(NaverTTS(line, lang="en", speed=-2, lang_check=False, pre_processor_funcs=[]))
        except:
            continue
    for i, tts in enumerate(body_tts):
        print('Starting audio download', i)
        try:
            tts.save(f"video_algorithm/reddit_stories/tmp/body{i:03}.mp3")
            time.sleep(0.03)
        except Exception as e:
            print(e)
    time.sleep(3)
    print("tts generation done!")

    SCREEN_SIZE = (720, 1280)
    TEXT_BIG_SIZE = (350 * 5, 240 * 5)
    TEXT_FIT_SIZE = (350, 240)
    FONT_NAME = "Argentum-Sans-ExtraBold"

    empty_audio_clip = AudioClip(lambda t: 0, duration = 0.03)
    duration = 0
    duration_index = []
    audiocliparr = []
    videocliparr = []
    for i, audio_filename in enumerate(sorted(os.listdir('video_algorithm/reddit_stories/tmp/'))):
        print(f'audio {i}')
        try:
            textclip = resize(TextClip(post_info_dict["body"][i-1] if i>0 else post_info_dict["title"], color='white', stroke_color='black', stroke_width = 6.66, font= FONT_NAME, size=TEXT_BIG_SIZE, align='center', method='caption'), width = 350, height=240).set_position((185, 520))
            audioclip = AudioFileClip('video_algorithm/reddit_stories/tmp/' + audio_filename)
            audiocliparr += [audioclip.set_start(duration), empty_audio_clip]
            videocliparr.append(textclip.set_start(duration).set_end(duration + audioclip.duration))
            duration += audioclip.duration + 0.03
            if duration >= 90:
                break
        except Exception as e:
            print(e)
            continue
    print(duration)

    videocliparr = [resize(get_clip(duration), width=720, height=1280)] + videocliparr

    final_video = CompositeVideoClip(videocliparr, size=(720, 1280))
    final_audio = CompositeAudioClip(audiocliparr)
    final_video.audio = final_audio
    final_video.duration = duration
    final_video.write_videofile(f"[REDDIT] {post_info_dict['title']}.mp4", codec="h264_nvenc", ffmpeg_params=["-crf", "28"])
    return f"[REDDIT] {post_info_dict['title']}.mp4", post_info_dict["title"]

def upload_to_tiktok(driver, video_filename, title):
    upload_video(video_filename, title, 'tiktok-cookies.txt', stitch=False, duet=False)
    input("Upload complete, check!")

def generate(update_post_list = False):
    # initialize geckodriver
    geckodriver_service = Service()
    geckodriver_options = Options()
    geckodriver_options.add_argument("--headless")
    driver = webdriver.Firefox(service=geckodriver_service, options=geckodriver_options)
    print('driver connected.')
    if update_post_list:
        get_popular_reddit_post(driver)

    posts_list = get_pending_posts()

    for post in posts_list:
        post.strip()
        # video_filename, title = "[REDDIT] My husband started teasing me after I suffered a serious head injury. I literally can't go on like this..mp4", "My husband started teasing me after I suffered a serious head injury. I literally can't go on like this."
        video_filename, title = generate_video(driver, post)
        upload_to_tiktok(driver, video_filename, "[REDDIT] "+title)
        posts_list.remove(post)
    
    driver.close()
    pending_file = open('video_algorithm/reddit_stories/pending_posts.txt', "w")
    for post in posts_list:
        pending_file.write(post)
    pending_file.close()

if __name__ == "__main__":
    generate()