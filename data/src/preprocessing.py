import os
from os import listdir
from os.path import isfile, join

import json
from urllib.request import urlopen, Request
from lxml import html
import requests
from bs4 import BeautifulSoup

import time
from tqdm.autonotebook import tqdm


import re

import pickle



def get_sep(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")

    # ================= aueditable
    aueditable = soup.find_all('div', id="aueditable")[0].find_all("h1")[0].get_text()
    # ================= author
    authorship = {
            "year": soup.find_all('div', id="article-copyright")[0].find_all("a")[0].get_text(),
            "author_text": str(soup.find_all('div', id="article-copyright")[0].get_text().split("by")[1]).strip(), # after "by"
            "author_links": [ {a['href']:a.get_text()} for a in soup.find_all('div', id="article-copyright")[0].find_all("a")[1:] ],
            "raw_html": str(soup.find_all('div', id="article-copyright")[0])
        }
    # ================= preamble
    preamble = soup.find_all('div', id="preamble")[0].get_text()
    # ================= pubinfo
    pubinfo = soup.find_all('div', id="pubinfo")[0].get_text().split('; ')
    # ================= content table
    toc = [ {a['href']:a.get_text()} for a in soup.find_all('div', id="toc")[0].find_all('a', href=True)]
    # ================= main text
    main_text = soup.find_all('div', id="main-text")[0].get_text()


    # ================= bibliography
    
    # sometimes the section titles have style, which means we cannot directly search it
    # so we shouldn't remove the style
    # assume that all the title should be after <div id="xxxx"> no matter whether there is a ID
    # which is the first >
    ref_cat = [str(i)[str(i).find(">")+1:].replace("</h3>","") for i in soup.find_all('div', id="bibliography")[0].find_all('h3')]
    # print(ref_cat)
    cat_check_list = []

    raw_text = str(soup.find_all('div', id="bibliography")[0])
    bibliography = {
            "categories": ref_cat,
            "cat_ref_text":{},
            "raw_text": raw_text
        }
    if ref_cat: # if there are sections in bibliography
        for category in ref_cat: # the loops leads to duplicates
            regex_pattern = '|'.join(map(re.escape, ref_cat))
            raw_text_list = re.split(regex_pattern,raw_text)
            try: # sometimes the section titles have style, which means we cannot directly search it
                # print(raw_text_list)
                bibliography["cat_ref_text"][category] = raw_text_list[ref_cat.index(category)+1]
                if "<td>" in bibliography["cat_ref_text"][category]: # sometimes in a table
                    bibliography["cat_ref_text"][category] = bibliography["cat_ref_text"][category].split("<td>")
                    bibliography["cat_ref_text"][category] = [str(i).replace("<td>","").replace("</td>","").replace("  "," ").strip() for i in bibliography["cat_ref_text"][category]]
                if "<li>" in bibliography["cat_ref_text"][category]: # normally as hanging url
                    bibliography["cat_ref_text"][category] = bibliography["cat_ref_text"][category].split("<li>")
                    bibliography["cat_ref_text"][category] = [str(i).replace("<li>","").replace("</li>","").replace("  "," ").strip() for i in bibliography["cat_ref_text"][category]]
            except:
                cat_check_list.append(bibliography)
                ref_list = [str(i).replace("<li>","").replace("</li>","") for i in soup.find_all('div', id="bibliography")[0].find_all('li')] + [str(i).replace("<td>","").replace("</td>","") for i in soup.find_all('div', id="bibliography")[0].find_all('td')]
                bibliography["cat_ref_text"]["ref_list"] = ref_list
    else: # if there is no categories
        ref_list = [str(i).replace("<li>","").replace("</li>","") for i in soup.find_all('div', id="bibliography")[0].find_all('li')] + [str(i).replace("<td>","").replace("</td>","") for i in soup.find_all('div', id="bibliography")[0].find_all('td')]
        bibliography["cat_ref_text"]["ref_list"] = ref_list
        
    # ================= academic-tools
    academic_tools = {
        "listed_text": [str(a).replace("<td>","").replace("</td>","") for a in soup.find_all('div', id="academic-tools")[0].find_all('td')],
        "listed_links":[{a['href']:a.get_text()} for a in soup.find_all('div', id="academic-tools")[0].find_all('a', href=True)]
    }
    # ================= other-internet-resources
    intres = {
        "listed_text": [str(a).replace("<li>","").replace("</li>","") for a in soup.find_all('div', id="other-internet-resources")[0].find_all('li')],
        "listed_links":[{a['href']:a.get_text()} for a in soup.find_all('div', id="other-internet-resources")[0].find_all('a', href=True)]
    }

    [{a.get_text():a['href']} for a in soup.find_all('div', id="")[0].find_all('a', href=True)] 
    # ================= related-entries
    # sometimes they do not have a link
    rel_ent = {
        "entry_list":[s.strip() for s in soup.find_all('div', id="related-entries")[0].get_text().replace("\nRelated Entries\n\n","").split('|\n')],
        "entry_link": [{a['href']:a.get_text()} for a in soup.find_all('div', id="related-entries")[0].find_all('a', href=True)]
    }

    file_name = [i for i in url.split("/")[-2:] if i][0] # in case /xxx/

    # save all information into a json file
    info_dict = {
        'url': file_name,
        'title':aueditable,
        'authorship':authorship,
        'pubinfo': pubinfo,
        'preamble': preamble,
        'toc': toc,
        'main_text': main_text,
        'bibliography': bibliography,
        'related_entries': rel_ent,
        'academic_tools': academic_tools,
        'other_internet_resources': intres   
    }

    with open("entry_data/"+file_name+".json", 'w') as outfile:
        json.dump(info_dict, outfile, indent=4)

    # return separated information: main text and meta data
    text_dict = {
        'title':aueditable,
        'main_text': main_text
    }    

    info_dict_short = {
        'url': file_name,
        'title':aueditable,
        'authorship':authorship,
        'pubinfo': pubinfo,
        'preamble': preamble,
        'toc': toc,
        # 'main_text': main_text,
        'bibliography': bibliography,
        'related_entries': rel_ent,
        'academic_tools': academic_tools,
        'other_internet_resources': intres  
    }


    return info_dict_short, text_dict




def load_data(filepath):
    with open(filepath, 'r') as f:
        return json.load(f)

def save_data(filepath, data):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)


def get_enhanced_bibli(url, headers_list):
    headers_index = 0  # Start with the first set of headers
    headers = headers_list[headers_index]
    response = requests.get(url, headers=headers)
    while response.status_code == 429:
        retry_after = int(response.headers.get("Retry-After", 60))  # Default to 60 seconds if the header is missing
        print(f"Rate limit hit. Sleeping for {retry_after} seconds.")
        time.sleep(retry_after)
        headers_index = (headers_index + 1) % len(headers_list)  # Rotate headers
        headers = headers_list[headers_index]
        response = requests.get(url, headers=headers)
    response.raise_for_status()  # This will raise an HTTPError if the status is 4xx, 5xx
    soup = BeautifulSoup(response.content, "html.parser")
    content = soup.find('div', id="contentContainer")

    philpaper_archived_url_list = [
        a['href'] for a in content.find_all('a', href=True)
        if a.get('rel') != ['nofollow'] and a['href'].startswith("https://philpapers.org")
    ]

    return {
        "url": url,
        "num_archived": len(philpaper_archived_url_list),
        "philpaper_archived_url_list": philpaper_archived_url_list
    }

def process_urls(ent_list):
    headers_list = [
        {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'},
        {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:125.0) Gecko/20100101 Firefox/125.0'},
        {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36 Edge/16.16299'}  # Additional user agent for diversity
    ]

    url_list = [
        list(i.keys())[0] for item in ent_list for i in item["academic_tools"]["listed_links"]
        if list(i.values())[0] == "Enhanced bibliography for this entry"
    ]

    for index, url in enumerate(url_list):
        try:
            info_dict = get_enhanced_bibli(url, headers_list)
            file_name = url.split('/')[-2]
            save_data("bibli_data/" + file_name + ".json", info_dict)
            print(f"{index + 1} LOADED: {file_name}")
        except Exception as e:
            print(f"{index + 1} ERROR: {url}, {str(e)}")
            time.sleep(5)  # Simple retry mechanism

def update_ent_list(ent_list, url, info_dict):
    for item in ent_list:
        if item["url"] == url.split('/')[-2]:
            item["bibliography"]["enhanced_bibliography"] = info_dict
    # !! bug here
    # save_data('get_data/entry_meta_list_enhanced_bibli.json', ent_list)




def read_all_files(directory):
    data = []
    for filename in os.listdir(directory):
        if filename.endswith(".json"):
            data.append(load_data(os.path.join(directory, filename)))
    return data


def get_all_info(directory):
    data = {}
    for filename in tqdm(os.listdir(directory)):
        if filename.endswith(".json"):
            info_dict = load_data(os.path.join(directory, filename))
            extracted_info_dict = {
                "num_archived": info_dict["num_archived"],
                "philpaper_archived_url_list": info_dict["philpaper_archived_url_list"]
            }
            data[info_dict["url"]] = extracted_info_dict
            # tqdm.write(f"Loaded {len(data)} files")

    # save to database/sep_clean
    save_data("database/sep_clean/enhanced_bibliographies.json", data)
    # return data






    
import re
import json
import uuid
import re
import pickle
import pandas as pd
import copy

import plotly.express as px

# these lists are for me to check the patterns
# if we can correctly extract the author, put them in the disctionary
author_1_list = []
author_2_list = []
author_3_list = [] # BCE
author_4_list = [] # start without author
# corner cases
# author_corner_list = [] # Crummell, A., [<em>AC</em>], Papers, Schomburg Center for Research in Black Culture, The New York Public Library.

year_check_list = []

def extract_info_from_ref(target):
    author, year, title, parent_title = "", "", "", ""
    
    # get author and year
    if "forthcoming" in target or "Forthcoming" in target:
        year = "forthcoming"
        try:
            author = target.split(re.findall(r"forthcoming", target)[0])[0]
        except:
            author = target.split(re.findall(r"Forthcoming", target)[0])[0]

    else:
        if len(re.findall(r'\s*(\d{4})[a-z]*', target)) > 0:
            # print(len(re.findall(r'\s*(\d{4})[a-z]*', target)))
            year = re.findall(r'\s*(\d{4})[a-z]*', target)[0]
            author = target.split(year)[0] # can find the year
            idx_year = target.index(year) # the index of the year
            # if the year is after the title
            for c in ("<em>", "(","“", "‘", "(ed"): # be careful!! Gil‘adi, A. 1979.
                if c in target[:idx_year]:
                    author = target.split(c)[0]
            author_1_list.append(author)
            
        else:
            # Augustine,  [c. 389/91]' / Justinian,  [533]', '<em>Justinian’s
            if "BCE" in target: # if there is no year find, consider if it is BCE. Note that sometimes BCE is in the title
                author = target
                author_3_list.append(author)
                year = "BCE"
            else:
                year = ""
                # be careful!! Gil‘adi, A. 1979.
                if re.findall(r"forthcoming|\s+\<em\>|\(Qing\)|\"[a-zA-Z]+|\“[a-zA-Z]+|\‘[a-zA-Z]+", target):
                    author = target.split(re.findall(r"forthcoming|\s+\<em\>|\(Qing\)|\"[a-zA-Z]+|\“[a-zA-Z]+|\‘[a-zA-Z]+", target)[0])[0]
                    author_2_list.append(author)
                else:
                    author = ""


    if "(might be primary sources)" in author:
        author = author.replace("(might be primary sources)","").strip()
    if "</a>" in author: 
        if "></a>" in author: # '<a name="abramsky94ic"></a>Abramsky, S.,', 'Jagadeesan, R., ']
            author = author.split("></a>")[1].strip()
        else: # '<a name="Hilbert:28b">Hilbert,  David, Ackermann Wilhelm</a>'
            author = " ".join(author.split("\">")[1:]).strip()
            author = author.replace("</a>","").strip()
    

    # check year
    if type(year)== int and year > 2022:
        year_check_list.append({
            "ref":target,
            "title": title,
            "author": author,
            "year": year
        })
        year = ""
        print("\nERORR NO YEAR: ", target)

    # title
        # e.g., Burgess, J. A., 1990, ‘Vague Objects and Indefinite Identity’, <em>Philosophical Studies</em>, 59: 263–287.
        # note: the order matters!

    # if it is an article, try to extract the title
    if re.findall(r"“[a-zA-Z]+|\"[a-zA-Z]+|‘[a-zA-Z]+", target):
    
        if re.findall('“(.*?)”', target, re.DOTALL):
            title = re.findall('“(.*?)”', target, re.DOTALL)[0].strip()
        # sometimes typo like this 
        # Gödel, K., 1970, “Appendix A: Notes in Kurt Gödel’s Hand“, in Sobel 2004, pp. 144–145.
        elif re.findall('“(.*?)“', target, re.DOTALL): 
            title = re.findall('“(.*?)“', target, re.DOTALL)[0].strip()
        elif re.findall('‘(.*?)’', target, re.DOTALL):
            title = re.findall('‘(.*?)’', target, re.DOTALL)[0].strip()
        elif re.findall('\"(.*?)\"', target, re.DOTALL):
            title = re.findall('\"(.*?)\"', target, re.DOTALL)[0].strip()
        else:
            title = ""

    # if there is another title after the title we have extracted
    if title != "":
        end_idx_title = target.index(title) + len(title)
        if re.findall('<em>(.*?)</em>', target[end_idx_title:], re.DOTALL):
            parent_title = re.findall('<em>(.*?)</em>', target, re.DOTALL)[0].strip()
        elif re.findall('<i>(.*?)</i>', target[end_idx_title:], re.DOTALL):
            parent_title = re.findall('<i>(.*?)</i>', target, re.DOTALL)[0].strip()
    else: # if it is a book 
        if re.findall('<em>(.*?)</em>', target, re.DOTALL):
            title = re.findall('<em>(.*?)</em>', target, re.DOTALL)[0].strip()
        elif re.findall('<i>(.*?)</i>', target, re.DOTALL):
            title = re.findall('<i>(.*?)</i>', target, re.DOTALL)[0].strip()
        else: # if they forgot to style the titles...
            title = ""
            print("\nERORR NO [ARCTILE/BOOK] TITLE: ", target)
    
    return author, year, title, parent_title

# note: cannot use "startswith" because if there are noices before the author...
def add_pre_author_name(listed_ref, i):
    '''
    the listed_ref is a list of references
    i is the index
    s is the string in the list, listed_ref[i]
    '''
    s = listed_ref[i]
    author = ""
    
    if "–––" in s or "\u2013\u2013\u2013" in s or "_______" in s:
        target = ""
        # find targeted ref item
        for j in range(i-1, -1, -1):
            if "–––" in listed_ref[j] or "\u2013\u2013\u2013" in listed_ref[j] or "_______" in listed_ref[j]:
                continue
            if listed_ref[j] == "":
                continue
            # if "</h3>\n<p>" in listed_ref[j]:
            #     continue
            # should try until there is an actual title. e.g., https://plato.stanford.edu/entries/frantz-fanon/#Bib
            author, year, title, parent_title = extract_info_from_ref(listed_ref[j])
            if author != "":
                target = listed_ref[j]
                # print("\n target: ",target)
                break

        # with target, find author
        if target == "":
            print("target is empty")
        else:
            author, year, title, parent_title = extract_info_from_ref(target)
            
    if author == "":
        print("ERROR author is empty:\n",s)
    else: # update s
        s = s.replace("–––", author).replace("\u2013\u2013\u2013", author).replace("_______", author)

    return s



def sep_author(author):

    sep_list = []

    # find the last author
    if " and " in author or " &amp; " in author or " with " in author: # and or &amp; (& in html)
        if " and " in author:
            author_list = author.split(" and ")
        elif " &amp; " in author:
            author_list = author.split(" &amp; ")
        # "Carpenter, Amber with Ngaserin, Sherice,
        elif " with " in author:
            author_list = author.split(" with ")
        # if len(author_list) > 2, treat it as divider
        if author_list:
            # 'Weis R. and C. Butterworth '
            if "," not in author_list[0]:
                sep_list = author_list
            
            first_author = ";".join(author_list[0].split(",")[:2])
            middle_author = ", ".join(author_list[0].split(",")[2:])
            last_author = author_list[1].strip()
            # if last name is separated by comma, than all previous names are separated by comma
            FIND_COMMA = False
            
            if re.findall('([a-zA-Z]+),+[\s]*([a-zA-Z]+)', last_author, re.DOTALL): # there is a comma in between
                FIND_COMMA = True
                ln = last_author.split(",")[0]
                fn = " ".join(last_author.split(",")[1:])
                last_author = fn + " " + ln
                # print(FIND_COMMA, last_author)
                # last_author = " ".join(re.findall('([a-zA-Z]+),*[\s]*([a-zA-Z]+)', last_author, re.DOTALL)[0])
            # print("FIND_COMMA",FIND_COMMA)
            if "," in author_list[0]:
                if FIND_COMMA:
                    middle_author_list = middle_author.split(",")
                    # print(middle_author_list)
                    middle_author_list = [ ';'.join(x) for x in zip(middle_author_list[0::2], middle_author_list[1::2]) ]
                    # reverse ln and fn
                    middle_author_list = [i.split(";")[1].strip() + " " + i.split(";")[0].strip() for i in middle_author_list]
                else:
                    middle_author_list = middle_author.split(",")
                    middle_author_list = [i.strip() for i in middle_author_list]
                # reverse ln and fn in first author
                first_author = first_author.split(";")[1].strip() + " " + first_author.split(";")[0].strip()
                sep_list = [first_author] + middle_author_list + [last_author]
                # have no clue why there is \n, but take them as space
                # e.g., 'Steven Michael\nBellovin'
                sep_list = [i.replace("\n"," ").replace("  "," ").strip() for i in sep_list if i]
                
        else:
            print("author_list is empty???")
    else:
        
        if author.count(",") >= 4: 
            
            first_author = ";".join(author.split(",")[:2])
            first_author = first_author.split(";")[1].strip() + " " + first_author.split(";")[0].strip()

            if re.findall('[A-Z]\.,', ",".join(author.split(",")[2:]), re.DOTALL):
                # print(re.findall('[A-Z]\.,', ",".join(author.split(",")[2:]), re.DOTALL))
                sep_list = author.split(",")[2:]
                sep_list = [ ';'.join(x) for x in zip(sep_list[0::2], sep_list[1::2]) ]
                # reverse ln and fn
                sep_list = [first_author] + [i.split(";")[1].strip() + " " + i.split(";")[0].strip() for i in sep_list]
            else:
                # print("%%%%%% not find \"A.,\"%%%%%%%  \n", author)
                sep_list = author.split(",")[2:]
                sep_list = [first_author] + [i.strip() for i in sep_list]
                    
        else: # single author
            first_author = author
            # the first author is written as {Last}, {First} e.g., Barandalla, Ana
            first_author_list = [i.strip() for i in first_author.split(",") if i.strip()!=""]
            if first_author_list:
                first_author_ln = first_author_list[0].strip()
                first_author_fn = " ".join(first_author_list[1:]).strip()
                # ERROR: Lewis, David Lewis, 1973, => Lewis, David
                if first_author_ln == first_author_list[-1]:
                    first_author_fn = " ".join(first_author_list[1:-1]).strip()
                # first_author_ln_list.append(first_author_ln)
                
                rev_first_author = first_author_fn + " " + first_author_ln
                sep_list = [rev_first_author]
            # else:
            #     print( first_author)

    # update the dictionary of each reference by adding the separated author list

    # 'Wilfrid  2013 Hodges'
    # don't use if len(i) > 5, since some names are like "Yu Ru"
    sep_list = [i.strip() for i in sep_list if len(i) > 2 and not (i[0]=="[" and i[-1]=="]") and i != "et al." and not i[0].isdigit()]
    # i if i not contains strings like ">" "<tb" "="
    sep_list = [i for i in sep_list if not re.findall('<tr|=|<tb', i, re.DOTALL)]
    

    # in case some names are not reversed
    # make sure 'Føllesdal D.' -> 'D. Føllesdal' / 'Carter C. L.' -> 'C. L. Carter'
    # E.g., first name: Hamilton W.D.,
    for name in sep_list:
        update_name = ""
        # find the last string that does not include "."
        if "." in name:
            for i in range(len(name.split(" "))-1, -1, -1):
                # print(name.split(" ")[i])
                if "." not in name.split(" ")[i]:
                    last_name = name.split(" ")[i]
                    first_name = name.replace(last_name, "") # include the middle name
                    update_name = first_name.strip() + " " + last_name.strip()
                    break
        if not update_name:
            update_name = name
        update_name = update_name.replace(" .","")
        # remove "[xxx]", e.g., "David  [T-O] Hume" => "David Hume"
        if re.findall('\[.*\]', update_name, re.DOTALL):
            # remove
            update_name = update_name.replace(re.findall('\[.*\]', update_name, re.DOTALL)[0], "")
        if re.findall('<.*>', update_name, re.DOTALL):
            # remove
            update_name = update_name.replace(re.findall('<.*>', update_name, re.DOTALL)[0], "")
        
        
        # remove punctuations other than "."
        # "Leo. A. Meyer" => "Leo A. Meyer"
        if re.findall('([a-z]+)[.]+', update_name, re.DOTALL):
            # remove the found "."
            if re.findall('([a-z]+)[.]+', update_name, re.DOTALL):
            # remove the found "."
                found_string = re.findall('([a-z]+[.]+)', update_name, re.DOTALL)[0]
                replace_string = found_string.replace(".", "")
                update_name = re.sub(found_string, replace_string, update_name, re.DOTALL)
        
        # problem: "trans"or"(trans)" "et al(.)" "editor(s)" "and"
        update_name = re.sub(' +', ' ', update_name.replace(".",". ").replace("[ ","").replace("\n", " ").replace(":","").replace(";","")).strip()
        # **** Note that sometimes it cannot be cleaned because of \n
        noise_list = [" trans ", "(trans)", " et al ", " et al. ", " editor ", " editors ", " ed ", " eds "]
        for noise in noise_list:
            update_name = " "+update_name+" "
            update_name = update_name.replace(noise, " ") # add a space to avoid merging words
        # if " A " => " A. "
        if re.findall(' [A-Z] ', update_name, re.DOTALL):
            found_string = re.findall(' ([A-Z]) ', update_name, re.DOTALL)[0]
            replace_string = found_string+"."
            update_name = re.sub(found_string, replace_string, update_name, re.DOTALL)
        # some punctuations are not removed

        # 'David Lewis Lewis' => 'David Lewis' otherwise it will bring error to author name disambiguation
        # don't remove middle names
        name_part_list = [i.strip() for i in update_name.split(" ") if i]
        for i in range(len(name_part_list)):
            for j in range(i+1, len(name_part_list)):
                if not "." in name_part_list[i] and not "." in name_part_list[j] and name_part_list[i] == name_part_list[j]:
                    name_part_list[j] = ""
        update_name = " ".join(name_part_list)

        # "C.M. Cheng" => "C. M. Cheng"
        update_name = re.sub(' +', ' ', update_name.replace(".",". ").replace("[ ","").replace("\n", " ").replace(":","").replace(";","")).strip()
        
        update_name = update_name.replace(",","").strip()

        # update
        sep_list[sep_list.index(name)] = update_name

    return sep_list


def target_name_var(name_var_list):
    MIN_ABBR = 100
    MAX_SEP = 0
    target_name = ''
    for name in name_var_list:
        # Do people really have two middle names??
        # ???????????????????
        if len(name.replace(" ","")) > len(target_name.replace(" ","")):
            MAX_SEP = len(name.split(" "))
            MIN_ABBR = name.count(".")
            target_name = name
        # the first criterion: more sep items, which indiates that there are more middle names
        # if len(name.split(" ")) > MAX_SEP:
        #     MAX_SEP = len(name.split(" "))
        #     MIN_ABBR = name.count(".")
        #     target_name = name
        # # the second criterion: length of each sep item
        # if len(name.split(" ")) == MAX_SEP:
        #     if name.count(".") < MIN_ABBR:
        #         MAX_ABBR = name.count(".")
        #         target_name = name
        #     else:
        #         continue

    # get the target name
    return target_name


