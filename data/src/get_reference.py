
import json
import pandas as pd
import re

import pickle

from termcolor import colored
# use NER to extract names
import spacy
nlp = spacy.load("en_core_web_sm")


def ner_people(text):
    # initialize a df
    df = pd.DataFrame(columns=["target", "label", "exact_string", "start_index", "end_index"])

    doc = nlp(text) # doc is a tokenized text
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            # "Barthold 2016"
            # if exist 4 dgits, use regular expression
            if re.search(r"\d{3}", ent.text):
                continue
            if len(ent.text) < 3:
                continue
            if not df["target"].isin([ent.text]).any():
                df = df.append({"target": ent.text, "label": ent.label_, "exact_string": text[int(ent.start_char):int(ent.end_char)], "start_index": ent.start_char, "end_index": ent.end_char}, ignore_index=True)
            # print(colored(ent.text, "red"), ent.label_)
    # return the first column of the df
    return df["target"].tolist()


def clean_ner_list(people_list):
    for i in range(len(people_list)):
        people_list[i] = re.sub(r"\s+", " ", people_list[i].replace(".",". "))
        noises = ["\\", "(",")", "[", "]","et al", "⊢", "&", "Theorem", "and", "Column", "Row", "Philosopher"]

        if re.search(r"\d{3}", people_list[i]):
            # print(list[i])
            people_list[i] = ""
        # if contain "\\\\" might be formulas
        elif any(noise in people_list[i] for noise in noises):
            # print(list[i])
            # remove
            people_list[i] = ""
        # if contain ’s or 's or s' or s’
        elif re.search(r"’s", people_list[i]):
            people_list[i] = people_list[i].split("’s")[0]
        elif re.search(r"s’", people_list[i]):
            people_list[i] = people_list[i].split("s’")[0]+"s"
        elif re.search(r"'s", people_list[i]):
            people_list[i] = people_list[i].split("'s")[0]
        elif re.search(r"s'", people_list[i]):
            people_list[i] = people_list[i].split("s'")[0]+"s"

    for i in range(len(people_list)):
        for j in range(len(people_list)):
            if j != i:
                if people_list[i] in people_list[j].split(" "):
                    # print(people_list[i], "|",people_list[j])
                    people_list[i] = ""
                    break
                elif people_list[i] == " ".join(people_list[j].split(" ")[:2]) or people_list[i] == " ".join(people_list[j].split(" ")[-2:]):
                    # print(people_list[i], "|",people_list[j])
                    people_list[i] = ""
                    break
                # or their lower cases are the same
                elif people_list[i].lower() == people_list[j].lower():
                    # print(people_list[i], "|",people_list[j])
                    people_list[i] = ""
                    break
    # remove duplicates and null
    people_list = list(set(people_list))
    people_list = [i.strip() for i in people_list if i]
    return people_list




# find the most frequently mentioned people and replace the name with names in thinker_list
# caution: It's also possible that the name appears frequently because it's too common
# and if it is the case, the name can be only the last name, and there's no links to that philosopher

def most_famous_lastname(ln_rn_list):
    # transform into a dict
    ln_rn_dict = {}
    for pair in ln_rn_list:
        ln = pair[0].lower()
        rn = pair[1] # don't use lowercase here
        ln_rn_dict[ln] = rn
    return ln_rn_dict

# counter
from collections import Counter


def refine_ner_list(ner_list, search_related_list, ln_rn_list):

    ln_rn_dict = most_famous_lastname(ln_rn_list)
    
    # find names in ner_list that are part of an item in rel_cited_list
    new_ner_list = []
    for name in ner_list:
        find = False
        for item in search_related_list:
            if name.lower() in item.lower(): 
                # If so, we take them to be the same person
                # print(name, "|", item)
                find = True
                break
        if not find:
            new_ner_list.append(name)
    # print("new_ner_list", new_ner_list)
    #     ner_all_list += new_ner_list

    # # find the most frequently mentioned people
    # # ner_all_list = [i.lower() for i in ner_all_list]
    # ner_all_list = Counter(ner_all_list)
    # ner_all_list = sorted(ner_all_list.items(), key=lambda x: x[1], reverse=True)
    # # print(ner_all_list[:1000])

    real_ner_list, toupdate_ner_list = [], []
    for thinker in new_ner_list:
        if len(thinker.split(" ")) > 1:
            # We consider this case as a real name and not mentioned
            real_ner_list.append(thinker)
            continue
        elif thinker.lower() in ln_rn_dict:
            # We consider this case as too common so only the last name is referred
            real_ner_list.append(ln_rn_dict[thinker.lower()])
            continue
        elif thinker == "PEOPLE_NAME":
            continue
        toupdate_ner_list.append(thinker)
    # print(toupdate_ner_list[:100])

    return real_ner_list

