from flask import Flask, render_template, request, send_file
import os
import uuid
import subprocess
import sys
import shutil

app = Flask(__name__)
DOWNLOAD_FOLDER = "temp"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/download", methods=["POST"])
def download():
    url = request.form["url"]
    uid = str(uuid.uuid4())
    mp4_filename = f"{uid}.mp4"
    mp3_filename = f"{uid}.mp3"
    mp4_path = os.path.join(DOWNLOAD_FOLDER, mp4_filename)
    mp3_path = os.path.join(DOWNLOAD_FOLDER, mp3_filename)

    # ✅ yt-dlp command with user-agent to bypass bot detection
    cmd = [
        "yt-dlp",
        "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "--no-playlist",
        "-f", "best[ext=mp4]/best",
        "-o", mp4_path,
        url
    ]
    subprocess.run(cmd)

    # ✅ Convert to MP3 if MP4 exists
    if shutil.which("ffmpeg") and os.path.exists(mp4_path):
        subprocess.run([
            "ffmpeg", "-i", mp4_path, "-vn", "-ab", "128k", "-ar", "44100", "-y", mp3_path
        ])

    return render_template("download_page.html",
        mp4_url=f"/download_file/{mp4_filename}" if os.path.exists(mp4_path) else None,
        mp3_url=f"/download_file/{mp3_filename}" if os.path.exists(mp3_path) else None
    )

@app.route("/download_file/<filename>")
def serve_file_and_delete(filename):
    path = os.path.join(DOWNLOAD_FOLDER, filename)
    if os.path.exists(path):
        response = send_file(path, as_attachment=True)
        @response.call_on_close
        def delete_file():
            try:
                os.remove(path)
            except Exception as e:
                print(f"Error deleting file: {e}")
        return response
    else:
        return "File not found.", 404

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    app.run(debug=True, port=port)
