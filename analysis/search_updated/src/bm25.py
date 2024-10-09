#!/usr/bin/env python

import math
import numpy as np
import json
import os
from tqdm.autonotebook import tqdm
from src.preprocessing import SECTION_SPLITTER, preprocess_text



def build_searcher(directory: str, k1: float = 1.5, b: float = 0.75, epsilon: float = 0.25) -> 'BM25Okapi':
    '''
    Build a searcher for the given directory.
    directory: the directory containing the entry data
    k1: parameter for the BM25 algorithm, controls the importance of the term frequency
    b: parameter for the BM25 algorithm, controls the importance of the document length, ranging from 0 to 1
    epsilon: parameter for the BM25 algorithm, controls the minimum importance of a term
    '''
    corpus = []
    id2title = []
    full_text = dict()
    for document_name in tqdm(os.listdir(directory)):
        document = json.load(open(directory + document_name))
        corpus.append(document['tokenized_text'])
        id2title.append(document['hierarchy_title'])
        full_text[document['hierarchy_title']] = document['main_text']

    return BM25Okapi(corpus, k1=k1, b=b, epsilon=epsilon, full_text=full_text, id2title=id2title)


def exclude_by_entry(ranking: list[tuple[str, float, list[tuple[str, float]]]], entry: str) -> list[tuple[str, float, list[tuple[str, float]]]]:
    '''
    Exclude a given entry from the ranking list.
    ranking: ranking list returned by the get_scores function of a searcher.
    entry: the entry to exclude
    '''
    return [doc for doc in ranking if doc[0].split(SECTION_SPLITTER)[0].strip().lower() != entry.lower()]



class BM25:
    def __init__(self, corpus, id2title=None, full_text=None):
        self.corpus_size = 0
        self.avgdl = 0
        self.doc_freqs = []
        self.idf = {}
        self.doc_len = []
        self.id2title = id2title
        self.full_text = full_text


        nd = self._initialize(corpus)
        self._calc_idf(nd)

    def _initialize(self, corpus):
        nd = {}  # word -> number of documents with word
        num_doc = 0
        for document in corpus:
            self.doc_len.append(len(document))
            num_doc += len(document)

            frequencies = {}
            for word in document:
                if word not in frequencies:
                    frequencies[word] = 0
                frequencies[word] += 1
            self.doc_freqs.append(frequencies)

            for word, freq in frequencies.items():
                try:
                    nd[word]+=1
                except KeyError:
                    nd[word] = 1

            self.corpus_size += 1

        self.avgdl = num_doc / self.corpus_size
        return nd



    def _calc_idf(self, nd):
        raise NotImplementedError()

    def get_scores(self, query):
        raise NotImplementedError()

    def get_batch_scores(self, query, doc_ids):
        raise NotImplementedError()

    def get_top_n(self, query, documents, n=5):

        assert self.corpus_size == len(documents), "The documents given don't match the index corpus!"

        scores = self.get_scores(query)
        top_n = np.argsort(scores)[::-1][:n]
        return [documents[i] for i in top_n]
    
    def parse_search_result(self, score, score_by_token):
        result = []
        for i, s in enumerate(score):
            doc_name = self.id2title[i] if self.id2title is not None else str(i)
            tmp = [doc_name, s]
            token_score_list = []
            for token, token_score in score_by_token.items():
                if token_score[i] > 0:
                    token_score_list.append((token, token_score[i]))
            token_score_list = sorted(token_score_list, key=lambda x: x[1], reverse=True)
            tmp.append(token_score_list)
            result.append(tmp)
        result = sorted(result, key=lambda x: x[1], reverse=True)
        return result
    


class BM25Okapi(BM25):
    def __init__(self, corpus, k1=1.5, b=0.75, epsilon=0.25, **kwargs):
        self.k1 = k1
        self.b = b
        self.epsilon = epsilon
        super().__init__(corpus, **kwargs)

    def _calc_idf(self, nd):
        """
        Calculates frequencies of terms in documents and in corpus.
        This algorithm sets a floor on the idf values to eps * average_idf
        """
        # collect idf sum to calculate an average idf for epsilon value
        idf_sum = 0
        # collect words with negative idf to set them a special epsilon value.
        # idf can be negative if word is contained in more than half of documents
        negative_idfs = []
        for word, freq in nd.items():
            idf = math.log(self.corpus_size - freq + 0.5) - math.log(freq + 0.5)
            self.idf[word] = idf
            idf_sum += idf
            if idf < 0:
                negative_idfs.append(word)
        self.average_idf = idf_sum / len(self.idf)

        eps = self.epsilon * self.average_idf
        for word in negative_idfs:
            self.idf[word] = eps

    def get_scores(self, query: str, word_importance: dict[str, float] = None) -> list[tuple[str, float, list[tuple[str, float]]]]:
        """
        Calculate the BM25 scores for a given query.
        query: the query string to search for
        word_importance: a dictionary of words and their importance, used to weight the query terms
        returns a list of tuples, where each tuple contains the document name, the score, and a list of tuples that contain the words and their scores in the document.
        """
        query = preprocess_text(query)
        score = np.zeros(self.corpus_size)
        doc_len = np.array(self.doc_len)
        score_by_token = dict()

        # preprocess and tokenize the word_importance
        if word_importance is not None:
            word_importance_token = dict()
            for q in word_importance:
                tokenized_q = preprocess_text(q)
                for token in tokenized_q:
                    word_importance_token[token] = word_importance[q]
            word_importance = word_importance_token

            print(word_importance)

        for q in query:
            q_freq = np.array([(doc.get(q) or 0) for doc in self.doc_freqs])
            q_score = (self.idf.get(q) or 0) * (q_freq * (self.k1 + 1) /
                                               (q_freq + self.k1 * (1 - self.b + self.b * doc_len / self.avgdl)))
            
            if word_importance is not None and q in word_importance:
                q_score = q_score * word_importance[q]
            score += q_score
            score_by_token[q] = q_score
            
        return self.parse_search_result(score, score_by_token)

    def get_batch_scores(self, query, doc_ids):
        """
        Calculate bm25 scores between query and subset of all docs
        """
        assert all(di < len(self.doc_freqs) for di in doc_ids)
        score = np.zeros(len(doc_ids))
        doc_len = np.array(self.doc_len)[doc_ids]
        for q in query:
            q_freq = np.array([(self.doc_freqs[di].get(q) or 0) for di in doc_ids])
            q_score = (self.idf.get(q) or 0) * (q_freq * (self.k1 + 1) /
                                               (q_freq + self.k1 * (1 - self.b + self.b * doc_len / self.avgdl)))
            score += q_score
            
        return score.tolist()


