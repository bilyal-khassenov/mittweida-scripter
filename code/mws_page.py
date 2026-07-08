# IMPORT STANDARD MODULES
import os, pathlib, time, re, getpass, json
import streamlit as st, pandas as pd
from PIL import Image
from datetime import datetime
from unidecode import unidecode
from wordcloud import WordCloud
from cryptography.fernet import Fernet
import matplotlib.pyplot as plt

# Import helper functions
import mws_helpers

# Define variables
dir_resources = mws_helpers.ProjectPaths().resources_path
dir_orig_files_temps = mws_helpers.ProjectPaths().temp_orig_file_path
dir_format_conversion = mws_helpers.ProjectPaths().folder_for_format_conversion_path
dir_in_progress = mws_helpers.ProjectPaths().in_progress_folder_path
stats_protocol_file_path = mws_helpers.ProjectPaths().uploads_protocol_fullfilename
configs = mws_helpers.get_configs()
texts_from_config_file = configs['texts']['page']


def logo_area():
    placeholder_column, logo_column = st.columns([2, 1])
    hsmw_logo = Image.open(os.path.join(dir_resources, 'logo.png'))
    logo_column.image(hsmw_logo)


def news_area():
    news_text = texts_from_config_file['news_text']
    if news_text:  # Python treats an empty string ("") as False in a boolean context
        st.write(f":blue[NEW! {news_text}]")
    # Problems area  #Python treats an empty string ("") as False in a boolean context
    problems_text = texts_from_config_file['problem_text']
    if problems_text:
        st.write(":red[CAUTION!]")
        st.write(problems_text)


def heading_area():
    st.markdown(f"<h1 class='no-fade'>{configs['texts']['general']['scripter_name']}</h1>", unsafe_allow_html=True)
    st.markdown(f"<h3 class='no-fade'>{texts_from_config_file['platform_heading']}</h3>", unsafe_allow_html=True)


def tutorial_area():
    expander_tutorial = st.expander(texts_from_config_file['how_it_works_header'])
    expander_tutorial.write(texts_from_config_file['how_it_works'])


def data_protection_declaration_area():
    # Data Prootection Declaration
    with st.container(border=True):
        # Consent Area
        col1_consent_text, col2_checkbox = st.columns([30, 1])
        with col1_consent_text:
            st.markdown(f"<p class='no-fade'>{texts_from_config_file['consent_text']}</p>", unsafe_allow_html=True)
        with col2_checkbox:
            data_protection_agreed = st.checkbox("&nbsp;", value=False, label_visibility='collapsed')
            # Divider with no margins
        st.markdown("<hr style='margin: 0;'/>", unsafe_allow_html=True)
        # Reference to the Data Protection Notice with Hyperlink
        st.markdown(f"<p class='no-fade'>{texts_from_config_file['data_privacy_note_notice']}</p>",
                    unsafe_allow_html=True)

    return (data_protection_agreed)


def data_privacy_note_area():
    expander_data_privacy = st.expander(texts_from_config_file['data_privacy_note_lable'])
    expander_data_privacy.markdown(
        f"<p class='no-fade' id='data_privacy_note'>{texts_from_config_file['data_privacy_note']}</p>",
        unsafe_allow_html=True)


def imprint_area():
    expander_imprint = st.expander(texts_from_config_file['imprint_area_lable'])
    expander_imprint.markdown(f"<p class='no-fade'>{texts_from_config_file['imprint_text']}</p>",
                              unsafe_allow_html=True)


def contact_area():
    expander_contact = st.expander(texts_from_config_file['contact_area_lable'])
    expander_contact.markdown(f"<p class='no-fade'>{texts_from_config_file['contact_text']}</p>",
                              unsafe_allow_html=True)


@st.cache_resource
def generate_wordcloud(text: str):
    wc = WordCloud(
        width=1200,
        height=600,
        background_color='black',
        colormap='Blues',
        margin=0
    ).generate(text)
    fig, ax = plt.subplots(figsize=(12, 6), dpi=150, facecolor='black')
    ax.imshow(wc, interpolation='bilinear')
    ax.axis("off")
    return fig


def stats_area():
    expander_stats = st.expander(texts_from_config_file['stats_expander_heading'])
    with expander_stats:
        if stats_protocol_file_path is not None:
            # Read the CSV file into a DataFrame
            df = pd.read_csv(stats_protocol_file_path, encoding='Windows-1252')

            # Ensure the required columns are present
            if all(column in df.columns for column in ["upload_timestamp", "duration_seconds", "institution"]):
                # Calculate the number of unique users
                unique_users = df["uploader_hash"].nunique()

                # New row for unique users
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    with st.container():
                        st.metric(label=texts_from_config_file['unique_users_heading_label'],
                                  value=f"{unique_users} {texts_from_config_file['unique_users_value_label']}")

                # Convert `upload_timestamp` to a readable date format
                df["upload_date"] = pd.to_datetime(df["upload_timestamp"], unit='s')

                # Convert duration_seconds to hours
                df["duration_hours"] = df["duration_seconds"] / 3600

                # Add a cumulative column for `duration_hours`
                df["cumulative_hours"] = df["duration_hours"].cumsum()

                # Add a row count column
                df["row_count"] = range(1, len(df) + 1)

                # Calculate total transcription hours
                total_hours = df["duration_hours"].sum()

                # Calculate total transcription counts
                total_transcriptions = len(df)

                # Display total hours and total transcriptions as metrics above the charts
                col_metrics1, col_metrics2 = st.columns(2)
                with col_metrics1:
                    st.metric(label=texts_from_config_file['hours_chart_heading'],
                              value=f"{total_hours:.2f} {texts_from_config_file['hours_chart_hours_wording']}")
                with col_metrics2:
                    st.metric(label=texts_from_config_file['count_chart_heading'],
                              value=f"{total_transcriptions} {texts_from_config_file['count_chart_files_wording']}")

                # Create two columns for side-by-side charts
                col1, col2 = st.columns(2)

                # First column: Cumulative Duration in Hours Chart
                with col1:
                    st.area_chart(df[["upload_date", "cumulative_hours"]].set_index("upload_date"))

                # Second column: Row Count Chart
                with col2:
                    st.area_chart(df[["upload_date", "row_count"]].set_index("upload_date"))

                # Word Cloud with Institutions Using the Service
                st.subheader(texts_from_config_file['word_cloud_heading'])

                fig = generate_wordcloud(texts_from_config_file['word_cloud_string'])
                st.pyplot(fig)
            else:
                st.error(
                    "The uploaded CSV must contain 'upload_timestamp', 'duration_seconds', and 'institution' columns.")
        else:
            st.info("Please upload a CSV file to get started.")


def main():
    # To test locally:
    # conda activate [env_name]
    # pushd/cd to Code Folder
    # streamlit run mws_page.py OR streamlit run mws_page.py --server.enableXsrfProtection false

    # Streamlit configs
    favicon_path = Image.open(os.path.join(dir_resources, 'favicon.ico'))
    st.set_page_config(page_title=configs['texts']['general']['scripter_name'], page_icon=favicon_path)

    # Read Stats
    df = pd.read_csv(stats_protocol_file_path, usecols=['duration_seconds'], encoding='Windows-1252')

    # Areas of the page
    logo_area()
    news_area()
    heading_area()
    data_protection_agreed = data_protection_declaration_area()

    # Define CSS for greyed-out & normal text using opacity (exclude specific sections)
    grey_style = mws_helpers.get_css_opacity_style_code('grey')
    normal_style = mws_helpers.get_css_opacity_style_code('normal')

    # Apply the styles conditionally based on checkbox state
    if data_protection_agreed:
        st.markdown(normal_style, unsafe_allow_html=True)
    else:
        st.markdown(grey_style, unsafe_allow_html=True)

    # Initialize values in Session State
    if "form_elements_disabled" not in st.session_state:
        st.session_state.disabled = False

    #Main form
    with st.form(key="Form :", clear_on_submit = False):
        
        #E-Mail-Address
        email_address_textbox = st.text_input(texts_from_config_file['email_field_lable'], disabled=any([st.session_state.disabled, data_protection_agreed!=True]))
        #Create two columns for Language & Translation Settings
        language_column, model_column, diarization_column, subtitle_column, translation_column   = st.columns([1, 1, 1, 1, 1])  # Adjust width ratios if needed
        # Create two columns for subtitles & summary generation
        summary_column, summary_language, _, _, _ = st.columns([1, 1, 1, 1, 1])
        #Placeholder for Summarization Area
        #Language Selection Area
        capitalized_languages = [texts_from_config_file['language_code_selectbox_default_option']] + sorted([lang.title() for lang in mws_helpers.get_whisper_language_codes().values()])
        with language_column:
            language_name = st.selectbox(texts_from_config_file['language_code_selectbox_label'], capitalized_languages)
        #Model Selection Area
        with model_column:
            transcription_model = st.selectbox(texts_from_config_file['model_selection_label'], ['large-v2', 'turbo'], help=texts_from_config_file['highest_speed_tip'])
        #Diarization Setting Area
        with diarization_column:
            diarization_setting = st.selectbox(texts_from_config_file['speaker_assignment_label'], [texts_from_config_file['no'], texts_from_config_file['yes']])
        #Subtitle Setting Area
        with subtitle_column:
            subtitle_setting = st.selectbox(texts_from_config_file['subtitle_selectbox_label'], options=[texts_from_config_file['no'], texts_from_config_file['yes']])
        #Translation Selection Area
        with translation_column:
            translation_setting = st.selectbox(texts_from_config_file['tranlation_selection_label'], [texts_from_config_file['no'], texts_from_config_file['yes']])
        # Summary Setting Area
        with summary_column:
            summary_setting = st.selectbox(
                texts_from_config_file['summary_selectbox_label'],
                options=[texts_from_config_file['no'], texts_from_config_file['yes']],
                disabled=any([st.session_state.disabled, data_protection_agreed != True])
            )
        with summary_language:
            summary_language_name = st.selectbox(
                texts_from_config_file['summary_language_selectbox_label'],
                options=summary_languages,
                disabled=any([st.session_state.disabled, data_protection_agreed != True])
            )

        prompt_hint = st.text_area(
            "Hinweise zur Zusammenfassung (optional)",
            placeholder="Fachbegriffe, Sprechernamen...",
            disabled=any([st.session_state.disabled, data_protection_agreed != True]),
            max_chars=500
        )

        # Upload section
        uploaded_files = st.file_uploader(
            accept_multiple_files=True,
            label=texts_from_config_file['select_file'],
            disabled=any([st.session_state.disabled, data_protection_agreed != True]),
            type=mws_helpers.get_acceptable_format_extensions()
        )

        submit_button = st.form_submit_button(
            label=texts_from_config_file['send_file'],
            disabled=any([st.session_state.disabled, data_protection_agreed != True])
        )

    # Action on submitting
    if submit_button:
        if email_address_textbox == '':
            st.error(texts_from_config_file['error_username_not_provided'], icon="🚨")
        elif uploaded_files is None:
            st.error(texts_from_config_file['error_file_not_selected'], icon="🚨")
        elif re.compile(r'^\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b$').search(
                email_address_textbox):  # If it is a valid e-mail address
            with st.spinner(texts_from_config_file['uploading_file_process_spinner_label']):  # Show spinner
                for uploaded_file in uploaded_files:
                    # Transliterate input file name
                    p = pathlib.Path(uploaded_file.name)
                    userdefined_file_name_stem = unidecode(p.stem)
                    file_extension_of_originally_uploaded_file = p.suffix.lower()

                    # Sanitize Filename
                    userdefined_file_name_stem = re.sub(r'[^a-zA-Z0-9._-]', "_", userdefined_file_name_stem)
                    # Replace spaces with undescore charachter
                    re_pattern_space_char = r'[^\w_.-]'
                    userdefined_file_name_stem = re.sub(re_pattern_space_char, '_', userdefined_file_name_stem)
                    # Replace consecutive non-alphanumeric characters with a single underscore
                    userdefined_file_name_stem = re.sub(r'[^a-zA-Z0-9]+', '_', userdefined_file_name_stem)
                    # Remove leading and trailing underscores
                    userdefined_file_name_stem = userdefined_file_name_stem.strip('_')
                    # Obtain Language Code
                    language_code = None
                    for code, name in mws_helpers.get_whisper_language_codes().items():
                        if name == language_name.lower():
                            language_code = code
                    language_setting = mws_helpers.get_language_setting_index_or_code(language_code)
                    # Obtain Translation Status
                    translation_setting = "1" if translation_setting == texts_from_config_file['yes'] else "0"
                    # Obtain Diarizatin Setting
                    diarization_setting = "1" if diarization_setting == texts_from_config_file['yes'] else "0"
                    # Subtitle Setting
                    subtitle_setting = "1" if subtitle_setting == texts_from_config_file['yes'] else "0"
                    # Summary Setting
                    summary_setting = "1" if summary_setting == texts_from_config_file['yes'] else "0"
                    # Obtain transcription model code
                    transcription_model_setting = mws_helpers.get_model_setting_index_or_name(transcription_model)
                    # Combine file name from compenents
                    plain_structured_original_file_name_stem = f"{datetime.today().strftime('%Y%m%d#%H%M%S')}#{email_address_textbox}#{language_setting}#{translation_setting}#{diarization_setting}#{subtitle_setting}#{summary_setting}#{transcription_model_setting}#{userdefined_file_name_stem}"[
                        0:120]
                    plain_structured_original_file_name = plain_structured_original_file_name_stem + file_extension_of_originally_uploaded_file
                    # Obfuscated
                    obfuscated_filename_stem = mws_helpers.obfuscate_string(plain_structured_original_file_name_stem)
                    # Prepare paths
                    file_extension_of_originally_uploaded_file = pathlib.Path(dir_orig_files_temps,
                                                                              uploaded_file.name).suffix
                    # obfuscated_original_file_fullpath = pathlib.Path(dir_orig_files_temps, obfuscated_original_file_name_stem + format_suffix_of_user_uploaded_file)
                    # obfuscated_encrypted_file_fullpath_enc_postfix = pathlib.Path(dir_orig_files_temps, obfuscated_filename_stem + ".enc")
                    obfuscated_file_fullpath_orig_postfix = pathlib.Path(dir_orig_files_temps,
                                                                         obfuscated_filename_stem + file_extension_of_originally_uploaded_file)

                    # Get bytes of uploaded file
                    uploaded_file_bytes = uploaded_file.getvalue()

                    # Temporarily save audio file to gather info
                    with open(obfuscated_file_fullpath_orig_postfix, mode='wb') as w:
                        w.write(uploaded_file.getvalue())

                    sidecar_path = obfuscated_file_fullpath_orig_postfix.with_suffix('.json')
                    sidecar_data = {
                        "prompt_hint": prompt_hint,
                        "summary_language": summary_language_name
                    }
                    with open(sidecar_path, 'w', encoding='utf-8') as f:
                        json.dump(sidecar_data, f, ensure_ascii=False, indent=2)

                    # Gather file info
                    media_info = mws_helpers.get_media_info(obfuscated_file_fullpath_orig_postfix)
                    duration_seconds = media_info['duration_seconds']
                    file_size = media_info['size_bytes']
                    # Delete temporary file
                    pathlib.Path.unlink(obfuscated_file_fullpath_orig_postfix)

                    # Write encrypted file
                    key = mws_helpers.get_encryption_key()
                    fernet = Fernet(key)
                    encrypted_bytes = fernet.encrypt(uploaded_file_bytes)

                    with open(obfuscated_file_fullpath_orig_postfix,
                              "wb") as enc_file:  # this filename is used to transfer the original file extension to mws_whisper.py
                        enc_file.write(encrypted_bytes)

                    # Prepare New Protocol Record
                    try:
                        institution_referer = st.context.headers[configs['header_names']['identity_provider']]
                    except:
                        institution_referer = '--'
                    # Prepare new protocol record
                    new_order_record = [{'upload_timestamp': time.time(),
                                         'uploader_hash': mws_helpers.generate_hash(email_address_textbox),
                                         'duration_seconds': duration_seconds,
                                         'file_size': file_size,
                                         'institution': institution_referer,
                                         'language_code': mws_helpers.get_language_setting_index_or_code(language_setting),
                                         'translation_status': translation_setting,
                                         'diarization_status': diarization_setting,
                                         'transcription_model': transcription_model}]

                #Prepare New Protocol Record
                try:
                    institution_referer = st.context.headers[configs['header_names']['identity_provider']]
                except:
                    institution_referer = '--'
                #Prepare new protocol record
                new_order_record = [{'upload_timestamp': time.time(),
                                        'uploader_hash': mws_helpers.generate_hash(email_address_textbox),
                                        'duration_seconds': duration_seconds,
                                        'file_size': file_size,
                                        'institution': institution_referer,
                                        'language_code': mws_helpers.get_language_setting_index_or_code(language_setting),
                                        'translation_status': translation_setting,
                                        'diarization_status': diarization_setting,
                                        'subtitles_status': subtitle_setting,
                                        'transcription_model': transcription_model}]

                #Register new record - transform it to a dataframe
                new_record_df = pd.DataFrame(new_order_record)
                #Check if protocol exists. If not, create it
                mws_helpers.make_sure_protocols_exist()
                #Read protocol
                protocol = pd.read_csv(stats_protocol_file_path, encoding='Windows-1252')
                #Concatanate protocol records
                result = pd.concat([protocol, new_record_df])
                #Save new state of the protocol
                result.to_csv(stats_protocol_file_path, encoding='Windows-1252', index=False)
                
                #Send notification to Admin to let him know a new file has been uploaded for Transcription
                if configs['telegram']['use_telegram'] == True:
                    count_unprocessed, _ = mws_helpers.count_and_list_files(dir_orig_files_temps)
                    count_in_progress, _ = mws_helpers.count_processing_jobs()

                    duration_minutes_for_message = (
                        round(duration_seconds / 60, 2)
                        if duration_seconds is not None
                        else "unknown"
                    )

                    mws_helpers.send_telegram_message(
                        configs['telegram']['admin_chat_id'],
                        f"NEW FILE HAS BEEN UPLOADED\n"
                        f"Machine: {getpass.getuser()}\n"
                        f"Institution: {institution_referer}\n"
                        f"Duration in Minutes: {duration_minutes_for_message}\n"
                        f"Language Code: {mws_helpers.get_language_setting_index_or_code(language_setting)}\n"
                        f"Transcription Model: {transcription_model}\n"
                        f"Diarization Status: {diarization_setting}\n"
                        f"Translation Status: {translation_setting}\n"
                        f"Subtitles Status: {subtitle_setting}\n"
                        f"Files Waiting: {count_unprocessed}\n"
                        f"Files in Progress: {count_in_progress}/{configs['features']['max_files_processed_simultaneously']}\n"
                    )
                    
                #Success message for user
                st.success(f"{texts_from_config_file['upload_success_message_part_1']} {email_address_textbox}")
        else:
            print(st.error(texts_from_config_file['error_wrong_email'], icon="🚨"))

    # Further Page Areas
    stats_area()
    tutorial_area()
    data_privacy_note_area()
    imprint_area()
    contact_area()


if __name__ == "__main__":
    main()