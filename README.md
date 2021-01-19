# Chatbot-Project

## How to install and run
1. Install spacy using the following command: ```pip3 install spacy```
2. Download the spacy model that I used by running this command: ```python3 -m spacy download en_core_web_sm```
3. Install VaderSentiment with the following command: ```pip3 install VaderSentiment```
4. Make sure that facts.db is in the same directory as main.py, then the program can simply be run with ```python3 main.py``` assuming that directory is work current working directory.

WebCrawler.py is not required for this program to run, its just for if you want to see how I created the database.

## How it works
The first part of this project was creating the database. That was done using a webcrawler program that started with one article about a folding smartphone and
followed links to similar articles. The webcrawler retreived facts about folding smartphones and stored them in the database. The database was trimmed down a
little bit by me to make sure that the facts would make grammatical sense if used by the chatbot. The chatbot retrieves facts from the database as part of its
conversation with the user. The database also keeps track of who the user has talked to and stores information about the users preferences. Named Enity Recognition
is used to detect the name of a user. Sentiment analysis is used at certain points to determine what the chatbot should say. To end a conversation with the bot,
simply type "goodbye". For a more detailed explination of how this bot works, look at the report included in this repository.
