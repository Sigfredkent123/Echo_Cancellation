from flask import Flask, render_template, request, send_file, jsonify
from pydub import AudioSegment
import uuid
import os
import wave
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from scipy.io import wavfile

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
PROCESSED_FOLDER = "processed"
STATIC_FOLDER = "static"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)
os.makedirs(STATIC_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'audio_file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['audio_file']
    if file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400
    print("Incoming request...")
    print("Files in request:", request.files)
    original_ext = file.filename.split('.')[-1]
    unique_id = str(uuid.uuid4())
    original_path = os.path.join(UPLOAD_FOLDER, f"{unique_id}.{original_ext}")
    file.save(original_path)
    simulate_echo = request.form.get("simulate_echo") == "true"

    # Convert to WAV if not already
    if original_ext.lower() != 'wav':
        sound = AudioSegment.from_file(original_path)
        filepath = os.path.join(UPLOAD_FOLDER, f"{unique_id}.wav")
        sound.export(filepath, format='wav')
    else:
        filepath = original_path
    try:
        # Read WAV file
        samplerate, data = wavfile.read(filepath)

        # Convert stereo to mono if needed
        if len(data.shape) > 1:
            data = data.mean(axis=1)

        data = data.astype(np.float32)

        # Reduce echo
        delay_sec = 0.3
        attenuation = 0.4
        delay_samples = int(delay_sec * samplerate)
        # Initialize output
        cleaned = np.copy(data).astype(np.float32)

        # Echo detection: check correlation between signal and its delayed version
        corr = np.corrcoef(data[delay_samples:], data[:-delay_samples])[0, 1]
        print(f"Correlation with delayed signal: {corr:.3f}")

        # If correlation is high, apply echo cancellation
        if abs(corr) > 0.2 or simulate_echo:
            for i in range(delay_samples, len(cleaned)):
                cleaned[i] = data[i] - attenuation * cleaned[i - delay_samples]
        else:
            print("Low echo correlation detected — skipping echo cancellation.")
        amplitude_scale = 0.5  # Lower the volume by 50% (change as needed)
        # Normalize the output to prevent excessive loudness
        max_val = np.max(np.abs(cleaned))
        if max_val > 0:
            cleaned = (cleaned / max_val) * 32767 * amplitude_scale

        # Clip and cast to int16
        cleaned = np.clip(cleaned, -32768, 32767).astype(np.int16)

        # Save cleaned audio
        cleaned_path = os.path.join(UPLOAD_FOLDER, "cleaned.wav")
        wavfile.write(cleaned_path, samplerate, cleaned)

        # Plot
        time_axis = np.linspace(0, len(data) / samplerate, num=len(data))
        time_axis_cleaned = np.linspace(0, len(cleaned) / samplerate, num=len(cleaned))

        plt.figure(figsize=(10, 4))
        plt.plot(time_axis, data, label="Original")
        plt.plot(time_axis_cleaned, cleaned, label="cleaned", alpha=0.6)
        plt.xlabel("Time [s]")
        plt.ylabel("Amplitude")
        plt.title("Original vs Cleaned Waveform")
        plt.legend()
        plt.tight_layout()

        # Ensure plot is saved
        plot_path = os.path.join(STATIC_FOLDER, "plot.png")
        plt.savefig(plot_path)
        plt.close()
        print("Saving plot to:", os.path.abspath(plot_path))

        if not os.path.exists(plot_path):
            raise Exception("Plot was not saved correctly!")

        return jsonify({
            "plot_url": f"/static/plot.png",
            "Cleaned_file_url": f"/download/cleaned.wav",
            "original_file_url": f"/download/{unique_id}.wav"
        })

    except Exception as e:
        print("Error while processing upload:", str(e))
        return jsonify({'error': f'An error occurred while processing the audio: {str(e)}'}), 500

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(os.path.join(UPLOAD_FOLDER, filename), as_attachment=True)
    
if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)
