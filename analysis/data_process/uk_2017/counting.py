#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import pandas as pd
import numpy as np

from config import CleaningConfig, NotebookConfig
from cleaning import CleaningData
from action_file import grouping_likert_yn
from plotting import get_plot

def freq_table(df, colnames=False, columns='count', add_ratio=False, sort_order=False):
    """
    """
    if colnames:
        df_to_freq = df[colnames]
    else:
        df_to_freq = df
    if add_ratio:
        output = pd.concat([pd.crosstab(df_to_freq, columns='count', normalize=False),
                            pd.crosstab(df_to_freq, columns='ratio', normalize=True)],
                           axis=1)
    else:
        output = pd.crosstab(df_to_freq, colnames=[''], columns=columns)
    if sort_order:
        output = output.sort_values(by='count')
    return output


def count_choice(df, colnames, rename_columns=False,
                 dropna=False, normalize=False,
                 multiple_choice=False, sort_values=False):
    """
    Count the values of different columns and transpose the count
    :params:
        :df pd.df(): dataframe containing the data
        :colnames list(): list of strings corresponding to the column header to select the right column
    :return:
        :result_df pd.df(): dataframe with the count of each answer for each columns
    """
    df_sub = df[colnames]

    if rename_columns is True:
        df_sub.columns = [s.split('[', 1)[1].split(']')[0] for s in colnames]

    # Calculate the counts for them
    if multiple_choice is True:
        df_sub = df_sub[df_sub == 'Yes'].apply(pd.Series.value_counts, dropna=dropna, normalize=normalize)
    else:
        df_sub = df_sub.apply(pd.Series.value_counts, dropna=dropna, normalize=normalize)
    if sort_values is True:
        df_sub.sort_values(ascending=False, inplace=True)
    # Transpose the column to row to be able to plot a stacked bar chart
    return df_sub.transpose()


def count_yn(df, colnames, multiple=False, normalize=False, dropna=False, sort_values=False):
    """
    """
    if multiple is True:
        df_sub = df[colnames]
    else:
        df_sub = df[colnames].to_frame(name=colnames)


    df_sub = df_sub.apply(pd.Series.value_counts,
                          dropna=dropna,
                          normalize=normalize)
    if sort_values is True:
        df_sub.sort_values(ascending=False, inplace=True)
    # Transpose the column to row to be able to plot a stacked bar chart
    df_sub = df_sub.transpose()
    if dropna is True:
        df_sub = df_sub[['Yes', 'No']]
    else:
        df_sub = df_sub[['Yes', 'No', 'NA']]
    if multiple is False:
        print(df_sub)
    return df_sub



def get_count(df, questions, type_question):
    """
    Choose which type of counting needs to be done

    :params:
        df dataframe(): dataframe containing all the data
        questions list(): list of the question strings to
        type_questions str(): type of questions that list_questions represent

    :return:
    """
    #
    # questions = [i for j in questions for i in j]

    if type_question.lower() == 'y/n/na':
        if len(questions) == 1:
            print('Single YN')
            questions = questions[0]
            multiple = False
            normalize = False
        else:
            print('Multiple YN')
            multiple = True
            normalize = True
        return count_yn(df, questions, multiple=multiple, normalize=normalize,
                        dropna=True)


    elif type_question.lower() == 'one choice':
        pass
        # return count_choice(df, questions, multiple_choice=False)

    elif type_question.lower() == 'multiple choice':
        pass
        # return count_choice(df, questions, multiple_choice=True)

    elif type_question.lower() == 'likert':
        pass
    elif type_question.lower() == 'ranking':
        pass
    elif type_question.lower() == 'freetext':
        pass
    elif type_question.lower() == 'freenumeric':
        pass
    elif type_question.lower() == 'datetime':
        pass
    else:
        pass


def main():
    """
    """
    pd.set_option('display.max_rows', 300)

    # Load dataset
    df = pd.read_csv(CleaningConfig.raw_data)

    # Cleaning_process
    cleaning_process = CleaningData(df)
    df = cleaning_process.cleaning()
    cleaning_process.write_df()
    cleaning_process.write_config_file()
    for s in cleaning_process.structure_by_section:
        section = cleaning_process.structure_by_section[s]
        for group in section:
            for question in grouping_likert_yn(section[group]):
                list_questions = question[0]
                original_question = question[1]
                answer_format = question[2]
                try:
                    v_to_count = get_count(df, list_questions, answer_format)
                    plot = get_plot(v_to_count, answer_format)
                    plot
                    # if v_to_count is not None:
                    #     print(v_to_count)

                    # notebook.add_freq_table(list_questions, answer_format)
                    # notebook.add_plot(counted_value, answer_format, file_answer)
                except KeyError:
                    print('Error for the question: {}'.format(original_question))
                except AttributeError:
                    print('Nothing return')


if __name__ == "__main__":
    main()
