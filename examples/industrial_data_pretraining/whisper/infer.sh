# Copyright FunASR (https://github.com/alibaba-damo-academy/FunASR). All Rights Reserved.
#  MIT License  (https://opensource.org/licenses/MIT)

# method1, inference from model hub

# for more input type, please ref to readme.md
input="https://isv-data.oss-cn-hangzhou.aliyuncs.com/ics/MaaS/ASR/test_audio/asr_example_zh.wav"

output_dir="./outputs/debug"

model="iic/speech_whisper-large_asr_multilingual"
model_revision="v2.0.4"

device="cuda:0" # "cuda:0" for gpu0, "cuda:1" for gpu1, "cpu"

python -m funasr.bin.inference \
++model=${model} \
++model_revision=${model_revision} \
++input="${input}" \
++output_dir="${output_dir}" \
++device="${device}" \
