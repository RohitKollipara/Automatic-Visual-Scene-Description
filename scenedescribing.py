import cv2
import base64
import json
import time
from pathlib import Path
from groq import Groq


def extract_frames(video_path: str, interval_seconds: int = 4) -> list[dict]:
    """Extract one frame every `interval_seconds` from the video."""
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frames = []

    frame_interval = int(fps * interval_seconds)
    frame_index = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if frame_index % frame_interval == 0:
            timestamp = round(frame_index / fps, 2)
            _, buffer = cv2.imencode(".jpg", frame)
            frames.append({
                "timestamp": timestamp,
                "bytes": buffer.tobytes()
            })

        frame_index += 1

    cap.release()
    print(f"Extracted {len(frames)} frames (every {interval_seconds}s)")
    return frames


def describe_frames(frames: list[dict], api_key: str) -> list[dict]:
    """Send each frame to Groq Vision and extract rich semantic context."""
    client = Groq(api_key=api_key)

    # Rich semantic prompt covering all 4 dimensions
    prompt = """You are a sports video analyst helping recreate a video using Gen AI.
Analyze this frame and return a JSON object with exactly these fields:

{
  "action": "What is physically happening — type of shot (drive, pull, hook, sweep), fielding action, bowling, celebration, etc.",
  "camera": "Camera angle and broadcast style — wide establishing shot, close-up, side-on, aerial, slow-motion replay, etc.",
  "emotion": "Player emotions and body language — confident, tense, celebrating, disappointed, focused, pumped up, etc.",
  "atmosphere": "Crowd energy and match intensity — roaring crowd, quiet tension, standing ovation, stadium full/empty, day/night match, etc.",
  "context": "One sentence combining all the above into a single scene description for video generation."
}

Return ONLY the JSON object, no extra text."""

    descriptions = []
    total = len(frames)

    for i, frame in enumerate(frames):
        timestamp = frame["timestamp"]
        print(f"Analyzing frame {i + 1}/{total} at {format_time(timestamp)}...")

        try:
            image_b64 = base64.b64encode(frame["bytes"]).decode("utf-8")

            response = client.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_b64}"
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ],
                max_tokens=400
            )

            raw = response.choices[0].message.content.strip()

            # Safely parse JSON response
            try:
                semantic = json.loads(raw)
            except json.JSONDecodeError:
                # If model returns non-JSON, store as plain context
                semantic = {
                    "action": "unknown",
                    "camera": "unknown",
                    "emotion": "unknown",
                    "atmosphere": "unknown",
                    "context": raw
                }

        except Exception as e:
            semantic = {
                "action": "error",
                "camera": "error",
                "emotion": "error",
                "atmosphere": "error",
                "context": f"[Error: {e}]"
            }

        # Add small delay to avoid rate limiting
        time.sleep(1)

        descriptions.append({
            "timestamp": timestamp,
            "semantic": semantic
        })

    return descriptions


def describe_video(video_file: str, api_key: str, interval_seconds: int = 4,
                   output_dir: str = "transcription_output") -> list[dict] | None:
    """
    Extract frames and generate rich semantic scene descriptions using Groq.

    Args:
        video_file (str): Path to the video file
        api_key (str): Groq API key
        interval_seconds (int): How often to sample frames (default: every 4 seconds)
        output_dir (str): Directory to save output files

    Returns:
        list[dict]: List of timestamped semantic descriptions
    """
    try:
        video_path = Path(video_file)
        if not video_path.exists():
            print(f"Error: File not found: {video_path}")
            return None

        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)

        # Step 1: Extract frames
        print("Extracting frames from video...")
        frames = extract_frames(str(video_path), interval_seconds)
        if not frames:
            print("No frames extracted.")
            return None

        # Step 2: Semantically describe each frame
        print("Sending frames to Groq for semantic analysis...")
        descriptions = describe_frames(frames, api_key)

        # Step 3: Save human-readable file
        readable_path = output / "scene_descriptions.txt"
        with readable_path.open("w", encoding="utf-8") as f:
            for d in descriptions:
                time_str = format_time(d["timestamp"])
                s = d["semantic"]
                f.write(f"[{time_str}]\n")
                f.write(f"  ACTION:     {s.get('action', 'N/A')}\n")
                f.write(f"  CAMERA:     {s.get('camera', 'N/A')}\n")
                f.write(f"  EMOTION:    {s.get('emotion', 'N/A')}\n")
                f.write(f"  ATMOSPHERE: {s.get('atmosphere', 'N/A')}\n")
                f.write(f"  CONTEXT:    {s.get('context', 'N/A')}\n\n")
        print(f"Scene descriptions saved to: {readable_path}")

        # Step 4: Save JSON for merge step
        json_path = output / "scene_descriptions.json"
        json_path.write_text(json.dumps(descriptions, indent=2), encoding="utf-8")
        print(f"Scene descriptions JSON saved to: {json_path}")

        return descriptions

    except Exception as e:
        import traceback
        traceback.print_exc()
        return None


def format_time(seconds: float) -> str:
    """Convert seconds to HH:MM:SS format."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02}:{m:02}:{s:02}"


if __name__ == "__main__":
    video_file = "D:\\Hackathon\\videos\cricket144.mp4"
    api_key = "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"
    describe_video(video_file, api_key, interval_seconds=4)
# ```

# **The `scene_descriptions.txt` will now look like:**
# ```
# [00:00:00]
#   ACTION:     Batsman playing a straight drive down the ground
#   CAMERA:     Wide side-on broadcast shot with full pitch visible
#   EMOTION:    Confident, elegant follow-through, bat raised high
#   ATMOSPHERE: Packed stadium, roaring crowd, bright daylight match
#   CONTEXT:    A side-on wide shot captures Kohli playing a textbook 
#               straight drive, his confident follow-through drawing 
#               a roaring response from a packed SCG crowd.