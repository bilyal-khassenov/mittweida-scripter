#Import main packages
import pathlib, os, sys, time, datetime, shutil, torch, pandas, whisper, getpass, traceback
from mutagen.mp3 import MP3
from docx.enum.text import WD_COLOR_INDEX
from docx import Document
from docx.shared import Pt
######from docx.document import Document #Keep it for Intellisense!

#Import helper functions
import mws_helpers

#Central paths definition
new_line_for_f_strings = '\n'
dir_temp_orig_files = mws_helpers.ProjectPaths().temp_orig_file_path
dir_format_conversion = mws_helpers.ProjectPaths().folder_for_format_conversion_path
dir_in_progress = mws_helpers.ProjectPaths().in_progress_folder_path
dir_processed = mws_helpers.ProjectPaths().processed_folder_path
path_to_perf_protocol = mws_helpers.ProjectPaths().performance_protocol_fullfilename
dir_transcription_errors = mws_helpers.ProjectPaths().errors_folder_path
dir_unprocessed = mws_helpers.ProjectPaths().unprocessed_folder_path
configs = mws_helpers.get_configs()

def diarize_file(file_path):
    from pyannote.audio import Pipeline
    pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1")
    #Check if CUDA is available and if it is, send pipeline to GPU
    if torch.cuda.is_available():
        pipeline.to(torch.device("cuda"))
    #Apply pretrained pipeline
    diarization = pipeline(file_path)
    #Print the result
    speech_turns = []
    index = 0
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        speech_turns.append({'index' : index, 'start' : turn.start, 'end' : turn.end, 'speaker' : speaker})
        index = index + 1
        # print(f"start={turn.start:.1f}s stop={turn.end:.1f}s speaker_{speaker}")
    return speech_turns

def diarize_timestamped_words(conversation_turns, timestamped_words):
    for conversation_turn in conversation_turns:
        #First prepare list of all words marked as temporary acceptable or not for this speech turn
        for word in timestamped_words:
            word['start_acceptable'] = float(word['end']) > float(conversation_turn['start'])                               #Word must end after the start of conversation turn
            word['end_acceptable'] = float(word['start']) < float(conversation_turn['end'])                                 #Word must start before th end of conversation turn
            word['acceptance_result'] = word['start_acceptable'] == True and word['end_acceptable'] == True                 #Both previous conditions must be met
        #Collect conversation turn from individual words that were accepted for it
        conversation_turn_text = ''
        for word in timestamped_words:
            if word['acceptance_result'] == True:
                conversation_turn_text = conversation_turn_text + word['word']
        #Save the collected conversation turn text to the processed conversation turn
        conversation_turn['text'] = conversation_turn_text.strip()
    return conversation_turns

def transcribe_file(current_file_location_fullname):
    try:

        #Remember start time of the transcription process
        transcription_start_time = time.time()

        #Move original file to the "In Progress" folder
        file_in_in_progress_folder_fullname = os.path.join(dir_in_progress, pathlib.Path(current_file_location_fullname).name)
        os.replace(current_file_location_fullname, file_in_in_progress_folder_fullname)
        #Update the path
        current_file_location_fullname = file_in_in_progress_folder_fullname

        #Extract Language Code from Base Name
        language_code = mws_helpers.get_language_setting_index_or_code(int(os.path.basename(current_file_location_fullname).split('#', 7)[3]))
        #Extract Translation Status from Base Name
        translation_status = int(os.path.basename(current_file_location_fullname).split('#', 7)[4])
        translation_status = 'translate' if translation_status == 1 else None
        #Extract Diarization Setting form Base Name
        diarization_setting = int(os.path.basename(current_file_location_fullname).split('#', 7)[5])
        #Extract Selected Transcription Model from Base Name
        selected_transcription_model = mws_helpers.get_model_setting_index_or_name(int(os.path.basename(current_file_location_fullname).split('#', 7)[6]))
        
        #Retrieve data for protocol
        file_duration = MP3(current_file_location_fullname).info.length
        file_size = os.path.getsize(current_file_location_fullname)

        #Load the model
        if torch.cuda.is_available():
            whisper_model = whisper.load_model(selected_transcription_model).cuda().eval()  #CUDA available and will be used for transcribing
        else:
            whisper_model = whisper.load_model(selected_transcription_model)                #CUDA not available

        #Transcribe
        result = whisper_model.transcribe(current_file_location_fullname, verbose=True, word_timestamps=True, language=language_code, task=translation_status)

        #Prepare full name and create document
        new_file_name_stem = pathlib.Path(current_file_location_fullname).stem
        transcript_text_only_file_fullname = os.path.join(dir_processed, new_file_name_stem + '_text.docx')
        document_text_only = Document()
        #Change Docx Settings
        style = document_text_only.styles['Normal']
        font = style.font
        font.name = configs['ui_settings']['corporate_design_font']
        font.size = Pt(10)
        
        #Define confidence levels bounds
        high_confidence_level_lower_bound = configs['features']['high_confidence_level_lower_bound']
        average_confidence_level_lower_bound = configs['features']['average_confidence_level_lower_bound']

        #Add colors legend
        document_text_only.add_heading(configs['texts']['whisper']['docx_color_legends_label'])
        confidence_high_run = document_text_only.add_paragraph().add_run(f"Hohes Konfidenzniveau (> {high_confidence_level_lower_bound}): Text wird nicht farblich hervorgehoben.")
        confidence_average_run = document_text_only.add_paragraph().add_run(f"Mittleres Konfidenzniveau ({average_confidence_level_lower_bound} ≤ Wert ≤ {high_confidence_level_lower_bound}): Text wird gelb hervorgehoben.")
        confidence_average_run.font.highlight_color = WD_COLOR_INDEX.YELLOW
        confidence_low_run = document_text_only.add_paragraph().add_run(f"Niedriges Konfidenzniveau (< {average_confidence_level_lower_bound}): Text wird rot hervorgehoben.")
        confidence_low_run.font.highlight_color = WD_COLOR_INDEX.RED

        #Add heading
        document_text_only.add_heading(configs['texts']['whisper']['docx_text_only_title'])
        #Add colors explanation
        #Add new paragraph
        text_paragraph = document_text_only.add_paragraph()
        #Function for coloring
        def select_highlight_color(confidence_value):
            if confidence_value > high_confidence_level_lower_bound:
                return None
            elif average_confidence_level_lower_bound <= confidence_value <= high_confidence_level_lower_bound:
                return WD_COLOR_INDEX.YELLOW
            else:
                return WD_COLOR_INDEX.RED
        #Add Text Segments in Loop
        if "segments" in result:
            for segment in result["segments"]:
                if "words" in segment:
                    segment_confidency = segment['avg_logprob']
                    print(segment_confidency)
                    highlight_color = select_highlight_color(segment_confidency)
                    run_text = segment['text']
                    current_run = text_paragraph.add_run(run_text)
                    # Set the highlight color
                    current_run.font.highlight_color = highlight_color
        
        #Save file
        document_text_only.save(transcript_text_only_file_fullname)

        #Perform diarization conditionally
        if diarization_setting == 1:
            conversation_turns_diarized = diarize_file(current_file_location_fullname)
            #Normalize diarized turns
            normalized_and_diarized_turns = []
            counterchecked_turns = []
            processed_turns_indexes = []
            start_clipboarded = None
            end_clipboarded = None
            speaker_clipboarded = None
            for main_turn_checked in conversation_turns_diarized:               #Main normalization loop
                if not main_turn_checked['index'] in processed_turns_indexes:   #Check if this turn has already been normalized
                    start_clipboarded = main_turn_checked['start']              #In not, remember its starting time
                    end_clipboarded = main_turn_checked['end']                  #Remember its ending time
                    speaker_clipboarded = main_turn_checked['speaker']          #Remember its speaker
                    #Extract only unprocessed turns for counter-check
                    counterchecked_turns = []
                    for counterchecked_turn in conversation_turns_diarized:
                        if counterchecked_turn['index'] > main_turn_checked['index']:
                            counterchecked_turns.append(counterchecked_turn)
                    #Perform counter-check
                    for counterchecked_turn in counterchecked_turns:
                        if counterchecked_turn['speaker'] == main_turn_checked['speaker']:
                            end_clipboarded = counterchecked_turn['end']
                            processed_turns_indexes.append(counterchecked_turn['index'])
                        else:
                            processed_turns_indexes.append(main_turn_checked['index'])
                            break
                    #Protocol normalized turn
                    normalized_and_diarized_turns.append({'start' : start_clipboarded, 'end' : end_clipboarded, 'speaker' : speaker_clipboarded})

            #Prepare word-level timestamps
            timestamped_words = []
            for segment in result['segments']:
                for word in segment['words']:
                    timestamped_words.append({'word' : word['word'], 'start' : word['start'], 'end' : word['end']})

            #Assign words to conversation turns
            completed_conversation_turns = diarize_timestamped_words(normalized_and_diarized_turns, timestamped_words)
            
            #Save conversation turns to a Docx File
            def convert_secs_to_timestamp(seconds):
                seconds_in_hours = seconds/3600    
                timestamp = str(datetime.timedelta(hours=seconds_in_hours))[:10]
                if len(timestamp) == 7:
                    timestamp = timestamp + '.00'
                return timestamp
            transcript_conversation_turns_file_fullname = os.path.join(dir_processed, new_file_name_stem + '_conversation_turns.docx')
            #Create Docx file
            document_conversation_turns = Document()
            #Change Docx Settings
            style = document_conversation_turns.styles['Normal']
            font = style.font
            font.name = configs['ui_settings']['corporate_design_font']
            font.size = Pt(10)
            #Add heading
            document_conversation_turns.add_heading(configs['texts']['whisper']['docx_text_conversation_turns_title'])
            #Add all conversation turns
            for conversation_turn in completed_conversation_turns:
                p = document_conversation_turns.add_paragraph('')                                                                                                                           #Add empty speaker line
                p.add_run(f"{conversation_turn['speaker']} -> {convert_secs_to_timestamp(conversation_turn['start'])}-{convert_secs_to_timestamp(conversation_turn['end'])}").bold = True   #Now add bold text in this speaker line
                document_conversation_turns.add_paragraph(f"{conversation_turn['text']}")                                                                                                   #And now add the text of this concersation turn
                document_conversation_turns.add_paragraph('')                                                                                                                               #And here a new line
            document_conversation_turns.save(transcript_conversation_turns_file_fullname)
        else:
            transcript_conversation_turns_file_fullname = None

        #Delete the original file
        pathlib.Path.unlink(current_file_location_fullname)
        
        #Get ending time of the transcription
        transcription_end_time = time.time()
        #Prepare new line for the performance stats
        language_code_for_protocol = '--' if language_code is None else language_code
        translation_status_for_protocol = 'translate' if translation_status == "translate" else 'original'
        new_perf_record = [{
            'model' : selected_transcription_model,
            'language_code' : language_code_for_protocol,
            'translation_status' : translation_status_for_protocol,
            'diarization_status' : diarization_setting,
            'duration_seconds' : file_duration,
            'file_size' : file_size,
            'transcription_start_time' : transcription_start_time,
            'transcription_end_time' : transcription_end_time,
            'transcription_time_per_one_raw_second' : (transcription_end_time - transcription_start_time)/file_duration
        }]
        #Create a dataframe of this dictionary
        new_perf_record_df = pandas.DataFrame(new_perf_record)
        #Transform this line to a dataframe
        perf_protocol = pandas.read_csv(path_to_perf_protocol, encoding='Windows-1252')
        #Concatanate both frames
        result = pandas.concat([perf_protocol, new_perf_record_df])
        #Save new state of the protocol
        result.to_csv(path_to_perf_protocol, encoding='Windows-1252', index=False)
        return [transcript_text_only_file_fullname, transcript_conversation_turns_file_fullname]
    except Exception as e:
        #Get exception infos
        error_string = traceback.format_exc()
        error_message_for_admins = f"({getpass.getuser()}) - {error_string}"
        if configs['telegram']['use_telegram'] == True:
            mws_helpers.send_telegram_message(configs['telegram']['admin_chat_id'], error_message_for_admins)
        print(error_message_for_admins)
        
        #Delete the original file - to-do for later: protocolling mail addresses of user whose files resulted in error?
        pathlib.Path.unlink(current_file_location_fullname)
        if configs['telegram']['use_telegram'] == True:
            mws_helpers.send_telegram_message(configs['telegram']['admin_chat_id'], f"({getpass.getuser()}) File that resulted in error has been deleted")

def process_file(fullname_of_next_unprocessed_file):
    import ffmpeg
    #First convert to an .mp3 in any case to have a standardized form of .mp3
    file_to_convert_name_stem = pathlib.Path(fullname_of_next_unprocessed_file).stem
    standardized_audio_temp_location = os.path.join(dir_format_conversion, file_to_convert_name_stem + '.mp3')  #Prepare path for the final audio file
    stream = ffmpeg.input(fullname_of_next_unprocessed_file)
    stream = ffmpeg.output(stream, standardized_audio_temp_location)
    ffmpeg.run(stream)
    #Delete Originally uploaded file
    pathlib.Path.unlink(fullname_of_next_unprocessed_file)
    #Move audio file to uprocessed folder
    ready_audio_file_location = pathlib.Path(dir_unprocessed, file_to_convert_name_stem + '.mp3')
    os.replace(standardized_audio_temp_location, ready_audio_file_location)
    
    try:
        #Get starting time
        loop_start_time = time.time()

        #Start transcription
        transcription_result_paths = transcribe_file(ready_audio_file_location)
        transcript_text_only_file_fullname = transcription_result_paths[0]
        transcript_conversation_turns_file_fullname = transcription_result_paths[1]

        #Get finish time
        loop_finish_time = time.time()
        elapsed_time = loop_finish_time - loop_start_time
        time_used_to_transcribe = str(datetime.timedelta(seconds=elapsed_time))

        #Prepare message
        if transcript_conversation_turns_file_fullname is not None:
            email_text = configs['texts']['whisper']['email_text_two_files']
        else:
            email_text = configs['texts']['whisper']['email_text_one_file']

        #Extract Email Address and File Name from Base Name (Last Path Component)
        email_address = os.path.basename(transcript_text_only_file_fullname).split('#', 7)[2]
        file_name = os.path.basename(transcript_text_only_file_fullname).split('#', 7)[7]

        #Prepare E-Mail subject
        subject_ready = f"{configs['texts']['whisper']['email_subject']}: {file_name}"
        if len(subject_ready) > 75: 
            email_subject = subject_ready[:75] + '...'
        else:
            email_subject = subject_ready

        #Prepare attachments
        if transcript_conversation_turns_file_fullname is not None:
            attachments = [transcript_text_only_file_fullname, transcript_conversation_turns_file_fullname]
        else:
            attachments = [transcript_text_only_file_fullname]

        #Send the results of transcribing
        try:
            mws_helpers.send_mail(configs['email']['noreply_email'], [email_address], email_subject, email_text, attachments)
        except Exception as e:
            if configs['telegram']['use_telegram'] == True:
                mws_helpers.send_telegram_message(configs['telegram']['admin_chat_id'], f"({getpass.getuser()}) - Transcription was successfull, but an error occured when we tried to send an email")
            e_type, e_object, e_traceback = sys.exc_info()
            e_line_number = e_traceback.tb_lineno
            error_message_for_admins = f"({getpass.getuser()}) - Following error happened when trying to send the email: {e.__class__.__name__}.{new_line_for_f_strings}{new_line_for_f_strings}Error araised on line: {e_line_number}{new_line_for_f_strings}{new_line_for_f_strings}{e}"
            if configs['telegram']['use_telegram'] == True:
                mws_helpers.send_telegram_message(configs['telegram']['admin_chat_id'], error_message_for_admins)
            #Copy transcription results to local testings folder
            if transcript_conversation_turns_file_fullname is not None:
                files_list = [transcript_text_only_file_fullname, transcript_conversation_turns_file_fullname]
            else:
                files_list = [transcript_text_only_file_fullname]
            #####files_list = [transcript_text_only_file_fullname, transcript_conversation_turns_file_fullname] if transcript_conversation_turns_file_fullname is not None else [transcript_text_only_file_fullname]
            for results_file in files_list:
                try:
                    # Copy the file
                    shutil.copy(results_file, os.path.join(mws_helpers.ProjectPaths().local_tests_folder_path, os.path.basename(results_file)))
                except FileNotFoundError:
                    print("Source file not found!")
                except PermissionError:
                    print("Permission denied!")
                except Exception as e:
                    print(f"An error occurred: {e}")

        #Delete Word files after sending them
        pathlib.Path.unlink(transcript_text_only_file_fullname)
        if transcript_conversation_turns_file_fullname is not None:
            pathlib.Path.unlink(transcript_conversation_turns_file_fullname)
    except Exception as e:
        #Get exception infos
        error_string = traceback.format_exc()
        error_message_for_admins = f"({getpass.getuser()}) - {error_string}"
        if configs['telegram']['use_telegram'] == True:
            mws_helpers.send_telegram_message(configs['telegram']['admin_chat_id'], error_message_for_admins)

def main():
    from multiprocessing import Process

    #Infinite Loop
    while 1 < 2:
        #Define seconds to sleep
        seconds = 10
        #If there are less than 2 videos currently in progress, then check if there are any new uploaded files to start new transcription process
        count_files_in_proggress, _ = mws_helpers.count_and_list_files(dir_in_progress)
        if count_files_in_proggress < configs['features']['max_files_processed_simultaneously']:
            #List unprocessed files
            count_unprocessed, unprocessed_files = mws_helpers.count_and_list_files(dir_temp_orig_files)

            # Get the name of the next unprocessed file
            if count_unprocessed >= 1:
                fullname_of_next_unprocessed_file = unprocessed_files[0]
                another_daemon_process = Process(target=process_file, args=(fullname_of_next_unprocessed_file,))
                another_daemon_process.daemon = True
                another_daemon_process.start()
                print(f"Something has been loaded and we created a new daemon process for it! Let's sleep again for {seconds} seconds till the next check...")
            else:
                print(f"Well... Nothing was loaded in the meanwhile! Let's sleep again for {seconds} seconds till the next check...")
        time.sleep(seconds)

if __name__ == "__main__":
    main()