import os
import requests
import feedparser
import asyncio
import edge_tts
from groq import Groq
from pexels_api import API as PexelsAPI
from moviepy.editor import VideoFileClip, AudioFileClip

async def generate_video():
    # 1. BRAIN: Find Trend & Write Script
    print("Finding trends...")
    feed = feedparser.parse("https://trends.google.com/trends/trendingsearches/daily/rss?geo=US")
    trend = feed.entries[0].title
    
    client = Groq(api_key=os.environ['GROQ_API_KEY'])
    prompt = f"Write a 15-second YouTube Short script about {trend}. Direct and punchy. No intro. Maximum 40 words."
    chat = client.chat.completions.create(model="llama3-8b-8192", messages=[{"role": "user", "content": prompt}])
    script = chat.choices[0].message.content
    print(f"Script generated: {script}")

    # 2. VOICE: Convert Script to Audio
    print("Generating voice...")
    communicate = edge_tts.Communicate(script, "en-US-ChristopherNeural")
    await communicate.save("voice.mp3")

    # 3. VISUALS: Get Clips from Pexels (Portrait Mode)
    print(f"Fetching video for: {trend}")
    api = PexelsAPI(os.environ['PEXELS_API_KEY'])
    # Search for PORTRAIT videos specifically
    api.search(trend, page=1, results_per_page=1)
    entries = api.get_entries()
    
    if not entries: # Fallback if trend has no videos
        api.search("technology", page=1, results_per_page=1)
        entries = api.get_entries()
        
    video_url = entries[0].urls['download']
    with open("video.mp4", 'wb') as f:
        f.write(requests.get(video_url).content)

    # 4. ASSEMBLY: Stitch it together
    print("Assembling final video...")
    audio = AudioFileClip("voice.mp3")
    # Load video, crop/resize to match audio length
    video = VideoFileClip("video.mp4").subclip(0, min(15, audio.duration))
    
    # Ensure it's a Short (Vertical)
    final = video.set_audio(audio)
    final.write_videofile("final_shorts.mp4", fps=24, codec="libx264", audio_codec="aac")
    print("Success!")

if __name__ == "__main__":
    asyncio.run(generate_video())
