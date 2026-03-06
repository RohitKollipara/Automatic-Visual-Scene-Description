from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os

from services.speechtotext import transcribe_video
from services.scenedescribing import describe_video
from services.merge2 import merge_transcription_and_scenes

FRONTEND_FOLDER = os.path.join(os.path.dirname(__file__), "../frontend")

app = Flask(__name__, static_folder=FRONTEND_FOLDER)
CORS(app)

UPLOAD_FOLDER = "uploads"
GROQ_API_KEY  = "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" 

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route("/")
def index():
    return send_from_directory(FRONTEND_FOLDER, "index.html")

@app.route("/result.html")
def result():
    return send_from_directory(FRONTEND_FOLDER, "result.html")


@app.route("/upload", methods=["POST"])
def upload_video():
    try:
        if "video" not in request.files:
            return jsonify({"error": "No video uploaded"}), 400

        video = request.files["video"]
        video_path = os.path.join(UPLOAD_FOLDER, video.filename)
        video.save(video_path)
        print("Video saved:", video_path)

        # ── Step 1: Speech to text ──
        transcription = transcribe_video(video_path)
        segments = transcription.get("segments", [])

        formatted = []
        for seg in segments:
            formatted.append({
                "start": seg["start"],
                "end":   seg["end"],
                "text":  seg["text"]
            })
        print("Transcription done:", len(formatted), "segments")

        # ── Step 2: Scene describing ──
        print("Running scene analysis...")
        scenes = describe_video(video_path, api_key=GROQ_API_KEY, interval_seconds=4)
        print("Scene analysis done:", len(scenes) if scenes else 0, "frames")

        # ── Step 3: Merge ──
        # Match each transcript segment to its nearest scene description
        merged = []
        for seg in formatted:
            seg_start = seg["start"]
            seg_end   = seg["end"]

            if scenes:
                matching = [s for s in scenes if seg_start <= s["timestamp"] < seg_end]
                if not matching:
                    matching = [min(scenes, key=lambda s: abs(s["timestamp"] - seg_start))]
                scene = matching[0]["semantic"]
            else:
                scene = {}

            merged.append({
                "start":      seg_start,
                "end":        seg_end,
                "text":       seg["text"],
                "action":     scene.get("action",     "N/A"),
                "camera":     scene.get("camera",     "N/A"),
                "emotion":    scene.get("emotion",    "N/A"),
                "atmosphere": scene.get("atmosphere", "N/A"),
                "context":    scene.get("context",    "N/A"),
            })

        print("Merge done. Returning response.")
        return jsonify({"transcript": merged})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Processing failed", "details": str(e)}), 500


def format_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02}:{m:02}:{s:02}"


if __name__ == "__main__":
    app.run(debug=True, port=5000)