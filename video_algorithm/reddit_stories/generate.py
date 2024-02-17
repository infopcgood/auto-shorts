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

CWD = os.getcwd()
sys.path.append("bgv/")

from get_clip import get_clip

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
        body += re.findall('[^.,:;?!]+|.,:;?!', text.replace('“', '').replace('”', ''))
    return {"title": title, "body": body}

def generate_video(driver, post):
    post_info_dict = get_post_info(driver, post)
    NaverTTS(post_info_dict["title"], lang="en").save("video_algorithm/reddit_stories/tmp/atitle.mp3")
    body_tts = []
    for line in post_info_dict["body"]:
        continue
        body_tts.append(NaverTTS(line, lang="en"))
    for i, tts in enumerate(body_tts):
        continue
        tts.save(f"video_algorithm/reddit_stories/tmp/body{i:03}.mp3")
    for i in range(len(body_tts)):
        while not os.path.isfile(f"video_algorithm/reddit_stories/tmp/body{i:03}.mp3"):
            trash_do_nothing_variable = 1 + 1
    time.sleep(3)
    print("tts generation done!")

    FONT_NAME = "IBM-Plex-Sans"

    empty_audio_clip = AudioClip(lambda t: 0, duration = 0.4)
    duration = 0
    duration_index = []
    audiocliparr = []
    videocliparr = []
    for i, audio_filename in enumerate(os.listdir('video_algorithm/reddit_stories/tmp/')):
        print(f'audio {i}')
        try:
            textclip = TextClip(post_info_dict["body"][i-1] if i>0 else post_info_dict["title"], color='white', stroke_color='black', stroke_width = 2.5, font= FONT_NAME)
            textclip.set_start(duration)
            audioclip = AudioFileClip('video_algorithm/reddit_stories/tmp/' + audio_filename)
            textclip.set_end(duration + audioclip.duration + 0.1)
            audiocliparr += [audioclip, empty_audio_clip]
            duration += audioclip.duration + 0.4
            videocliparr.append(textclip)
        except:
            continue
    
    videocliparr = [get_clip(duration)] + videocliparr

    final_video = CompositeVideoClip(videocliparr)
    final_audio = CompositeAudioClip(audiocliparr)
    final_video.audio = final_audio
    final_video.duration = duration
    final_video.write_videofile(f"{post.split('/')[6]}.mp4", codec="h264_nvenc")
    input("Finished!")

def generate(update_post_list = False):
    # initialize geckodriver
    geckodriver_service = Service(executable_path=r'./geckodriver')
    geckodriver_options = Options()
    geckodriver_options.add_argument("--headless")
    driver = webdriver.Firefox(service=geckodriver_service, options=geckodriver_options)
    print('driver connected.')
    if update_post_list:
        get_popular_reddit_post(driver)

    posts_list = get_pending_posts()

    for post in posts_list:
        post.strip()
        video_filename = generate_video(driver, post)
        posts_list.remove(post)
    
    driver.close()
    pending_file = open('video_algorithm/reddit_stories/pending_posts.txt', "w")
    for post in posts_list:
        pending_file.write(post)
    pending_file.close()

if __name__ == "__main__":
    generate()