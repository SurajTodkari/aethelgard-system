# VERSION 3.2 - STABLE PRODUCTION
import os, requests, feedparser, asyncio, edge_tts, re
from groq import Groq

try:
    from moviepy import VideoFileClip, AudioFileClip, concatenate_videoclips, CompositeAudioClip
    V2 = True
except ImportError:
    from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips, CompositeAudioClip
    V2 = False

def clean_text(text):
    # Removes AI stage directions like [0s-5s] or (Visual: ...)
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'\(.*?\)', '', text)
    return text.replace('*', '').strip()

async def generate_world_class_video():
    try:
        print("--- AETHELGARD v3.2: STABLE PRODUCTION ---")
        client = Groq(api_key=os.environ.get('GROQ_API_KEY'))

        # 1. BRAIN: High-Precision Prompting
        print("Brain: Generating Viral Narrative...")
        prompt = """
        Write a 20-second YouTube Short script about 'Future Technology'.
        STRICT FORMAT:
        VOICEOVER: [Write only the spoken words here, no timestamps]
        KEYWORDS: [Keyword1, Keyword2, Keyword3, Keyword4, Keyword5]
        """
        chat = client.chat.completions.create(model="llama-3.1-8b-instant", messages=[{"role": "user", "content": prompt}])
        response = chat.choices[0].message.content
        
        # Robust Parsing
        script_raw = response.split("VOICEOVER:")[1].split("KEYWORDS:")[0]
        script_text = clean_text(script_raw)
        kw_section = response.split("KEYWORDS:")[1]
        keywords = [k.strip().replace('*', '') for k in kw_section.split(',')]
        
        print(f"Script: {script_text}\nKeywords: {keywords}")

        # 2. VOICE
        print("Voice: Synthesizing Neural Audio...")
        await edge_tts.Communicate(script_text, "en-US-AndrewNeural").save("voice.mp3")
        voice_audio = AudioFileClip("voice.mp3")
        total_duration = voice_audio.duration

        # 3. VISUALS: Scavenging with Fallbacks
        print("Visuals: Building Cinematic Timeline...")
        pexels_key = os.environ.get('PEXELS_API_KEY')
        final_clips = []
        clip_target_dur = total_duration / len(keywords)

        for i, kw in enumerate(keywords):
            search_url = f"https://api.pexels.com/videos/search?query={kw}&per_page=1&orientation=portrait"
            r = requests.get(search_url, headers={"Authorization": pexels_key}).json()
            
            video_files = r.get('videos', [])
            if not video_files: # Fallback if specific keyword fails
                print(f"Fallback for keyword: {kw}")
                r = requests.get("https://api.pexels.com/videos/search?query=technology&per_page=1&orientation=portrait", 
                                 headers={"Authorization": pexels_key}).json()
                video_files = r.get('videos', [])

            v_url = video_files[0]['video_files'][0]['link']
            v_path = f"temp_v_{i}.mp4"
            with open(v_path, 'wb') as f: f.write(requests.get(v_url).content)
            
            clip = VideoFileClip(v_path)
            # Standardizing resolution
            clip = clip.resized(height=1920) if V2 else clip.resize(height=1920)
            clip = clip.cropped(center_x=clip.w/2, center_y=clip.h/2, width=1080, height=1920) if V2 \
                   else clip.crop(x_center=clip.w/2, y_center=clip.h/2, width=1080, height=1920)
            
            # Use subclipped (v2) or subclip (v1)
            duration_to_use = min(clip.duration, clip_target_dur)
            final_clips.append(clip.subclipped(0, duration_to_use) if V2 else clip.subclip(0, duration_to_use))

        # 4. AUDIO: Layering Music
        print("Audio: Layering background track...")
        music_req = requests.get("https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3")
        with open("bg_music.mp3", "wb") as f: f.write(music_req.content)
        bg_music = AudioFileClip("bg_music.mp3")
        bg_music = bg_music.with_volume_scaled(0.15) if V2 else bg_music.volumex(0.15)
        bg_music = bg_music.with_duration(total_duration) if hasattr(bg_music, 'with_duration') else bg_music.set_duration(total_duration)

        # 5. FINAL RENDER
        print("Assembly: Multi-track Render...")
        video_track = concatenate_videoclips(final_clips, method="compose")
        comp_audio = CompositeAudioClip([voice_audio, bg_music])
        
        final_video = video_track.with_audio(comp_audio) if V2 else video_track.set_audio(comp_audio)
        final_video.write_videofile("final_shorts.mp4", fps=24, codec="libx264", audio_codec="aac")
        print("--- SUCCESS ---")

    except Exception as e:
        print(f"!!! CRITICAL ERROR: {str(e)}")
        raise e

if __name__ == "__main__":
    asyncio.run(generate_world_class_video())
