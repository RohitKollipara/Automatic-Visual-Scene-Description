import json
from pathlib import Path


def merge_transcription_and_scenes(
    transcription_json: str = "transcription_output/transcription_full.json",
    scenes_json: str = "transcription_output/scene_descriptions.json",
    output_dir: str = "transcription_output"
) -> str | None:
    """
    Merge timestamped transcription and semantic scene descriptions into a
    single combined prompt file for Gen AI video generation.

    Args:
        transcription_json (str): Path to transcription_full.json
        scenes_json (str): Path to scene_descriptions.json
        output_dir (str): Directory to save merged output

    Returns:
        str: Path to the combined prompt file, or None if failed
    """
    try:
        t_path = Path(transcription_json)
        s_path = Path(scenes_json)

        if not t_path.exists():
            print(f"Error: Transcription file not found: {t_path}")
            return None

        if not s_path.exists():
            print(f"Error: Scene descriptions file not found: {s_path}")
            return None

        transcription = json.loads(t_path.read_text(encoding="utf-8"))
        scenes = json.loads(s_path.read_text(encoding="utf-8"))

        # Merge by matching closest timestamps
        merged = []
        for seg in transcription:
            seg_start = seg["start"]
            seg_end = seg["end"]

            # Find all scenes that fall within this segment
            matching_scenes = [
                s for s in scenes
                if seg_start <= s["timestamp"] < seg_end
            ]

            # If no scene falls exactly in range, use closest one
            if not matching_scenes:
                closest = min(scenes, key=lambda s: abs(s["timestamp"] - seg_start))
                matching_scenes = [closest]

            # Pull out semantic fields from all matching scenes
            actions     = " | ".join(s["semantic"].get("action",     "N/A") for s in matching_scenes)
            cameras     = " | ".join(s["semantic"].get("camera",     "N/A") for s in matching_scenes)
            emotions    = " | ".join(s["semantic"].get("emotion",    "N/A") for s in matching_scenes)
            atmospheres = " | ".join(s["semantic"].get("atmosphere", "N/A") for s in matching_scenes)
            contexts    = " | ".join(s["semantic"].get("context",    "N/A") for s in matching_scenes)

            merged.append({
                "start":      seg_start,
                "end":        seg_end,
                "audio":      seg["text"],
                "action":     actions,
                "camera":     cameras,
                "emotion":    emotions,
                "atmosphere": atmospheres,
                "context":    contexts
            })

        # Save merged JSON
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)

        json_path = output / "merged_full.json"
        json_path.write_text(json.dumps(merged, indent=2), encoding="utf-8")
        print(f"Merged JSON saved to: {json_path}")

        # Save human-readable video generation prompt
        prompt_path = output / "video_generation_prompt.txt"
        with prompt_path.open("w", encoding="utf-8") as f:
            f.write("VIDEO GENERATION PROMPT\n")
            f.write("=" * 60 + "\n\n")
            f.write(
                "Recreate a video based on the following timestamped segments.\n"
                "Each segment contains the spoken audio and full semantic context\n"
                "of the scene. Match visuals, energy, and audio as closely as possible.\n\n"
            )
            f.write("=" * 60 + "\n\n")

            for seg in merged:
                start = format_time(seg["start"])
                end   = format_time(seg["end"])
                f.write(f"[{start} --> {end}]\n")
                f.write(f"  AUDIO:      {seg['audio']}\n")
                f.write(f"  ACTION:     {seg['action']}\n")
                f.write(f"  CAMERA:     {seg['camera']}\n")
                f.write(f"  EMOTION:    {seg['emotion']}\n")
                f.write(f"  ATMOSPHERE: {seg['atmosphere']}\n")
                f.write(f"  CONTEXT:    {seg['context']}\n\n")

        print(f"Video generation prompt saved to: {prompt_path}")
        return str(prompt_path)

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
    result = merge_transcription_and_scenes()
    if result:
        print(f"\nDone! Combined prompt ready at: {result}")
# ```

# **The `video_generation_prompt.txt` will now look like:**
# ```
# VIDEO GENERATION PROMPT
# ============================================================

# Recreate a video based on the following timestamped segments.
# Each segment contains the spoken audio and full semantic context
# of the scene. Match visuals, energy, and audio as closely as possible.

# ============================================================

# [00:00:00 --> 00:00:04]
#   AUDIO:      He's away.
#   ACTION:     Batsman playing a straight drive down the ground
#   CAMERA:     Wide side-on broadcast shot with full pitch visible
#   EMOTION:    Confident, elegant follow-through, bat raised high
#   ATMOSPHERE: Packed stadium, roaring crowd, bright daylight match
#   CONTEXT:    A side-on wide shot captures Kohli playing a textbook
#               straight drive, drawing a roaring response from the SCG.
# ```

# **Your complete pipeline is now:**
# ```
# Video File
#     ↓
# Extract Audio (MoviePy)          → extracted_audio.wav
#     ↓
# Transcribe (Whisper)             → transcription_full.json
#     +
# Semantic Analysis (Groq Vision)  → scene_descriptions.json
#               ↓
#          Merge Step              → video_generation_prompt.txt
#               ↓
#       Gen AI Video (Veo)         → generated_video.mp4
