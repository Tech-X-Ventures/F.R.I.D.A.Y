import time
import queue
import threading
import numpy as np
import sounddevice as sd
import speech_recognition as sr
import pyttsx3
from typing import Callable, Optional
from core.config import Config

class VoiceEngine:
    def __init__(self, on_state_change: Optional[Callable[[str], None]] = None):
        """
        VoiceEngine handles asynchronous speech synthesis (TTS) 
        and microphone recording / speech recognition (STT) via sounddevice.
        """
        self.on_state_change = on_state_change
        self.tts_queue = queue.Queue()
        self.is_speaking = False
        self.is_listening = False
        self._stop_listening = False
        self._interrupt_event = threading.Event()

        # Audio recording parameters
        self.sample_rate = 16000
        self.channels = 1
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True

        # Initialize background TTS thread
        self.tts_thread = threading.Thread(target=self._tts_worker, daemon=True)
        self.tts_thread.start()

    def set_state(self, state: str):
        if self.on_state_change:
            try:
                self.on_state_change(state)
            except Exception:
                pass

    # ==========================
    # TEXT TO SPEECH (TTS)
    # ==========================
    @staticmethod
    def _clean_for_speech(text: str) -> str:
        """Strip markdown syntax, emojis, and format text for natural vocalization."""
        import re
        t = text
        # Remove code blocks
        t = re.sub(r'```[\s\S]*?```', ' Code block omitted for speech. ', t)
        t = re.sub(r'`[^`]+`', '', t)
        # Remove markdown bold/italics
        t = t.replace('**', '').replace('*', '').replace('__', '')
        # Remove markdown headers
        t = re.sub(r'#+\s*', '', t)
        # Convert bullet points to natural pauses
        t = re.sub(r'^\s*[-•*]\s+', ' ', t, flags=re.MULTILINE)
        # Replace symbols
        t = t.replace('%', ' percent')
        t = t.replace('&', ' and ')
        # Strip emojis and non-ASCII characters to avoid Windows console / SAPI encoding crashes
        t = re.sub(r'[^\x00-\x7F]+', ' ', t)
        # Clean up repeated spaces/newlines
        t = re.sub(r'\s+', ' ', t).strip()
        return t

    def _tts_worker(self):
        """Background worker consuming speech synthesis requests via native Windows SAPI."""
        try:
            import pythoncom
            pythoncom.CoInitialize()
        except Exception:
            pass

        # Primary engine: Native Windows SAPI Voice (direct, zero driver sink bugs)
        sapi_speaker = None
        try:
            import win32com.client
            sapi_speaker = win32com.client.Dispatch("SAPI.SpVoice")
        except Exception as e:
            print(f"[Native SAPI Init Notice] {e}")

        # Fallback engine: pyttsx3
        fallback_engine = None
        if not sapi_speaker:
            try:
                fallback_engine = pyttsx3.init()
            except Exception as e:
                print(f"[pyttsx3 Fallback Init Error] {e}")

        self._sapi_speaker = sapi_speaker

        while True:
            raw_text = self.tts_queue.get()
            if not raw_text:
                continue

            speech_text = self._clean_for_speech(raw_text)
            if not speech_text:
                self.tts_queue.task_done()
                continue

            self.is_speaking = True
            self.set_state("SPEAKING")

            spoken_ok = False

            # 1. Try Native Windows SAPI.SpVoice
            if self._sapi_speaker:
                try:
                    # Apply volume (0 - 100)
                    vol = int(Config.get_voice_volume() * 100)
                    self._sapi_speaker.Volume = max(0, min(100, vol))

                    # Apply rate (-10 to +10, where 0 is ~180 wpm)
                    rate_wpm = Config.get_voice_rate()
                    sapi_rate = max(-10, min(10, int((rate_wpm - 180) / 10)))
                    self._sapi_speaker.Rate = sapi_rate

                    # Apply voice selection
                    voices = self._sapi_speaker.GetVoices()
                    voice_idx = Config.get_voice_index()
                    if voices and 0 <= voice_idx < voices.Count:
                        self._sapi_speaker.Voice = voices.Item(voice_idx)

                    self._interrupt_event.clear()
                    # Speak asynchronously (1 = SVSFlagsAsync)
                    self._sapi_speaker.Speak(speech_text, 1)

                    # Monitor until finished or interrupted
                    while not self._interrupt_event.is_set():
                        if self._sapi_speaker.WaitUntilDone(35):
                            break

                    if self._interrupt_event.is_set():
                        # Purge active speech immediately (2 = SVSFPurgeBeforeSpeak)
                        self._sapi_speaker.Speak("", 2)

                    spoken_ok = True
                except Exception as e:
                    print(f"[Native SAPI Speak Error] {e}")
                    # Re-dispatch in case COM disconnected
                    try:
                        import pythoncom
                        pythoncom.CoInitialize()
                        import win32com.client
                        self._sapi_speaker = win32com.client.Dispatch("SAPI.SpVoice")
                        self._sapi_speaker.Speak(speech_text, 1)
                        while not self._interrupt_event.is_set():
                            if self._sapi_speaker.WaitUntilDone(35):
                                break
                        spoken_ok = True
                    except Exception:
                        pass

            # 2. Fallback to pyttsx3 if native SAPI was unavailable
            if not spoken_ok and fallback_engine:
                try:
                    fallback_engine.setProperty('rate', Config.get_voice_rate())
                    fallback_engine.setProperty('volume', Config.get_voice_volume())
                    fallback_engine.say(speech_text)
                    fallback_engine.runAndWait()
                    spoken_ok = True
                except Exception as e:
                    print(f"[Fallback TTS Error] {e}")

            self.is_speaking = False
            self.set_state("IDLE")
            self.tts_queue.task_done()

    def stop_speech(self):
        """Immediately cancel current vocalization and clear pending queue (thread-safe, non-blocking)."""
        # 1. Clear queue
        while not self.tts_queue.empty():
            try:
                self.tts_queue.get_nowait()
                self.tts_queue.task_done()
            except Exception:
                break

        # 2. Signal worker thread to interrupt SAPI immediately in its own apartment
        self._interrupt_event.set()

        self.is_speaking = False
        self.set_state("IDLE")

    def speak(self, text: str):
        """Enqueue text for speech synthesis."""
        clean_text = text.strip()
        if clean_text:
            self.tts_queue.put(clean_text)

    # ==========================
    # SPEECH TO TEXT (STT)
    # ==========================
    def record_and_transcribe(self, 
                              max_seconds: float = 6.0, 
                              on_audio_level: Optional[Callable[[float], None]] = None) -> str:
        """
        Record audio from microphone using sounddevice and transcribe with Google Speech Recognition.
        Returns recognized string or empty string on failure/silence.
        """
        if self.is_listening:
            return ""

        self.is_listening = True
        self._stop_listening = False
        self.set_state("LISTENING")

        frames = []
        chunk_size = 1024
        silence_threshold = 120  # RMS threshold
        silent_chunks = 0
        max_silent_chunks = int((self.sample_rate / chunk_size) * 1.5)  # 1.5s silence triggers stop
        has_spoken = False

        try:
            with sd.InputStream(samplerate=self.sample_rate, channels=self.channels, dtype='int16') as stream:
                total_chunks = int((self.sample_rate * max_seconds) / chunk_size)

                for _ in range(total_chunks):
                    if self._stop_listening:
                        break

                    data, _ = stream.read(chunk_size)
                    frames.append(data)

                    # Compute approximate RMS level for visualization
                    rms = np.sqrt(np.mean(data.astype(np.float32)**2))
                    if on_audio_level:
                        normalized = min(1.0, float(rms) / 2500.0)
                        on_audio_level(normalized)

                    if rms > silence_threshold:
                        has_spoken = True
                        silent_chunks = 0
                    else:
                        if has_spoken:
                            silent_chunks += 1
                            if silent_chunks > max_silent_chunks:
                                break

        except Exception as e:
            print(f"[Microphone Error] {e}")
            self.is_listening = False
            self.set_state("IDLE")
            return ""

        self.is_listening = False
        self.set_state("ANALYZING")

        if not frames or not has_spoken:
            self.set_state("IDLE")
            return ""

        # Concatenate audio frames
        audio_array = np.concatenate(frames, axis=0)
        raw_bytes = audio_array.tobytes()

        # Convert to SpeechRecognition AudioData
        audio_data = sr.AudioData(raw_bytes, sample_rate=self.sample_rate, sample_width=2)

        try:
            transcript = self.recognizer.recognize_google(audio_data)
            self.set_state("IDLE")
            return transcript.strip()
        except sr.UnknownValueError:
            self.set_state("IDLE")
            return ""
        except sr.RequestError as e:
            print(f"[SpeechRecognition API Error] {e}")
            self.set_state("IDLE")
            return ""

    def stop_listening(self):
        """Signal recording loop to terminate immediately."""
        self._stop_listening = True
