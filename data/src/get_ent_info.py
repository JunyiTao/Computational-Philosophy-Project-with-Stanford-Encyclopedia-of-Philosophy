# packages
import json
import pandas as pd
import re

import pickle


# ===========================================================

with open("database/entry_meta_dict.json", "r") as f:
    entry_meta_dict = json.load(f)

with open("database/sep_clean/ent_ref_sep_dict.json", "r") as f:
    ent_ref_sep_dict = json.load(f)

with open("get_data/sep_entry_text_list.json", "r") as f:
    ent_text_list = json.load(f)

with open("database/NER/ent_cited_work_dict.json", "r") as f:
    ent_cited_work_dict = json.load(f)
with open("database/NER/ent_cited_author_dict.json", "r") as f:
    ent_cited_author_dict = json.load(f)

# Open files


def get_search_list(key):
   # in lower case
   if key == "ai":
      return ["machine learning", "deep learning",
               "artificial intelligence", " neural network ",  # , " ai "
               " natural language processing ",  " computer vision ", # " nlp ",
               " reinforcement learning ", 
            #    这个地方不改好像也问题不大，因为大概率提到unsupervised肯定也会说supervised
               " supervised learning", " unsupervised learning", "semi-supervised learning",
               "generative adversarial network", "generative model", 
            #    "convolutional neural network", " cnn ", "recurrent neural network", " rnn ",
               "transfer learning", "self-supervised learning", "self-supervision",
            #    "self-learning", "self-learning system", "self-learning systems", can be Xunzi's self-leanring
               " language model"]
            #    " technology ", "technologies", "technological", "technological development"]
   elif key == "feminist":
      return ["feminism", "feminist"]

# text list is a list of strings, specifically for an entry
def find_keyword(search_list, text):
   if type(text) == list:
      text = " ".join(text)
   found_list = []
   
   for kw in search_list:
      if kw in text:
         found_list.append(kw)
   return found_list



#  a function to get ent_url from ent_title
def get_ent_url(ent_title):

    for k, v in entry_meta_dict.items():
        if v["title"] == ent_title:
            ent_url = k
            return ent_url

# a function to get ent_title from ent_url
def get_ent_title(ent_url):

    ent_title = entry_meta_dict[ent_url]["title"]
    return ent_title

# a fundtion to get main text for an entry
def get_ent_text(ent_title):

    for item in ent_text_list:
        if item["title"] == ent_title:
            return item["main_text"].replace("\n"," ")


# get related titles for an entry
def get_related_list(ent_title, key):
    # ent_related_dict
    
    ent_url = get_ent_url(ent_title)
    if key == "url":
        return entry_meta_dict[ent_url]["related_entries"]["entry_link"]
    elif key == "title":
        title_list = []
        # note that refered titles can be inconsistent, so we only use the url to access the real title
        url_list = entry_meta_dict[ent_url]["related_entries"]["entry_link"]
        for ent_url in url_list:
            ent_title = entry_meta_dict[ent_url]["title"]
            title_list.append(ent_title)
        return title_list
    else:
        # raise error
        print("Key Error: key should be 'url' or 'title'")




# ========================= cited sources =========================

# get citation info as a list
def get_save_cite_info():
    
    ent_cited_author_dict, ent_cited_work_dict = {}, {}
    # for each url, get category, for each catgory, get update_author_list
    for ent_url in ent_ref_sep_dict:
        ent_cited_author_dict[ent_url] = {}
        author_info_dict, ref_info_dict = {}, {}
        for cat in ent_ref_sep_dict[ent_url]:
            author_info_dict[cat] = []
            author_list, ref_list = [], []
            for ref in ent_ref_sep_dict[ent_url][cat]["ref_dict"]:
                author_list += ent_ref_sep_dict[ent_url][cat]["ref_dict"][ref]["update_author_list"]
                ref_list.append(ent_ref_sep_dict[ent_url][cat]["ref_dict"][ref]["update_ref"])
            
            # make author_list into a dict => author_dict_list = [{author name: count}]
            # NOTE that author_list is a list of lists
            # NOTE multiple authors
            author_dict_list = []
            for author in list(set(author_list)):
                author_dict = {}
                author_dict[author] = author_list.count(author)
                author_dict_list.append(author_dict)
            author_dict_list = sorted(author_dict_list, key=lambda k: list(k.values())[0], reverse=True)
            author_info_dict[cat] = author_dict_list

            # NOTE that ref_list is a list of strings
            ref_dict_list = []
            for ref in list(set(ref_list)):
                ref_dict = {}
                ref_dict[ref] = ref_list.count(ref)
                ref_dict_list.append(ref_dict)
            ref_dict_list = sorted(ref_dict_list, key=lambda k: list(k.values())[0], reverse=True)
            ref_info_dict[cat] = ref_dict_list

        ent_cited_author_dict[ent_url] = author_info_dict
        ent_cited_work_dict[ent_url] = ref_info_dict

    # replace the key with the title

    ent_cited_author_dict_update, ent_cited_work_dict_update = {}, {}

    for ent_url in ent_cited_author_dict:
        title  = entry_meta_dict[ent_url]["title"]
        ent_cited_author_dict_update[title] = ent_cited_author_dict[ent_url]

    for ent_url in ent_cited_work_dict:
        title  = entry_meta_dict[ent_url]["title"]
        ent_cited_work_dict_update[title] = ent_cited_work_dict[ent_url]

    # save
    with open("database/NER/ent_cited_author_dict.json", "w") as f:
        json.dump(ent_cited_author_dict_update, f, indent=4)
    with open("database/NER/ent_cited_work_dict.json", "w") as f:
        json.dump(ent_cited_work_dict_update, f, indent=4)
    # print save info
    print("database/NER/ent_cited_author_dict.json ==== saved")
    print("database/NER/ent_cited_work_dict.json ==== saved")

# # print the fist item of ent_cited_work_dict_update
# for key, value in ent_cited_work_dict_update.items():
#     print(key, value)
#     break


# a function to get cited titles from ent_title
# no categories
def get_cited_ref_all_list(ent_title):
    
    cited_ref_list = []
    for cat, v in ent_cited_work_dict[ent_title].items():
        for item in v:
            cited_ref_list.append(list(item.keys())[0])
    
    return cited_ref_list

# get all cited_authors for an entry, no categories
def get_cited_author_all_list(ent_title):
    # ent_cited_author_dict
    
    cited_author_list = []
    for cat, v in ent_cited_author_dict[ent_title].items():
        for item in v:
            cited_author_list.append(list(item.keys())[0])
    
    return cited_author_list

    

