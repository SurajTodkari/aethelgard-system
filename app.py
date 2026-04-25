import os
import requests
import feedparser
import asyncio
import edge_tts
import random
from groq import Groq
from moviepy.editor import VideoFileClip, AudioFileClip

async def generate_video():
    try:
        # 1. BRAIN: Find Trend
        print("--- STEP 1: FINDING TREND ---")
        feed = feedparser.parse("https://trends.google.com/trends/trendingsearches/daily/rss?geo=US")
        trend = feed.entries[0].title if feed.entries else "Future Technology"
        print(f"Trend: {trend}")
        
        # 2. SCRIPT: Groq LLM
        print("--- STEP 2: WRITING SCRIPT ---")
        client = Groq(api_key=os.environ.get('GROQ_API_KEY'))
        prompt = f"Write a 15-second YouTube Short script about {trend}. Direct and punchy. No intro. Maximum 40 words."
        chat = client.chat.completions.create(model="llama3-8b-8192", messages=[{"role": "user", "content": prompt}])
        script = chat.choices[0].message.content
        print(f"Script: {script}")

        # 3. VOICE: Edge-TTS
        print("--- STEP 3: GENERATING VOICE ---")
        communicate = edge_tts.Communicate(script, "en-US-ChristopherNeural")
        await communicate.save("voice.mp3")

        # 4. VISUALS: Pexels (Using direct API call)
        print("--- STEP 4: FETCHING VIDEO ---")
        pexels_key = os.environ.get('PEXELS_API_KEY')
        # We search for videos directly via URL
        search_url = f"https://api.pexels.com/videos/search?query={trend}&per_page=1&orientation=portrait"
        headers = {"Authorization": pexels_key}
        r = requests.get(search_url, headers=headers)
        
        # If no video found for trend, search for 'technology'
        if not r.json().get('videos'):
            search_url = "https://api.pexels.com/videos/search?query=technology&per_page=1&orientation=portrait"
            r = requests.get(search_url, headers=headers)
            
        video_data = r.json()['videos'][0]
        # Get the HD video link
        video_url = video_data['video_files'][0]['link']
        print(f"Downloading: {video_url}")
        
        with open("video.mp4", 'wb') as f:
            f.write(requests.get(video_url).content)

        # 5. ASSEMBLY: MoviePy
        print("--- STEP 5: ASSEMBLING ---")
        audio = AudioFileClip("voice.mp3")
        video = VideoFileClip("video.mp4")
        
        # Clip and match duration
        video = video.subclip(0, min(video.duration, 15))
        if video.duration < audio.duration:
            video = video.loop(duration=audio.duration)
        else:
            video = video.set_duration(audio.duration)
            
        final = video.set_audio(audio)
        final.write_videofile("final_shorts.mp4", fps=24, codec="libx264", audio_codec="aac")
        print("--- SUCCESS! ---")

    except Exception as e:
        print(f"!!! CRITICAL ERROR: {str(e)}")
        raise e

if __name__ == "__main__":
    asyncio.run(generate_video())
