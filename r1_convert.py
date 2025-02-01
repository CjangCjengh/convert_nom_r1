import os
import json
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from langchain_openai import ChatOpenAI
import hashlib
from tqdm import tqdm
from cv_template import generate_prompt

json_dir = 'json'
cache_dir = 'cache/r1_q1'
convert_front_n = 100

os.makedirs(cache_dir, exist_ok=True)

os.environ['OPENAI_API_KEY'] = 'none'
os.environ['OPENAI_API_BASE'] = 'http://127.0.0.1:54321/v1'
llm = ChatOpenAI(model_name='DeepSeek-R1-GGUF/DeepSeek-R1-UD-IQ1_S/DeepSeek-R1-UD-IQ1_S-00001-of-00003.gguf')

def stream_generate(prompt: str) -> str:
    messages = [HumanMessage(content=prompt)]
    full_response = ''
    for chunk in llm.stream(messages):
        content_chunk = chunk.content
        print(content_chunk, end='', flush=True)
        full_response += content_chunk
    print()
    return full_response

def calculate_md5(input_string):
    md5_object = hashlib.md5()
    md5_object.update(input_string.encode('utf-8'))
    md5_hash = md5_object.hexdigest()
    return md5_hash


for novel in os.listdir(json_dir):
    if not novel.endswith('.json'):
        continue
    print(novel)
    with open(f'{json_dir}/{novel}','r',encoding='utf-8') as f:
        novel_data = json.load(f)
    for item in tqdm(novel_data[:convert_front_n]):
        zh_text = item['zh'].replace('\n', '')
        vi_text = item['vi'].replace('\n', ' ')
        prompt = generate_prompt(vi_text, zh_text)
        md5_cache = calculate_md5(prompt)
        cache_path = f'{cache_dir}/{md5_cache}.txt'
        if os.path.exists(cache_path):
            continue
        else:
            try:
                response = stream_generate(prompt)
            except ValueError:
                continue
            with open(cache_path,'w',encoding='utf-8') as f:
                f.write(response.strip())
