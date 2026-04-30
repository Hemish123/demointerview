# # core/services/tts.py

# from pathlib import Path
# import os
# import base64
# import azure.cognitiveservices.speech as speechsdk

# from dotenv import load_dotenv


# # -------------------------------------------------
# # FORCE LOAD .env FROM PROJECT ROOT
# # -------------------------------------------------

# ROOT = Path(__file__).resolve().parents[2]
# load_dotenv(ROOT / ".env")


# # -------------------------------------------------
# # ENV CONFIG (READ FROM .env)
# # -------------------------------------------------

# AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
# AZURE_SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION")

# if not AZURE_SPEECH_KEY or not AZURE_SPEECH_REGION:
#     raise RuntimeError(
#         "AZURE_SPEECH_KEY / AZURE_SPEECH_REGION not set in .env"
#     )


# _synthesizer = None


# # -------------------------------------------------
# # TERMINAL SPEAKER TTS
# # -------------------------------------------------

# def get_synthesizer():

#     global _synthesizer

#     if _synthesizer is None:

#         speech_config = speechsdk.SpeechConfig(
#             subscription=AZURE_SPEECH_KEY,
#             region=AZURE_SPEECH_REGION,
#         )

#         # 🇮🇳 Indian English neural voice
#         speech_config.speech_synthesis_voice_name = "en-IN-NeerjaNeural"

#         _synthesizer = speechsdk.SpeechSynthesizer(
#             speech_config=speech_config
#         )

#     return _synthesizer


# def speak(text: str):

#     if not text:
#         return

#     print("🔊 Speaking...")
#     synthesizer = get_synthesizer()
#     synthesizer.speak_text_async(text).get()


# # -------------------------------------------------
# # FRONTEND SAFE (BASE64 AUDIO)
# # -------------------------------------------------

# _b64_synthesizer = None


# def _get_b64_synthesizer():
#     """Reusable synthesizer for base64 output (no audio device)."""
#     global _b64_synthesizer

#     if _b64_synthesizer is None:
#         speech_config = speechsdk.SpeechConfig(
#             subscription=AZURE_SPEECH_KEY,
#             region=AZURE_SPEECH_REGION,
#         )
#         speech_config.speech_synthesis_voice_name = "en-IN-NeerjaNeural"

#         # Increase timeouts to prevent ServiceTimeout errors
#         speech_config.set_property_by_name(
#             "SpeechSynthesis_FrameTimeoutInterval", "10000"
#         )

#         _b64_synthesizer = speechsdk.SpeechSynthesizer(
#             speech_config=speech_config,
#             audio_config=None,   # in-memory
#         )

#     return _b64_synthesizer


# def synthesize_to_base64(text: str) -> str:
#     """
#     Convert text → speech → base64 WAV bytes
#     Used by browser frontend.
#     """

#     if not text:
#         return ""

#     # Truncate very long text to prevent timeouts
#     if len(text) > 500:
#         text = text[:497] + "..."

#     for attempt in range(2):  # retry once on failure
#         try:
#             synthesizer = _get_b64_synthesizer()
#             result = synthesizer.speak_text_async(text).get()

#             if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
#                 return base64.b64encode(result.audio_data).decode("utf-8")

#             # Log the actual error details
#             cancellation = result.cancellation_details
#             print(f"⚠️ TTS failed (attempt {attempt + 1})")
#             print(f"   Reason: {result.reason}")
#             print(f"   Cancel reason: {cancellation.reason}")
#             print(f"   Error code: {cancellation.error_code}")
#             print(f"   Error details: {cancellation.error_details}")

#             if attempt == 0:
#                 # Reset synthesizer on failure so next attempt uses a fresh one
#                 global _b64_synthesizer
#                 _b64_synthesizer = None
#                 import time
#                 time.sleep(0.5)

#         except Exception as e:
#             print(f"⚠️ TTS exception (attempt {attempt + 1}): {e}")
#             _b64_synthesizer = None

#     print("⚠️ TTS failed after 2 attempts — continuing without audio")
#     return ""
















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