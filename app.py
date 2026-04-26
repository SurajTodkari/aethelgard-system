import os, requests, feedparser, asyncio, edge_tts
from groq import Groq

# --- VERSION-RESILIENT MOVIEPY IMPORTS ---
try:
    from moviepy import VideoFileClip, AudioFileClip, concatenate_videoclips, CompositeAudioClip
    import moviepy.video.fx as fx
    V2 = True
    print("Detected MoviePy v2.0+")
except ImportError:
    from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips, CompositeAudioClip
    V2 = False
    print("Detected MoviePy v1.0")

# --- UTILITY FUNCTIONS FOR VERSION COMPATIBILITY ---
def get_subclip(clip, start, end):
    return clip.subclipped(start, end) if V2 else clip.subclip(start, end)

def set_audio(clip, audio):
    return clip.with_audio(audio) if V2 else clip.set_audio(audio)

def resize_clip(clip, width, height):
    # This centers and crops for vertical 9:16 aspect ratio
    return clip.resized(height=height).cropped(center_x=clip.w/2, center_y=clip.h/2, width=width, height=height) if V2 \
        else clip.resize(height=height).crop(x_center=clip.w/2, y_center=clip.h/2, width=width, height=height)

async def generate_world_class_video():
    try:
        print("--- AETHELGARD v3.1: ARCHITECT EDITION ---")
        client = Groq(api_key=os.environ.get('GROQ_API_KEY'))

        # 1. BRAIN: Advanced Prompting
        print("Brain: Generating Viral Narrative...")
        prompt = """
        Write a 20-second high-retention YouTube Short script about 'Future Tech'.
        Start with a shocker. Use punchy sentences. 
        Provide 5 'Visual Keywords' for stock footage.
        Format:
        Script: [Text]
        Keywords: [KW1, KW2, KW3, KW4, KW5]
        """
        chat = client.chat.completions.create(model="llama-3.1-8b-instant", messages=[{"role": "user", "content": prompt}])
        response = chat.choices[0].message.content
        script_text = response.split("Keywords:")[0].replace("Script:", "").strip()
        keywords = [k.strip() for k in response.split("Keywords:")[1].strip().replace("[", "").replace("]", "").split(",")]
        print(f"Script: {script_text}\nKeywords: {keywords}")

        # 2. VOICE
        print("Voice: Synthesizing Neural Audio...")
        await edge_tts.Communicate(script_text, "en-US-AndrewNeural").save("voice.mp3")
        voice_audio = AudioFileClip("voice.mp3")
        total_duration = voice_audio.duration

        # 3. VISUALS: Multi-Scene Assembly
        print(f"Visuals: Scavenging {len(keywords)} clips...")
        pexels_key = os.environ.get('PEXELS_API_KEY')
        final_clips = []
        clip_target_dur = total_duration / len(keywords)

        for i, kw in enumerate(keywords):
            search_url = f"https://api.pexels.com/videos/search?query={kw}&per_page=1&orientation=portrait"
            r = requests.get(search_url, headers={"Authorization": pexels_key}).json()
            
            if r.get('videos'):
                v_url = r['videos'][0]['video_files'][0]['link']
                v_path = f"temp_v_{i}.mp4"
                with open(v_path, 'wb') as f: f.write(requests.get(v_url).content)
                
                raw_clip = VideoFileClip(v_path)
                # Apply high-quality resize/crop for vertical 1080x1920
                processed_clip = resize_clip(raw_clip, 1080, 1920)
                final_clips.append(get_subclip(processed_clip, 0, clip_target_dur))

        # 4. AUDIO: Background Music Integration
        print("Audio: Adding Background Music...")
        # Using a reliable royalty-free music link
        music_req = requests.get("https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3")
        with open("bg_music.mp3", "wb") as f: f.write(music_req.content)
        
        bg_music = AudioFileClip("bg_music.mp3")
        bg_music = bg_music.with_volume_scaled(0.1) if V2 else bg_music.volumex(0.1)
        bg_music = bg_music.with_duration(total_duration) if V2 else bg_music.set_duration(total_duration)

        # 5. FINAL RENDER
        print("Assembly: Merging Multi-Track Video...")
        video_track = concatenate_videoclips(final_clips, method="compose")
        
        # Mix Voice + Music
        comp_audio = CompositeAudioClip([voice_audio, bg_music])
        video_with_audio = set_audio(video_track, comp_audio)
        
        video_with_audio.write_videofile("final_shorts.mp4", fps=24, codec="libx264", audio_codec="aac")
        print("--- MISSION SUCCESS ---")

    except Exception as e:
        print(f"!!! CRITICAL ERROR: {str(e)}")
        raise e

if __name__ == "__main__":
    asyncio.run(generate_world_class_video())
