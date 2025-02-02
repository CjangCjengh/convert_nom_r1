import os
import re
import json
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from langchain_openai import ChatOpenAI
import hashlib
from tqdm import tqdm
from cv_template import generate_prompt

json_dir = 'json'
result_dir = 'result'
cache_dir = 'cache/r1_q1'
convert_front_n = 100

os.makedirs(result_dir, exist_ok=True)
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

def parse_json(response):
    json_matches = re.findall(r'```json(.*?)```', response, re.DOTALL)
    if len(json_matches) > 0:
        return json_matches[-1]
    json_matches = re.findall(r'```(.*?)```', response, re.DOTALL)
    if len(json_matches) > 0:
        return json_matches[-1]
    json_matches = re.findall(r'\{.*?\}', response, re.DOTALL)
    if len(json_matches) > 0:
        return json_matches[-1]
    return None

def get_response(prompt):
    md5_cache = calculate_md5(prompt)
    cache_path = f'{cache_dir}/{md5_cache}.txt'
    if os.path.exists(cache_path):
        with open(cache_path,'r',encoding='utf-8') as f:
            response = f.read()
    else:
        response = stream_generate(prompt)
        with open(cache_path,'w',encoding='utf-8') as f:
            f.write(response.strip())
    json_str = parse_json(response)
    json_data = json.loads(json_str)
    assert type(json_data['chu_nom']) == str
    return json_data

def check_nom_script(nom_text, nom_options):
    nom_groups = [v for v in nom_options.values()]
    group_ptr = 0
    for c in nom_text:
        if c in nom_groups[group_ptr]:
            group_ptr += 1
            if group_ptr == len(nom_groups):
                return True
    return False

def align_vi_nom(vi_text, nom_text):
    if (vi_text.startswith('“') or vi_text.startswith('"')) and not nom_text.startswith('“'):
        nom_text = '“' + nom_text
    if (vi_text.endswith('”') or vi_text.endswith('"')) and not nom_text.endswith('”'):
        nom_text += '”'
    if vi_text.startswith('(') and not nom_text.startswith('（'):
        nom_text = '（' + nom_text
    if vi_text.endswith(')') and not nom_text.endswith('）'):
        nom_text += '）'
    return nom_text

def get_nom_text(vi_text, zh_text):
    prompt, nom_options = generate_prompt(vi_text, zh_text)
    result = get_response(prompt)
    nom_text = result['chu_nom']
    assert check_nom_script(nom_text, nom_options)
    nom_text = align_vi_nom(vi_text, nom_text)
    return nom_text

def split_at_punctuation(text: str) -> tuple[str, str]:
    punctuation_marks = [',', '.', '!', '"', '?', '\'', '”', '—', '…', '’']
    mid_point = len(text) // 2

    punctuation_positions = []
    for i, char in enumerate(text):
        if char in punctuation_marks:
            end_pos = i
            while end_pos + 1 < len(text) and text[end_pos + 1] in punctuation_marks:
                end_pos += 1
            punctuation_positions.append(end_pos)
    
    if not punctuation_positions:
        return text[:mid_point], text[mid_point:]

    split_pos = min(punctuation_positions, key=lambda x: abs(x - mid_point))
    
    return text[:split_pos + 1].strip(), text[split_pos + 1:].strip()

def process_with_split(vi_text: str, zh_text: str) -> str:
    try:
        return get_nom_text(vi_text, zh_text)
    except ValueError as e:
        assert e.args[0] == 'No generation chunks were returned'
        first_half, second_half = split_at_punctuation(vi_text)
        first_result = process_with_split(first_half, zh_text)
        second_result = process_with_split(second_half, zh_text)
        return first_result + second_result


novel_files = os.listdir(json_dir)
novel_files.sort()
for novel in novel_files:
    if not novel.endswith('.json'):
        continue
    print(novel)
    with open(f'{json_dir}/{novel}','r',encoding='utf-8') as f:
        novel_data = json.load(f)

    result_path = f'{result_dir}/{novel}'
    nom_pairs = []
    start_idx = 0
    if os.path.exists(result_path):
        with open(result_path,'r',encoding='utf-8') as f:
            nom_pairs = json.load(f)
            start_idx = len(nom_pairs)

    for item in tqdm(novel_data[start_idx:convert_front_n]):
        zh_text = item['zh'].replace('\n', '')
        vi_text = item['vi'].replace('\n', ' ')
        try:
            nom_text = process_with_split(vi_text, zh_text)
        except:
            nom_text = ''
        nom_pairs.append({'zh': item['zh'], 'nom': nom_text})
        with open(result_path, 'w', encoding='utf-8') as f:
            json.dump(nom_pairs, f, ensure_ascii=False, indent=0)
