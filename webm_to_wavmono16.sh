#!/bin/bash

converted_dir=converted_wavs

for file in "$@"
do
    if [[ ${file} != *.webm ]]
    then
        echo skipping ${file}
        break
    fi

    file_destination_dir=$(dirname "$file")/${converted_dir}
    file_path_end=$(basename "$file")
    file_destination=$file_destination_dir/${file_path_end/%webm/wav}
    mkdir -p "${file_destination_dir}"

    # ffmpeg -loglevel quiet -i "${file}" -acodec pcm_s16le -ac 1 -ar 16000 -vn -y "${file/%webm/wav}"
    ffmpeg -loglevel quiet -i "${file}" -acodec pcm_s16le -ac 1 -ar 16000 -vn -y "${file_destination}"

    if [ $? -ne 0 ]
    then
        echo conversion of ${file} failed
    fi
done

