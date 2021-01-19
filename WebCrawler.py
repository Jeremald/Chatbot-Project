# Homework 5 Jason Garza

from bs4 import BeautifulSoup
from nltk.tokenize import sent_tokenize
from nltk import word_tokenize
from nltk.corpus import stopwords
import requests
import re
import sqlite3
from sqlite3 import Error

url_count = 25


def web_crawler():
    starter_url = 'https://www.digitaltrends.com/mobile/best-folding-phones/'
    r = requests.get(starter_url)
    data = r.text
    soup = BeautifulSoup(data, 'html.parser')

    counter = 0
    sub_link_index = 0
    url_list = []

    with open('urls.txt', 'w') as f:
        # keep going until we get 20 links
        while counter < url_count:
            for link in soup.findAll('a'):
                link_str = str(link.get('href'))
                # don't allow duplicate links
                if link_str in url_list:
                    continue
                # narrow down urls. Rules (from lots of trial and error):
                # must start with http
                # must be about phones, not headphones
                # no jpg files (no text to extract)
                # no links to huawei's website. That's not an article, it's a store page
                # must be about folding phones, if fold is in url it is probably about folding phones
                # Could be an article about the Microsoft Duo that does not have fold in the url
                # Could be an article about the Huawei Mate X that does not have fold in the url
                # Could be an article about the Motorola Razr that does not have fold in the url
                if link_str.startswith('http') and 'phone' in link_str and 'headphone' not in link_str and '.jpg' not in link_str and 'huawei.com' not in link_str:
                    if 'fold' in link_str or 'duo' in link_str or 'mate-x' in link_str or 'razr' in link_str:
                        f.write(link_str + '\n')
                        url_list.append(link_str)
                        # stop once we reach the desired number of urls
                        counter += 1
                        if counter >= url_count:
                            break
            # if we haven't reached 20 yet and need to go to next iteration of while loop
            r = requests.get(url_list[sub_link_index])
            # don't expand this url again
            sub_link_index += 1
            data = r.text
            soup = BeautifulSoup(data, 'html.parser')


def get_url_text():
    # file number
    i = 1
    # get urls from file
    with open('urls.txt', 'r') as f:
        urls = f.read().splitlines()
    # get data from each url
    for url in urls:
        html = requests.get(url)
        # Did it this way because if I didn't, many of my files had weird characters instead of the website text
        soup = BeautifulSoup(html.content, 'html.parser', from_encoding='utf-8')
        data = soup.findAll(text=True)
        result = filter(visible, data)
        text_list = list(result)
        text = ' '.join(text_list)
        # write url text to a file
        with open('url' + str(i) + 'text.txt', 'w') as f:
            f.write(text)
        # increase file number so next url writes to different file
        i += 1


def visible(element):
    if element.parent.name in ['style', 'script', '[document]', 'head', 'title']:
        return False
    elif re.match('<!--.*-->', str(element.encode('utf-8'))):
        return False
    return True


def get_url_sentences():
    i = 1
    while i <= url_count:
        with open('url' + str(i) + 'text.txt', 'r') as f:
            text = f.read()
        text = text.replace('\n', '')
        text = text.replace('\t', '')
        # Articles start with date. This gets rid of links at top of page (Removes text before date)
        date = re.search(r'[A-Za-z]{3,}\.?\s+[0-9]{1,2},? [0-9]{4}', text)
        if date:
            text = text[date.start():]
        sentences = sent_tokenize(text)
        with open('url' + str(i) + 'sentences.txt', 'w') as f:
            for sentence in sentences:
                # remove weird formatting from picture based article
                if sentence.startswith('Read the article          '):
                    sentence = sentence[154:]
                    if sentence.strip().startswith('Read the article          '):
                        continue
                # remove unimportant stuff from end of article
                elif sentence.startswith('More Galleries'):
                    continue
                # remove long stuff from end of articles
                elif sentence.startswith('Editors\' Recommendations') or sentence.startswith('Comments          '):
                    break
                f.write(sentence + ' ')
        i += 1


def important_terms():
    i = 1
    raw_text = ''
    # combine text of all sentences files
    while i <= url_count:
        with open('url' + str(i) + 'sentences.txt', 'r') as f:
            raw_text += f.read()
        i += 1
    # lower case and remove punctuation
    text = re.sub(r'[.?!,:;()\-\n]', ' ', raw_text.lower())
    # tokenize then remove stopwords
    tokens = word_tokenize(text)
    tokens = [t for t in tokens if t not in stopwords.words('english')]
    # create term frequency dictionary (each unique term and the count of how many times it appears in the files)
    unique_tokens = set(tokens)
    tf_dict = {t: tokens.count(t) for t in unique_tokens}
    # sort by descending count
    sorted_tf = sorted(tf_dict.items(), key=lambda x: x[1], reverse=True)
    for i in range(40):
        print(i + 1, sorted_tf[i])


def build_database():
    with open('urls.txt', 'r') as f:
        urls = f.read().splitlines()
    # classify each url by the phone it talks about. This way the chat bot can look up info about specific phones.
    galaxy_fold = []
    duo = []
    mate_x = []
    tcl = []
    google = []
    apple = []
    other = []

    i = 1
    # add each url to appropriate list
    for url in urls:
        if 'samsung' in url:
            galaxy_fold.append('url' + str(i) + 'sentences.txt')
        elif 'tcl' in url:
            tcl.append('url' + str(i) + 'sentences.txt')
        elif 'mate' in url:
            mate_x.append('url' + str(i) + 'sentences.txt')
        elif 'duo' in url:
            duo.append('url' + str(i) + 'sentences.txt')
        elif 'google' in url:
            google.append('url' + str(i) + 'sentences.txt')
        elif 'apple' in url or 'iphone' in url:
            apple.append('url' + str(i) + 'sentences.txt')
        # urls that talk about more than one phone, or just left phone name out of url.
        else:
            other.append('url' + str(i) + 'sentences.txt')
        i += 1

    # create sqlite database
    conn = sqlite3.connect('facts.db')
    # create table for each phone
    for phone in ['galaxy_fold', 'duo', 'mate_x', 'tcl', 'google', 'apple']:
        # Create table for each phone with two attributes:
        # fact, which is the fact being stored
        # category, which will allow the chat bot to get more specific facts about a phone
        # (such as facts about the display, which will have the display category)
        # normally this is vulnerable to sql injection, but since this is not user input it should be fine
        query = 'CREATE TABLE IF NOT EXISTS ' + phone + '(fact TEXT PRIMARY KEY, category TEXT NOT NULL);'
        execute_query(conn, query)
    # add phone facts (used pixel and iphone for phone name since those are used in articles when talking about phone)
    add_phone_facts(conn, 'galaxy_fold', 'fold', galaxy_fold)
    add_phone_facts(conn, 'duo', 'duo', duo)
    add_phone_facts(conn, 'mate_x', 'mate x', mate_x)
    add_phone_facts(conn, 'tcl', 'tcl', tcl)
    add_phone_facts(conn, 'google', 'pixel', google)
    add_phone_facts(conn, 'apple', 'iphone', apple)
    # gets facts from documents that may talk about more than one phone
    add_other_facts(conn, other)

    conn.commit()
    conn.close()


def execute_query(connection, query):
    cursor = connection.cursor()
    try:
        cursor.execute(query)
    except Error as e:
        print('Error:', e)


def add_phone_facts(connection, table_name, phone_name, doc_list):
    # get facts from each document in doc_list
    for document in doc_list:
        with open(document, 'r') as d:
            raw_text = d.read()
            raw_text = raw_text.replace('\n', '')
            raw_text = raw_text.replace('\t', '')
            # remove single quotes since that messes up the sql command syntax
            raw_text = raw_text.replace('\'', '')
        # get sentences from document
        sentences = sent_tokenize(raw_text)
        for sentence in sentences:
            query = None
            # if sentence is fact about display / screen, add to table_name with category display
            if 'screen' in sentence.lower() or 'display' in sentence.lower():
                query = 'INSERT INTO ' + table_name + ' (fact, category) VALUES (\'' + sentence + '\',\'display\');'
            # if sentence is fact about camera, add to table_name with category camera
            elif 'camera' in sentence.lower():
                query = 'INSERT INTO ' + table_name + ' (fact, category) VALUES (\'' + sentence + '\',\'camera\');'
            # if sentence is fact how the phone handles apps, add to table_name with category apps
            elif 'apps' in sentence.lower():
                query = 'INSERT INTO ' + table_name + ' (fact, category) VALUES (\'' + sentence + '\',\'apps\');'
            # if sentence is general fact about phone, add to table_name with category general
            elif phone_name in sentence.lower():
                query = 'INSERT INTO ' + table_name + ' (fact, category) VALUES (\'' + sentence + '\',\'general\');'
            # if we decided this sentence is a fact that must be added to the database, add it
            if query:
                execute_query(connection, query)


def add_other_facts(connection, doc_list):
    # get facts from each document
    for document in doc_list:
        with open(document, 'r') as d:
            raw_text = d.read()
            raw_text = raw_text.replace('\n', '')
            raw_text = raw_text.replace('\t', '')
            # remove single quotes since that messes up the sql command syntax
            raw_text = raw_text.replace('\'', '')
        # get sentences from document
        sentences = sent_tokenize(raw_text)
        for sentence in sentences:
            query = None
            sentence = sentence.lower()
            # if sentence is about the galaxy fold
            # use galaxy, in these articles fold could be used to mention folding phones in general
            if 'galaxy' in sentence:
                if 'display' in sentence or 'screen' in sentence:
                    query = 'INSERT INTO galaxy_fold (fact, category) VALUES (\'' + sentence + '\',\'display\');'
                elif 'camera' in sentence:
                    query = 'INSERT INTO galaxy_fold (fact, category) VALUES (\'' + sentence + '\',\'camera\');'
                elif 'apps' in sentence:
                    query = 'INSERT INTO galaxy_fold (fact, category) VALUES (\'' + sentence + '\',\'apps\');'
                else:
                    query = 'INSERT INTO galaxy_fold (fact, category) VALUES (\'' + sentence + '\',\'general\');'
            # if sentence is about the microsoft duo
            elif 'duo' in sentence:
                if 'display' in sentence or 'screen' in sentence:
                    query = 'INSERT INTO duo (fact, category) VALUES (\'' + sentence + '\',\'display\');'
                elif 'camera' in sentence:
                    query = 'INSERT INTO duo (fact, category) VALUES (\'' + sentence + '\',\'camera\');'
                elif 'apps' in sentence:
                    query = 'INSERT INTO duo (fact, category) VALUES (\'' + sentence + '\',\'apps\');'
                else:
                    query = 'INSERT INTO duo (fact, category) VALUES (\'' + sentence + '\',\'general\');'
            # if sentence is about the mate x
            elif 'mate x' in sentence:
                if 'display' in sentence or 'screen' in sentence:
                    query = 'INSERT INTO mate_x (fact, category) VALUES (\'' + sentence + '\',\'display\');'
                elif 'camera' in sentence:
                    query = 'INSERT INTO mate_x (fact, category) VALUES (\'' + sentence + '\',\'camera\');'
                elif 'apps' in sentence:
                    query = 'INSERT INTO mate_x (fact, category) VALUES (\'' + sentence + '\',\'apps\');'
                else:
                    query = 'INSERT INTO mate_x (fact, category) VALUES (\'' + sentence + '\',\'general\');'
            # if sentence is about tcl's folding phones
            elif 'tcl' in sentence:
                if 'display' in sentence or 'screen' in sentence:
                    query = 'INSERT INTO tcl (fact, category) VALUES (\'' + sentence + '\',\'display\');'
                elif 'camera' in sentence:
                    query = 'INSERT INTO tcl (fact, category) VALUES (\'' + sentence + '\',\'camera\');'
                elif 'apps' in sentence:
                    query = 'INSERT INTO tcl (fact, category) VALUES (\'' + sentence + '\',\'apps\');'
                else:
                    query = 'INSERT INTO tcl (fact, category) VALUES (\'' + sentence + '\',\'general\');'
            # if sentences is about a potential google folding phone
            # use google, in these articles pixel may be reference to screen resolution
            elif 'google' in sentence:
                if 'display' in sentence or 'screen' in sentence:
                    query = 'INSERT INTO google (fact, category) VALUES (\'' + sentence + '\',\'display\');'
                elif 'camera' in sentence:
                    query = 'INSERT INTO google (fact, category) VALUES (\'' + sentence + '\',\'camera\');'
                elif 'apps' in sentence:
                    query = 'INSERT INTO google (fact, category) VALUES (\'' + sentence + '\',\'apps\');'
                else:
                    query = 'INSERT INTO google (fact, category) VALUES (\'' + sentence + '\',\'general\');'
            # if sentence is about a potential folding iphone
            elif 'apple' in sentence or 'iphone' in sentence:
                if 'display' in sentence or 'screen' in sentence:
                    query = 'INSERT INTO apple (fact, category) VALUES (\'' + sentence + '\',\'display\');'
                elif 'camera' in sentence:
                    query = 'INSERT INTO apple (fact, category) VALUES (\'' + sentence + '\',\'camera\');'
                elif 'apps' in sentence:
                    query = 'INSERT INTO apple (fact, category) VALUES (\'' + sentence + '\',\'apps\');'
                else:
                    query = 'INSERT INTO apple (fact, category) VALUES (\'' + sentence + '\',\'general\');'
            # if we decided this sentence is a fact that must be added to the database, add it
            if query:
                execute_query(connection, query)


if __name__ == '__main__':
    # web_crawler()
    # get_url_text()
    # get_url_sentences()
    # important_terms()
    build_database()
