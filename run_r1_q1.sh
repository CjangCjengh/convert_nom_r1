llama-server \
    --model DeepSeek-R1-GGUF/DeepSeek-R1-UD-IQ1_S/DeepSeek-R1-UD-IQ1_S-00001-of-00003.gguf \
    --cache-type-k q4_0 \
    --threads 12 --prio 2 \
    --temp 0.8 \
    --ctx-size 8192 \
    --n-gpu-layers 80 \
    --host 0.0.0.0 \
    --port 54321
