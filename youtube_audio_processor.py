import os
import yt_dlp
import subprocess
from moviepy import AudioFileClip, ImageClip, CompositeVideoClip, TextClip
import tempfile
import logging
import base64
import re

logger = logging.getLogger(__name__)

class YouTubeAudioProcessor:
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
        
    def download_and_extract_segment(self, song_title: str, artist: str, start_time: str, duration: int = 15) -> dict:
        """
        Download full song from YouTube and extract specific segment
        start_time format: "1:15" or "75" (seconds)
        """
        try:
            # Search and download full song
            search_query = f"{song_title} {artist} official audio full song"
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(self.temp_dir, '%(title)s.%(ext)s'),
                'quiet': True,
                'no_warnings': True,
                'extractaudio': True,
                'audioformat': 'mp3',
                'audioquality': '192K',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Search for the song
                search_results = ydl.extract_info(
                    f"ytsearch1:{search_query}",
                    download=False
                )
                
                if not search_results['entries']:
                    logger.warning(f"No YouTube results found for {song_title} by {artist}")
                    return None
                
                video_info = search_results['entries'][0]
                video_url = video_info['webpage_url']
                video_duration = video_info.get('duration', 0)
                
                logger.info(f"Found: {video_info['title']} ({video_duration}s)")
                
                # Download the full audio
                ydl.download([video_url])
                
                # Find downloaded file
                downloaded_files = [f for f in os.listdir(self.temp_dir) 
                                  if f.endswith('.mp3')]
                
                if not downloaded_files:
                    logger.error("No audio file downloaded")
                    return None
                
                full_audio_path = os.path.join(self.temp_dir, downloaded_files[0])
                
                # Extract the specific 15-second segment
                segment_info = self._extract_specific_segment(
                    full_audio_path, start_time, duration, song_title, artist
                )
                
                return segment_info
                
        except Exception as e:
            logger.error(f"YouTube download/extraction failed: {e}")
            return None
    
    def _extract_specific_segment(self, audio_path: str, start_time: str, duration: int, song_title: str, artist: str) -> dict:
        """Extract specific segment from full audio"""
        try:
            # Parse start time
            start_seconds = self._parse_time_to_seconds(start_time)
            
            # Load full audio
            full_audio = AudioFileClip(audio_path)
            
            # Validate start time
            if start_seconds >= full_audio.duration:
                start_seconds = max(0, full_audio.duration - duration)
                logger.warning(f"Start time adjusted to {start_seconds}s")
            
            # Extract segment
            end_time = min(start_seconds + duration, full_audio.duration)
            segment = full_audio.subclip(start_seconds, end_time)
            
            # Save segment
            segment_path = os.path.join(self.temp_dir, f"segment_{start_seconds}s.mp3")
            segment.write_audiofile(segment_path, verbose=False, logger=None)
            
            # Convert to base64 for web delivery
            with open(segment_path, 'rb') as f:
                audio_base64 = base64.b64encode(f.read()).decode('utf-8')
            
            # Cleanup
            full_audio.close()
            segment.close()
            
            return {
                'audio_base64': audio_base64,
                'segment_path': segment_path,
                'start_time': start_seconds,
                'duration': end_time - start_seconds,
                'song_title': song_title,
                'artist': artist,
                'source': 'youtube_full_download'
            }
            
        except Exception as e:
            logger.error(f"Segment extraction failed: {e}")
            return None
    
    def _parse_time_to_seconds(self, time_str: str) -> int:
        """Convert time string to seconds"""
        try:
            if ':' in time_str:
                # Format: "1:15" or "1:15-1:30"
                if '-' in time_str:
                    time_str = time_str.split('-')[0]  # Take start time
                
                parts = time_str.split(':')
                if len(parts) == 2:
                    return int(parts[0]) * 60 + int(parts[1])
                elif len(parts) == 3:
                    return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            else:
                # Format: "75" (seconds)
                return int(time_str)
        except:
            logger.warning(f"Could not parse time: {time_str}, using 30s default")
            return 30
    
    def create_video_composition(self, image_base64: str, audio_segment_info: dict, output_path: str) -> str:
        """Create video composition with image and audio segment"""
        try:
            # Decode image
            image_data = base64.b64decode(image_base64)
            image_path = os.path.join(self.temp_dir, 'image.jpg')
            with open(image_path, 'wb') as f:
                f.write(image_data)
            
            # Create video composition
            audio_duration = audio_segment_info['duration']
            
            # Create image clip
            image_clip = ImageClip(image_path, duration=audio_duration)
            
            # Resize for Instagram story format (9:16)
            image_clip = image_clip.resize(height=1920)
            if image_clip.w > 1080:
                image_clip = image_clip.resize(width=1080)
            
            # Create background
            background = ImageClip(size=(1080, 1920), color=(0, 0, 0), duration=audio_duration)
            
            # Center the image
            image_clip = image_clip.set_position('center')
            
            # Add text overlays
            title_text = TextClip(
                audio_segment_info['song_title'],
                fontsize=48,
                color='white',
                font='Arial-Bold'
            ).set_position(('center', 1600)).set_duration(audio_duration)
            
            artist_text = TextClip(
                f"by {audio_segment_info['artist']}",
                fontsize=36,
                color='lightgray',
                font='Arial'
            ).set_position(('center', 1660)).set_duration(audio_duration)
            
            segment_text = TextClip(
                f"Segment: {audio_segment_info['start_time']}s - {audio_segment_info['start_time'] + audio_segment_info['duration']}s",
                fontsize=24,
                color='yellow',
                font='Arial'
            ).set_position(('center', 1720)).set_duration(audio_duration)
            
            # Composite video
            final_video = CompositeVideoClip([
                background,
                image_clip,
                title_text,
                artist_text,
                segment_text
            ])
            
            # Add audio
            audio_clip = AudioFileClip(audio_segment_info['segment_path'])
            final_video = final_video.set_audio(audio_clip)
            
            # Export video
            final_video.write_videofile(
                output_path,
                fps=24,
                codec='libx264',
                audio_codec='aac',
                verbose=False,
                logger=None
            )
            
            # Cleanup
            audio_clip.close()
            image_clip.close()
            final_video.close()
            
            return output_path
            
        except Exception as e:
            logger.error(f"Video composition creation failed: {e}")
            return None
    
    def cleanup(self):
        """Clean up temporary files"""
        try:
            import shutil
            shutil.rmtree(self.temp_dir)
        except Exception as e:
            logger.warning(f"Cleanup failed: {e}")
