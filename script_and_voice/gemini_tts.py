#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gemini TTS Generator Module
Handles text-to-speech generation using Google Gemini API via proxy.
"""

import logging
import json
import requests
from pathlib import Path

class GeminiTTS:
    """
    Handles text-to-speech generation using Google Gemini API.
    Generates audio files with metadata for synchronization.
    """

    def __init__(self, config):
        """
        Initialize Gemini TTS generator with configuration.
        
        Args:
            config (dict): Configuration loaded from config.yml
        """
        self.config = config
        # Get absolute paths relative to this module's directory
        module_dir = Path(__file__).parent
        self.audio_path = module_dir / config['paths']['audio']
        self.temp_path = module_dir / config['paths']['temp']
        self.gemini_config = config['api']['gemini']
        self.audio_config = config['audio']['gemini_tts']
        
        # Create audio directory if it doesn't exist
        self.audio_path.mkdir(exist_ok=True)

    def extract_text_from_full_script_json(self, full_script_path):
        """
        Extract all paragraph text from full_script.json for audio generation.
        
        Args:
            full_script_path (str): Path to full_script.json file
            
        Returns:
            str: Combined text from all paragraphs
        """
        try:
            with open(full_script_path, 'r', encoding='utf-8') as f:
                full_script_data = json.load(f)
            
            paragraphs = []
            
            # Extract paragraphs from all micro_sections
            for section in full_script_data.get('sections', []):
                for micro_section in section.get('micro_sections', []):
                    paragraph = micro_section.get('paragraph', '')
                    if paragraph.strip():
                        paragraphs.append(paragraph.strip())
            
            # Join paragraphs with double newlines
            combined_text = '\n\n'.join(paragraphs)
            logging.info(f"Extracted {len(paragraphs)} paragraphs from full_script.json")
            
            return combined_text
            
        except Exception as e:
            logging.error(f"Error extracting text from full_script.json: {e}")
            raise

    def read_script(self, script_type='i3'):
        """
        Read script file (i1, i2, or i3).
        
        Args:
            script_type (str): Type of script to read ('i1', 'i2', or 'i3')
            
        Returns:
            str: Script content
        """
        script_path = self.temp_path / f"{script_type}.txt"
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            logging.error(f"Error reading {script_type}.txt: {e}")
            raise

    def split_into_bullets(self, script_content):
        """
        Split script content into bullet points based on paragraphs.
        
        Args:
            script_content (str): Full script content
            
        Returns:
            list: List of bullet point texts
        """
        # Split by double newlines (paragraphs)
        paragraphs = [p.strip() for p in script_content.split('\n\n') if p.strip()]
        
        # Each paragraph becomes a bullet point
        bullets = []
        for para in paragraphs:
            if para:
                bullets.append(para)
        
        logging.info(f"Script split into {len(bullets)} bullet points")
        return bullets

    def generate_audio(self, text, output_filename):
        """
        Generate audio file from text using Gemini TTS via proxy.
        
        Args:
            text (str): Text to convert to speech
            output_filename (str): Output audio filename
            
        Returns:
            float: Duration of generated audio in seconds
        """
        import base64
        import subprocess
        import wave
        
        try:
            # Prepare request payload
            payload = {
                'text': text,
                'api_key': self.gemini_config['api_key']
            }
            
            # Add voice settings if configured
            if 'voice_settings' in self.audio_config:
                settings = self.audio_config['voice_settings']
                if 'speed' in settings:
                    payload['speed'] = settings['speed']
                if 'pitch' in settings:
                    payload['pitch'] = settings['pitch']
                if 'volume_gain_db' in settings:
                    payload['volume_gain_db'] = settings['volume_gain_db']
            
            logging.info(f"Generating audio via Gemini proxy: {output_filename}")
            
            # Call proxy endpoint with longer timeout for longer texts
            response = requests.post(
                self.gemini_config['proxy_url'],
                json=payload,
                timeout=120  # Increased timeout for longer texts
            )
            
            if response.status_code == 200:
                # Parse JSON response from proxy
                result = response.json()
                
                # Extract audio data (PCM format from Gemini TTS)
                data = result['candidates'][0]['content']['parts'][0]['inlineData']['data']
                
                # Decode base64 PCM data
                pcm_data = base64.b64decode(data)
                logging.info(f"📡 PCM data decoded: {len(pcm_data)} bytes")
                
                # Save temporary WAV file (for debugging)
                wav_filename = output_filename.replace('.mp3', '.wav')
                wav_path = self.audio_path / wav_filename
                temp_wav_path = self.temp_path / f"temp_{wav_filename}"
                
                # Create WAV file with proper format
                with wave.open(str(temp_wav_path), "wb") as wf:
                    wf.setnchannels(1)  # Mono
                    wf.setsampwidth(2)  # 16-bit
                    wf.setframerate(24000)  # 24kHz (Gemini TTS standard)
                    wf.writeframes(pcm_data)
                
                logging.info(f"🎵 WAV created: {temp_wav_path.name} ({temp_wav_path.stat().st_size} bytes)")
                
                # Convert WAV to MP3 using ffmpeg
                audio_path = self.audio_path / output_filename
                
                try:
                    convert_cmd = [
                        'ffmpeg', '-y',  # Overwrite without asking
                        '-i', str(temp_wav_path),  # Input WAV
                        '-acodec', 'libmp3lame',  # MP3 codec
                        '-ab', '128k',  # 128k bitrate
                        str(audio_path)  # Output MP3
                    ]
                    
                    result = subprocess.run(convert_cmd, capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        mp3_size = audio_path.stat().st_size
                        logging.info(f"✅ MP3 converted: {output_filename} ({mp3_size} bytes)")
                        
                        # Keep WAV for debugging (as requested)
                        wav_path.write_bytes(temp_wav_path.read_bytes())
                        logging.info(f"🔍 WAV kept for debug: {wav_filename}")
                        
                        # Clean up temp file
                        temp_wav_path.unlink()
                        
                        # Calculate duration (approximate based on text length and speed)
                        words = len(text.split())
                        speed = self.audio_config.get('voice_settings', {}).get('speed', 1.0)
                        duration = (words / 150.0) * 60.0 / speed
                        
                        logging.info(f"✅ Audio generated: {output_filename} (~{duration:.2f}s)")
                        return duration
                    else:
                        logging.error(f"❌ ffmpeg conversion failed: {result.stderr}")
                        # Fallback: use WAV file
                        audio_path = wav_path
                        logging.warning(f"⚠️ Using WAV file instead: {wav_filename}")
                        
                except FileNotFoundError:
                    logging.error("❌ ffmpeg not found on system")
                    # Fallback: use WAV file
                    audio_path = wav_path
                    logging.warning(f"⚠️ Using WAV file instead: {wav_filename}")
                
                # Calculate duration (approximate based on text length and speed)
                words = len(text.split())
                speed = self.audio_config.get('voice_settings', {}).get('speed', 1.0)
                duration = (words / 150.0) * 60.0 / speed
                
                logging.info(f"✅ Audio generated: {output_filename} (~{duration:.2f}s)")
                return duration
            else:
                error_msg = f"Gemini proxy error: {response.status_code} - {response.text}"
                logging.error(error_msg)
                raise Exception(error_msg)
                
        except Exception as e:
            logging.error(f"Error generating audio for {output_filename}: {e}")
            raise

    def generate_all_audio(self, script_content):
        """
        Generate audio files for all bullet points in the script.
        
        Args:
            script_content (str): Full script content
            
        Returns:
            dict: Metadata with audio file information
        """
        logging.info("Starting Gemini TTS audio generation")
        
        # Clear audio directory before starting
        if self.audio_path.exists():
            import shutil
            shutil.rmtree(self.audio_path)
            logging.info("🧹 Audio directory cleared")
        
        # Recreate audio directory
        self.audio_path.mkdir(exist_ok=True)
        
        # Split script into bullets based on granularity
        granularity = self.audio_config.get('granularity', 'bullet')
        
        if granularity == 'bullet':
            bullets = self.split_into_bullets(script_content)
        else:
            # For other granularities, treat each paragraph as a bullet
            bullets = [p.strip() for p in script_content.split('\n\n') if p.strip()]
        
        # Generate metadata structure
        metadata = {
            "granularity": granularity,
            "total_bullets": len(bullets),
            "bullets": []
        }
        
        cumulative_time = 0.0
        
        # Generate audio for each bullet
        for i, bullet_text in enumerate(bullets, 1):
            output_filename = f"bullet_{i:03d}.mp3"
            
            try:
                duration = self.generate_audio(bullet_text, output_filename)
                
                bullet_metadata = {
                    "bullet_number": i,
                    "text": bullet_text,
                    "audio_file": output_filename,
                    "start_time": cumulative_time,
                    "duration": duration,
                    "end_time": cumulative_time + duration
                }
                
                metadata["bullets"].append(bullet_metadata)
                cumulative_time += duration
                
                logging.info(f"Bullet {i}/{len(bullets)}: {duration:.2f}s (total: {cumulative_time:.2f}s)")
                
            except Exception as e:
                logging.error(f"Failed to generate audio for bullet {i}: {e}")
                raise
        
        # Save metadata to JSON file
        metadata_path = self.audio_path / "audio_bullet_metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        logging.info(f"✅ All audio generated successfully. Total duration: {cumulative_time:.2f}s")
        logging.info(f"Metadata saved to: {metadata_path}")
        
        return metadata

    def process(self):
        """
        Main processing function to generate audio from script.
        
        Returns:
            dict: Metadata with audio generation results
        """
        try:
            # Read the final script (i3)
            script_content = self.read_script('i3')
            
            # Generate all audio files
            metadata = self.generate_all_audio(script_content)
            
            return {
                "success": True,
                "total_duration": metadata["bullets"][-1]["end_time"] if metadata["bullets"] else 0,
                "total_bullets": metadata["total_bullets"],
                "audio_files": [b["audio_file"] for b in metadata["bullets"]],
                "metadata_file": str(self.audio_path / "audio_bullet_metadata.json")
            }
            
        except Exception as e:
            logging.error(f"Audio generation process failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

