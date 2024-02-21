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
from youtube_up import AllowCommentsEnum, Metadata, PrivacyEnum, YTUploaderSession
import json
import asyncio
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip

DOTENV_CONFIG = dotenv_values(".env")
change_settings({"FFMPEG_BINARY":"ffmpeg"})

CWD = os.getcwd()
sys.path.append("bgv/")
sys.path.append("uploaders/")

from get_clip import get_clip

def clear_tmp():
    for f in os.listdir('video_algorithm/reddit_stories/tmp/'):
        os.remove('video_algorithm/reddit_stories/tmp/'+f)

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
    for i in range(200):
        driver.execute_script(f"window.scrollTo(0, {screen_height}*{i});") 
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
        if text.find("Upvote") != -1 or text.lower().find("edit:") == 0 or text == 'X':
            break
        body += re.findall('[^.…,~:;?!]+|.…,~:;?!', text.replace('“', '').replace('”', ''))
    return {"title": title, "body": body}

def generate_video(driver, post_info_dict):
    clear_tmp()
    if not os.path.exists("[REDDIT] "+post_info_dict["title"]+".mp4"):
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

        CR = 1080 / 720

        SCREEN_SIZE = (1080, 1920)
        TEXT_BIG_SIZE = (350 * 5 * CR, 200 * 5 * CR)
        TEXT_FIT_SIZE = (350 * CR, 200 * CR)
        FONT_NAME = "Argentum-Sans-ExtraBold"

        empty_audio_clip = AudioClip(lambda t: 0, duration = 0.03)
        duration = 0
        duration_index = []
        audiocliparr = []
        videocliparr = []
        for i, audio_filename in enumerate(sorted(os.listdir('video_algorithm/reddit_stories/tmp/'))):
            print(f'audio {i}')
            try:
                textclip = resize(TextClip(post_info_dict["body"][i-1].upper() if i>0 else post_info_dict["title"], color='white' if i>0 else 'black', stroke_color='black', stroke_width = 6.66*CR if i>0 else 0, font= FONT_NAME, size=TEXT_BIG_SIZE, align='center', method='caption'), width = 350 * CR, height=200 * CR).set_position((185 * CR, 540 * CR))
                audioclip = AudioFileClip('video_algorithm/reddit_stories/tmp/' + audio_filename)
                audiocliparr += [audioclip.set_start(duration), empty_audio_clip]
                videocliparr.append(textclip.set_start(duration).set_end(duration + audioclip.duration))
                duration += audioclip.duration + 0.04
                if not full_video and duration >= 60:
                    break
            except Exception as e:
                print(e)
                continue
        print(duration)

        title_image_clip = ImageClip("video_algorithm/reddit_stories/sbrshorts.png", duration=audiocliparr[0].duration).set_start(0)
        videocliparr = [resize(get_clip(duration), width=1080, height=1920), title_image_clip] + videocliparr

        final_video = CompositeVideoClip(videocliparr, size=(1080, 1920))
        final_audio = CompositeAudioClip(audiocliparr)
        final_video.audio = final_audio
        final_video.write_videofile(f"uncut_[REDDIT] {post_info_dict['title']}.mp4", codec="h264_nvenc")
        ffmpeg_extract_subclip(f"uncut_[REDDIT] {post_info_dict['title']}.mp4", 0, 59, f"[REDDIT] {post_info_dict['title']}.mp4")
    
    return f"[REDDIT] {post_info_dict['title']}.mp4", post_info_dict["title"]

def upload(filename, options):
    uploader = YTUploaderSession.from_cookies_txt('cookies-youtube-com.txt')
    metadata = Metadata(
        title=options["title"],
        description=options["description"],
        privacy=PrivacyEnum.PUBLIC,
        made_for_kids=False,
        tags=options["keywords"].split(", "),
        allow_comments_mode=AllowCommentsEnum.ALL_COMMENTS
    )
    uploader.upload(filename, metadata)
    print("Uploaded", filename)

def generate(update_post_list = False, full_video = False):
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
        origpost = post
        post.strip()
        print("Generating", post)
        post_info_dict = get_post_info(driver, post)
        if not ((post_info_dict["title"].lower().find('part ') + 1) or (post_info_dict["title"].lower().find('pt. ') + 1) or (post_info_dict["body"][0].lower().find('part') == 0)):
            video_filename, title = generate_video(driver, post_info_dict)
            input('Waiting.')
            upload(video_filename, {"title": "#shorts #redditstories #scary #horror", "description": title, "keywords": "shorts, reddit, stories, redditstories, redditshorts, redditvideos, scary, horror, tales, posts, stories, redditor, nosleep, mildlyinfuriating, scarystories"})
            if full_video:
                upload("uncut_"+video_filename, {"title": title, "description": title+"\n\nHey, please subscribe & like if you want to support me!\n\n\n\n\n\n\n\nreddit, stories, redditstories, redditshorts, redditvideos, scary, horror, tales, posts, stories, redditor, nosleep, mildlyinfuriating, scarystories", "keywords": "reddit, stories, redditstories, redditshorts, redditvideos, scary, horror, tales, posts, stories, redditor, nosleep, mildlyinfuriating, scarystories"})
            os.remove(video_filename)
            os.remove("uncut_"+video_filename)
        posts_list.remove(origpost)
        history_file = open('video_algorithm/reddit_stories/history.txt', 'a')
        history_file.write(origpost)
        history_file.close()
        pending_file = open('video_algorithm/reddit_stories/pending_posts.txt', "w")
        for ipost in posts_list:
            pending_file.write(ipost)
        pending_file.close()
    
    driver.close()

if __name__ == "__main__":
    generate(False)