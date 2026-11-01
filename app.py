import os
import json
import base64
import hashlib
import html
import streamlit as st
from dotenv import load_dotenv
from sarvamai import SarvamAI
from sarvamai.core.request_options import RequestOptions

# Load environment variables
load_dotenv()

# App title and configuration
st.set_page_config(
    page_title="Panchayat AI — Neutral Dispute Mediator",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for Panchayat AI
st.markdown("""
<style>
    .main-title {
        font-size: 2.3rem;
        font-weight: 700;
        color: #1a237e;
        margin-bottom: 0.2rem;
    }
    .tagline {
        font-size: 1.15rem;
        color: #455a64;
        margin-bottom: 1.2rem;
        font-style: italic;
    }
    .card {
        padding: 1.2rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        border-left: 6px solid #ccc;
        background-color: #fcfcfc;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }
    .card-agreed {
        background-color: #f1f8e9;
        border-left: 6px solid #4caf50;
    }
    .card-disputed {
        background-color: #ffebee;
        border-left: 6px solid #e53935;
    }
    .card-apparent {
        background-color: #fff8e1;
        border-left: 6px solid #ffa000;
    }
    .card-interest {
        background-color: #e8eaf6;
        border-left: 6px solid #3f51b5;
    }
    .card-proposal {
        background-color: #f3e5f5;
        border-left: 6px solid #8e24aa;
    }
    .speaker-pill-a {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 16px;
        background-color: #e3f2fd;
        color: #0d47a1;
        font-weight: 600;
        font-size: 0.85rem;
        margin-bottom: 6px;
    }
    .speaker-pill-b {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 16px;
        background-color: #fbe9e7;
        color: #bf360c;
        font-weight: 600;
        font-size: 0.85rem;
        margin-bottom: 6px;
    }
    .sample-badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 10px;
        background-color: #fff3e0;
        color: #e65100;
        font-size: 0.75rem;
        font-weight: bold;
        border: 1px solid #ffe0b2;
        margin-left: 6px;
    }
    .footer-note {
        text-align: center;
        margin-top: 2.5rem;
        padding-top: 1rem;
        border-top: 1px solid #e0e0e0;
        color: #78909c;
        font-size: 0.9rem;
    }
    .card-list {
        margin: 0.5rem 0 0 1.2rem;
        padding: 0;
    }
    .card-list li {
        margin-bottom: 0.35rem;
        color: #263238;
    }
</style>
""", unsafe_allow_html=True)

# Language options supported by Sarvam AI (Mayura:v1 / Bulbul:v3)
LANGUAGE_OPTIONS = {
    "Hindi (हिन्दी)": "hi-IN",
    "English": "en-IN",
    "Bengali (বাংলা)": "bn-IN",
    "Gujarati (ગુજરાતી)": "gu-IN",
    "Kannada (ಕನ್ನಡ)": "kn-IN",
    "Malayalam (മലയാളം)": "ml-IN",
    "Marathi (मराठी)": "mr-IN",
    "Odia (ଓଡ଼ିଆ)": "od-IN",
    "Punjabi (ਪੰਜਾਬੀ)": "pa-IN",
    "Tamil (தமிழ்)": "ta-IN",
    "Telugu (తెలుగు)": "te-IN"
}

# Pre-baked sample dispute data for offline/demo resilience
SAMPLE_DISPUTE_CONTEXT = "Apartment security deposit return after lease termination"

SAMPLE_TURNS = [
    {
        "speaker": "Person A (Tenant)",
        "original": "मैंने फ्लैट पूरा साफ करके छोड़ा था। मुझे मेरा पूरा 50,000 रुपये का सिक्योरिटी डिपॉजिट वापस चाहिए।",
        "lang_code": "hi-IN",
        "translated": "I had left the flat completely clean. I want my entire security deposit of 50,000 rupees back.",
        "target_lang": "en-IN",
        "is_fallback": True
    },
    {
        "speaker": "Person B (Landlord)",
        "original": "The living room walls have deep scratches and the kitchen sink pipe is broken. I spent 18,000 on repairs, so I can only return 32,000.",
        "lang_code": "en-IN",
        "translated": "लिविंग रूम की दीवारों पर गहरे खरोंच हैं और किचन सिंक का पाइप टूटा हुआ है। मैंने मरम्मत पर 18,000 रुपये खर्च किए हैं, इसलिए मैं केवल 32,000 ही लौटा सकता हूँ।",
        "target_lang": "hi-IN",
        "is_fallback": True
    }
]

SAMPLE_MEDIATION_RESULT = {
    "dispute_summary": "Tenant A seeks the full ₹50,000 security deposit return believing the flat was left clean, while Landlord B deducted ₹18,000 for repair of wall scratches and damaged sink plumbing.",
    "agreed": [
        "Tenant A has officially vacated the apartment and is entitled to the deposit return.",
        "The total original security deposit amount is ₹50,000."
    ],
    "disputed": [
        "Whether wall repainting constitutes routine tenant wear-and-tear or tenant-caused damage.",
        "The exact cost and contractor verification for the ₹18,000 deduction."
    ],
    "apparent_conflicts": [
        "Both parties agree that legitimate repair costs should be covered, but differ on verification of actual receipts.",
        "A desires immediate financial closure, while B seeks reassurance against out-of-pocket repair burdens."
    ],
    "interests_A": [
        "Prompt financial return of funds needed for their new home deposit.",
        "Validation that they treated the rented home with dignity and diligence."
    ],
    "interests_B": [
        "Ensuring the apartment is restored to rentable condition without personal loss.",
        "Fairness and transparent coverage of actual repair out-of-pocket expenses."
    ],
    "proposal": {
        "text_en": "In the spirit of village harmony, both parties seek fairness and respect. We propose that Landlord B presents the actual verified receipt for the urgent sink repair (₹6,000) to be deducted, while the aesthetic wall repainting (₹12,000) is split evenly at ₹6,000 each. Landlord B immediately refunds ₹38,000 to Tenant A.",
        "steps": [
            "Landlord B shares verified plumber receipts for ₹6,000 within 24 hours.",
            "Tenant A and Landlord B agree to share the ₹12,000 painting expense 50-50 (₹6,000 each).",
            "Landlord B transfers ₹38,000 directly to Tenant A's bank account within 2 business days.",
            "Both parties sign a full and final lease clearance receipt with handshake and mutual goodwill."
        ]
    },
    "tone_check": "neutral"
}

# Initialize session state variables
if "conversation" not in st.session_state:
    st.session_state.conversation = []
if "mediation_result" not in st.session_state:
    st.session_state.mediation_result = None
if "proposal_audio_a" not in st.session_state:
    st.session_state.proposal_audio_a = None
if "proposal_audio_b" not in st.session_state:
    st.session_state.proposal_audio_b = None
if "proposal_text_a" not in st.session_state:
    st.session_state.proposal_text_a = ""
if "proposal_text_b" not in st.session_state:
    st.session_state.proposal_text_b = ""
if "dispute_context" not in st.session_state:
    st.session_state.dispute_context = ""
if "last_processed_audio_a" not in st.session_state:
    st.session_state.last_processed_audio_a = None
if "last_processed_audio_b" not in st.session_state:
    st.session_state.last_processed_audio_b = None
if "api_error_banner" not in st.session_state:
    st.session_state.api_error_banner = None

# Sidebar Controls
st.sidebar.title("🌿 Panchayat AI Controls")

lang_names = list(LANGUAGE_OPTIONS.keys())
default_a_idx = 0  # Hindi
default_b_idx = 1  # English

lang_a_label = st.sidebar.selectbox("Person A Language", lang_names, index=default_a_idx)
lang_b_label = st.sidebar.selectbox("Person B Language", lang_names, index=default_b_idx)

lang_code_a = LANGUAGE_OPTIONS[lang_a_label]
lang_code_b = LANGUAGE_OPTIONS[lang_b_label]

dispute_context_input = st.sidebar.text_area(
    "What is the dispute about? (Optional)",
    value=st.session_state.dispute_context,
    placeholder="e.g. Deposit return after moving out, boundary dispute, unpaid invoice",
    help="Gives the mediator helpful context before hearing the parties."
)
st.session_state.dispute_context = dispute_context_input

st.sidebar.markdown("---")
st.sidebar.subheader("Resilience & Testing")

demo_fallback = st.sidebar.toggle(
    "Demo Fallback Mode",
    value=False,
    help="When enabled, bypasses live API calls and uses pre-baked sample data for guaranteed demo reliability."
)

if st.sidebar.button("📂 Load Sample Landlord/Tenant Dispute", use_container_width=True):
    st.session_state.conversation = list(SAMPLE_TURNS)
    st.session_state.dispute_context = SAMPLE_DISPUTE_CONTEXT
    st.session_state.mediation_result = dict(SAMPLE_MEDIATION_RESULT)
    st.session_state.proposal_text_a = "दोनों पक्षों के हित में, हम प्रस्ताव करते हैं कि मकान मालिक सिंक की मरम्मत (₹6,000) घटाए और पेंटिंग का खर्च 50-50 बांटे। मकान मालिक ₹38,000 तुरंत किरायेदार को लौटाए।"
    st.session_state.proposal_text_b = SAMPLE_MEDIATION_RESULT["proposal"]["text_en"]
    st.session_state.proposal_audio_a = None
    st.session_state.proposal_audio_b = None
    st.session_state.api_error_banner = None
    st.sidebar.success("Sample dispute loaded!")
    st.rerun()

if st.sidebar.button("🔄 Reset Conversation", use_container_width=True):
    st.session_state.conversation = []
    st.session_state.mediation_result = None
    st.session_state.proposal_audio_a = None
    st.session_state.proposal_audio_b = None
    st.session_state.proposal_text_a = ""
    st.session_state.proposal_text_b = ""
    st.session_state.last_processed_audio_a = None
    st.session_state.last_processed_audio_b = None
    st.session_state.api_error_banner = None
    st.sidebar.info("Session reset.")
    st.rerun()

# Client initialization helper with session-level caching
def get_sarvam_client():
    api_key = os.environ.get("SARVAM_API_KEY", "").strip()
    if not api_key:
        try:
            api_key = str(st.secrets.get("SARVAM_API_KEY", "")).strip()
        except Exception:
            pass
    if not api_key:
        return None
    if "sarvam_client_instance" not in st.session_state or st.session_state.get("_cached_api_key") != api_key:
        try:
            st.session_state["sarvam_client_instance"] = SarvamAI(api_subscription_key=api_key)
            st.session_state["_cached_api_key"] = api_key
        except Exception as e:
            print(f"[Sarvam API] Client initialization error: {e}")
            return None
    return st.session_state["sarvam_client_instance"]

# Reusable request options with timeout and retry
REQUEST_OPTS: RequestOptions = {"timeout_in_seconds": 25, "max_retries": 1}

# API Call Wrappers with logging, timeouts, retries, and fallback
def sarvam_stt(audio_bytes: bytes, lang_code: str, fallback_mode: bool):
    """Transcribes audio using Sarvam Saaras:v3 model."""
    print(f"[Sarvam API] STT transcribe request (lang: {lang_code}, size: {len(audio_bytes)} bytes)")
    if fallback_mode:
        print("[Sarvam API] Demo fallback mode: using sample transcript")
        sample_txt = "मैंने फ्लैट साफ करके दिया था, कृपया मेरा पूरा डिपॉजिट लौटा दीजिए।" if lang_code == "hi-IN" else "I left the apartment in clean condition, please return my full deposit."
        return sample_txt, True, None

    client = get_sarvam_client()
    if not client:
        return "", False, "Sarvam API key missing. Please set SARVAM_API_KEY in .env or enable Demo Fallback Mode."

    try:
        response = client.speech_to_text.transcribe(
            file=("audio.wav", audio_bytes, "audio/wav"),
            model="saaras:v3",
            language_code=lang_code,
            request_options=REQUEST_OPTS
        )
        transcript = (response.transcript or "").strip()
        print(f"[Sarvam API] STT success: '{transcript[:60]}...'")
        return transcript, False, None
    except Exception as e:
        err_msg = f"Speech-to-Text error: {str(e)}"
        print(f"[Sarvam API] STT failure: {err_msg}")
        return "", False, err_msg

def sarvam_translate(text: str, src_lang: str, tgt_lang: str, fallback_mode: bool):
    """Translates text between languages using Sarvam Mayura:v1 model with 1000 char safety limit."""
    text_clean = text.strip()
    if src_lang == tgt_lang or not text_clean:
        return text_clean, False, None

    # Guard Mayura:v1 1000-character limit
    if len(text_clean) > 950:
        text_clean = text_clean[:950]

    print(f"[Sarvam API] Translate request ({src_lang} -> {tgt_lang}): '{text_clean[:40]}...'")
    if fallback_mode:
        print("[Sarvam API] Demo fallback mode: using sample translation")
        return f"[Translated to {tgt_lang}]: {text_clean}", True, None

    client = get_sarvam_client()
    if not client:
        return text_clean, False, "Sarvam API key missing."

    try:
        response = client.text.translate(
            input=text_clean,
            source_language_code=src_lang,
            target_language_code=tgt_lang,
            model="mayura:v1",
            request_options=REQUEST_OPTS
        )
        translated = (response.translated_text or "").strip()
        print(f"[Sarvam API] Translate success: '{translated[:60]}...'")
        return translated, False, None
    except Exception as e:
        err_msg = f"Translation error: {str(e)}"
        print(f"[Sarvam API] Translate failure: {err_msg}")
        return text_clean, False, err_msg

def sarvam_tts(text: str, lang_code: str, speaker: str = "ratan", fallback_mode: bool = False):
    """Converts proposal text into spoken audio using Bulbul:v3 with a neutral mediator voice and 2500 char guard."""
    text_clean = text.strip()
    if not text_clean or fallback_mode:
        return None, True, None

    # Guard Bulbul:v3 2500-character limit
    if len(text_clean) > 2400:
        text_clean = text_clean[:2400]

    print(f"[Sarvam API] TTS convert request (voice: {speaker}, lang: {lang_code}, text len: {len(text_clean)})")
    client = get_sarvam_client()
    if not client:
        return None, False, "Sarvam API key missing for TTS."

    try:
        response = client.text_to_speech.convert(
            text=text_clean,
            language_code=lang_code,
            speaker=speaker,
            model="bulbul:v3",
            request_options=REQUEST_OPTS
        )
        if response.audios and len(response.audios) > 0:
            audio_bytes = base64.b64decode(response.audios[0])
            print(f"[Sarvam API] TTS success: generated {len(audio_bytes)} bytes audio")
            return audio_bytes, False, None
        return None, False, "No audio data returned from Bulbul TTS."
    except Exception as e:
        err_msg = f"TTS generation error: {str(e)}"
        print(f"[Sarvam API] TTS failure: {err_msg}")
        return None, False, err_msg

def sarvam_mediate(conversation: list, dispute_context: str, fallback_mode: bool):
    """Sends dispute conversation to Sarvam-105B and requests structured JSON mediation analysis."""
    print(f"[Sarvam API] Mediation LLM request with {len(conversation)} turns")
    if fallback_mode:
        print("[Sarvam API] Demo fallback mode: using sample mediation result")
        return SAMPLE_MEDIATION_RESULT, True, None

    client = get_sarvam_client()
    if not client:
        return None, False, "Sarvam API key missing. Please configure SARVAM_API_KEY in .env."

    # Construct conversation transcript
    transcript_lines = []
    if dispute_context:
        transcript_lines.append(f"Context of dispute: {dispute_context}\n")
    for idx, turn in enumerate(conversation, 1):
        transcript_lines.append(f"Turn {idx} - {turn['speaker']} (Language: {turn['lang_code']}): {turn['original']}")
        if turn.get('translated') and turn['translated'] != turn['original']:
            transcript_lines.append(f"  [Translation for counterpart]: {turn['translated']}")
    full_transcript = "\n".join(transcript_lines)

    system_prompt = (
        "You are a calm, fair, neutral mediator in the spirit of a trusted village elder. "
        "You are given a conversation between two people in a dispute. "
        "Rules:\n"
        "1. Do not take sides.\n"
        "2. Do not give legal advice or claim legal authority.\n"
        "3. Do not invent facts that neither person stated.\n"
        "4. Identify what each person asked for (position) and why they likely want it (underlying interest).\n"
        "5. Identify what both agree on, what truly conflicts, and what only APPEARS to conflict (issues where both parties' underlying needs can actually be satisfied together without mutual exclusion).\n"
        "6. Propose one concrete, practical compromise in plain English that addresses both sides' interests, with specific next steps.\n"
        "7. Write in plain, simple language. Return ONLY valid JSON matching the exact schema with no extra text or markdown formatting."
    )

    schema_hint = (
        "Return strictly valid JSON with exact keys:\n"
        "{\n"
        '  "dispute_summary": "one neutral sentence",\n'
        '  "agreed": ["point 1", "point 2"],\n'
        '  "disputed": ["real conflict 1", "real conflict 2"],\n'
        '  "apparent_conflicts": ["compatible underlying need 1"],\n'
        '  "interests_A": ["underlying need A"],\n'
        '  "interests_B": ["underlying need B"],\n'
        '  "proposal": {\n'
        '    "text_en": "concrete fair compromise in 2-4 sentences",\n'
        '    "steps": ["actionable step 1", "actionable step 2"]\n'
        '  },\n'
        '  "tone_check": "neutral | leans_A | leans_B"\n'
        "}"
    )

    messages = [
        {"role": "system", "content": f"{system_prompt}\n\nSchema Requirements:\n{schema_hint}"},
        {"role": "user", "content": f"Here is the dispute conversation to mediate:\n\n{full_transcript}\n\nProvide the complete JSON mediation analysis now."}
    ]

    for attempt in range(2):
        try:
            res = client.chat.completions(
                model="sarvam-105b-conversations",
                messages=messages,
                temperature=0.2,
                request_options=REQUEST_OPTS
            )
            raw_text = res.choices[0].message.content.strip()
            print(f"[Sarvam API] Mediation response received ({len(raw_text)} chars)")

            # Strip markdown code blocks
            clean_text = raw_text
            if clean_text.startswith("```"):
                lines = clean_text.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                clean_text = "\n".join(lines).strip()

            # Attempt JSON parse
            try:
                parsed = json.loads(clean_text)
            except json.JSONDecodeError:
                # Substring match between first { and last }
                start_idx = clean_text.find("{")
                end_idx = clean_text.rfind("}")
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    parsed = json.loads(clean_text[start_idx:end_idx + 1])
                else:
                    raise

            # Validate and apply defaults
            result = {
                "dispute_summary": str(parsed.get("dispute_summary", "Dispute analysis completed.")),
                "agreed": [str(x) for x in parsed.get("agreed", [])] if isinstance(parsed.get("agreed"), list) else [str(parsed.get("agreed"))],
                "disputed": [str(x) for x in parsed.get("disputed", [])] if isinstance(parsed.get("disputed"), list) else [str(parsed.get("disputed"))],
                "apparent_conflicts": [str(x) for x in parsed.get("apparent_conflicts", [])] if isinstance(parsed.get("apparent_conflicts"), list) else [str(parsed.get("apparent_conflicts"))],
                "interests_A": [str(x) for x in parsed.get("interests_A", [])] if isinstance(parsed.get("interests_A"), list) else [str(parsed.get("interests_A"))],
                "interests_B": [str(x) for x in parsed.get("interests_B", [])] if isinstance(parsed.get("interests_B"), list) else [str(parsed.get("interests_B"))],
                "proposal": {
                    "text_en": str(parsed.get("proposal", {}).get("text_en", "A balanced compromise is recommended.")) if isinstance(parsed.get("proposal"), dict) else str(parsed.get("proposal")),
                    "steps": [str(s) for s in parsed.get("proposal", {}).get("steps", [])] if isinstance(parsed.get("proposal"), dict) and isinstance(parsed.get("proposal", {}).get("steps"), list) else []
                },
                "tone_check": str(parsed.get("tone_check", "neutral"))
            }
            return result, False, None
        except Exception as e:
            print(f"[Sarvam API] Mediation attempt {attempt + 1} failed: {e}")
            if attempt == 0:
                messages.append({"role": "user", "content": "Your previous response could not be parsed as valid JSON. Return ONLY the raw JSON object adhering to the schema."})
            else:
                return None, False, f"Mediation LLM parse error: {str(e)}"

def process_turn(speaker_label: str, text: str, src_lang: str, tgt_lang: str):
    """Handles appending a turn, translating it, and updating the state."""
    text_clean = text.strip()
    if not text_clean:
        st.warning("Statement was empty. Please speak or type your argument.")
        return

    with st.spinner(f"🌐 Translating {speaker_label}'s words with Mayura..."):
        translated, is_fallback, err = sarvam_translate(text_clean, src_lang, tgt_lang, demo_fallback)
        if err:
            st.session_state.api_error_banner = err

        st.session_state.conversation.append({
            "speaker": speaker_label,
            "original": text_clean,
            "lang_code": src_lang,
            "translated": translated,
            "target_lang": tgt_lang,
            "is_fallback": is_fallback
        })

    # Automatically mediate once at least 2 turns have been exchanged
    if len(st.session_state.conversation) >= 2:
        trigger_mediation()

def trigger_mediation():
    """Runs the mediation LLM, translates the proposal for both speakers, and generates Bulbul audio with step-by-step spinners."""
    if not st.session_state.conversation:
        st.info("No conversation turns to mediate yet.")
        return

    st.session_state.api_error_banner = None

    with st.spinner("🌾 Step 1/3: Village Elder is deliberating common ground with Sarvam-105B..."):
        med_result, is_fallback, err = sarvam_mediate(
            st.session_state.conversation,
            st.session_state.dispute_context,
            demo_fallback
        )
        if err:
            st.session_state.api_error_banner = err
            return

        st.session_state.mediation_result = med_result

    proposal_en = med_result.get("proposal", {}).get("text_en", "")

    with st.spinner("🌐 Step 2/3: Translating elder compromise for each speaker with Mayura..."):
        # Translate proposal into Person A's language
        if lang_code_a != "en-IN":
            text_a, _, _ = sarvam_translate(proposal_en, "en-IN", lang_code_a, demo_fallback)
        else:
            text_a = proposal_en
        st.session_state.proposal_text_a = text_a

        # Translate proposal into Person B's language
        if lang_code_b != "en-IN":
            text_b, _, _ = sarvam_translate(proposal_en, "en-IN", lang_code_b, demo_fallback)
        else:
            text_b = proposal_en
        st.session_state.proposal_text_b = text_b

    with st.spinner("🔊 Step 3/3: Generating spoken elder voice with Bulbul (speaker: ratan)..."):
        audio_a, _, _ = sarvam_tts(text_a, lang_code_a, speaker="ratan", fallback_mode=demo_fallback)
        st.session_state.proposal_audio_a = audio_a

        audio_b, _, _ = sarvam_tts(text_b, lang_code_b, speaker="ratan", fallback_mode=demo_fallback)
        st.session_state.proposal_audio_b = audio_b


# Main Screen UI
st.markdown('<div class="main-title">⚖️ Panchayat AI</div>', unsafe_allow_html=True)
st.markdown('<div class="tagline">"A neutral voice before the argument escalates" — Village Elder Mediation</div>', unsafe_allow_html=True)

# Status notification if API key is missing or fallback mode is active
has_key = bool(os.environ.get("SARVAM_API_KEY", "").strip())
if not has_key:
    try:
        has_key = bool(st.secrets.get("SARVAM_API_KEY", "").strip())
    except Exception:
        pass

if not has_key and not demo_fallback:
    st.warning("⚠️ `SARVAM_API_KEY` is not set in `.env` or Streamlit Secrets. Please configure your key or enable **Demo Fallback Mode** in the sidebar.")

if demo_fallback:
    st.info("ℹ️ **Demo Fallback Mode is ON**: Using pre-baked sample responses for guaranteed demo reliability without API calls.")

if st.session_state.api_error_banner:
    st.error(f"⚠️ {st.session_state.api_error_banner}")

# Speaker Inputs Section (Two Columns)
st.subheader("🗣️ Live Speaker Turns")
col_a, col_b = st.columns(2)

with col_a:
    st.markdown(f'<div class="speaker-pill-a">Person A ({lang_a_label})</div>', unsafe_allow_html=True)
    audio_a = st.audio_input("Record Statement (Person A)", key="audio_input_a")
    if audio_a is not None:
        audio_bytes_a = audio_a.getvalue()
        if len(audio_bytes_a) > 2000:
            audio_hash_a = hashlib.md5(audio_bytes_a).hexdigest()
            if audio_hash_a != st.session_state.last_processed_audio_a:
                st.session_state.last_processed_audio_a = audio_hash_a
                with st.spinner("🎙️ Transcribing Person A's speech with Saaras..."):
                    transcript_a, is_fb, err_stt = sarvam_stt(audio_bytes_a, lang_code_a, demo_fallback)
                    if transcript_a:
                        process_turn("Person A", transcript_a, lang_code_a, lang_code_b)
                        st.rerun()
                    elif err_stt:
                        st.session_state.api_error_banner = err_stt
                        st.rerun()

    # Form text turn input (clears cleanly on submit)
    with st.form("form_turn_a", clear_on_submit=True):
        text_input_a = st.text_input("Or type statement for Person A:", placeholder="State your side of the dispute...")
        btn_a = st.form_submit_button("Submit Statement (A)", use_container_width=True)
        if btn_a and text_input_a.strip():
            process_turn("Person A", text_input_a.strip(), lang_code_a, lang_code_b)
            st.rerun()

with col_b:
    st.markdown(f'<div class="speaker-pill-b">Person B ({lang_b_label})</div>', unsafe_allow_html=True)
    audio_b = st.audio_input("Record Statement (Person B)", key="audio_input_b")
    if audio_b is not None:
        audio_bytes_b = audio_b.getvalue()
        if len(audio_bytes_b) > 2000:
            audio_hash_b = hashlib.md5(audio_bytes_b).hexdigest()
            if audio_hash_b != st.session_state.last_processed_audio_b:
                st.session_state.last_processed_audio_b = audio_hash_b
                with st.spinner("🎙️ Transcribing Person B's speech with Saaras..."):
                    transcript_b, is_fb, err_stt = sarvam_stt(audio_bytes_b, lang_code_b, demo_fallback)
                    if transcript_b:
                        process_turn("Person B", transcript_b, lang_code_b, lang_code_a)
                        st.rerun()
                    elif err_stt:
                        st.session_state.api_error_banner = err_stt
                        st.rerun()

    # Form text turn input (clears cleanly on submit)
    with st.form("form_turn_b", clear_on_submit=True):
        text_input_b = st.text_input("Or type statement for Person B:", placeholder="State your side of the dispute...")
        btn_b = st.form_submit_button("Submit Statement (B)", use_container_width=True)
        if btn_b and text_input_b.strip():
            process_turn("Person B", text_input_b.strip(), lang_code_b, lang_code_a)
            st.rerun()

st.markdown("---")

# Shared Bilingual Conversation Log
st.subheader("📜 Shared Bilingual Conversation Log")
if not st.session_state.conversation:
    st.info("No statements recorded yet. Speak into the microphone above or click **'Load Sample Landlord/Tenant Dispute'** in the sidebar.")
else:
    for idx, turn in enumerate(st.session_state.conversation, 1):
        pill_class = "speaker-pill-a" if "Person A" in turn["speaker"] else "speaker-pill-b"
        fallback_badge = '<span class="sample-badge">sample data</span>' if turn.get("is_fallback") else ""
        escaped_orig = html.escape(turn['original'])
        escaped_trans = html.escape(turn.get('translated', ''))
        
        st.markdown(
            f"""
            <div class="card">
                <div><span class="{pill_class}">Turn {idx}: {html.escape(turn['speaker'])}</span> {fallback_badge}</div>
                <div style="font-size: 1.05rem; margin-top: 4px;"><strong>Original:</strong> {escaped_orig}</div>
                <div style="font-size: 0.95rem; color: #455a64; margin-top: 4px;"><em>Translated for counterpart:</em> {escaped_trans}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Manual Re-mediate button
    if st.button("🌾 Mediate Now (Deliberate Compromise)", use_container_width=True, type="primary"):
        trigger_mediation()
        st.rerun()

# Common Ground Board
if st.session_state.mediation_result:
    med = st.session_state.mediation_result
    st.markdown("---")
    st.subheader("🤝 The Common Ground Board")
    
    # Dispute summary banner
    summary = html.escape(med.get("dispute_summary", ""))
    tone = html.escape(med.get("tone_check", "neutral"))
    st.info(f"**Neutral Elder Assessment:** {summary} &nbsp;*(Tone Check: `{tone}`)*")

    # Three-column card layout with proper HTML nesting
    c1, c2, c3 = st.columns(3)

    with c1:
        agreed_items = med.get("agreed", [])
        agreed_li = "".join(f"<li>{html.escape(item)}</li>" for item in agreed_items) if agreed_items else "<li>No explicit shared points identified yet.</li>"
        st.markdown(f"""
        <div class="card card-agreed">
            <h4 style="color: #2e7d32; margin-top: 0;">✅ Agreed (Common Ground)</h4>
            <ul class="card-list">{agreed_li}</ul>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        disputed_items = med.get("disputed", [])
        disputed_li = "".join(f"<li>{html.escape(item)}</li>" for item in disputed_items) if disputed_items else "<li>No fundamental deadlocks identified.</li>"
        st.markdown(f"""
        <div class="card card-disputed">
            <h4 style="color: #c62828; margin-top: 0;">⚔️ Truly In Conflict</h4>
            <ul class="card-list">{disputed_li}</ul>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        apparent_items = med.get("apparent_conflicts", [])
        apparent_li = "".join(f"<li>{html.escape(item)}</li>" for item in apparent_items) if apparent_items else "<li>No superficial miscommunications found.</li>"
        st.markdown(f"""
        <div class="card card-apparent">
            <h4 style="color: #ef6c00; margin-top: 0;">🔍 Only Looks Like Conflict</h4>
            <ul class="card-list">{apparent_li}</ul>
        </div>
        """, unsafe_allow_html=True)

    # Underlying Interests (Positions vs Interests)
    st.subheader("💡 Underlying Interests (Beyond Positions)")
    int_a_col, int_b_col = st.columns(2)

    with int_a_col:
        interests_a = med.get("interests_A", [])
        int_a_li = "".join(f"<li>{html.escape(item)}</li>" for item in interests_a) if interests_a else "<li>No underlying needs identified.</li>"
        st.markdown(f"""
        <div class="card card-interest">
            <h4 style="color: #283593; margin-top: 0;">What Person A Really Needs</h4>
            <ul class="card-list">{int_a_li}</ul>
        </div>
        """, unsafe_allow_html=True)

    with int_b_col:
        interests_b = med.get("interests_B", [])
        int_b_li = "".join(f"<li>{html.escape(item)}</li>" for item in interests_b) if interests_b else "<li>No underlying needs identified.</li>"
        st.markdown(f"""
        <div class="card card-interest">
            <h4 style="color: #283593; margin-top: 0;">What Person B Really Needs</h4>
            <ul class="card-list">{int_b_li}</ul>
        </div>
        """, unsafe_allow_html=True)

    # Mediator's Proposal & Audio
    st.subheader("🕊️ Mediator's Practical Proposal")
    prop = med.get("proposal", {})
    prop_en = html.escape(prop.get("text_en", ""))
    steps = prop.get("steps", [])

    st.markdown(f"""
    <div class="card card-proposal">
        <h4 style="color: #6a1b9a; margin-top: 0;">Village Elder's Compromise</h4>
        <p style="font-size: 1.05rem; margin-bottom: 0;">{prop_en}</p>
    </div>
    """, unsafe_allow_html=True)

    if steps:
        st.markdown("**Actionable Next Steps Both Can Accept:**")
        for idx, step in enumerate(steps, 1):
            st.markdown(f"**{idx}.** {html.escape(step)}")

    # Spoken Audio Players for both languages
    st.markdown("#### 🎧 Spoken Proposal (Elder's Voice in Each Language)")
    audio_col1, audio_col2 = st.columns(2)

    with audio_col1:
        st.markdown(f"**For Person A ({lang_a_label}):**")
        if st.session_state.proposal_text_a:
            st.caption(f'"{st.session_state.proposal_text_a}"')
        if st.session_state.proposal_audio_a:
            st.audio(st.session_state.proposal_audio_a, format="audio/wav")
        else:
            if demo_fallback:
                st.info("Demo fallback mode active (audio synthesis skipped).")
            else:
                st.info("Audio ready upon mediation.")

    with audio_col2:
        st.markdown(f"**For Person B ({lang_b_label}):**")
        if st.session_state.proposal_text_b:
            st.caption(f'"{st.session_state.proposal_text_b}"')
        if st.session_state.proposal_audio_b:
            st.audio(st.session_state.proposal_audio_b, format="audio/wav")
        else:
            if demo_fallback:
                st.info("Demo fallback mode active (audio synthesis skipped).")
            else:
                st.info("Audio ready upon mediation.")

# Footer Note
st.markdown(
    '<div class="footer-note">⚖️ <em>AI-suggested compromise. Not legal advice. You decide.</em></div>',
    unsafe_allow_html=True
)
