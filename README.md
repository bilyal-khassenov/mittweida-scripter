# Mittweida Scripter

The Mittweida Scripter is a robust transcription tool developed at Mittweida University of Applied Sciences. It allows users to transcribe audio and video files quickly and securely. Built with privacy and efficiency in mind, it utilizes the Whisper Large v2 open-source transcription model for accurate transcription results. This tool is designed to operate exclusively on Hochschule Mittweida’s servers, ensuring GDPR compliance.

---

## Features

### Core Functionalities
- **Transcription Services**: Converts audio and video files to text using state-of-the-art machine learning.
- **Speaker Diarization**: Identifies and separates different speakers in the transcription.
- **Confidence Highlighting**: Color-codes transcription accuracy in the output (high, medium, low confidence levels).
- **Data Privacy**: Fully compliant with GDPR (DSGVO) regulations; all data is deleted immediately after transcription.
- **File Support**: Supports a wide range of audio and video formats.

### User Interface
- Intuitive web interface powered by Streamlit.
- Easy-to-use file upload and email-based notification system.
- Provides visual usage statistics, including the total transcription hours and file count.

### Output Formats
- **Plain Text Document**: Transcription of the audio/video content.
- **Speaker-Attributed Document**: Transcriptions segmented by speaker with timestamps.

---

## Getting Started

### Prerequisites
To run the project locally, ensure you have the following installed:
- Python 3.11+
- Conda (optional) for virtual environment management

### Setup
1. Clone the repository:
   ```bash
   git clone PLACEHOLDER
   cd mittweida-scripter

2. Create and activate a virtual environment (optional):
   ```bash
   conda create --name mittweida-scripter python=3.11
   conda activate mittweida-scripter

3. Install dependencies:
   ```bash
   pip install -r requirements.txt

4. Add the necessary configuration:
   - Edit the config.json file in the resources folder to include your server details and other settings.

5. Run the application:
   ```bash
   streamlit run mws_page.py

## File Structure
- **`mws_page.py`**: The Streamlit-based web interface for user interaction.
- **`mws_whisper.py`**: Contains transcription logic, speaker diarization, and document generation.
- **`mws_helpers.py`**: Helper functions for file management, configurations, and utilities like email/Telegram notifications.
- **`config.json`**: Configuration file for server settings, UI texts, and feature toggles.
- **`resources/`**: Contains the logo, favicon, and other static resources.
- **`uploads/`**: Handles file management in different stages (uploaded, processed, errors, etc.).
- **`stats/`**: Stores protocols and statistics for processed files.

---

## Usage Instructions
1. Access the web interface.
2. Provide your email address.
3. Upload an audio or video file in one of the supported formats.
4. Agree to the privacy policy and click **Submit**.
5. Receive the transcription results via email.

---

## Supported File Formats
This tool supports a wide range of file formats, including:
- **Audio**: `.mp3`, `.wav`, `.flac`, `.aac`, etc.
- **Video**: `.mp4`, `.mkv`, `.avi`, `.mov`, etc.

---

## Usage Statistics
The platform provides insights into its usage via the Statistics Panel:
- Total transcription hours
- Total number of files processed
- Number of unique users
- Top 10 institutions based on usage

---

## Privacy and Security
- **Data Retention**: All uploaded files and generated transcriptions are deleted immediately after processing.
- **Pseudonymized Data**: Email addresses are hashed to ensure privacy.
- **GDPR Compliance**: The tool adheres strictly to GDPR guidelines, ensuring the protection of user data.

---

## Development Notes

### Extending the Tool
- Add new features by modifying `mws_page.py` (UI logic) or `mws_whisper.py` (backend processing).
- Update configurations in `config.json` to adapt text, settings, or feature flags.

### Testing
Run tests locally by uploading files through the web interface. Check the logs and output in the respective folders (`uploads/`, `stats/`).

### Notifications
- **Email Notifications**: Sends transcription results directly to the user's email.
- **Telegram Alerts**: Optional admin notifications for system status and new uploads.

---

## License
This project is licensed under the MIT License.

---

## Acknowledgments
- OpenAI’s Whisper Model for transcription.
- `pyannote` for Speaker Diarization.
- Streamlit for the intuitive web interface.
- Hochschule Mittweida for supporting this initiative.

---

## Contact
For questions, feedback, or issues, please contact:
- **Email**: khasseno@hs-mittweida.de (Bilyal Khassenov)

We hope the Mittweida Scripter helps streamline your transcription workflows!