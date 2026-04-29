# core/services/tts.py

from pathlib import Path
import os
import base64
import azure.cognitiveservices.speech as speechsdk

from dotenv import load_dotenv


# -------------------------------------------------
# FORCE LOAD .env FROM PROJECT ROOT
# -------------------------------------------------

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")


# -------------------------------------------------
# ENV CONFIG (READ FROM .env)
# -------------------------------------------------

AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
AZURE_SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION")

if not AZURE_SPEECH_KEY or not AZURE_SPEECH_REGION:
    raise RuntimeError(
        "AZURE_SPEECH_KEY / AZURE_SPEECH_REGION not set in .env"
    )


_synthesizer = None


# -------------------------------------------------
# TERMINAL SPEAKER TTS
# -------------------------------------------------

def get_synthesizer():

    global _synthesizer

    if _synthesizer is None:

        speech_config = speechsdk.SpeechConfig(
            subscription=AZURE_SPEECH_KEY,
            region=AZURE_SPEECH_REGION,
        )

        # 🇮🇳 Indian English neural voice
        speech_config.speech_synthesis_voice_name = "en-IN-NeerjaNeural"

        _synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config
        )

    return _synthesizer


def speak(text: str):

    if not text:
        return

    print("🔊 Speaking...")
    synthesizer = get_synthesizer()
    synthesizer.speak_text_async(text).get()


# -------------------------------------------------
# FRONTEND SAFE (BASE64 AUDIO)
# -------------------------------------------------

def synthesize_to_base64(text: str) -> str:
    """
    Convert text → speech → base64 WAV bytes
    Used by browser frontend.
    """

    if not text:
        return ""

    speech_config = speechsdk.SpeechConfig(
        subscription=AZURE_SPEECH_KEY,
        region=AZURE_SPEECH_REGION,
    )

    speech_config.speech_synthesis_voice_name = "en-IN-NeerjaNeural"

    synthesizer = speechsdk.SpeechSynthesizer(
        speech_config=speech_config,
        audio_config=None,   # in-memory
    )

    result = synthesizer.speak_text_async(text).get()

    if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
        raise RuntimeError("Azure TTS synthesis failed")

    return base64.b64encode(result.audio_data).decode("utf-8")
