#IMPORT STANDARD MODULES
import os, pathlib, time, re, ffmpeg, getpass
import streamlit as st, pandas as pd
from PIL import Image
from datetime import datetime
from mutagen.mp3 import MP3
from unidecode import unidecode
from wordcloud import WordCloud
import matplotlib.pyplot as plt

#Import helper functions
import mws_helpers

#Define variables
dir_resources = mws_helpers.ProjectPaths().resources_path
dir_orig_files_temps = mws_helpers.ProjectPaths().temp_orig_file_path
dir_format_conversion = mws_helpers.ProjectPaths().folder_for_format_conversion_path
dir_unprocessed = mws_helpers.ProjectPaths().unprocessed_folder_path
stats_protocol_file_path = mws_helpers.ProjectPaths().uploads_protocol_fullfilename
configs = mws_helpers.get_configs()
texts_from_config_file = configs['texts']['page']

def logo_area():
    placeholder_column, logo_column = st.columns([2,1])
    hsmw_logo = Image.open(os.path.join(dir_resources, 'logo.png'))
    logo_column.image(hsmw_logo)
def news_area():
    news_text = texts_from_config_file['news_text']
    if news_text:   #Python treats an empty string ("") as False in a boolean context
        st.write(f":blue[NEW! {news_text}]")
    #Problems area  #Python treats an empty string ("") as False in a boolean context
    problems_text = texts_from_config_file['problem_text']
    if problems_text:
        st.write(f":red[CAUTION! {problems_text}]")
def heading_area():
    st.markdown(f"<h1 class='no-fade'>{configs['texts']['general']['scripter_name']}</h1>", unsafe_allow_html=True)
    st.markdown(f"<h3 class='no-fade'>{texts_from_config_file['platform_heading']}</h3>", unsafe_allow_html=True)
def tutorial_area():
    expander_tutorial = st.expander(texts_from_config_file['how_it_works_header'])
    expander_tutorial.write(texts_from_config_file['how_it_works'])
def data_protection_declaration_area():
    #Data Prootection Declaration
    with st.container(border=True):
        #Consent Area
        col1_checkbox, col2_text = st.columns([20, 1])
        with col1_checkbox:
            st.markdown(f"<p class='no-fade'>{texts_from_config_file['consent_text']}</p>", unsafe_allow_html=True)
        with col2_text:
            data_protection_agreed = st.checkbox("&nbsp;", value=False, label_visibility='collapsed')    
    return(data_protection_agreed)
def data_privacy_note_area():
    expander_data_privacy = st.expander(texts_from_config_file['data_privacy_note_lable'])
    expander_data_privacy.markdown(f"<p class='no-fade' id='data_privacy_note'>{texts_from_config_file['data_privacy_note']}</p>", unsafe_allow_html=True)
def imprint_area():
    expander_imprint = st.expander(texts_from_config_file['imprint_area_lable'])
    expander_imprint.markdown(f"<p class='no-fade'>{texts_from_config_file['imprint_text']}</p>", unsafe_allow_html=True)
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
                        st.metric(label=texts_from_config_file['unique_users_heading_label'], value=f"{unique_users} {texts_from_config_file['unique_users_value_label']}")

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
                    st.metric(label=texts_from_config_file['hours_chart_heading'], value=f"{total_hours:.2f} {texts_from_config_file['hours_chart_hours_wording']}")
                with col_metrics2:
                    st.metric(label=texts_from_config_file['count_chart_heading'], value=f"{total_transcriptions} {texts_from_config_file['count_chart_files_wording']}")

                # Create two columns for side-by-side charts
                col1, col2 = st.columns(2)

                # First column: Cumulative Duration in Hours Chart
                with col1:
                    st.area_chart(df[["upload_date", "cumulative_hours"]].set_index("upload_date"))

                # Second column: Row Count Chart
                with col2:
                    st.area_chart(df[["upload_date", "row_count"]].set_index("upload_date"))
                
                #Word Cloud with Institutions Using the Service
                st.subheader(texts_from_config_file['word_cloud_heading'])
        
                # Create and generate a word cloud image
                wordcloud = WordCloud(
                    width=1200,         # Increase canvas width
                    height=600,         # Increase canvas height
                    background_color='black',
                    colormap='Blues',   # Or your preferred colormap
                    margin=0            # Remove extra margin
                ).generate(texts_from_config_file['word_cloud_string'])

                # Create a figure and axis explicitly
                fig, ax = plt.subplots(figsize=(12, 6), dpi=150, facecolor='black')
                ax.imshow(wordcloud, interpolation='bilinear')
                ax.axis("off")  # Hide axes

                # Display the figure in Streamlit
                st.pyplot(fig)
            else:
                st.error("The uploaded CSV must contain 'upload_timestamp', 'duration_seconds', and 'institution' columns.")
        else:
            st.info("Please upload a CSV file to get started.")

def main():
    #To test locally:
    #conda activate [env_name]
    #pushd/cd to the Code Folder
    #streamlit run mws_page.py --server.enableXsrfProtection false

    #Streamlit configs
    favicon_path = Image.open(os.path.join(dir_resources, 'favicon.ico'))
    st.set_page_config(page_title=configs['texts']['general']['scripter_name'], page_icon=favicon_path)

    #Read Stats
    df = pd.read_csv(stats_protocol_file_path, usecols=['duration_seconds'], encoding='Windows-1252')

    #Areas of the page
    logo_area()
    news_area()
    heading_area()
    data_protection_agreed = data_protection_declaration_area()

    #Define CSS for greyed-out & normal text using opacity (exclude specific sections)
    grey_style = mws_helpers.get_css_opacity_style_code('grey')
    normal_style = mws_helpers.get_css_opacity_style_code('normal')

    #Apply the styles conditionally based on checkbox state
    if data_protection_agreed:
        st.markdown(normal_style, unsafe_allow_html=True)
    else:
        st.markdown(grey_style, unsafe_allow_html=True)

    #Initialize values in Session State
    if "form_elements_disabled" not in st.session_state:
        st.session_state.disabled = False

    #Main form
    with st.form(key="Form :", clear_on_submit = False):
        
        #E-Mail-Address
        email_address_textbox = st.text_input(texts_from_config_file['email_field_lable'], disabled=any([st.session_state.disabled, data_protection_agreed!=True]))
        #Create two columns for Language & Translation Settings
        language_column, translation_column, model_column = st.columns([1, 1, 1])  # Adjust width ratios if needed
        #Language Selection Area
        capitalized_languages = [texts_from_config_file['language_code_selectbox_default_option']] + sorted([lang.title() for lang in mws_helpers.get_whisper_language_codes().values()])
        with language_column:
            language_name = st.selectbox(texts_from_config_file['language_code_selectbox_label'], capitalized_languages)
        #Translation Selection Area
        with translation_column:
            translation_status = st.selectbox(texts_from_config_file['tranlation_selection_label'], [texts_from_config_file['no'], texts_from_config_file['yes']])
        #Model Selection Area
        with model_column:
            transcription_model = st.selectbox(texts_from_config_file['model_selection_label'], ['large-v2', 'large-v3-turbo'])
        #Upload section
        uploaded_file = st.file_uploader(label = texts_from_config_file['select_file'], disabled=any([st.session_state.disabled, data_protection_agreed!=True]), type=mws_helpers.get_acceptable_format_extensions())
        submit_button = st.form_submit_button(label=texts_from_config_file['send_file'], disabled=any([st.session_state.disabled, data_protection_agreed!=True]))

    #Action on submitting
    if submit_button:
        if email_address_textbox == '':
            st.error(texts_from_config_file['error_username_not_provided'], icon="🚨")
        elif uploaded_file is None:
            st.error(texts_from_config_file['error_file_not_selected'], icon="🚨")
        elif re.compile(r'^\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b$').search(email_address_textbox):   #If it is a valid e-mail address
            with st.spinner(texts_from_config_file['uploading_file_process_spinner_label']):  # Show spinner
                #Transliterate input file name
                file_name_stem = unidecode(uploaded_file.name)
                #Sanitize Filename
                file_name_stem = re.sub(r'[^a-zA-Z0-9._-]', "_", file_name_stem)
                #Replace spaces with undescore charachter
                re_pattern_space_char = r'[^\w_.-]'
                file_name_stem = re.sub(re_pattern_space_char, '_', file_name_stem)
                #Replace consecutive non-alphanumeric characters with a single underscore
                file_name_stem = re.sub(r'[^a-zA-Z0-9]+', '_', file_name_stem)
                #Remove leading and trailing underscores
                file_name_stem = file_name_stem.strip('_')
                #Obtain Language Code
                language_code = None
                for code, name in mws_helpers.get_whisper_language_codes().items():
                    if name == language_name.lower():
                        language_code = code
                #Obtain Translation Status
                translation_status = "To_En" if translation_status == texts_from_config_file['yes'] else "Orig"
                #Combine file name from compenents
                language_code_for_file_name = "Auto" if language_code is None else language_code
                new_file_name_stem = f"{datetime.today().strftime('%Y%m%d#%H%M%S')}#{email_address_textbox}#{language_code_for_file_name}#{translation_status}#{transcription_model}#{file_name_stem}"[0:120]

                #Prepare initial path
                format_suffix_of_user_uploaded_file = pathlib.Path(dir_orig_files_temps, uploaded_file.name).suffix
                originally_uploaded_file_fullname = pathlib.Path(dir_orig_files_temps, new_file_name_stem + format_suffix_of_user_uploaded_file)

                #Prepare New Protocol Record
                try:
                    institution_referer = st.context.headers[configs['header_names']['identity_provider']]
                except:
                    institution_referer = '--'
                language_code_for_protocol = '--' if language_code is None else language_code
                translation_status_for_protocol = 'translate' if translation_status == "To_En" else 'original'
                new_order_record = [{'upload_timestamp': time.time(),
                                        'uploader_hash': mws_helpers.generate_hash(email_address_textbox),
                                        'duration_seconds': None,
                                        'file_size': None,
                                        'institution': institution_referer,
                                        'language_code': language_code_for_protocol,
                                        'translation_status': translation_status_for_protocol,
                                        'transcription_model': transcription_model}]

                #Save uploaded file to the folder for file conversion
                with open(originally_uploaded_file_fullname, mode='wb') as w:
                    w.write(uploaded_file.getvalue())

                #Transform to an .mp3 in any case to have a standardized form of .mp3
                standardized_audio_temp_location = os.path.join(dir_format_conversion, new_file_name_stem + '.mp3')  #Prepare path for the final audio file
                stream = ffmpeg.input(originally_uploaded_file_fullname)
                stream = ffmpeg.output(stream, standardized_audio_temp_location)
                ffmpeg.run(stream)
                #Delete Originally uploaded file
                pathlib.Path.unlink(originally_uploaded_file_fullname)

                #Update record
                new_order_record[0]['duration_seconds'] = MP3(standardized_audio_temp_location).info.length
                new_order_record[0]['file_size'] = os.path.getsize(standardized_audio_temp_location)

                #Move audio file to uprocessed folder
                ready_audio_file_location = pathlib.Path(dir_unprocessed, new_file_name_stem + '.mp3')
                os.replace(standardized_audio_temp_location, ready_audio_file_location)

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
                    mws_helpers.send_telegram_message(['BK'], f"{configs['texts']['general']['scripter_name']} ({getpass.getuser()}) - A file has been uploaded")
                
                #Success message for user
                st.success(f"{texts_from_config_file['upload_success_message_part_1']} {email_address_textbox}")
        else:
            print(st.error(texts_from_config_file['error_wrong_email'], icon="🚨"))
    
    #Further Page Areas
    stats_area()
    tutorial_area()
    data_privacy_note_area()
    imprint_area()

if __name__ == "__main__":
    main()