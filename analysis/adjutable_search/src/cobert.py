import numpy as np
import torch
from transformers import AutoTokenizer, AutoModel
import torch
import re
from tqdm.autonotebook import tqdm

from dataclasses import dataclass, field

@dataclass(order=False)
class EmbeddingResult:
    text: str
    tokens: list
    emb: np.ndarray



def get_token_embedding(text, model, tokenizer)->list[EmbeddingResult]: 

    assert tokenizer.name_or_path == 'BAAI/bge-m3', 'This function is only compatible with the BAAI/bge-m3 model since it assumes special tokens.'

    # prepare the text
    text = [re.sub(r'\n', ' ', t) for t in text]
    text = [re.sub(r'\r', ' ', t) for t in text]
    text = [re.sub(r'\t', ' ', t) for t in text]
    # Remove extra whitespaces
    text = [re.sub(' +', ' ', t) for t in text]



    # Tokenize sentences
    encoded_input = tokenizer(text, padding=True, truncation=True, return_tensors='pt')
    # for s2p(short query to long passage) retrieval task, add an instruction to query (not add instruction for passages)
    # encoded_input = tokenizer([instruction + q for q in queries], padding=True, truncation=True, return_tensors='pt')

    encoded_input = {key: tensor.to(model.device) for key, tensor in encoded_input.items()}

    # Compute token embeddings
    with torch.no_grad():
        model_output = model(**encoded_input)
        # Perform pooling. In this case, cls pooling.
        token_emb = model_output.last_hidden_state
        token_emb = torch.nn.functional.normalize(token_emb, p=2, dim=-1)

    results = []
    # for each sentence, we only keep the embedding of the actual tokens (i.e., remove padding, cls, etc)
    for i, (sentence, input_ids) in enumerate(zip(text, encoded_input['input_ids'])):
        # Find the last non-padding token and return its embedding
        last_non_padding = (input_ids != tokenizer.pad_token_id).nonzero(as_tuple=True)[0].max()
        sentence_token_emb = token_emb[i, 1:last_non_padding, :].cpu().numpy()
        input_tks = input_ids[1:last_non_padding]
        input_tks = tokenizer.convert_ids_to_tokens(input_tks)
        results.append(EmbeddingResult(sentence, input_tks, sentence_token_emb))
        

    return results

def score_ranking_list(query, ranking, full_text, model, tokenizer):
    result = []
    for title in tqdm(ranking):
        text = full_text[title]
        result.append((title, query_score_per_token(query, text, model, tokenizer)))
    return result

def query_score_per_token(query: str, passage: str, model, tokenizer):
    query, passage = get_token_embedding([query, passage], model, tokenizer)
    token_scores = np.einsum('in,jn->ij', query.emb, passage.emb)
    scores = token_scores.max(axis=-1)
    scores_idx = np.argmax(token_scores, axis=-1)
    result = []
    for i, idx in enumerate(scores_idx):
        result.append((query.tokens[i], passage.tokens[idx], scores[i]))

    result = sorted(result, key=lambda x: x[2], reverse=True)
    return result

def colbert_score(q_reps, p_reps):
    token_scores = np.einsum('in,jn->ij', q_reps, p_reps)
    scores = token_scores.max(axis=-1)
    scores = np.sum(scores) / q_reps.shape[0]
    return scores

# def colbert_score_torch(q_reps, p_reps):
#     q_reps, p_reps = torch.from_numpy(q_reps), torch.from_numpy(p_reps)
#     token_scores = torch.einsum('in,jn->ij', q_reps, p_reps)
#     scores, _ = token_scores.max(-1)
#     scores = torch.sum(scores) / q_reps.size(0)
#     return scores