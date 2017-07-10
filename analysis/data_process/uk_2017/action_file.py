#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pandas as pd
from config import CleaningConfig, NotebookConfig
from cleaning import CleaningData
from generate_notebook import GenerateNotebook

"""
Action file that holds all the different configuration for a
specific dataset.

Import the specific cleaning and plotting methods that are
in the same folder
"""


# FIXME Move that function into cleaning
def grouping_likert_yn(group_question):
    """
    """
    regroup_q, regroup_txt_q = list(), list()
    previous_type = None
    previous_file_answer = None
    for q in group_question:
        print(group_question[q])
        current_type = group_question[q]['answer_format'].lower()
        survey_q = group_question[q]['survey_q']
        original_q = group_question[q]['original_question']
        file_answer = group_question[q]['file_answer']

        if previous_type in ['y/n/na', 'likert'] or current_type in ['y/n/na', 'likert']:
            if current_type == previous_type or previous_type is None:
                if previous_type == 'likert' and current_type == 'likert':
                    if previous_file_answer != file_answer:
                        yield regroup_q, regroup_txt_q, previous_type, previous_file_answer
                        regroup_q, regroup_txt_q = list(), list()
                regroup_q.extend(survey_q)
                regroup_txt_q.append(original_q)
            else:
                yield regroup_q, regroup_txt_q, previous_type, previous_file_answer
                regroup_q, regroup_txt_q = list(), list()
                regroup_q.extend(survey_q)
                regroup_txt_q.append(original_q)
        else:
            if len(regroup_q) > 0:
                yield regroup_q, regroup_txt_q, previous_type, previous_file_answer
            regroup_q, regroup_txt_q = list(), list()
            regroup_q.extend(survey_q)
            regroup_txt_q.append(original_q)

        previous_type = current_type
        previous_file_answer = file_answer

    yield regroup_q, regroup_txt_q, previous_type, file_answer


def main():
    pd.set_option('display.max_rows', 300)

    # Load dataset
    df = pd.read_csv(CleaningConfig.raw_data)

    # Cleaning_process
    cleaning_process = CleaningData(df)
    df = cleaning_process.cleaning()
    cleaning_process.write_df()
    cleaning_process.write_config_file()

    # Notebook writing
    notebook = GenerateNotebook(NotebookConfig.notebook_filename)

    for s in cleaning_process.structure_by_section:
        section = cleaning_process.structure_by_section[s]
        notebook.add_section(s)
        for group in section:
            notebook.add_group(group)
            for question in grouping_likert_yn(section[group]):
                list_questions = question[0]
                original_question = question[1]
                answer_format = question[2]
                file_answer = question[3]
                try:
                    for txt in original_question:
                        notebook.add_question_title(txt)
                    notebook.add_count(list_questions, answer_format, file_answer)
                    notebook.add_display_count()
                    # if answer_format in ['y/n/na', 'one choice']:
                    #     notebook.add_percentage()
                    #     notebook.add_display_percentage()
                    notebook.add_plot(answer_format)
                except KeyError:
                    print('Error for the question: {}'.format(original_question))

    print('Running notebook')
    notebook.run_notebook()
    # Catching error before saving
    print('Saving notebook')
    notebook.save_notebook()


if __name__ == "__main__":
    main()
