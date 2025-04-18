import argparse
import hvplot
import itertools
import math
import numpy as np
import os
import re
import pandas as pd
from bokeh.models import NumeralTickFormatter
from nltk.corpus import stopwords
from nltk import word_tokenize


# filter out documents that contain more tokens than the given number
def check_if_over_max_tokens(directory, blacklist, max, easy):
    files = os.listdir(directory)
    for filename in files:
        with open(os.path.join(directory, filename), mode='r') as f:
            lines = f.read()
            words_list = word_tokenize(lines)
            words = len(words_list)
            if words > max:
                if filename not in blacklist:
                    blacklist.append(filename)
                if easy:
                    pair = 'r' + filename[1:]
                else:
                    pair = 'e' + filename[1:]
                if pair not in blacklist:
                    blacklist.append(pair)
    return blacklist


# remove duplicate articles and their pairs, excluding them from the dataset
def remove_duplicates(directory, blacklist, easy):
    files = os.listdir(directory)
    all_files = []
    for filename in files:
        with open(os.path.join(directory, filename), mode='r') as f:
            lines = f.read()
            page_not_found = re.findall('(Seite nicht gefunden)', lines)
            if lines in all_files or page_not_found or lines == '\n\n':
                if filename not in blacklist:
                    blacklist.append(filename)
                if easy:
                    pair = 'r' + filename[1:]
                else:
                    pair = 'e' + filename[1:]
                if pair not in blacklist:
                    blacklist.append(pair)
            else:
                all_files.append(lines)
    return blacklist


# get the vocabulary size of individual documents using frequency info
def vocab_individual_texts(data):
    data = [word for word in data if re.match('([a-zA-ZÄÜÖäüößéí\d])', word)]
    word_freq_total = pd.Series(data).value_counts()
    vocab_size = word_freq_total.size
    return vocab_size


# get the vocabulary size and other statistics for all of the given documents
def get_vocab(data, dataset_identifyer):
    data = list(itertools.chain.from_iterable(data))
    data = [word for word in data if re.match('([a-zA-ZÄÜÖäüößéí\d])', word)]
    word_freq_total = pd.Series(data).value_counts()
    vocab_size = word_freq_total.size
    german_stop_words = stopwords.words('german')
    vocabulary_words = word_freq_total.index.values
    words_cleaned = [word for word in data if word.lower() not in german_stop_words and not re.match(
        '(mdr.de)', word.lower())]
    word_freq_cleaned = pd.Series(words_cleaned).value_counts()
    cleaned_vocab_words = word_freq_cleaned.index.values
    plot = word_freq_cleaned[1:25].rename(
        "Word frequency of most common cleaned words in {0} documents".format(dataset_identifyer)).hvplot.bar(
        rot=45
    ).opts(width=700, height=400, yformatter=NumeralTickFormatter(format="0,0"))
    hvplot.save(plot, '{0}_hist_word_freq.png'.format(dataset_identifyer), fmt='png')
    table = word_freq_cleaned[1:50].reset_index(
        name="frequency").hvplot.table()  # columns=['words', 'frequency'], selectable=True
    hvplot.save(table, '{0}_words_by_freq.png'.format(dataset_identifyer), fmt='png')
    return vocab_size, vocabulary_words, word_freq_cleaned, cleaned_vocab_words


# get text from documents and analyse data
def statistics_and_data(directory, blacklist, dataset_identifyer):
    files = os.listdir(directory)
    max_len = 0
    data = {}
    data_word_tokenized = {}
    words = []
    sents = []
    letters = []
    vocab_per_document = []
    count = 0
    files_removed = 0
    for filename in files:
        with open(os.path.join(directory, filename), mode='r') as f:
            if filename in blacklist:
                files_removed += 1
            if filename not in blacklist:
                lines = f.read()
                words_tokenized = word_tokenize(lines)
                words_document = len(words_tokenized)
                if words_document > max_len:
                    max_len = words_document
                sents_document = count_sentences(lines)
                words.append(words_document)
                sents.append(sents_document)
                letters.append(len(''.join(words_tokenized)))
                vocab_size_file = vocab_individual_texts(words_tokenized)
                vocab_per_document.append(vocab_size_file)
                data[count] = lines
                data_word_tokenized[count] = words_tokenized
                count += 1
    vocab_size, vocabulary_words, word_freq_cleaned, words_cleaned = get_vocab(data_word_tokenized.values(),
                                                                               dataset_identifyer)

    return letters, words, sents, max_len, data, vocab_size, vocabulary_words, vocab_per_document, word_freq_cleaned, words_cleaned


# count the number of sentences using regular expressions
def count_sentences(text):
    # Match and count sentences. A sentence starts with an uppercase letter and ends with one of the defined
    # punctuation marks followed by a whitespace character.
    return len(re.findall(r'[•A-ZÄÖÜ].*?([.:!?]\s)', text))


# print and write out individual statistics
def print_and_write_data(max_tokens, max_len, num_files, vocab_size, vocab_file, letters, words, sents, language):
    print('\ntotal number of files: ' + str(num_files))
    print('total number of letters: ' + str(sum(letters)))
    print('total number of words: ' + str(sum(words)))
    print('total number of sentences: ' + str(sum(sents)))
    print('total vocabulary size: ' + str(vocab_size))
    print('average number of letters per word: ' + str(math.ceil(sum(letters) / sum(words))))
    print('average number of words per sentence: ' + str(math.ceil(sum(words) / sum(sents))))
    print('\naverage number of letters per file: ' + str(math.ceil(sum(letters) / num_files)))
    print('average number of words per file: ' + str(math.ceil(sum(words) / num_files)))
    print('average number of sentences per file: ' + str(math.ceil(sum(sents) / num_files)))
    print('average vocabulary size per file: ' + str(math.ceil(sum(vocab_file) / num_files)))
    print('\nmedian of the number of letters per file: ' + str(np.median(letters)))
    print('median of the number of words per file: ' + str(np.median(words)))
    print('median of the number of sentences per file: ' + str(np.median(sents)))
    print('median of the vocabulary size per file: ' + str(np.median(vocab_file)))
    print('\nmaximum number of words per file: ' + str(max_len) + '\n')

    filename = 'statistics_easyGerman_{0}'.format(max_tokens)
    if language:
        filename = filename + '_' + language
    filename += '.txt'

    save_path = './statistics'
    os.makedirs(save_path, exist_ok=True)

    with open(save_path + '/' + filename, 'w') as file:
        file.write('Dataset EasyGerman {0}\n'.format(language.capitalize()))
        file.write('\ntotal number of files: ' + str(num_files) + '\n')
        file.write('total number of letters: ' + str(sum(letters)) + '\n')
        file.write('total number of words: ' + str(sum(words)) + '\n')
        file.write('total number of sentences: ' + str(sum(sents)) + '\n')
        file.write('total vocabulary size: ' + str(vocab_size) + '\n')
        file.write('average number of letters per word: ' + str(math.ceil(sum(letters) / sum(words))) + '\n')
        file.write('average number of words per sentence: ' + str(math.ceil(sum(words) / sum(sents))) + '\n')
        file.write('\naverage number of letters per file: ' + str(math.ceil(sum(letters) / num_files)) + '\n')
        file.write('average number of words per file: ' + str(math.ceil(sum(words) / num_files)) + '\n')
        file.write('average number of sentences per file: ' + str(math.ceil(sum(sents) / num_files)) + '\n')
        file.write('average vocabulary size per file: ' + str(math.ceil(sum(vocab_file) / num_files)) + '\n')
        file.write('\nmedian of the number of letters per file: ' + str(np.median(letters)) + '\n')
        file.write('median of the number of words per file: ' + str(np.median(words)) + '\n')
        file.write('median of the number of sentences per file: ' + str(np.median(sents)) + '\n')
        file.write('median of the vocabulary size per file: ' + str(np.median(vocab_file)) + '\n')
        file.write('\nmaximum number of words per file: ' + str(max_len) + '\n')


# all calls to print and write different parts of data
def print_statistics(max_tokens, r_max_len, r_num_files, r_vocab_size, r_vocab_file, r_letters, r_words, r_sents,
                     e_max_len, e_num_files, e_vocab_size, e_vocab_file, e_letters, e_words, e_sents,
                     all_max_len, all_num_files, all_vocab_size, all_vocab_file, all_letters, all_words, all_sents):
    print('\n-------------------------------------------------------------------')
    print('\nDocuments Regular German\n')
    print_and_write_data(max_tokens, r_max_len, r_num_files, r_vocab_size, r_vocab_file, r_letters, r_words, r_sents,
                         language='regular')
    print('-------------------------------------------------------------------')
    print('\nDocuments Easy-to-read German\n')
    print_and_write_data(max_tokens, e_max_len, e_num_files, e_vocab_size, e_vocab_file, e_letters, e_words, e_sents,
                         language='easy-to-read')
    print('-------------------------------------------------------------------')
    print('\nDocuments entire Datset\n')
    print_and_write_data(max_tokens, all_max_len, all_num_files, all_vocab_size, all_vocab_file, all_letters, all_words,
                         all_sents, '')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('max_tokens', type=str, nargs='?',
                        help='max number of word tokens considered for dataset')
    # give the entire file path to the directories you wish to access
    parser.add_argument('dir_all', type=str, nargs='?',
                        help='directory of documents containing both easy and regular german')
    parser.add_argument('dir_regular', type=str, nargs='?',
                        help='directory of documents containing regular german')
    parser.add_argument('dir_easy', type=str, nargs='?',
                        help='directory of documents containing easy german')

    args = parser.parse_args()
    dir_regular = args.dir_regular
    dir_easy = args.dir_easy
    dir_all = args.dir_all
    max_tokens = 1024
    blacklist = []

    if not dir_regular:
        dir_regular = dir_regular
    if not dir_easy:
        dir_easy = dir_easy
    if not dir_all:
        dir_all = dir_all
    if max_tokens:
        max_tokens = int(args.max_tokens)

    blacklist = check_if_over_max_tokens(dir_regular, blacklist, max_tokens, False)
    blacklist = check_if_over_max_tokens(dir_easy, blacklist, max_tokens, True)
    name_tokens = '_' + str(max_tokens)

    blacklist = remove_duplicates(dir_regular, blacklist, False)
    blacklist = remove_duplicates(dir_easy, blacklist, True)
    print('\n- ' + str(len(blacklist)) + ' samples were removed -\n')

    # get all the statistical data and the text from each document
    r_letters, r_words, r_sents, r_max_len, r_data, r_vocab_size, r_vocabulary, r_vocab_per_document, r_word_freq_cleaned, r_words_cleaned = statistics_and_data(
        dir_regular, blacklist, 'Regular German')
    e_letters, e_words, e_sents, e_max_len, e_data, e_vocab_size, e_vocabulary, e_vocab_per_document, e_word_freq_cleaned, e_words_cleaned = statistics_and_data(
        dir_easy, blacklist, 'Leichte Sprache')
    all_letters, all_words, all_sents, all_max_len, all_data, all_vocab_size, all_vocabulary, all_vocab_per_document, all_word_freq_cleaned, all_words_cleaned = statistics_and_data(
        dir_all, blacklist, 'all')

    r_num_files = len(r_data)
    e_num_files = len(e_data)
    all_num_files = len(all_data)

    # print and write data to file
    print_statistics(max_tokens, r_max_len, r_num_files, r_vocab_size, r_vocab_per_document, r_letters, r_words,
                     r_sents,
                     e_max_len, e_num_files, e_vocab_size, e_vocab_per_document, e_letters, e_words, e_sents,
                     all_max_len, all_num_files, all_vocab_size, all_vocab_per_document, all_letters, all_words,
                     all_sents
                     )

    # build dataset as csv file
    df = pd.DataFrame()
    df['Regular German'] = r_data.values()
    df['Leichte Sprache'] = e_data.values()
    df.columns = ['Regular German', 'Leichte Sprache']
    df.to_csv('EasyGerman{0}.csv'.format(name_tokens), encoding='utf-8', index=False)
    # build small version with 100 samples for testing as csv file
    df_small = pd.DataFrame()
    df_small['Regular German'] = list(r_data.values())[:100]
    df_small['Leichte Sprache'] = list(e_data.values())[:100]
    df_small.columns = ['Regular German', 'Leichte Sprache']
    df_small.to_csv('EasyGerman{0}_small.csv'.format(name_tokens), encoding='utf-8', index=False)


if __name__ == '__main__':
    main()
