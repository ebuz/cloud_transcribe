import io
import json
from os.path import join, dirname
import requests
import configparser

from requests.auth import AuthBase

config = configparser.ConfigParser()
config.read('api_keys')

normalized_transcription = {'transcription': '',
        'service': '',
        'raw_result': {}
        }

class AzureAuth(AuthBase):
    """Attaches HTTP Azure Authentication to the given Request object."""
    azure_auth_headers = {
            'Content-type': 'application/x-www-form-urlencoded',
            'Content-Length': '0',
            }

    def __init__(self, auth_url, api_key):
        # setup any auth-related data here
        self.api_key = api_key
        token = requests.post(
                auth_url,
                headers = {**azure_auth_headers,
                    'Ocp-Apim-Subscription-Key': configure['azure']['api_key']})
        self.session_token = token.text

    def __call__(self, r):
        # modify and return the request
        r.headers['Authorization'] = 'Bearer ' + self.session_token
        return r

def azure_transcribe_file(speech_file = None, speech_binary = None, credentials = config['azure']['api_key'], url = config['azure']['speech_url'], auth_url = config['azure']['auth_url']):
    assert speech_file is not None or speech_binary is not None
    assert credentials is not None
    assert url is not None

    azure_headers = {
            'Accept': 'application/json',
            'Content-type': 'audio/wav; codec=audio/pcm; samplerate=16000'
            }

    azure_headers['Ocp-Apim-Subscription-Key'] = credentials

    azure_speech_params = {
            'language': 'en-US',
            'locale': 'en-US',
            'format': 'detailed',
            'profanity': 'raw'
            }

    response = None
    transcript = {'transcription': None,
        'confidence': None,
        'service': 'azure',
        'raw_result': None
        }
    speech_data = speech_binary

    if speech_file is not None:
        with io.open(speech_file, 'rb') as audio_file:
            speech_data = audio_file.read()

    if speech_data is not None:
        response = requests.post(url,
                params = azure_speech_params,
                data = speech_data,
                headers = azure_headers #, auth = AzureAuth(auth_url, credentials)
                ).json()

    if response is not None and response['RecognitionStatus'] == 'Success':
        transcript['transcription'] = response['NBest'][0]['Lexical']
        transcript['confidence'] = response['NBest'][0]['Confidence']
        transcript['raw_result'] = response

    return transcript

def convert_google_results(results):
    converted_results = []
    for result in results:
        converted_result = {'alternatives': []}
        for alternative in result.alternatives:
            converted_alternative = {
                    'transcript': alternative.transcript,
                    'confidence': alternative.confidence
                    }
            if hasattr(alternative, 'words'):
                converted_alternative['words'] = []
                for word in alternative.words:
                    converted_word = {'word': word.word,}
                    converted_word['start_time'] = {
                            'seconds': word.start_time.seconds,
                            'nanos': word.start_time.nanos}
                    converted_word['end_time'] = {
                            'seconds': word.end_time.seconds,
                            'nanos': word.end_time.nanos}
                    converted_alternative['words'].append(converted_word)
            converted_result['alternatives'].append(converted_alternative)
        converted_results.append(converted_result)
    return converted_results

def google_transcribe_file(speech_file = None, speech_binary = None, hints = [], credentials_file = config['google']['credentials_file']):
    assert speech_file is not None or speech_binary is not None
    assert credentials_file is not None

    """Transcribe the given audio file or binary."""
    from google.cloud import speech
    from google.cloud.speech import enums
    from google.cloud.speech import types

    client = speech.SpeechClient.from_service_account_json(credentials_file)

    response = None
    transcript = {'transcription': None,
        'confidence': None,
        'service': 'google',
        'raw_result': None
        }
    speech_data = speech_binary

    if speech_file is not None:
        with io.open(speech_file, 'rb') as audio_file:
            speech_data = audio_file.read()

    if speech_data is not None:
        audio = types.RecognitionAudio(content = speech_data)
        config = types.RecognitionConfig(
            encoding = enums.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz = 16000,
            enable_word_time_offsets = True,
            max_alternatives = 3,
            speech_contexts = [speech.types.SpeechContext(
                phrases = hints,
                )],
            language_code = 'en-US')
        response = client.recognize(config, audio)


    if response is not None and response.results is not None:
        # response.results <- [
        #         {alternatives <- [
        #             {transcript, confidence, words <- []}, ]
        #             }, ]
        transcript['transcription'] = response.results[0].alternatives[0].transcript.strip()
        transcript['confidence'] = response.results[0].alternatives[0].confidence
        transcript['raw_result'] = json.dumps(convert_google_results(response.results))

    return transcript

def watson_transcribe_file(speech_file = None, speech_binary = None, credentials = config['watson']['api_key'], url = config['watson']['speech_url']):
    assert speech_file is not None or speech_binary is not None
    assert credentials is not None
    assert url is not None

    """Transcribe the given audio file or binary."""
    from watson_developer_cloud import SpeechToTextV1
    from watson_developer_cloud.websocket import RecognizeCallback, AudioSource

    client = SpeechToTextV1(iam_apikey = credentials,
        url = url)

    response = None
    transcript = {'transcription': None,
        'confidence': None,
        'service': 'watson',
        'raw_result': None
        }
    speech_data = speech_binary

    if speech_file is not None:
        with io.open(speech_file, 'rb') as audio_file:
            speech_data = audio_file.read()

    if speech_data is not None:
        response = client.recognize(
                audio = speech_data,
                content_type = 'audio/wav',
                model = 'en-US_BroadbandModel',
                word_confidence = True).get_result()

    if response is not None:
        transcript['transcription'] = response['results'][0]['alternatives'][0]['transcript'].strip()
        transcript['confidence'] = response['results'][0]['alternatives'][0]['confidence']
        transcript['raw_result'] = json.dumps(response['results'])

    return transcript
