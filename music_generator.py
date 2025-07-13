import numpy as np
import wave
import struct
import math
import io
import base64

class MusicGenerator:
    def __init__(self):
        self.sample_rate = 44100
        self.duration = 30  # 30 seconds
        
    def generate_background_music(self, mood: str, tempo: str = "medium") -> str:
        """Generate 30-second background music based on mood"""
        
        # Define musical parameters based on mood
        mood_params = {
            'happy': {'base_freq': 440, 'harmony': [554, 659], 'rhythm': 'upbeat'},
            'sad': {'base_freq': 220, 'harmony': [277, 330], 'rhythm': 'slow'},
            'energetic': {'base_freq': 523, 'harmony': [659, 784], 'rhythm': 'fast'},
            'romantic': {'base_freq': 349, 'harmony': [415, 523], 'rhythm': 'medium'},
            'mysterious': {'base_freq': 311, 'harmony': [370, 466], 'rhythm': 'slow'},
            'peaceful': {'base_freq': 261, 'harmony': [329, 392], 'rhythm': 'slow'}
        }
        
        params = mood_params.get(mood.lower(), mood_params['happy'])
        
        # Generate audio data
        audio_data = self._create_melody(params)
        
        # Convert to WAV format and encode as base64
        wav_data = self._create_wav_file(audio_data)
        return base64.b64encode(wav_data).decode('utf-8')
    
    def _create_melody(self, params: dict) -> np.ndarray:
        """Create a simple melody based on parameters"""
        samples = self.sample_rate * self.duration
        audio = np.zeros(samples)
        
        base_freq = params['base_freq']
        harmonies = params['harmony']
        
        # Create a simple chord progression
        chord_duration = self.sample_rate * 2  # 2 seconds per chord
        
        for i in range(0, samples, chord_duration):
            end_idx = min(i + chord_duration, samples)
            chord_samples = end_idx - i
            
            # Generate time array for this chord
            t = np.linspace(0, chord_samples / self.sample_rate, chord_samples)
            
            # Create chord with base frequency and harmonies
            chord = np.sin(2 * np.pi * base_freq * t)
            for harmony_freq in harmonies:
                chord += 0.3 * np.sin(2 * np.pi * harmony_freq * t)
            
            # Add envelope (fade in/out)
            envelope = np.exp(-t * 0.5) * (1 - np.exp(-t * 10))
            chord *= envelope
            
            # Add to main audio
            audio[i:end_idx] = chord
            
            # Vary the frequency for next chord
            base_freq *= 1.1 if (i // chord_duration) % 2 == 0 else 0.9
        
        # Normalize audio
        audio = audio / np.max(np.abs(audio)) * 0.7
        
        return audio
    
    def _create_wav_file(self, audio_data: np.ndarray) -> bytes:
        """Convert audio data to WAV file format"""
        # Convert to 16-bit integers
        audio_int = (audio_data * 32767).astype(np.int16)
        
        # Create WAV file in memory
        wav_buffer = io.BytesIO()
        
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 2 bytes per sample (16-bit)
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(audio_int.tobytes())
        
        wav_buffer.seek(0)
        return wav_buffer.read()

# Test function
def test_music_generator():
    """Test music generation"""
    generator = MusicGenerator()
    
    moods = ['happy', 'sad', 'energetic', 'romantic']
    
    for mood in moods:
        print(f"Generating {mood} music...")
        music_data = generator.generate_background_music(mood)
        print(f"Generated {len(music_data)} characters of base64 audio data")

if __name__ == "__main__":
    test_music_generator()
