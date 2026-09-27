import argparse
import random
import openai
import uuid
import json
import os

# define supported languages
SUPPORTED_LANGUAGES = [
    'simple_chinese',
    'traditional_chinese',
    'english',
    'american_english',
    'spanish',
    'french',
    'german',
    'japanese',
    'korean',
    'italian',
    'russian',
]

# utils function: random_languages
def random_select_languages(count: int=None, exclude: list=[]) -> list[str]:
    '''
    Random select count languages from SUPPORTED_LANGUAGES
    If count is None, will shuffle all languages in SUPPORTED_LANGUAGES
    '''
    select_range = SUPPORTED_LANGUAGES.copy()
    for language in exclude:
        if language in select_range:
            select_range.remove(language)
    
    real_count = len(select_range)

    if count and count > real_count:
        raise IndexError(f'count {count} must be less than {real_count}')
    elif count is None or count == real_count:
        random.shuffle(select_range)
        return select_range, real_count
    else:
        return random.sample(select_range, real_count), real_count

# utils function: translate_text
def translate_text(
    content: str,
    client: openai.OpenAI,
    openai_args: dict,
    source_language: str,
    target_language: str,
) -> openai.Stream:
    '''Translate text to target language'''
    messages = [
        {'role': 'system', 'content': f'你是一个专业的翻译, 结果为文本, 不包含引号、解释等其他内容'},
        {'role': 'user', 'content': f'请将 "{content}" (不含引号) 从 {source_language} 翻译成 {target_language}'},
    ]
    return client.chat.completions.create(
        **openai_args,
        messages=messages,
        stream=True,
    )

# core function: multi_translat
def multi_translat(
    model: dict,
    source_text: str,
    source_language: str,
    target_language: str,
    count: int=None,
) -> tuple[str, list[dict]]:
    '''Translate text to many times'''
    # 1. init openai client
    client = openai.OpenAI(
        api_key=model['api_key'],
        base_url=model['base_url'],
    )

    # 2. select languages
    real_count = count - 1 if count else count
    languages, real_count = random_select_languages(real_count, [source_language, target_language])

    # 3. len of count and len of the longest language name
    count_len = len(str(real_count))
    max_language_len = max(len(language) for language in [*languages, source_language, target_language])

    # 4. init logs
    logs = []
    logs_txt = ''

    def get_start_log(now_count: int, language: str) -> str:
        return f'[{now_count:{count_len}}/{real_count} {language:{max_language_len}}]'

    def log(now_count: int, language: str, text: str, need_print: bool=False):
        nonlocal logs, logs_txt
        logs.append({'language': language, 'text': text})
        logs_txt += f'{get_start_log(now_count, language)} {text}\n'
        if need_print:
            print(f'{get_start_log(now_count, language)} {text}')

    # 4. translate text
    now_text = source_text
    now_language = source_language

    log(0, source_language, source_text, need_print=True)
    for now_count, language in enumerate([*languages, target_language], 1):
        print(f'{get_start_log(now_count, language)} ', end='', flush=True)

        response = ''
        for chunk in translate_text(
            content=now_text,
            client=client,
            openai_args=model['args'],
            source_language=now_language,
            target_language=language,
        ):
            if hasattr(chunk, 'choices') and chunk.choices \
                and hasattr(chunk.choices[0], 'delta') and chunk.choices[0].delta:
                if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content:
                    chunk_text = chunk.choices[0].delta.content
                    if chunk_text:
                        print(chunk_text, end='', flush=True)
                        response += chunk_text
                # if hasattr(chunk.choices[0].delta, 'reasoning_content') and chunk.choices[0].delta.reasoning_content:
                #     chunk_text = chunk.choices[0].delta.reasoning_content
                #     if chunk_text:
                #         print(chunk_text, end='', flush=True)
                #         response += chunk_text

        print()
        now_text = response
        now_language = language
        log(now_count, language, response)

    return now_text, logs, logs_txt

def main():
    parser = argparse.ArgumentParser(description='Translate text to many times')
    parser.add_argument('source_text', type=str, help='source text')
    parser.add_argument('-s', '--source_language', type=str, default='simple_chinese', help='source language')
    parser.add_argument('-t', '--target_language', type=str, default='simple_chinese', help='target language')
    parser.add_argument('-c', '--count', type=int, default=None, help='count of times to translate')
    parser.add_argument('-m', '--model', type=str, default='model', help='model\'s name in models/')

    args = parser.parse_args()

    with open(os.path.join('models', args.model + '.json'), 'r', encoding='utf-8') as f:
        model = json.load(f)

    log_dir = 'logs'
    log_file_dir = f'{log_dir}/data'
    os.makedirs(log_file_dir, exist_ok=True)
    index_file = f'{log_dir}/index.json'

    final_text, logs, logs_txt = multi_translat(model, args.source_text, args.source_language, args.target_language, args.count)

    try:
        with open(index_file, 'r', encoding='utf-8') as f:
            index = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        index = {}

    data_id = uuid.uuid4().hex

    index[data_id] = {
        'source_text': args.source_text,
        'source_language': args.source_language,
        'target_language': args.target_language,
        'count': args.count,
        'final_text': final_text,
        'model': model['args']['model'],
    }

    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=4)

    with open(os.path.join(log_file_dir, f'{data_id}.json'), 'w', encoding='utf-8') as f:
        json.dump(logs, f, ensure_ascii=False, indent=4)
    
    with open(os.path.join(log_file_dir, f'{data_id}.txt'), 'w', encoding='utf-8') as f:
        f.write(logs_txt)

if __name__ == '__main__':
    main()