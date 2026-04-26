# VERSION 3.4 - PRECISION CROP & HIGH-RETENTION PROMPTING
import os, requests, feedparser, asyncio, edge_tts, json, re
from groq import Groq

try:
    from moviepy import VideoFileClip, AudioFileClip, concatenate_videoclips, CompositeAudioClip
    V2 = True
except ImportError:
    from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips, CompositeAudioClip
    V2 = False

async def generate_world_class_video():
    try:
        print("--- AETHELGARD v3.4: PRECISION EDITION ---")
        client = Groq(api_key=os.environ.get('GROQ_API_KEY'))

        # 1. BRAIN: High-Retention Hook Scripting
        print("Brain: Generating Narrative...")
        prompt = """
        Act as a viral YouTube Shorts creator. Topic: 'Future Technology'.
        Write a 20-second script that starts with a 'Negative Hook' (e.g., 'Stop waiting for the future, it's already here').
        Return ONLY a JSON object:
        {
            "voiceover": "Script text without timestamps or stage directions",
            "keywords": ["5 specific search terms for visual clips"]
        }
        """
        chat = client.chat.completions.create(
            model="llama-3.1-8b-instant", 
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        data = json.loads(chat.choices[0].message.content)
        script_text = data.get("voiceover", "")
        keywords = data.get("keywords", [])
        print(f"Script: {script_text}\nKeywords: {keywords}")

        # 2. VOICE: Synthesis
        await edge_tts.Communicate(script_text, "en-US-AndrewNeural").save("voice.mp3")
        voice_audio = AudioFileClip("voice.mp3")
        total_duration = voice_audio.duration

        # 3. VISUALS: Precision Crop Logic
        print("Visuals: Building Vertical Timeline...")
        pexels_key = os.environ.get('PEXELS_API_KEY')
        final_clips = []
        clip_target_dur = total_duration / len(keywords)

        for i, kw in enumerate(keywords):
            search_url = f"https://api.pexels.com/videos/search?query={kw}&per_page=1&orientation=portrait"
            r = requests.get(search_url, headers={"Authorization": pexels_key}).json()
            video_list = r.get('videos', [])
            
            if not video_list:
                r = requests.get("https://api.pexels.com/videos/search?query=technology&per_page=1&orientation=portrait", 
                                 headers={"Authorization": pexels_key}).json()
                video_list = r.get('videos', [])

            v_url = video_list[0]['video_files'][0]['link']
            v_path = f"temp_v_{i}.mp4"
            with open(v_path, 'wb') as f: f.write(requests.get(v_url).content)
            
            clip = VideoFileClip(v_path)
            
            # Step A: Resize height to 1920
            clip = clip.resized(height=1920) if V2 else clip.resize(height=1920)
            
            # Step B: Manual Center Crop (1080x1920)
            # We calculate the center based on the new width after resizing
            current_w = clip.w
            x1 = (current_w - 1080) / 2
            x2 = x1 + 1080
            
            if V2:
                clip = clip.cropped(x1=x1, y1=0, x2=x2, y2=1920)
            else:
                clip = clip.crop(x1=x1, y1=0, x2=x2, y2=1920)
            
            seg_dur = min(clip.duration, clip_target_dur)
            final_clips.append(clip.subclipped(0, seg_dur) if V2 else clip.subclip(0, seg_dur))

        # 4. AUDIO: Layering Music
        music_url = "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3"
        with open("bg_music.mp3", "wb") as f: f.write(requests.get(music_url).content)
        bg_music = AudioFileClip("bg_music.mp3")
        bg_music = bg_music.with_volume_scaled(0.12) if V2 else bg_music.volumex(0.12)
        bg_music = bg_music.with_duration(total_duration) if hasattr(bg_music, 'with_duration') else bg_music.set_duration(total_duration)

        # 5. ASSEMBLY
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
