import os
import requests
import feedparser
import asyncio
import edge_tts
import random
from groq import Groq
from pexels_api import API as PexelsAPI
from moviepy.editor import VideoFileClip, AudioFileClip

async def generate_video():
    try:
        # 1. BRAIN: Find Trend
        print("--- STEP 1: FINDING TREND ---")
        feed = feedparser.parse("https://trends.google.com/trends/trendingsearches/daily/rss?geo=US")
        if not feed.entries:
            trend = "Technology and Future" # Fallback
        else:
            trend = feed.entries[0].title
        print(f"Trend found: {trend}")
        
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

        # 4. VISUALS: Pexels
        print("--- STEP 4: FETCHING VIDEO ---")
        api = PexelsAPI(os.environ.get('PEXELS_API_KEY'))
        
        # Try to find video for the trend, if not, try 'nature' as fallback
        api.search(trend, page=1, results_per_page=1)
        results = api.get_entries()
        
        if not results:
            print("No video found for trend. Using fallback search...")
            api.search("abstract tech", page=1, results_per_page=1)
            results = api.get_entries()
            
        video_url = results[0].urls['download']
        print(f"Downloading video from: {video_url}")
        
        v_data = requests.get(video_url)
        with open("video.mp4", 'wb') as f:
            f.write(v_data.content)

        # 5. ASSEMBLY: MoviePy
        print("--- STEP 5: ASSEMBLING ---")
        audio = AudioFileClip("voice.mp3")
        video = VideoFileClip("video.mp4")
        
        # Loop video to match audio length and resize for mobile
        video = video.subclip(0, min(video.duration, 15))
        if video.duration < audio.duration:
            video = video.loop(duration=audio.duration)
        else:
            video = video.set_duration(audio.duration)
            
        final = video.set_audio(audio)
        # Force a lower resolution for faster free rendering
        final.write_videofile("final_shorts.mp4", fps=24, codec="libx264", audio_codec="aac", temp_audiofile='temp-audio.m4a', remove_temp=True)
        print("--- SUCCESS! ---")

    except Exception as e:
        print(f"!!! CRITICAL ERROR: {str(e)}")
        raise e # This tells GitHub the run failed

if __name__ == "__main__":
    asyncio.run(generate_video())
