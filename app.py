import os
import requests
import feedparser
from groq import Groq
from pexels_api import API as PexelsAPI
import asyncio
import edge_tts
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, concatenate_videoclips

# 1. BRAIN: Find Trend & Write Script
def get_content():
    # Gets trending news via RSS
    feed = feedparser.parse("https://trends.google.com/trends/trendingsearches/daily/rss?geo=US")
    trend = feed.entries[0].title
    
    client = Groq(api_key=os.environ['GROQ_API_KEY'])
    prompt = f"Write a 30-second viral YouTube Short script about {trend}. Direct and punchy. No intro. Max 75 words."
    chat = client.chat.completions.create(model="llama3-8b-8192", messages=[{"role": "user", "content": prompt}])
    return trend, chat.choices[0].message.content

# 2. VOICE: Convert Script to Audio
async def make_voice(text):
    communicate = edge_tts.Communicate(text, "en-US-ChristopherNeural")
    await communicate.save("voice.mp3")

# 3. VISUALS: Get Clips from Pexels
def get_video(query):
    api = PexelsAPI(os.environ['PEXELS_API_KEY'])
    api.search(query, page=1, results_per_page=5)
    video_url = api.get_entries()[0].urls['download']
    with open("video.mp4", 'wb') as f:
        f.write(requests.get(video_url).content)

# 4. ASSEMBLY: Stitch it together
def build_video():
    audio = AudioFileClip("voice.mp3")
    video = VideoFileClip("video.mp4").subclip(0, audio.duration).loop(duration=audio.duration)
    final = video.set_audio(audio)
    final.write_videofile("final_shorts.mp4", fps=24, codec="libx264")

if __name__ == "__main__":
    trend, script = get_content()
    print(f"Trend found: {trend}")
    asyncio.run(make_voice(script))
    get_video(trend)
    build_video()
