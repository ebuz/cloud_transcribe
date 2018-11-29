import argparse
import io
import os.path
import glob
import csv
import pickle
import sys

# import wave
# import json
# import inspect


from cloud_transcribers import azure_transcribe_file, google_transcribe_file, watson_transcribe_file

parser = argparse.ArgumentParser()
parser.add_argument("audio_files_path", help = "The path to the audio files directory")
parser.add_argument("csv_output", help = "csv output file name")
parser.add_argument("pickle_output", help = "pickle output file name")

args = parser.parse_args()

wav_files = glob.glob(os.path.join(args.audio_files_path, '*.wav' ))

csv_file = open(args.csv_output, 'w')
csv_writer = csv.DictWriter(csv_file,
        fieldnames = ['filename', 'transcription', 'confidence', 'service'],
        extrasaction = 'ignore',
        dialect = 'excel')
csv_writer.writeheader()

pickle_file = open(args.pickle_output, 'wb')
pickle_writer = pickle.Pickler(pickle_file,
        protocol = pickle.HIGHEST_PROTOCOL)

transcribers = {
        'google': google_transcribe_file,
        # 'azure': azure_transcribe_file,
        'watson': watson_transcribe_file
        }

for wav in wav_files:
    speech_binary = io.open(wav, 'rb').read()
    for name,method in transcribers.items():
        try:
            result = {}
            result = method(speech_binary = speech_binary)
            csv_writer.writerow({'filename': wav, **result})
            pickle_writer.dump({'filename': wav, **result})
        except Exception as e:
            print('problem with {0} transcription for {1}'.format(name, wav))
            print('Error: {!s}'.format(e))

csv_file.close()
pickle_file.close()



# inspect.getmembers(google_result['raw_result'])
# [name for name,item in inspect.getmembers(google_result['raw_result'][0])]
# google_result['raw_result'].__dir__
# google_result['raw_result'][0].alternatives[0]



