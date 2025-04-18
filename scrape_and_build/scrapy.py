import argparse
import os
import pandas as pd
import re
import requests
from bs4 import *
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# download and webscrape each news article from a given set of urls which reference mdr news articles read from a
# text file and also download the article's metadata
def download_document(filename, name):
    with open(filename, 'r') as file:
        article_count = 0
        print('Download urls from file {0}'.format(filename))
        print('\n------------------------------------------------------------------------\n')
        metadata = {}
        lines = file.readlines()
        document_name = ''
        url = ''
        for url in lines:
            url = url.strip('\n')
            easy = False
            if url.startswith('http'):
                # set if simpletext or regular, default is regular German
                prefix_identifier = 'r'
                if article_count % 2 == 1:
                    prefix_identifier = 'e'
                    easy = True
                # set index of document pair
                pair_index = int(article_count / 2)
                prefix_identifier += str(pair_index)
                # set file name, create or check for directory and set save path
                file_name = name
                if not os.path.exists('./mdr_articles'):
                    os.makedirs('./mdr_articles')
                save_path = './mdr_articles'
                directory = "/" + file_name
                os.makedirs(save_path, exist_ok=True)
                os.makedirs(save_path + directory, exist_ok=True)
                document_name = prefix_identifier + '_' + file_name + '.txt'
                # set session parameters for webscraping, see docu
                # at https://docs.python-requests.org/en/latest/user/advanced/
                session = requests.Session()
                retry = Retry(total=8, backoff_factor=2)
                adapter = HTTPAdapter(max_retries=retry)
                session.mount('https://', adapter)
                page = session.get(url, timeout=10)
                content = page.content
                # get text elements using bs4, parse using the html parser and filter for all paragraphs and subheadings
                le_soup = BeautifulSoup(content, 'html.parser', from_encoding='utf-8')
                title = ''
                if le_soup.title:
                    title = le_soup.title.string
                paragraphs = le_soup.find_all(['p', 'h3'], class_=["text", "einleitung", "subtitle"])

                # scrape raw text to get mdr news article
                text = ''
                p = 0
                size = len(paragraphs)
                for paragraph in paragraphs:
                    # write each paragraph to the buffer
                    p += 1
                    p_text = paragraph.text
                    if p == size:
                        # check if last line contains credits without meaning, if so disregard the line
                        lastline = re.findall('(MDR)|(dpa)', p_text)
                        if lastline:
                            continue
                    text += p_text + '\n'
                # clean text by removing redundant linebreaks and characters that cannot be as utf-8
                text = re.sub('(\n){3,}', '\n\n', text)
                text = re.sub('([^a-zA-ZÄÜÖäüößéí\d:!?\.\,\- \"\'\\n•])', ' ', text)
                text = re.sub(r'([.!?:])([A-Z])', r'\1 \2', text)
                text.encode('utf-8')

                try:
                    # download metadata
                    metadata = download_metadata(le_soup, document_name, title, content, text, url, article_count, metadata)
                except:
                    # don't crash if metadata unavailable
                    return [], document_name + ':  ' + url

                document_directory = save_path + directory + '/' + document_name
                if not os.path.exists('./mdr_articles/all_files/'):
                    os.makedirs('./mdr_articles/all_files/')
                if not os.path.exists('./mdr_articles/all_easy/'):
                    os.makedirs('./mdr_articles/all_easy/')
                if not os.path.exists('./mdr_articles/all_regular/'):
                    os.makedirs('./mdr_articles/all_regular/')
                document_all_files = './mdr_articles/all_files/' + document_name
                document_easy_files = './mdr_articles/all_easy/' + document_name
                document_regular_files = './mdr_articles/all_regular/' + document_name

                # write data to all files and individual directories needed to build and assess the dataset
                with open(document_directory, 'w') as d:
                    d.write(title + '\n\n' + text)
                    print(document_name + ':  ' + url)
                # write to directory containing all files
                with open(document_all_files, 'w') as d:
                    d.write(title + '\n\n' + text)
                if easy:
                    # write to directory containing only easy-to-read / 'leichte sprache' files
                    with open(document_easy_files, 'w') as d:
                        d.write(title + '\n\n' + text)
                else:
                    # write to directory containing only regular German files
                    with open(document_regular_files, 'w') as d:
                        d.write(title + '\n\n' + text)
                article_count += 1

        return metadata, document_name + ':  ' + url


# get all metadata of one document from parsed html soup to later write to metadata file
def download_metadata(le_soup, document_name, title, content, text, url, count, metadata):
    # download metadata
    date = le_soup.find('meta', attrs={"name": "date"})
    if date:
        date = date['content']
    else:
        date = 'None'
    description = le_soup.find('meta', attrs={"name": "description"})
    if description:
        description = description['content']
    else:
        description = 'None'
    keywords = le_soup.find('meta', attrs={"name": "keywords"})
    if keywords:
        keywords = keywords['content']
    else:
        keywords = 'None'
    metadata.update({count: {'document_name': document_name, 'title': title, 'description': description,
                             'url': url, 'date': date, 'keywords': keywords, 'data': title + '\n\n' + text,
                             'raw_html': content}})
    return metadata


# write metadata gained from all documents to separate files at designated location
def write_metadata(metadata, path, file):
    document_name = []
    title = []
    description = []
    url = []
    date = []
    keywords = []
    cleaned_text = []
    raw_html = []
    relation = []

    # determine relation between easy german and regular german samples
    for i in range(len(metadata.keys())):
        meta = metadata[i]

        document_name.append(meta['document_name'])
        title.append(meta['title'])
        description.append(meta['description'])
        url.append(meta['url'])
        date.append(meta['date'])
        keywords.append(meta['keywords'])
        cleaned_text.append(meta['data'])
        raw_html.append(meta['raw_html'])

        # if sample is in leichte sprache, check sample index-wise before which is pairwise sample in regular language
        if i % 2 == 1:
            meta_relation = metadata[i - 1]
        # if sample is in regular German, check sample index-wise after which is pairwise sample in leichte sprache
        else:
            meta_relation = metadata[i + 1]

        relation_name = meta_relation['document_name']
        relation_title = meta_relation['title']
        relation.append(relation_name + '; ' + relation_title)

    df = pd.DataFrame()
    df['Document_Name'] = document_name
    df['Title'] = title
    df['Keywords'] = keywords
    df['Url'] = url
    df['Date'] = date
    df['Description'] = description
    df['Cleaned_text'] = cleaned_text
    df['Raw_html'] = raw_html
    df['Relation'] = relation
    df.columns = ['Document_Name', 'Title', 'Keywords', 'Url', 'Date',
                  'Description', 'Cleaned_text', 'Raw_html', 'Relation']
    # write metadata to csv
    df.to_csv(path + '/{0}_Metadata_EasyGerman.csv'.format(file), encoding='utf-8', index=False)


def download_single_file(file, path, errorlog):
    filename = str(file.split('.txt')[0])
    document_name = ''
    print('\n------------------------------------------------------------------------\n')
    print(filename)
    print('\n------------------------------------------------------------------------\n')
    metadata, document_name = download_document(path + '/' + file, filename)
    if not metadata:
        print('\n-------------------------------------\n')
        print(
            '\n {0}:  {1}\n'.format(path.split('/')[len(path.split('/'))-1], filename))
        print('\n-------------------------------------\n')
        errorlog.write(
            '\n {0}:  {1}\n'.format(path.split('/')[len(path.split('/'))-1], filename))
    else:
        write_metadata(metadata, './metadata' + '/' + path, filename)


# recursively download news article files from input
def webscrape_rec(input, path, errorlog):
    # if input is a single directory
    if input == path:
        if os.path.isdir(path):
            if not os.path.exists('./metadata' + '/' + path):
                os.makedirs('./metadata' + '/' + path)
            files = os.listdir(path)
            for file in files:
                webscrape_rec(file, path, errorlog)
        # if input is a file not directory then webscrape its urls
        else:
            download_single_file(input, path, errorlog)
    # if input is a nested nested directory
    else:
        if os.path.isdir(path + '/' + input):
            if not os.path.exists('./metadata' + '/' + path + '/' + input):
                os.makedirs('./metadata' + '/' + path + '/' + input)
            files = os.listdir(path + '/' + input)
            for file in files:
                webscrape_rec(file, path + '/' + input, errorlog)
        # if input is a file not directory then webscrape its urls
        else:
            download_single_file(input, path, errorlog)


# script to download a urls referencing pairs of german news websites in regular and easy language / 'leichte Sprache'
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input', type=str, nargs='?',
                        help='single directory, nested directory or single text file containing urls to be downloaded to later build the EasyGerman dataset')
    args = parser.parse_args()
    input = args.input

    # make folder to write metadata into
    if not os.path.exists('./metadata'):
        os.makedirs('./metadata')

    # download all given urls in folder or file given as input
    with open('./metadata/errorlog.txt', 'w') as errorlog:
        errorlog.write('Error log of Metatdata Download for EasyGerman Dataset\n\nthe following files could not be fully downloaded:\n')
        webscrape_rec(input, input, errorlog)


if __name__ == '__main__':
    main()
