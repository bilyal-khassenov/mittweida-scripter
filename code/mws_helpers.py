import pathlib, os, json
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
        self.unprocessed_folder_path = os.path.join(self.uploads_path, '2_unprocessed')
        self.in_progress_folder_path = os.path.join(self.uploads_path, '3_in_progress')
        self.processed_folder_path = os.path.join(self.uploads_path, '4_processed')
        self.errors_folder_path = os.path.join(self.uploads_path, '5_errors')
        self.local_tests_folder_path = os.path.join(self.uploads_path, '5_local_tests')
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
    """Compose and send email with provided info and attachments.

    Args:
        send_from (str): from name
        send_to (list[str]): to name(s)
        subject (str): message title
        message (str): message body
        files (list[str]): list of file paths to be attached to email
        server (str): mail server host name
        port (int): port number
        username (str): server auth username
        password (str): server auth password
        use_tls (bool): use TLS mode
    """
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

    for path in files:
        part = MIMEBase('application', "octet-stream")
        with open(path, 'rb') as file:
            part.set_payload(file.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition',
                        'attachment; filename={}'.format(Path(path).name))
        msg.attach(part)

    smtp = smtplib.SMTP(server, port)
    if use_tls:
        smtp.starttls()
    # smtp.login(username, password)
    smtp.sendmail(send_from, send_to, msg.as_string())
    smtp.quit()
    print('Mail sent!')

def send_telegram_message(admin_recipients, message_string: str):
    from urllib.parse import quote_plus
    import requests

    #Read configs
    configs = get_configs()

    #Check how recipients were provided and transform them to list if needed
    if not isinstance(admin_recipients, list):
        admin_recipients = [recipient.strip() for recipient in admin_recipients.split(',')]

    # Send message to each recipient
    for admin_recipient in admin_recipients:
        send_text = f"https://api.telegram.org/bot{configs['telegram']['bot_token']}/sendMessage?chat_id={admin_recipient}&parse_mode=Markdown&text={quote_plus(message_string)}&disable_web_page_preview=True"
        response = requests.get(send_text)
    
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
    
def count_and_list_files(folder_path):
    files = []
    # Initialize counter variables
    files_count = 0
    # Count files in progress
    for path in os.listdir(folder_path):
        file_path = os.path.join(folder_path, path)
        # Exclude .gitignore and check if it is a file
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