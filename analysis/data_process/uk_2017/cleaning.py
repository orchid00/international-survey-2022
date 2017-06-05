#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import os
import csv
import glob
import pandas as pd
import numpy as np
import matplotlib
# from include import plotting
# When using Ipython within vim
matplotlib.use('TkAgg')

# When using within jupyter
# get_ipython().magic('matplotlib inline')  # Activat that line to use in Jupyter

import matplotlib.pyplot as plt
#  When using this script with ipython and vim
plt.ion()
plt.show()
pd.set_option('display.max_rows', 300)
# Load dataset
df = pd.read_csv('./dataset/raw_results-survey245554.csv')


# load the different answers to questions to classify questions based on that
answer_items_folder = '../../../survey_creation/uk_17/listAnswers'

# Parse list of files that contains all the possible created answers
def get_answer_item(path_to_file):
    """
    Parse all the files contained in the folder and
    create a dictionary with the data contained into the value
    and the filename as key

    :param:
        path_to_file str(): path to the folder
    :return:
        dict(): containing all the data
    """
    answer_item_dict = dict()
    for filename in glob.glob(os.path.join(path_to_file, '*.csv')):
        with open(filename) as f:
            file_key, _ = os.path.splitext(os.path.basename(filename))
            reader = csv.reader(f, delimiter=':')  # Set the delimiter as : to avoid taking
                                                   # the comma as delimiter
            answer_item_dict[file_key] = [i[0] for i in reader]

    return answer_item_dict

answer_item_dict = get_answer_item(answer_items_folder)


# Number of row == number of participants
len(df.index)

# # Drop unused fields
columns_to_drop = ['Response ID', 'Date submitted', 'Start language',
                   'Date started', 'Date last action', 'Referrer URL']
df = df.drop(columns_to_drop, axis=1)

# # Drop the columns about the time for each questions if present (from limesurvey)
df = df.loc[:, ~df.columns.str.contains('^Question time|Group time')]
df = df.loc[:, ~df.columns.str.contains('Question time')]

# # The last page is the last page the participants reached. To
# # do a compromise between keeping some and getting rid of the participants that haven't complete
# # enough answers
nb_answer = pd.DataFrame(df['Last page'].value_counts()).sort_index(ascending=True)
nb_answer['cumfreq'] = nb_answer.cumsum()
nb_answer.plot(kind='bar')

# SPECIFIC UK
# Overall, as soon as the participants passed the first page, they reached the last page.
# In consequence, if a participant passed the first page, (s)he is kept.
df = df.loc[df['Last page']> 1]

# This reduce the size of the population to:
len(df.index)

# Replace variation of 'Do not want to answer', Do not wish to declare', 'Prefer not to say' into nan
# if len(df.loc[:, df.columns.to_series().str.contains('Prefer not to answer').tolist()].columns) > 0:
df.replace('Prefer not to answer', np.NaN, inplace=True)
df.replace('Do not wish to declare', np.NaN, inplace=True)
df.replace('Do not wish to answer', np.NaN, inplace=True)

# # Replace Yes and No to Boolean when it is possible
# y_n_bool = {'Yes': True, 'No': False}
# df.replace(y_n_bool)


def cleaning_columns_white_space(df):
    """
    Various cleaning white spaces in columns name
    Can extend that function if some other form of errors
    are found later

    :params:
        df dataframe(): the input dataframe

    :return:
        df dataframe(): the same df but with cleaned columns
    """
    # Some columns have a unbreakable space in their name, replace it
    df.columns = df.columns.str.replace('\xa0', ' ')
    # Some columns have a tabular instead of a space
    df.columns = df.columns.str.replace('\t', ' ')
    df = df.rename(columns=lambda x: re.sub('(?<=\s) +|^ +(?=\s)| (?= +[\n\0])', ' ', x))
    #Replace all ending white space
    df.columns = df.columns.str.strip()
    return df


def merging_others(df, colname, replacement_values=None):
    """
    Function to wrap the different modification applied on
    the columns that have a `other` column associated.
    Search if some others could be merged with the prexisting answers
    and merge it into the original column, then transform the column into
    categorical variable
    :params:
        :df pd.df(): dataframe containing the data
        :colname str(): string that have the column header to select the right column
        :replacement_values dict(): contain which value to match in the column 'other' as
        the key and which value to replace with. If it is None, skip the transformation (Default)
    :return:
        :None: The operation is a replace `inplace`
    """
    if replacement_values:
        df[colname_other] = df[colname_other].apply(recode_values, args=(replacement_values, 'Other'))
        df[colname].replace('Other', df[colname_other], inplace=True)

    df[colname] = df[colname].str.capitalize().astype('category')


def duplicating_other(df):
    """
    When there is an option for 'Other', the column contains the value typed
    by the participants. However, to plot later, it is better to recode all this
    values as 'Yes', as for the other items. Then duplicating these value in another
    column with the tags [Other Raw] for later analysis if we want to analyse it in
    details.
    Creating the tag [Other Raw] at the beginning of the column name to avoid that
    columns being picked up by the grouping_question()

    :params:

    :return:
        :df dataframe(): Return the modified dataframe
    """
    for col in df.columns:
        if col[-7:] == '[Other]':
            # Duplicate the column
            df['[OTHER_RAW] '+col] = df[col]
            # Replace all the values with 'Yes'
            df[col] = df[col].apply(lambda x: 'Yes' if not pd.isnull(x) else np.nan)
    return df


def grouping_question(df):
    """
    Group question together by merging them when they have a [TAG]
    at the end of their column name.
    They group them in a list of list to be able to parse later.
    The list as the columns name for later operation on the df.
    1. Loop through the columns of the dataframe
    2. Check if the question is similar to the previous one,
    if it is True, it add it to a list until it is False
    3. When it is False, add that list to a larger list that
    contains all the columns split in group lists.

    :params:
        pd.dataframe(): dataframe to parse all columns

    :return:
        list(): a list() of list() of columns name str(). Each list
        contains one group of question.
        If a list only contains one question, this question doesn't belong
        to any group
    """
    def compare_question(current_question, previous_question, current_particule, previous_particule):
        """
        """
        current_q = current_question.replace(current_particule, '')
        previous_q = previous_question.replace(previous_particule, '')
        if current_q == previous_q:
            # if set(df[col].unique()) == set(df[previous_col].unique()):
            return True

    def get_particule(col):
        """
        Do a regex match to get the bracket content and return the
        matched string, or None if not

        :param:
            col str(): the column name to apply the regex on it

        :return:
            last_bit str(): the str between the bracket (w/ the bracket)
            None, if no match is found
        """
        re_match_brac = '\[([^]]+)\]'
        last_bit = re.search(re_match_brac, col)
        if last_bit:
            return last_bit[0]  # If [0], output w/ [], if [1] output w/o []

    def check_similar_q(col, full_list, current_list):
        """
        Check if the colnames passed is similar to the previous
        one.
        First it check if the size of the list is
        It removed the text within brackets and the brackets
        to compare if the two strings are similar.

        :params:
            col str(): column name
            full_list list(): entire list of the all passed grouped questions
            current_list list(): the current list of the previous questions.

        :returns:
            full_list list(): the same full_list appended with the current_list
            if the current question was different than the previous one
            current_list list(): the same current_list, appended with the current
            question if similar to the last element of it or a new one only composed
            of the current question if it was different
        """
        # if len(current_list) > 0:
        current_particule = get_particule(col)
        previous_particule = get_particule(current_list[-1])
        if current_particule and previous_particule:
            if compare_question(col, current_list[-1], current_particule, previous_particule):
                current_list.append(col)
                return full_list, current_list
        full_list.append(current_list)
        current_list = [col]
        return full_list, current_list


    def split_group(group_q):
        """
        Split the list into one list with single element
        and a list with the grouped questions
        :param:
            group_q list(): list of the list
            of question previously grouped or not

        :returns:
            single_q list(): list of single question
            group_q list(): list of group of questions
        """
        single_q = list()
        i = 0
        while i < len(group_q):
            if len(group_q[i]) == 1:
                single_q.append(group_q.pop(i))
            else:
                i+=1
        return single_q, group_q

    grouped_question = list()
    for col in df.columns:
        try:
            grouped_question, current_list = check_similar_q(col, grouped_question, current_list)
        except (NameError, TypeError):  # NameError when it parsed the 1st column
            current_list = [col]

    single_q, group_q = split_group(grouped_question)
    return single_q, group_q

df = duplicating_other(df)
single_q, group_q = grouping_question(df)



# # Split grouped questions in type

for col in group_q:
    for c in col:
        print(c)
        print(len(df[c].unique()))
        print(df[c].unique())
        print('\n')

for q in single_q:
    print(q)
    print('\n')
    print(df[q[0]].unique())
    print('\n')
    print('\n')
    print('\n')
    print('\n')


# # Write the question type into a config file for plotting

# # Write the filtered df into a new file to be used for later analysis
