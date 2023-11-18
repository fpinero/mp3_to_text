import boto3
from docx import Document
import sys
import time
import urllib.parse


def upload_file_to_s3(file_path, bucket_name):
    s3_client = boto3.client('s3')
    try:
        response = s3_client.upload_file(file_path, bucket_name, file_path)
        return f's3://{bucket_name}/{file_path}'
    except Exception as e:
        print(e)
        sys.exit()


def start_transcription_job(file_uri, transcribe_client):
    job_name = "TranscriptionJob_" + str(int(time.time()))
    transcribe_client.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={'MediaFileUri': file_uri},
        MediaFormat='mp3',
        LanguageCode='en-US'
    )
    return job_name


def get_transcription_result(job_name, transcribe_client):
    while True:
        status = transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
        if status['TranscriptionJob']['TranscriptionJobStatus'] in ['COMPLETED', 'FAILED']:
            break
        print("Waiting for transcription to complete...")
        time.sleep(10)

    if status['TranscriptionJob']['TranscriptionJobStatus'] == 'COMPLETED':
        response = urllib.request.urlopen(status['TranscriptionJob']['Transcript']['TranscriptFileUri'])
        return response.read().decode('utf-8')
    return None


def save_transcription_to_docx(transcription, output_file):
    doc = Document()
    doc.add_paragraph(transcription)
    doc.save(output_file)


def convert_mp3_to_docx():
    file_path = input("Please enter the path to the MP3 file or type 'exit' to abort: ")
    if file_path.lower() == 'exit':
        print('Program aborted by the user.')
        sys.exit()

    # Configura aquí tu bucket de S3
    s3_bucket_name = 'your-s3-bucket-name'
    s3_uri = upload_file_to_s3(file_path, s3_bucket_name)

    transcribe_client = boto3.client('transcribe')
    job_name = start_transcription_job(s3_uri, transcribe_client)

    print("Transcription job started...")
    transcription = get_transcription_result(job_name, transcribe_client)

    if transcription:
        docx_output = file_path.rsplit('.', 1)[0] + '.docx'
        save_transcription_to_docx(transcription, docx_output)
        print(f'Transcription completed. DOCX output saved as {docx_output}')
    else:
        print("Transcription failed.")


convert_mp3_to_docx()
