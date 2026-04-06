import json
import queue
import tempfile
import threading
import time
import wave
import winsound
from pathlib import Path

import sounddevice as sd
from piper import PiperVoice
from vosk import Model, KaldiRecognizer


class VoiceManager:
    def __init__(
        self,
        model_path: str = "models/vosk-model-small-fr-0.22",
        sample_rate: int = 16000,
        piper_model_path: str = "fr_FR-tom-medium.onnx",
    ) -> None:
        self.sample_rate = sample_rate
        self.audio_queue: queue.Queue[bytes] = queue.Queue()

        self.is_speaking = False
        self.current_wav_path: Path | None = None
        self._speech_lock = threading.Lock()

        # ===== STT : Vosk =====
        vosk_dir = Path(model_path)
        if not vosk_dir.exists():
            raise FileNotFoundError(
                f"Le dossier du modèle Vosk est introuvable : {vosk_dir}"
            )

        self.model = Model(str(vosk_dir))
        self.recognizer = KaldiRecognizer(self.model, self.sample_rate)

        # ===== TTS : Piper =====
        self.piper_model_path = Path(piper_model_path)
        if not self.piper_model_path.exists():
            raise FileNotFoundError(
                f"Le modèle Piper est introuvable : {self.piper_model_path}"
            )

        config_path = Path(str(self.piper_model_path) + ".json")
        if not config_path.exists():
            raise FileNotFoundError(
                f"Le fichier de configuration Piper est introuvable : {config_path}"
            )

        self.tts_voice = PiperVoice.load(str(self.piper_model_path))

    def stop_speaking(self) -> None:
        with self._speech_lock:
            winsound.PlaySound(None, 0)
            self.is_speaking = False

            if self.current_wav_path is not None:
                try:
                    if self.current_wav_path.exists():
                        self.current_wav_path.unlink()
                except Exception:
                    pass
                self.current_wav_path = None

    def _cleanup_old_file(self, wav_path: Path) -> None:
        time.sleep(2.0)
        try:
            if wav_path.exists():
                wav_path.unlink()
        except Exception:
            pass

    def speak(self, text: str) -> None:
        text = text.strip()
        if not text:
            return

        # Coupe immédiatement toute lecture en cours
        self.stop_speaking()

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            wav_path = Path(tmp_file.name)

        try:
            with wave.open(str(wav_path), "wb") as wav_file:
                self.tts_voice.synthesize_wav(text, wav_file)

            with self._speech_lock:
                self.current_wav_path = wav_path
                self.is_speaking = True

            winsound.PlaySound(
                str(wav_path),
                winsound.SND_FILENAME | winsound.SND_ASYNC
            )

            cleanup_thread = threading.Thread(
                target=self._cleanup_old_file,
                args=(wav_path,),
                daemon=True
            )
            cleanup_thread.start()

        except Exception as e:
            print(f"[INFO] Erreur Piper TTS : {e}")
            self.is_speaking = False
            try:
                if wav_path.exists():
                    wav_path.unlink()
            except Exception:
                pass

    def _audio_callback(self, indata, frames, time_info, status) -> None:
        if status:
            return
        self.audio_queue.put(bytes(indata))

    def listen_forever(self):
        print("Jarvis > Système vocal actif. Je suis à l'écoute, Monsieur.")

        with sd.RawInputStream(
            samplerate=self.sample_rate,
            blocksize=8000,
            dtype="int16",
            channels=1,
            callback=self._audio_callback,
        ):
            while True:
                data = self.audio_queue.get()

                if self.recognizer.AcceptWaveform(data):
                    result = json.loads(self.recognizer.Result())
                    text = result.get("text", "").strip()

                    if text:
                        yield text