


import exploratory_analysis

import json
import uuid
import re
import pickle
import pandas as pd

import plotly.express as px





# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Distribution of single variables

# %%%%%%%%%% Bibliography %%%%%%%%%%%%
# ####################### count, and save as list and dict

def ref_var_count_with_id(ent_ref_dict, var, is_list):
    '''Count the number of times a variable appears in the data set.
    ent_ref_dict: (dict) dictionary of entities and references
    var: (str) variable to count
    is_list: (boolean)
    '''
    print("Length of ent ref dict:", len(ent_ref_dict))
    print(f'The input variable is {var}.', 'Is it a list?', is_list)

    # print keys
    # get var list and find unique values
    uni_var_id_dict = {} # {var:uuid}
    var_list, uni_var_list =[], []
    var_dict = {} # initialize the dict (add all empty elements)

    for ent_url in list(ent_ref_dict.keys()): # for each entry
        cat_ref_list = list(ent_ref_dict[ent_url].keys())
        for cat in cat_ref_list: # for each categories in bibliogrpahies
            ref_list = list(ent_ref_dict[ent_url][cat]["ref_dict"].values()) # get the info dict of each ref
            # note that "" != str
            var_list = var_list  + [i[var] for i in ref_list] # get the variable

    if is_list: # flatten the list if the var is a list, e.g., author_list
        var_list = [var_item for sublist in var_list for var_item in sublist]

    uni_var_list =list(set(var_list))
    with open(f'database/single_variable_list/uni_{var}_list.pickle', 'wb') as f:
        pickle.dump(uni_var_list, f, pickle.HIGHEST_PROTOCOL)

    print(var,"list:", len(var_list))
    print("unique",var,"list:", len(uni_var_list))

    for s in uni_var_list:
        # unique id
        uni_var_id_dict[s] = str(uuid.uuid4())
        # initialize the disctionary
        var_dict[uni_var_id_dict[s]] = {
            "name": s,
            "ref_count": 0,
            "ref_list": []
        }
    with open(f'database/single_variable_list/uni_{var}_id_dict.json', 'w') as f:
        json.dump(uni_var_id_dict, f, indent=4)

    # count
    for ent_url in list(ent_ref_dict.keys()): # for each entry
        cat_ref_list = list(ent_ref_dict[ent_url].keys())
        for cat in cat_ref_list: # for each categories in bibliogrpahies
            ref_list = list(ent_ref_dict[ent_url][cat]["ref_dict"].values()) # the ref_list for this cat
            # build a list of var items in this specific cat
            cat_var_list = [i[var] for i in ref_list] # get the variable           
            if is_list: # flatten the list if the var is a list, e.g., author_list
                cat_var_list = [var_item for sublist in cat_var_list for var_item in sublist]
            # iterate cat_var_list to get each var
            for var_item in cat_var_list:
                var_id = uni_var_id_dict[var_item]
                var_dict[var_id]["ref_count"] += 1 # count how many letters the var occurs
                var_dict[var_id]["ref_list"].append({ent_url:cat})

    # sort
    var_dict = dict(sorted(var_dict.items(), key=lambda item: item[1]["ref_count"], reverse=True))
    # save
    with open(f'database/single_variable_list/{var}_dict.json', 'w') as f:
        json.dump(var_dict, f, indent=4)


# ###################################### vis

def vis_single_var(var, HEAD):
    '''
    HEAD: (int) number of top items to show
    '''
    # open 
    with open(f'database/single_variable_list/{var}_dict.json', 'r') as f:
        var_dict = json.load(f)

    nan_count = 0
    if var == "update_ref":
        for k, v in var_dict.items():
            if v["name"].replace("() []", "").strip() == "":
                # count and remove
                nan_count += 1
    if var == "title_year":
        for k, v in var_dict.items():
            if v["name"].replace("()", "").strip() == "":
                # count and remove
                nan_count += 1

    print("nan:", nan_count)

    # remove them
    var_dict = {k:v for k, v in var_dict.items() if v["name"].replace("() []", "").strip() != ""}

    # build a df, with the title and the count
    var_count_list = []
    for var_id in list(var_dict.keys()):
        var_count_list.append([var_dict[var_id]["name"], var_dict[var_id]["ref_count"]])

    # remove nan: check these NaN values later
    to_check_nan = [i for i in var_count_list if i[0] == ""]
    print("to_check_nan:", len(to_check_nan))

    var_count_list = [i for i in var_count_list if i[0] != ""]
    var_count_df = pd.DataFrame(var_count_list, columns=[var, "count"])
    # visualize only the first {HEAD} rows
    var_count_df_top = var_count_df.head(HEAD)

    # %%%%%%%%%%%%%%%%%%%%%% bar plot
    fig = px.bar(var_count_df_top, x=var, y='count')
    # add title and axis labels
    fig.update_layout(
        title=f"Top {HEAD} \"{var}\" of Bibliographies in SEP",
        xaxis_title=var,
        yaxis_title="count",
        font=dict(
            family="Merriweather",
            size=12,
            color= "black",
        ),
    )
    # center the title
    fig.update_layout(title_x=0.5)
    # set tickmode='linear'
    fig.update_xaxes(tickmode='linear')

    fig.update_traces(marker_color="rgba(70,130,180, 0.5)")
    # beautify the design, old school style
    fig.update_layout(
        margin=dict(l=20, r=20, t=50, b=20),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(220,220,220, 0.2)",
        # paper_bgcolor="rgba(250,235,210, 0.3)"
    )
    fig.show()
    # save fig
    fig.write_html(f"database/single_variable_list/vis/html/bar_{var}.html")
    # save as png
    fig.write_image(f"database/single_variable_list/vis/fig/bar_{var}.png")

    # %%%%%%%%%%%%%%%%%%% build a box plot to visualize this var_dict
    # build a list of ref_count
    ref_count_list = []
    for var_id in list(var_dict.keys()):
        ref_count_list.append(var_dict[var_id]["ref_count"])
    # ignore those with 0 ref_count
    ref_count_list = [i for i in ref_count_list if i != 0]

    # build a df
    ref_count_df = pd.DataFrame(ref_count_list, columns=["count"])
    # visualize
    fig = px.box(ref_count_df, y="count")
    # add title and axis labels
    fig.update_layout(
        title=f"Boxplot of \"{var}\" of Bibliographies in SEP",
        xaxis_title="count",
        yaxis_title="frequency",
        font=dict(
            family="Merriweather",
            size=12,
            color= "black",
        ),
    )
    fig.update_layout(
        margin=dict(l=40, r=40, t=50, b=20),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(220,220,220, 0.2)",
        # paper_bgcolor="rgba(250,235,210, 0.3)"
    )
    fig.update_traces(marker_color="rgba(27, 90, 24, 0.5)")
    # center the title
    fig.update_layout(title_x=0.5)

    fig.show()
    fig.write_image(f"database/single_variable_list/vis/fig/box_{var}.png")




# %%%%%%%%%% ref_text




# %%%%%%%%%% author


# %%%%%%%%%% year


# %%%%%%%%%% title


# %%%%%%%%%% Related entries %%%%%%%%%%%%


# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Relationship between two variables











# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%




