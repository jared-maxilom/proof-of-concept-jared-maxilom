import streamlit as st
import requests
import os
import time
from zipfile import ZipFile
from pytube import YouTube

st.title('🗣 **Speech-To-Text App**')
st.write("A trusty web tool to convert any YouTube video to text!")
# Custom functions 
def get_yt(URL):
    video = YouTube(URL)
    yt = video.streams.get_audio_only()
    yt.download()

def transcribe_yt():
        current_dir = os.getcwd()
        for file in os.listdir(current_dir):
            if file.endswith(".mp4"):
                mp4_file = os.path.join(current_dir, file)
        filename = mp4_file
        def read_file(filename, chunk_size=5242880):
                with open(filename, 'rb') as _file:
                    while True:
                        data = _file.read(chunk_size)
                        if not data:
                            break
                        yield data

        #Output a success response if the file is uploaded
        st.success('File Uploaded')

        # Upload audio file to AssemblyAI
        headers = {'authorization': api_key}
        response = requests.post('https://api.assemblyai.com/v2/upload',
                                headers=headers,
                                data=read_file(mp4_file))
        audio_url = response.json()['upload_url']

        # Transcribe uploaded audio file
        endpoint = "https://api.assemblyai.com/v2/transcript"

        json = {
            "audio_url": audio_url
        }

        headers = {
            "authorization": api_key,
            "content-type": "application/json"
        }

        transcript_input_response = requests.post(endpoint, json=json, headers=headers)

        # Extract transcript ID
        transcript_id = transcript_input_response.json()["id"]

        # Retrieve transcription results
        endpoint = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"
        headers = {
            "authorization": api_key,
        }
        transcript_output_response = requests.get(endpoint, headers=headers)

        st.warning('Transcription is processing ...')
        # Check if transcription is complete
        while transcript_output_response.json()['status'] != 'completed':
            time.sleep(5)
            transcript_output_response = requests.get(endpoint, headers=headers)
        
        # Print transcribed text
        st.header('Output')
        timestamped_text = []
        for utterance in transcript_input_response['utterances']:
            start_time = utterance['start_time']
            end_time = utterance['end_time']
            text = utterance['text']
            timestamped_text.append(f'[{start_time:.2f}-{end_time:.2f}] {text}')

        # Display the timestamped text
        st.header('Timestamped Text')
        st.markdown('\n'.join(timestamped_text))

        # Save transcribed text to file
        with open('yt.txt', 'w') as yt_txt:
            yt_txt.write(transcript_output_response.json()["text"])

        # Save as SRT file
        srt_endpoint = endpoint + "/srt"
        srt_response = requests.get(srt_endpoint, headers=headers)
        with open("yt.srt", "w") as _file:
            _file.write(srt_response.text)
        
        # Create zip file with transcriptions
        with ZipFile('transcription.zip', 'w') as zip_file:
            zip_file.write('yt.txt')
            zip_file.write('yt.srt')

# The App
# Read API from text file
api_key = st.secrets['api_key']

# Get YouTube video URL from user input

st.subheader('Paste your URL below')
with st.form('Input'):
    URL = st.text_input('Enter YouTube video URL:')
    button = st.form_submit_button(label='Transcribe')

if button:
    # Retrieve audio file from YouTube video
    get_yt(URL)
    # Transcribe YouTube audio file and save transcriptions to file
    transcribe_yt()

# Display link to download transcriptions
    with open("transcription.zip", "rb") as zip_download:
        btn = st.download_button(
            label="Download ZIP",
            data=zip_download,
            file_name="transcription.zip",
            mime="application/zip"
        )