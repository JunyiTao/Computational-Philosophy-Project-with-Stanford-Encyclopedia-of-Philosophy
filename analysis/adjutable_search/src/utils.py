import pandas as pd
import json
from collections import defaultdict
author_data = json.load(open('../database/sep_clean/author_cited_count.json'))
article_data = pd.read_csv('../database/sep_clean/ent_ref_info_list.csv')

def find_author(author):
    if type(author) is str:
        author = [author]
    result = defaultdict(dict)
    for a in author:
        for ent, count in eval(author_data[a]['cited_ent_dict']).items():
            result[ent][a] = count
    
    return sorted(result.items(), key=lambda x: (len(x[1]),sum(x[1].values())), reverse=True)
        

def find_article(article):
    if type(article) is str:
        article = [article]
    result = defaultdict(dict)
    for a in article:
        subset = article_data[article_data['ref_text'] == a]
        for ent in subset['cited_by_ent']:
            result[ent][a] = 1
    return sorted(result.items(), key=lambda x: (len(x[1]),sum(x[1].values())), reverse=True)