from pytubefix import YouTube
from moviepy.editor import *
import os
from pytube.exceptions import AgeRestrictedError
import whisper
import joblib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOADS_DIR = os.path.join(BASE_DIR, "downloads")
SPAM_MODEL_PATH = os.path.join(BASE_DIR, "spam_classifier.pkl")
VECTORIZER_PATH = os.path.join(BASE_DIR, "count_vectorizer.pkl")

def download_youtube_video(url, output_path=DOWNLOADS_DIR):
    try:
        yt = YouTube(url)
        # Get highest quality progressive video (with audio)
        video_stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
        video_path = video_stream.download(output_path=output_path)
        return video_path
        
    except AgeRestrictedError:
        print("Error: Age-restricted content. Try authenticating with cookies.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def process_video(url):
    if not os.path.exists(DOWNLOADS_DIR):
        os.makedirs(DOWNLOADS_DIR)

    video_path = download_youtube_video(url, DOWNLOADS_DIR)
    if not video_path:
        return None

    # Load video and extract audio for transcription
    video_clip = VideoFileClip(video_path)
    audio_path = os.path.splitext(video_path)[0] + ".mp3"
    video_clip.audio.write_audiofile(audio_path)

    # Transcribe audio
    model = whisper.load_model("base")
    result = model.transcribe(audio_path, word_timestamps=True)
    
    # Load spam classification model
    spam_model = joblib.load(SPAM_MODEL_PATH)
    cv = joblib.load(VECTORIZER_PATH)
    
    # Process video segments
    valid_clips = []
    for segment in result['segments']:
        text = segment['text']
        vec = cv.transform([text]).toarray()
        prediction = spam_model.predict(vec)[0]
        
        if prediction == 'NOT A SPAM COMMENT':
            start = segment['start']
            end = segment['end']
            # Create VIDEO subclip
            clip = video_clip.subclip(start, end)
            valid_clips.append(clip)
    
    if not valid_clips:
        print("No non-spam content found")
        return None

    # Concatenate and save VIDEO clips
    final_video = concatenate_videoclips(valid_clips)
    
    # Prepare output paths
    base_name = os.path.basename(video_path)
    filtered_video_path = os.path.join(DOWNLOADS_DIR, f"filtered_{base_name}")
    filtered_audio_path = os.path.join(DOWNLOADS_DIR, f"filtered_audio_{base_name.replace('.mp4', '.mp3')}")
    
    # Write output files
    final_video.write_videofile(filtered_video_path, codec="libx264", audio_codec="aac")
    
    # Fix audio export by creating proper AudioFileClip
    final_audio = final_video.audio.set_fps(video_clip.audio.fps)
    final_audio.write_audiofile(filtered_audio_path)
    
    # Cleanup resources
    video_clip.close()
    final_video.close()
    final_audio.close()
    
    return filtered_video_path, filtered_audio_path

# Wrap the example usage in a main guard
if __name__ == "__main__":
    # Example usage:
    
    url = "https://www.youtube.com/watch?v=gsEYCQgPSTc"
    print(process_video(url))


