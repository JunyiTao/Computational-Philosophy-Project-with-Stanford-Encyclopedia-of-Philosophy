from FlagEmbedding import BGEM3FlagModel
import json
from tqdm.autonotebook import tqdm
import numpy as np
import os


model = BGEM3FlagModel('BAAI/bge-m3',  use_fp16=True, device='cuda')
print(model.device)

for doc_name in tqdm(os.listdir('entry_data_token_by_section')):

    text = json.load(open(f'entry_data_token_by_section/{doc_name}'))['main_text']
    emb = model.encode([text], return_dense=True, return_sparse=True, return_colbert_vecs=True)['colbert_vecs'][0]
    emb = np.float16(emb)
    np.save(f'entry_data_token_by_section_emb/{doc_name}.npy', emb)
