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

def send_telegram_message(recipients, message_string: str):
    from urllib.parse import quote_plus
    import requests

    #Read configs
    configs = get_configs()

    #Check how recipients were provided and transform them to list if needed
    if not isinstance(recipients, list):
        recipients = [recipient.strip() for recipient in recipients.split(',')]

    # Send message to each recipient
    for recipient in recipients:
        ###chat_id = allowed_recipients[recipient]
        send_text = f"https://api.telegram.org/bot{configs['telegram']['bot_token']}/sendMessage?chat_id={configs['telegram']['admin_chat_id']}&parse_mode=Markdown&text={quote_plus(message_string)}&disable_web_page_preview=True"
        response = requests.get(send_text)
    
def get_css_opacity_style_code(style: Literal['grey', 'normal']):
    if style == 'grey':
        grey_style = """<style>
        h1, h2, h3, h4, h5, h6, button {
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