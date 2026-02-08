from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
from yt_download import process_video
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOADS_DIR = os.path.join(BASE_DIR, 'downloads')
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

app = Flask(__name__, static_folder='../frontend', template_folder='../frontend')
CORS(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_url():
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'No URL provided'}), 400
        
        result = process_video(url)
        
        if not result:
            return jsonify({'error': 'Failed to process video'}), 500
            
        video_path, audio_path = result

        proto = request.headers.get('X-Forwarded-Proto', request.scheme)
        base_url = f"{proto}://{request.host}".rstrip('/')

        return jsonify({
            'video_url': f"{base_url}/download/{os.path.basename(video_path)}",
            'audio_url': f"{base_url}/download/{os.path.basename(audio_path)}"
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    try:
        safe_name = os.path.basename(filename)
        file_path = os.path.join(DOWNLOADS_DIR, safe_name)
        return send_file(file_path, as_attachment=True)
    except FileNotFoundError:
        return jsonify({'error': 'File not found'}), 404

if __name__ == '__main__':
    # Create downloads directory if it doesn't exist
    if not os.path.exists(DOWNLOADS_DIR):
        os.makedirs(DOWNLOADS_DIR)
        
    app.run(debug=True)
