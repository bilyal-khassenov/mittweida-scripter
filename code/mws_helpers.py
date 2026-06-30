import pathlib, os, json, time, uuid
from typing import Literal

class ProjectPaths:
    def __init__(self):
        self.project_folder_path = pathlib.Path(__file__).parent.parent
        self.code_path = pathlib.Path(__file__).parent
        self.resources_path = os.path.join(self.code_path.parent, 'resources')
        self.stats_path = os.path.join(self.code_path.parent, 'stats')
        self.uploads_path = os.path.join(self.code_path.parent, 'uploads')
        self.temp_orig_file_path = os.path.join(self.uploads_path, '0_temp_orig_file')
        self.folder_for_format_conversion_path = os.path.join(self.uploads_path, '1_format_conversion')
        #self.unprocessed_folder_path = os.path.join(self.uploads_path, '2_unprocessed')
        self.in_progress_folder_path = os.path.join(self.uploads_path, '2_in_progress')
        self.processed_folder_path = os.path.join(self.uploads_path, '3_processed')
        self.local_tests_folder_path = os.path.join(self.uploads_path, '4_local_tests')
        self.uploads_protocol_fullfilename = os.path.join(self.stats_path, 'protocol.csv')
        self.performance_protocol_fullfilename = os.path.join(self.stats_path, 'performance.csv')

def get_acceptable_format_extensions():
    return [
        '.webm', '.mkv', '.flv', '.vob', '.ogv', '.ogg', '.drc', '.avi', '.MTS', '.M2TS', '.TS',
        '.mov', '.qt', '.wmv', '.rm', '.rmvb', '.viv', '.asf', '.amv', '.mp4', '.m4p', '.m4v', '.mpg',
        '.mp2', '.mpeg', '.mpe', '.mpv', '.mpg', '.m2v', '.m4v', '.3gp', '.3g2', '.f4v',
        '.f4p', '.f4a', '.f4b', '.3gp', '.aa', '.aac', '.aax', '.act', '.aiff', '.alac', '.amr', '.ape',
        '.au', '.awb', '.dss', '.dvf', '.flac', '.gsm', '.iklax', '.ivs', '.m4a', '.m4b', '.m4p', '.mmf',
        '.movpkg', '.mp3', '.mpc', '.msv', '.nmf', '.ogg', '.oga', '.mogg', '.opus', '.ra', '.rm', '.raw',
        '.rf64', '.sln', '.tta', '.voc', '.vox', '.wav', '.wma', '.wv', '.webm', '.8svx', '.cda'
    ]

def get_whisper_language_codes():
    return {"en": "english", "zh": "chinese", "de": "german", "es": "spanish", "ru": "russian", "ko": "korean", "fr": "french",
            "ja": "japanese", "pt": "portuguese", "tr": "turkish", "pl": "polish", "ca": "catalan", "nl": "dutch", "ar": "arabic",
            "sv": "swedish", "it": "italian", "id": "indonesian", "hi": "hindi", "fi": "finnish", "vi": "vietnamese", "he": "hebrew",
            "uk": "ukrainian", "el": "greek", "ms": "malay", "cs": "czech", "ro": "romanian", "da": "danish", "hu": "hungarian",
            "ta": "tamil", "no": "norwegian", "th": "thai", "ur": "urdu", "hr": "croatian", "bg": "bulgarian","lt": "lithuanian",
            "la": "latin", "mi": "maori", "ml": "malayalam", "cy": "welsh", "sk": "slovak", "te": "telugu", "fa": "persian",
            "lv": "latvian", "bn": "bengali", "sr": "serbian", "az": "azerbaijani", "sl": "slovenian", "kn": "kannada", "et": "estonian",
            "mk": "macedonian", "br": "breton", "eu": "basque", "is": "icelandic", "hy": "armenian", "ne": "nepali", "mn": "mongolian",
            "bs": "bosnian", "kk": "kazakh", "sq": "albanian", "sw": "swahili", "gl": "galician", "mr": "marathi", "pa": "punjabi",
            "si": "sinhala", "km": "khmer", "sn": "shona", "yo": "yoruba", "so": "somali", "af": "afrikaans", "oc": "occitan",
            "ka": "georgian", "be": "belarusian", "tg": "tajik", "sd": "sindhi", "gu": "gujarati", "am": "amharic", "yi": "yiddish",
            "lo": "lao", "uz": "uzbek", "fo": "faroese", "ht": "haitian creole", "ps": "pashto", "tk": "turkmen", "nn": "nynorsk",
            "mt": "maltese", "sa": "sanskrit", "lb": "luxembourgish", "my": "myanmar", "bo": "tibetan", "tl": "tagalog", "mg": "malagasy",
            "as": "assamese", "tt": "tatar", "haw": "hawaiian", "ln": "lingala", "ha": "hausa", "ba": "bashkir", "jw": "javanese",
            "su": "sundanese", "yue": "cantonese"}

def get_language_setting_index_or_code(value):
    language_codes = get_whisper_language_codes()
    keys = list(language_codes.keys())

    if value == -1:
        return None
    elif value is None:
        return -1
    elif isinstance(value, str):
        return keys.index(value)
    else:
        return keys[value]

def get_model_setting_index_or_name(value):
    if isinstance(value, str):
        if value == 'large-v2':
            return 0
        elif value == 'turbo':
            return 1
    elif isinstance(value, int):
        if value == 0:
            return 'large-v2'
        elif value == 1:
            return 'turbo'

def get_configs():
    with open(os.path.join(ProjectPaths().resources_path, 'config.json'), 'r', encoding='utf-8') as config_file:
        configs = json.load(config_file)
    return configs

def make_sure_protocols_exist():
    #Check if Order Protocol exists and if not, create it
    if not os.path.exists(ProjectPaths().uploads_protocol_fullfilename):
        # If not, create the file without writing headers
        with open(ProjectPaths().uploads_protocol_fullfilename, 'w') as file:
            file.write('upload_timestamp,uploader_hash,duration_seconds,file_size,institution\n')
    #Check if Performance Protocol exists and if not, create it
    if not os.path.exists(ProjectPaths().performance_protocol_fullfilename):
        # If not, create the file without writing headers
        with open(ProjectPaths().performance_protocol_fullfilename, 'w') as file:
            file.write('model,duration_seconds,file_size,transcription_start_time,transcription_end_time,transcription_time_per_one_raw_second\n')

def send_mail(send_from, send_to, subject, message, files=[],
              server=get_configs()['email']['server'], port=get_configs()['email']['port'], username='', password='',
              use_tls=False):

    import smtplib
    from pathlib import Path
    from email.mime.multipart import MIMEMultipart
    from email.mime.base import MIMEBase
    from email.mime.text import MIMEText
    from email.utils import COMMASPACE, formatdate
    from email import encoders

    msg = MIMEMultipart()
    msg['From'] = send_from
    msg['To'] = COMMASPACE.join(send_to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject

    msg.attach(MIMEText(message))

    for item in files:
        # Support both old and new style
        if isinstance(item, (tuple, list)):
            path, attachment_name = item
        else:
            path = item
            attachment_name = Path(path).name

        part = MIMEBase('application', "octet-stream")
        with open(path, 'rb') as file:
            part.set_payload(file.read())

        encoders.encode_base64(part)

        part.add_header(
            'Content-Disposition',
            f'attachment; filename="{attachment_name}"'
        )

        msg.attach(part)

    smtp = smtplib.SMTP(server, port)
    if use_tls:
        smtp.starttls()

    smtp.sendmail(send_from, send_to, msg.as_string())
    smtp.quit()
    print('Mail sent!')

def send_telegram_message(admin_recipients, message_string: str):
    import requests

    # Read configs
    configs = get_configs()

    # Check how recipients were provided and transform them to list if needed
    if not isinstance(admin_recipients, list):
        admin_recipients = [
            recipient.strip()
            for recipient in admin_recipients.split(',')
        ]

    url = f"https://api.telegram.org/bot{configs['telegram']['bot_token']}/sendMessage"

    for admin_recipient in admin_recipients:
        payload = {
            "chat_id": admin_recipient,
            "text": message_string,
            "disable_web_page_preview": True
        }

        response = requests.get(url, params=payload)

        if not response.ok:
            print(f"Telegram message failed: {response.status_code} - {response.text}")
    
def get_css_opacity_style_code(style: Literal['grey', 'normal']):
    if style == 'grey':
        grey_style = """<style>
        h1, h2, h3, h4, h5, h6, button, [data-testid="stSelectbox"] {
            opacity: 0.5;
        }
        .no-fade {
            opacity: 1 !important;
        }
        </style>"""
        return grey_style
    elif style == 'normal':
        normal_style = """<style>body, h1, h2, h3, h4, h5, h6, button, span { opacity: 1; }</style>"""
        return normal_style

def generate_hash(input_string):
    if input_string is not None:
        import hashlib
        # Create a sha256 hash object
        hash_object = hashlib.sha256(input_string.encode())
        # Generate the hash value (digest) in hexadecimal
        hash_hex = hash_object.hexdigest()
        return hash_hex
    else:
        return '!!!VALUE NOT PROVIDED!!!'

def generate_key():
    from cryptography.fernet import Fernet, InvalidToken
    key = Fernet.generate_key()  # 32-byte URL-safe base64-encoded key
    print(key)

def get_encryption_key():
    # Prefer env var for security
    key = os.environ.get('FILE_ENCRYPTION_KEY')
    if not key:
        configs = get_configs()
        key = configs.get('encryption', {}).get('key')
    if not key:
        raise ValueError("Encryption key not found in env or config!")
    return key.encode()  # Ensure it's bytes

def obfuscate_string(name: str) -> str:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend
    import base64
    import hashlib
    key = hashlib.sha256(get_encryption_key()).digest()
    iv = b"\x00" * 16  # fixed IV (for obfuscation)
    cipher = Cipher(algorithms.AES(key), modes.CTR(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ct = encryptor.update(name.encode()) + encryptor.finalize()
    return base64.urlsafe_b64encode(ct).decode("ascii").rstrip("=")

def clarify_string(token: str) -> str:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend
    import base64
    import hashlib
    padded = token + "=" * ((4 - len(token) % 4) % 4)
    ct = base64.urlsafe_b64decode(padded)
    key = hashlib.sha256(get_encryption_key()).digest()
    iv = b"\x00" * 16
    cipher = Cipher(algorithms.AES(key), modes.CTR(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    return (decryptor.update(ct) + decryptor.finalize()).decode()

def safe_unlink(file_path, label="file"):
    """
    Safely delete a file if it exists.
    Accepts either str or pathlib.Path.
    """
    if file_path is None:
        return

    try:
        path = pathlib.Path(file_path)

        if path.exists():
            path.unlink()
            print(f"{label} deleted successfully: {path}")

    except FileNotFoundError:
        print(f"{label} does not exist: {file_path}")

    except PermissionError:
        print(f"No permission to delete {label}: {file_path}")

    except Exception as e:
        print(f"Could not delete {label} {file_path}: {e}")


def create_processing_marker(source_file_path):
    """
    Creates a marker file representing one active processing job.
    The marker is used for counting active daemon processes.
    """
    marker_dir = pathlib.Path(ProjectPaths().in_progress_folder_path)
    marker_dir.mkdir(parents=True, exist_ok=True)

    source_stem = pathlib.Path(source_file_path).stem
    marker_name = f"{source_stem}.{uuid.uuid4().hex}.job"
    marker_path = marker_dir / marker_name

    marker_data = {
        "source_file": str(source_file_path),
        "source_stem": source_stem,
        "created_at": time.time(),
        "pid": os.getpid()
    }

    with open(marker_path, "x", encoding="utf-8") as marker_file:
        json.dump(marker_data, marker_file)

    return str(marker_path)


def count_processing_jobs():
    """
    Count active processing jobs by counting .job marker files only.
    This intentionally ignores .opus, .wav, .docx, .srt, .vtt, etc.
    """
    marker_dir = pathlib.Path(ProjectPaths().in_progress_folder_path)

    if not marker_dir.exists():
        return 0, []

    marker_files = []

    for path in marker_dir.iterdir():
        if path.is_file() and path.suffix.lower() == ".job":
            marker_files.append(str(path))

    return len(marker_files), marker_files


def cleanup_processing_markers():
    """
    Removes all old processing markers.

    Use this once when starting/restarting the daemon script.
    Do NOT call this from the Streamlit page and do NOT call this repeatedly
    while workers may still be running.
    """
    _, marker_files = count_processing_jobs()

    for marker_file in marker_files:
        safe_unlink(marker_file)

def count_and_list_files(folder_path):
    files = []
    files_count = 0

    for path in os.listdir(folder_path):
        file_path = os.path.join(folder_path, path)

        if os.path.isfile(file_path) and path != '.gitignore':
            files_count += 1
            files.append(file_path)

    return files_count, files

def get_media_info(path):
    import subprocess
    import json
    # Get duration using ffprobe
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries',
             'format=duration', '-of', 'json', path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        duration = float(json.loads(result.stdout)['format']['duration'])
    except Exception:
        duration = None

    # Get file size in bytes
    try:
        size_bytes = os.path.getsize(path)
    except OSError:
        size_bytes = None

    return {
        'duration_seconds': duration,
        'size_bytes': size_bytes
    }