# 🦈 Visual Context Extractor — SharkAttack

> **AI-powered video intelligence platform** that transcribes speech, analyses scenes visually, and produces rich semantic context for every moment of your video.

---

## 🎯 What It Does

Visual Context Extractor is a full-stack AI pipeline that takes any MP4 video and returns:

- **Timestamped speech transcription** powered by OpenAI Whisper
- **Per-frame scene analysis** — ACTION, CAMERA, EMOTION, ATMOSPHERE, CONTEXT — powered by Groq + Llama-4 Scout Vision
- **Merged semantic output** combining audio and visual understanding into a unified, time-aligned dataset
- **Accuracy Score** — a quality metric based on transcript density
- **Semantic Score** — TF-IDF cosine similarity measuring how well the visual analysis matches the spoken content
- **Video generation prompt** ready to feed into Google Veo for AI video recreation

---

## 📸 Demo

| Upload Page | Processing Overlay | Results Dashboard |
|---|---|---|
| Drop any MP4 | Live step-by-step progress | Transcript + Scene Analysis |

---

## 🏗️ System Architecture

```
User uploads MP4
       │
       ▼
┌─────────────────────┐
│   Flask Backend     │  ← app.py
│   (port 5000)       │
└────────┬────────────┘
         │
    ┌────▼────┐
    │  Step 1 │  MoviePy      → Extract audio (.wav)
    │         │  noisereduce  → Denoise audio
    │         │  Whisper base → Transcribe → segments[{start, end, text}]
    └────┬────┘
         │
    ┌────▼────┐
    │  Step 2 │  OpenCV       → Extract 1 frame every 4 seconds
    │         │  base64       → Encode frames as JPEG
    │         │  Groq Vision  → Analyse each frame → semantic[{action, camera, emotion, atmosphere, context}]
    └────┬────┘
         │
    ┌────▼────┐
    │  Step 3 │  Merge by nearest timestamp
    │         │  → merged[{start, end, text, action, camera, emotion, atmosphere, context}]
    └────┬────┘
         │
    ┌────▼────┐
    │  Step 4 │  TF-IDF Cosine Similarity
    │         │  → semantic_score (0–100%)
    └────┬────┘
         │
         ▼
  JSON Response → Frontend → result.html dashboard
```

---

## 🧠 AI Models Used

| Model | Provider | Purpose |
|---|---|---|
| **Whisper (base)** | OpenAI (local) | Speech-to-text transcription with timestamps |
| **Llama-4 Scout 17B Vision** | Groq Cloud | Frame-by-frame visual scene understanding |
| **TF-IDF Vectorizer** | scikit-learn | Semantic similarity scoring |
| **Veo 2.0** *(roadmap)* | Google Gemini | AI video generation from merged prompt |

---

## 📁 Project Structure

```
visual-context-extractor/
│
├── backend/
│   ├── app.py                  # Flask server — main pipeline orchestrator
│   └── services/
│       ├── speechtotext.py     # Whisper transcription + audio denoising
│       ├── scenedescribing.py  # Groq Vision frame analysis
│       ├── merge2.py           # Timestamp-based transcript + scene merger
│       ├── semanticscore.py    # TF-IDF cosine similarity scoring
│       └── videogeneration.py  # Google Veo integration (Phase 2)
│
├── frontend/
│   ├── index.html              # Upload page with drag & drop
│   └── result.html             # Results dashboard with scene analysis panel
│
├── transcription_output/       # Auto-created at runtime
│   ├── transcription_plain.txt
│   ├── transcription_timestamped.txt
│   ├── transcription_full.json
│   ├── scene_descriptions.txt
│   ├── scene_descriptions.json
│   ├── merged_full.json
│   └── video_generation_prompt.txt
│
└── README.md
```

---

## ⚙️ Installation & Setup

### Prerequisites

- Python 3.10+
- Node.js (optional, only if regenerating PPT)
- A **Groq API key** — get one free at [console.groq.com](https://console.groq.com)
- FFmpeg installed and on PATH (required by MoviePy)

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/visual-context-extractor.git
cd visual-context-extractor
```

### 2. Install Python dependencies

```bash
pip install flask flask-cors openai-whisper moviepy opencv-python groq \
            noisereduce soundfile numpy scikit-learn
```

> **Note:** Whisper will download the `base` model (~140MB) on first run automatically.

### 3. Set your Groq API key

Open `backend/app.py` and replace the key on line 16:

```python
GROQ_API_KEY = "your_groq_api_key_here"
```

Or set it as an environment variable:

```bash
# Windows
set GROQ_API_KEY=your_groq_api_key_here

# Mac / Linux
export GROQ_API_KEY=your_groq_api_key_here
```

Then update `app.py` to read it:

```python
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "fallback_key_here")
```

### 4. Run the server

```bash
cd backend
python app.py
```

You should see:
```
* Running on http://127.0.0.1:5000
```

### 5. Open the app

Visit **http://127.0.0.1:5000** in your browser.

---

## 🚀 How to Use

1. **Open** `http://127.0.0.1:5000`
2. **Drag & drop** any `.mp4` video onto the upload zone, or click to browse
3. Click **Submit** — the processing overlay will appear showing live pipeline steps
4. Wait for processing to complete (2–5 minutes depending on video length)
5. Results page loads automatically with:
   - Accuracy Score and Semantic Score
   - Clickable transcript segments
   - Scene analysis panel (Action, Camera, Emotion, Atmosphere, Context)
   - Click any segment to seek the video to that timestamp

---

## 🔬 How It Works — Detailed Pipeline

### Step 1 — Audio Extraction & Denoising (`speechtotext.py`)

MoviePy reads the video file and extracts the raw audio track as a `.wav` file. The first 0.5 seconds of audio are used as a noise profile sample, and `noisereduce` performs spectral subtraction to clean background noise before transcription.

### Step 2 — Speech Transcription (`speechtotext.py`)

OpenAI Whisper (base model) processes the denoised audio and returns a list of segments. Each segment contains:
- `start` — timestamp in seconds
- `end` — timestamp in seconds  
- `text` — the transcribed words

Whisper runs entirely locally — no API key or internet connection required for this step.

### Step 3 — Visual Scene Analysis (`scenedescribing.py`)

OpenCV opens the video file and extracts one frame every 4 seconds (configurable). Each frame is JPEG-encoded and base64-encoded, then sent to the Groq Cloud API running **Llama-4 Scout 17B Vision**. The model analyses each frame and returns a structured JSON object:

```json
{
  "action": "Batsman playing a straight drive down the ground",
  "camera": "Wide side-on broadcast shot with full pitch visible",
  "emotion": "Confident, elegant follow-through",
  "atmosphere": "Packed stadium, roaring crowd, bright daylight",
  "context": "A textbook straight drive draws a roaring response from the crowd."
}
```

A 1-second delay between API calls prevents rate limiting.

### Step 4 — Merging (`app.py` / `merge2.py`)

Each transcript segment is matched to its nearest scene frame by timestamp. The merge logic:
1. Finds all scene frames whose timestamp falls within the segment's `[start, end]` window
2. If no frame falls within range, uses the frame with the closest timestamp (`min` by absolute difference)
3. Combines transcript text with scene semantic fields into a single unified object

### Step 5 — Semantic Scoring (`semanticscore.py`)

TF-IDF (Term Frequency–Inverse Document Frequency) converts two texts into numerical vectors:
- **Text A:** Plain transcript (all spoken words joined)
- **Text B:** All `text` + `context` fields from merged segments

Cosine similarity measures the angle between the vectors. Score close to 1.0 = same topic. Multiplied by 100 for display as a percentage.

| Score | Interpretation |
|---|---|
| 80–100% | Excellent — visual context tightly matches speech |
| 60–80% | Good — minor details differ |
| 40–60% | Moderate — general theme matches |
| 0–40% | Low — short videos with brief commentary score lower naturally |

### Step 6 — Video Generation (`videogeneration.py`)

*(Phase 2 — not yet wired to UI button)*

The merged output is formatted into a structured prompt and sent to Google Veo 2.0 via the `google-genai` SDK. The model generates a video matching the described scenes and audio.

---

## 📊 Scoring Formulas

### Accuracy Score

```
BASE = 88
SEG_BONUS  = min(segments × 0.4, 6)
DENSITY_BONUS = min((avgWordsPerSegment / 8) × 1.2, 5)
ACCURACY = BASE + SEG_BONUS + DENSITY_BONUS   (capped at 99)
```

Rewards longer, denser transcripts — a quality signal for Whisper performance.

### Semantic Score

```
TF-IDF vectorize([plain_transcript, audio+context_text])
SEMANTIC = cosine_similarity(vector_A, vector_B) × 100
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | HTML5, CSS3, Vanilla JavaScript |
| **Backend** | Python 3, Flask, flask-cors |
| **Audio** | MoviePy, noisereduce, soundfile, NumPy |
| **Transcription** | OpenAI Whisper (base, local) |
| **Vision AI** | Groq Cloud API, Llama-4 Scout 17B Vision |
| **Frame Extraction** | OpenCV (cv2) |
| **Scoring** | scikit-learn TF-IDF + Cosine Similarity |
| **Video Gen** | Google Gemini Veo 2.0 *(roadmap)* |

---

## 🗺️ Roadmap

- [x] Speech transcription with timestamps
- [x] Visual scene analysis per frame
- [x] Transcript + scene merge pipeline
- [x] Semantic similarity scoring
- [x] Live processing overlay with step tracking
- [x] Dark / light theme toggle
- [ ] Wire "Make a Video" button to Google Veo
- [ ] SRT / VTT subtitle export
- [ ] Multi-language transcription support
- [ ] Parallel Groq API calls for faster scene analysis
- [ ] Speaker diarisation (identify who is speaking)
- [ ] Real-time stream processing
- [ ] Emotion timeline visualisation
- [ ] Searchable video database with vector embeddings

---

## ⚡ Performance Notes

- **Processing time** scales with video length: ~2–5 minutes for a 2-minute video
- The bottleneck is Groq Vision API calls — one per frame, ~3–5 seconds each
- To speed up: increase `interval_seconds` in `app.py` (e.g., `8` instead of `4` halves frame count)
- Whisper `base` model runs on CPU — use `small` or `medium` for higher accuracy at the cost of speed

---

## 🐛 Known Issues & Fixes

| Issue | Cause | Fix |
|---|---|---|
| Video not showing in results | File >10MB can't fit in sessionStorage | Uses FileReader base64; works for files under ~50MB |
| Semantic score shows N/A | `video_generation_prompt.txt` not found | Score now computed in-memory, no files needed |
| Processing overlay frozen | sessionStorage quota exceeded on large files | Each storage write is independently try/catched |
| Old video showing in results | Stale sessionStorage from previous upload | All keys cleared on new file selection |

---

## 👥 Team

**SharkAttack 🦈**

Built at a hackathon with the goal of making video content searchable, understandable, and re-generatable using AI.

---

## 📄 License

MIT License — feel free to use, modify, and build on this project.

---

## 🙏 Acknowledgements

- [OpenAI Whisper](https://github.com/openai/whisper) — automatic speech recognition
- [Groq](https://groq.com) — ultra-fast LLM inference
- [Meta Llama 4](https://ai.meta.com/blog/llama-4-multimodal/) — vision language model
- [Google Veo](https://deepmind.google/technologies/veo/) — video generation model
- [scikit-learn](https://scikit-learn.org) — TF-IDF and cosine similarity
