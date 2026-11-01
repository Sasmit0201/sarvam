# ⚖️ Panchayat AI — The Live AI Mediator

> *"A neutral voice before the argument escalates"*

Panchayat AI is a hackathon prototype of an AI-powered village-elder mediator designed for two people in a dispute speaking different languages (e.g., Hindi and English). Built entirely on **Sarvam AI** foundational models, it facilitates live bilingual conversations, extracts core underlying interests beneath rigid positions, maps out a shared **Common Ground Board**, and speaks a fair compromise in each person's language.

---

## 🏛️ Sarvam AI Architecture

- **Speech-to-Text (STT)**: `Saaras:v3` transcribes colloquial and code-mixed speech (e.g., Hinglish) from audio recordings.
- **Translation**: `Mayura:v1` bidirectionally translates each speaker's statement into the listener's native language.
- **Elder Reasoning (LLM)**: `sarvam-105b-conversations` deliberates neutrally, separates surface positions from underlying interests, flags apparent conflicts vs real deadlocks, and synthesizes an actionable compromise.
- **Text-to-Speech (TTS)**: `Bulbul:v3` with elder voice persona (`ratan`) speaks the compromise aloud in both parties' languages.

---

## 🚀 Setup & Installation

### 1. Requirements
- Python 3.10+
- A valid Sarvam AI API Key from [Sarvam Dashboard](https://dashboard.sarvam.ai)

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Variables
Create a `.env` file in the project root:
```env
SARVAM_API_KEY=your_sarvam_api_key_here
```

### 4. Run the Application
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## ⏱️ 60-Second Hackathon Demo Script

1. **The Hook (10s)**:
   > *"Disputes escalate when people talk past each other in anger and across languages. In India, local Panchayats resolve issues by listening to underlying interests rather than legal arguments. Panchayat AI brings this village elder wisdom to a live bilingual screen."*

2. **The Incident (15s)**:
   - Click **"📂 Load Sample Landlord/Tenant Dispute"** in the sidebar (or record live turns via mic / form).
   - Show Turn 1: Tenant A speaking in **Hindi** demanding their ₹50,000 security deposit back.
   - Show Turn 2: Landlord B speaking in **English** deducting ₹18,000 for scratched walls and sink leaks.
   - Point to the **Shared Bilingual Log**: each sees the counterpart's argument translated into their own language.

3. **The Common Ground Board (20s)**:
   - Highlight the 3 cards:
     - 🟩 **Agreed**: Both accept the tenancy is over and a deposit exists.
     - 🟥 **Truly In Conflict**: Disagreement over who caused the damage and actual repair cost.
     - 🟨 **Only Looks Like Conflict**: Both want fair compensation and closure; the conflict is over *verification*, not malice.
   - Highlight **Underlying Interests**: A needs relocation funds; B needs to avoid uncompensated repair bills.

4. **The Resolution & Elder Voice (15s)**:
   - Scroll to **Elder's Compromise**: ₹6,000 plumber repair deducted upon receipt, ₹12,000 painting split 50-50, ₹38,000 returned immediately.
   - Click **Play Audio** for Person A (spoke in Hindi by *ratan*) and Person B (in English).
   - Point out the footer: *"AI-suggested compromise. Not legal advice. You decide."*

---

## 🛡️ Resilience & Safety
- **Demo Fallback Mode**: Toggle in the sidebar guarantees an offline presentation will never crash if the network or API is unavailable.
- **Timeouts & Retries**: All API calls use 25s timeouts and transient error retries.
- **Safe State**: Audio recordings are deduplicated via MD5 hash to prevent rerun loops.
