import re
import json

chars_path = 'chars_merged_short.json'
hans_path = 'qn2hans_del.json'

with open(chars_path,'r',encoding='utf-8') as f:
    chars_dict = json.load(f)
with open(hans_path,'r',encoding='utf-8') as f:
    hans_dict = json.load(f)

template = '''Translate the following Vietnamese text written in Quốc Ngữ into Nôm script. Below is the text in Quốc Ngữ with its Chinese translation. Sometimes the Quốc Ngữ Text only corresponds to a portion of the Chinese translation. For each word in Quốc Ngữ, I will provide possible Nôm script representations (including both native Nôm characters and Han Việt/Sino-Vietnamese characters) with example phrases. Use this information to produce the accurate Nôm script translation.

Quốc Ngữ Text: {viet_text}
Chinese Translation: {chinese_translation}

Please find the possible Nôm script candidates for each word in the Quốc Ngữ text:
{word_details}

Your task is to choose the most suitable Nôm script for each word based on its meaning in the context of the entire text.
If a word has no Nôm script candidates provided, keep the original word as is.
For proper nouns such as person names and place names, refer to the Chinese translation to select candidates - the appropriate choice is typically the traditional Chinese characters corresponding to that proper noun.
Nôm script does not require spaces between characters. Please use full-width punctuation marks, including ，。……“”：；！？（）【】

Output the complete Nôm script translation of the given Quốc Ngữ text in JSON format:
```json
{{
    "quoc_ngu": "{viet_text}"
    "chu_nom": "Nôm script here."
}}
```'''

def normalize_qn(qn):
    TONE_MAP = {
        'òa': 'oà',
        'óa': 'oá',
        'ỏa': 'oả',
        'õa': 'oã',
        'ọa': 'oạ',
        'òe': 'oè',
        'óe': 'oé',
        'ỏe': 'oẻ',
        'õe': 'oẽ',
        'ọe': 'oẹ',
        'ùy': 'uỳ',
        'úy': 'uý',
        'ủy': 'uỷ',
        'ũy': 'uỹ',
        'ụy': 'uỵ'
    }
    for key, value in TONE_MAP.items():
        if qn.endswith(key):
            return qn[:-len(key)] + value
    return qn

def swap_yi(qn):
    swap_dict = {
        'y': 'i',
        'i': 'y',
        'ý': 'í',
        'í': 'ý',
        'ỳ': 'ì',
        'ì': 'ỳ',
        'ỷ': 'ỉ',
        'ỉ': 'ỷ',
        'ỹ': 'ĩ',
        'ĩ': 'ỹ',
        'ỵ': 'ị',
        'ị': 'ỵ'
    }
    last_char = qn[-1]
    new_char = swap_dict.get(last_char, last_char)
    return qn[:-1] + new_char

def quoc_ngu_in_dict(qn, dict):
    qn = normalize_qn(qn)
    if qn in dict:
        return dict[qn]
    qn = swap_yi(qn)
    if qn in dict:
        return dict[qn]
    return None

def generate_prompt(vi_text, zh_text):
    word_details_list = []
    words = re.findall(r'\b\w+\b', vi_text)
    nom_options = []
    for word in words:
        representations_list = []
        word_lower = word.lower()
        noms = []
        meanings_list = quoc_ngu_in_dict(word_lower, chars_dict)
        if meanings_list is not None:
            noms.extend([n['char'] for n in meanings_list])
            for _, nom in enumerate(meanings_list, start=1):
                representations_list.append(f'     - {nom["char"]} : {nom["words"]}')
        hans_list = quoc_ngu_in_dict(word_lower, hans_dict)
        if hans_list is not None:
            noms.extend(hans_list)
            representations_list.append('     - Other Han Việt characters : ' + ', '.join(hans_list))
        if len(noms) > 0:
            nom_options.append([word, noms])
        if len(representations_list) > 0:
            word_detail = f'{len(word_details_list)+1}. Quốc Ngữ Word: {word}\n' + '\n'.join(representations_list)
            word_details_list.append(word_detail)

    word_details = '\n\n'.join(word_details_list)
    prompt_filled = template.format(
        viet_text=vi_text,
        chinese_translation=zh_text,
        word_details=word_details
    )
    prompt_filled = prompt_filled.replace('※𡨸翻音', '※Phonetic transcription character')
    return prompt_filled, nom_options
