# VERSION 2.3 - MOVIEPY v2 METHOD NAMES
import os
import requests
import feedparser
import asyncio
import edge_tts
from groq import Groq

# Handling the new MoviePy 2.0 imports
try:
    from moviepy import VideoFileClip, AudioFileClip
except ImportError:
    from moviepy.editor import VideoFileClip, AudioFileClip

async def generate_video():
    try:
        print("--- STARTING ENGINE v2.3 ---")
        
        # 1. BRAIN
        print("Finding trend...")
        feed = feedparser.parse("https://trends.google.com/trends/trendingsearches/daily/rss?geo=US")
        trend = feed.entries[0].title if feed.entries else "Future Technology"
        
        client = Groq(api_key=os.environ.get('GROQ_API_KEY'))
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
            r = requests.get("https://api.pexels.com/videos/search?query=technology&per_page=1&orientation=portrait", 
                             headers={"Authorization": pexels_key})
            data = r.json()
            
        video_url = data['videos'][0]['video_files'][0]['link']
        with open("video.mp4", 'wb') as f:
            f.write(requests.get(video_url).content)

        # 4. ASSEMBLY (Updated for MoviePy v2.0)
        print("Rendering final video...")
        audio = AudioFileClip("voice.mp3")
        video = VideoFileClip("video.mp4")
        
        # New method names in MoviePy v2.0:
        # .subclip() -> .subclipped()
        # .set_audio() -> .with_audio()
        
        duration = min(video.duration, audio.duration, 15)
        
        # Check if we use new or old method names
        if hasattr(video, 'subclipped'):
            video = video.subclipped(0, duration)
            final = video.with_audio(audio)
        else:
            video = video.subclip(0, duration)
            final = video.set_audio(audio)
        
        # Ensure the final file is exactly the length of the audio
        final = final.with_duration(audio.duration) if hasattr(final, 'with_duration') else final.set_duration(audio.duration)

        final.write_videofile("final_shorts.mp4", fps=24, codec="libx264", audio_codec="aac")
        print("--- SUCCESS! ---")

    except Exception as e:
        print(f"!!! ERROR: {str(e)}")
        raise e

if __name__ == "__main__":
    asyncio.run(generate_video())
