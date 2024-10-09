import json
import os
import sys
import src.preprocessing as preprocessing
from tqdm.autonotebook import tqdm





if __name__ == '__main__':

    entry_data_path = sys.argv[1]

    os.mkdir('entry_data_token_by_section')

    for document_name in tqdm(os.listdir(entry_data_path)):
        document = json.load(open(os.path.join(entry_data_path, document_name)))
        sections = preprocessing.split_by_section(document['main_text'], document['toc'], document['title'])
        document_name = document_name.split('.')[0]
        for i, (k, v)in enumerate(sections.items()):
            v['tokenized_text'] = preprocessing.preprocess_text(v['main_text'])

            with open(f'entry_data_token_by_section/{document_name}_{i}.json', 'w') as f:
                json.dump(v, f, indent=4)
        

    for document_name in tqdm(os.listdir(entry_data_path)):
        document = json.load(open(os.path.join(entry_data_path, document_name)))
        text = document['preamble']
        entry = dict()
        entry['main_text'] = text
        entry['section_title'] = 'Preamble'
        entry['entry_title'] = document['title']
        entry['hierarchy_title'] = document['title'] + preprocessing.SECTION_SPLITTER + 'Preamble'
        entry['tokenized_text'] = preprocessing.preprocess_text(text)
        document_name = document_name.split('.')[0]
        with open(f'entry_data_token_by_section/{document_name}_preamble.json', 'w') as f:
            json.dump(entry, f, indent=4)

