# VERSION 2.2 - UPDATED LLM MODEL
import os
import requests
import feedparser
import asyncio
import edge_tts
from groq import Groq

try:
    from moviepy.editor import VideoFileClip, AudioFileClip
except ImportError:
    from moviepy import VideoFileClip, AudioFileClip

async def generate_video():
    try:
        print("--- STARTING ENGINE v2.2 ---")
        
        # 1. BRAIN
        print("Finding trend...")
        feed = feedparser.parse("https://trends.google.com/trends/trendingsearches/daily/rss?geo=US")
        trend = feed.entries[0].title if feed.entries else "Future Technology"
        
        print(f"Trend identified: {trend}")
        client = Groq(api_key=os.environ.get('GROQ_API_KEY'))
        
        # WE UPDATED THE MODEL NAME BELOW TO llama-3.1-8b-instant
        prompt = f"Write a 15-second YouTube Short script about {trend}. Direct and punchy. No intro. Maximum 40 words."
        chat = client.chat.completions.create(
            model="llama-3.1-8b-instant", 
            messages=[{"role": "user", "content": prompt}]
        )
        script = chat.choices[0].message.content
        print(f"Script: {script}")

        # 2. VOICE
        print("Generating voice...")
        communicate = edge_tts.Communicate(script, "en-US-ChristopherNeural")
        await communicate.save("voice.mp3")

        # 3. VISUALS
        print("Fetching video...")
        pexels_key = os.environ.get('PEXELS_API_KEY')
        search_url = f"https://api.pexels.com/videos/search?query={trend}&per_page=1&orientation=portrait"
        r = requests.get(search_url, headers={"Authorization": pexels_key})
        data = r.json()
        
        if not data.get('videos'):
            print("Trend video not found, using tech fallback...")
            r = requests.get("https://api.pexels.com/videos/search?query=technology&per_page=1&orientation=portrait", 
                             headers={"Authorization": pexels_key})
            data = r.json()
            
        video_url = data['videos'][0]['video_files'][0]['link']
        with open("video.mp4", 'wb') as f:
            f.write(requests.get(video_url).content)

        # 4. ASSEMBLY
        print("Rendering final video...")
        audio = AudioFileClip("voice.mp3")
        video = VideoFileClip("video.mp4")
        
        duration = min(video.duration, audio.duration, 15)
        video = video.subclip(0, duration)
        
        if video.duration < audio.duration:
            video = video.loop(duration=audio.duration)
        
        final = video.set_audio(audio)
        final.write_videofile("final_shorts.mp4", fps=24, codec="libx264", audio_codec="aac")
        print("--- SUCCESS! ---")

    except Exception as e:
        print(f"!!! ERROR: {str(e)}")
        raise e

if __name__ == "__main__":
    asyncio.run(generate_video())
