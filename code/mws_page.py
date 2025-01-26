#IMPORT STANDARD MODULES
import os, pathlib, time, re, ffmpeg
import streamlit as st, pandas as pd
from PIL import Image
from datetime import datetime
from mutagen.mp3 import MP3
from unidecode import unidecode

#Import helper functions
import mws_helpers

def main():
    #To test locally:
    #conda activate [env_name]
    #pushd/cd to the Code Folder
    #streamlit run mws_page.py

    #______________NEWS_AREA______________
    news_text = "Das Transkriptionstool ist ab sofort für alle Personen mit einem Hochschulaccount einer deutschen Hochschule zugänglich. Zusätzlich wurde ein spezieller Bereich mit Nutzungsstatistiken des Tools eingeführt. In den Transkriptionsergebnissen werden die Konfidenzniveaus nun durch eine farbliche Markierung hervorgehoben."    #If ==None, nothing will be shown below
    #______________NEWS_AREA______________

    #Define variables
    dir_resources = mws_helpers.ProjectPaths().resources_path
    dir_orig_files_temps = mws_helpers.ProjectPaths().temp_orig_file_path
    dir_format_conversion = mws_helpers.ProjectPaths().folder_for_format_conversion_path
    dir_unprocessed = mws_helpers.ProjectPaths().unprocessed_folder_path
    stats_protocol_file_path = mws_helpers.ProjectPaths().uploads_protocol_fullfilename

    #Read main configs
    configs = mws_helpers.get_configs()
    main_corporate_design_color = configs['ui_settings']['corporate_design_color']
    previously_transcribed_files_count = configs['features']['previously_transcribed_files_count']
    previously_transcribed_seconds_count = configs['features']['previously_transcribed_seconds_count']
    ###organisation_email_domain = configs['email']['email_domain']
    texts_from_config_file = configs['texts']['page']

    #Streamlit configs
    favicon_path = Image.open(os.path.join(dir_resources, 'favicon.ico'))
    st.set_page_config(page_title=configs['texts']['general']['scripter_name'], page_icon=favicon_path)

    #Read Stats
    df = pd.read_csv(stats_protocol_file_path, usecols=['duration_seconds'], encoding='Windows-1252')
    total_duration = df['duration_seconds'].sum()
    lines_count = df['duration_seconds'].count()

    #Logo Area
    placeholder_column, logo_column = st.columns([2,1])
    hsmw_logo = Image.open(os.path.join(dir_resources, 'logo.png'))
    logo_column.image(hsmw_logo)

    #News area
    if news_text is not None:
        st.write(f":blue[NEW! {news_text}]")   #FOR NEWS

    #Heading Area
    placeholder_column.markdown(f"<h1 class='no-fade'>{configs['texts']['general']['scripter_name']}</h1>", unsafe_allow_html=True)
    ####st.markdown(f"<h3 class='no-fade'>{texts['platform_heading']}</h3>", unsafe_allow_html=True)
    st.markdown(f"{texts_from_config_file['welcome_message']}", unsafe_allow_html=True)

    #Expander for Stats
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

                # Add a bar chart for top 10 institutions
                st.subheader(texts_from_config_file['top_ten_institutions_chart_heading'])
                institution_counts = df["institution"].value_counts().head(10)

                # Prepare a DataFrame for bar chart
                institution_df = institution_counts.reset_index()
                institution_df.columns = ["institution", "Count"]

                # Streamlit bar chart
                st.bar_chart(institution_df.set_index("institution"))
            else:
                st.error("The uploaded CSV must contain 'upload_timestamp', 'duration_seconds', and 'institution' columns.")
        else:
            st.info("Please upload a CSV file to get started.")

    #Expander for Tutorial
    expander_tutorial = st.expander(texts_from_config_file['how_it_works_header'])
    expander_tutorial.write(texts_from_config_file['how_it_works'])

    # # # # with placeholder_column:
    # # # #     placeholder_column.markdown(f"<div class='no-fade' style='color: {main_corporate_design_color}; font-size: 25px;'><b>{texts['usage_overview']}:</b></div>", unsafe_allow_html=True)
    # # # #     placeholder_column.markdown(f"<div class='no-fade' style='color: {main_corporate_design_color};'><b>{texts['transcribed_files']}: {lines_count + previously_transcribed_files_count} 💪</b></div>", unsafe_allow_html=True) #Set previously_transcribed_files_count to 0 in config by new instance of the app
    # # # #     placeholder_column.markdown(f"<div class='no-fade' style='color: {main_corporate_design_color};'><b>{texts['total_duration']}: {int((total_duration+previously_transcribed_seconds_count)/60/60)} 😎</b></div>", unsafe_allow_html=True) #Set previously_transcribed_seconds_count to 0 in config by new instance of the app

    #Data Prootection Declaration
    with st.container(border=True):
        #Consent Area
        col1_checkbox, col2_text = st.columns([20, 1])
        with col1_checkbox:
            st.markdown(f"<p class='no-fade'>{texts_from_config_file['consent_text']}</p>", unsafe_allow_html=True)
        with col2_text:
            data_protection_agreed = st.checkbox("&nbsp;", value=False, label_visibility='collapsed')    
        #Expander for Data Privacy Note
        expander_data_privacy = st.expander(texts_from_config_file['data_privacy_note_lable'])
        expander_data_privacy.markdown(f"<p class='no-fade'>{texts_from_config_file['data_privacy_note']}</p>", unsafe_allow_html=True)

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
    def disable_form():
        st.session_state.disabled = True

    #Get list of acceptable file formats
    acceptable_formats = mws_helpers.get_acceptable_format_extenstions()

    #Main form
    with st.form(key="Form :", clear_on_submit = False):
        #E-Mail Adress
        email_address_textbox = st.text_input(texts_from_config_file['email_field_lable'], disabled=any([st.session_state.disabled, data_protection_agreed!=True]))
        #Upload section
        uploaded_file = st.file_uploader(label = texts_from_config_file['select_file'], disabled=any([st.session_state.disabled, data_protection_agreed!=True]), type=acceptable_formats)
        submit_button = st.form_submit_button(label=texts_from_config_file['send_file'], disabled=any([st.session_state.disabled, data_protection_agreed!=True]))

    #Action on submitting
    if submit_button:
        if email_address_textbox == '':
            st.error(texts_from_config_file['error_username_not_provided'], icon="🚨")
        elif uploaded_file is None:
            st.error(texts_from_config_file['error_file_not_selected'], icon="🚨")
        elif re.compile(r'^\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b$').search(email_address_textbox):   #If it is a valid e-mail address
            #Replace spaces with undescore charachter
            re_pattern_space_char = r'[^\w_.-]'
            filename_no_spaces = re.sub(re_pattern_space_char, '_', pathlib.Path(dir_orig_files_temps, uploaded_file.name).stem)
            #Transliterate file name
            transliterated_text = unidecode(filename_no_spaces)
            # Replace consecutive non-alphanumeric characters with a single underscore
            transliterated_text = re.sub(r'[^a-zA-Z0-9]+', '_', transliterated_text)
            # Remove leading and trailing underscores
            transliterated_text = transliterated_text.strip('_')
            #Combine file name from compenents
            new_file_name_stem = f"{datetime.today().strftime('%Y%m%d#%H%M%S')}#{email_address_textbox}#{transliterated_text}"[0:68]

            #Prepare initial path
            format_suffix_of_user_uploaded_file = pathlib.Path(dir_orig_files_temps, uploaded_file.name).suffix
            originally_uploaded_file_fullname = pathlib.Path(dir_orig_files_temps, new_file_name_stem + format_suffix_of_user_uploaded_file)

            #Prepare New Protocol Record
            #TO DO - Get Shibboleth value of the institution here!!!
            new_order_record = [{'upload_timestamp': time.time(),
                                    'uploader_hash': mws_helpers.generate_hash(email_address_textbox),
                                    'duration_seconds': None,
                                    'file_size': None}]

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
            protocol = pd.read_csv(stats_protocol_file_path)
            #Concatanate protocol records
            result = pd.concat([protocol, new_record_df])
            #Save new state of the protocol
            result.to_csv(stats_protocol_file_path, index=False)
            
            #Send notification to Admin to let him know a new file has been uploaded for Transcription
            if configs['telegram']['use_telegram'] == True:
                mws_helpers.send_telegram_message(['BK'], f"{configs['texts']['general']['scripter_name']} - A file has been uploaded")
            
            #Success message for user
            st.success(f"{texts_from_config_file['upload_success_message_part_1']} {email_address_textbox}")
        else:
            print(st.error(texts_from_config_file['error_email_in_username'], icon="🚨"))

if __name__ == "__main__":
    main()