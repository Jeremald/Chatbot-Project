# Jason Garza HW 7

import spacy
import random
import sqlite3
from sqlite3 import Error
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

bot_prompt = 'Foldy>'
user_prompt = '> '
user_name = ''
topic = ''
topic_list = ['galaxy_fold', 'tcl', 'mate_x', 'duo', 'google', 'apple']
name_list = ['the Galaxy Fold', 'an upcoming TCL phone', 'the Mate X', 'the Duo', 'a possible google folding phone', 'a possible folding iPhone']
topic_to_name = {'galaxy_fold': 'the Galaxy Fold',
                 'tcl': 'upcoming TCL phones',
                 'mate_x': 'the Mate X',
                 'duo': 'the Duo',
                 'google': 'Google\'s plans for a folding phone',
                 'apple': 'Apple\'s plans for a folding phone'}
topic_to_list_name = {'galaxy_fold': 'Samsung Galaxy Fold',
                      'tcl': 'TCL folding phones',
                      'mate_x': 'Huawei Mate X',
                      'duo': 'Microsoft Duo',
                      'google': 'Folding Pixel',
                      'apple': 'Folding iPhone'}
counter = 0


def get_name(conn):
    global user_name
    # Use NER from spaCy
    nlp = spacy.load('en_core_web_sm')
    # Bot prompts user for name, records response
    print(bot_prompt, 'Hello, I\'m Foldy, the folding phone chat bot! What\'s your name?')
    response = input(user_prompt)
    found_name = False
    # Keep prompting until the user enters a name
    while not found_name:
        doc = nlp(response)
        # Use NER on response, look for PERSON tag
        for ent in doc.ents:
            if ent.label_ == 'PERSON':
                # set the name of the user
                user_name = ent.text
                found_name = True
                break
        # if the user did not type a name
        if not found_name:
            print(bot_prompt, 'I couldn\'t find a name in your response. What is your name?')
            response = input(user_prompt)
    # after getting name from user, check if name if database
    if found_user(conn, user_name):
        # if in database, say welcome back, make comment about their preferences (if able to)
        comment = get_comment(conn)
        print(f'{bot_prompt} Welcome back {user_name}! {comment}')
    else:
        # if not, add to database, just say hello
        print(f'{bot_prompt} Hello {user_name}!')


def get_initial_topic(conn):
    global topic
    # loop until a topic is chosen
    while topic == '':
        print('Which phone would you like to talk about?')
        response = input(user_prompt).lower()
        # user wants to talk about the Samsung Galaxy Fold
        if 'galaxy' in response or 'samsung' in response or 'the fold' in response:
            topic = 'galaxy_fold'
        # user wants to talk about a TCL phone
        elif 'tcl' in response:
            topic = 'tcl'
        # user wants to talk about the Huawei Mate X
        elif 'huawei' in response or 'mate' in response:
            topic = 'mate_x'
        # user wants to talk about the Microsoft Duo
        elif 'microsoft' in response or 'duo' in response:
            topic = 'duo'
        # user wants to talk about a possible Google folding phone
        elif 'google' in response or 'pixel' in response:
            topic = 'google'
        # user wants to talk about a possible folding iPhone
        elif 'apple' in response or 'iphone' in response:
            topic = 'apple'
        # user wants bot to choose phone to talk about
        elif 'pick' in response or 'choose' in response or 'want' in response or 'choice' in response or 'decide' in response:
            # randomly pick a topic
            number = random.randint(0, len(topic_list) - 1)
            topic = topic_list[number]
            print(f'{bot_prompt} Okay, let\'s talk about {name_list[number]}')
        # user wants to know what phones they can talk about or types something not covered by an above case
        else:
            answer = 'I know facts about the Samsung Galaxy Fold, the Huawei Mate X,\n'
            answer += 'the Microsoft Duo, and an upcoming TCL phone. I\'ve also heard a few things about\n'
            answer += 'upcoming folding phones from Google and Apple.'
            print(bot_prompt, answer)
    # Display a general fact about the chosen phone
    get_fact(conn, 'general')


def get_fact(conn, category):
    global counter
    # Retrieve fact about the phone that matches the topic for a given category
    cursor = conn.cursor()
    query = 'SELECT fact FROM ' + topic + ' WHERE category=\"' + category + '\";'
    cursor.execute(query)
    result = cursor.fetchall()
    # If no facts in that category, get general fact
    if len(result) == 0:
        print(f'{bot_prompt} I couldn\'t find any facts about that for this phone, so here is a general fact about it:')
        query = 'SELECT fact FROM ' + topic + ' WHERE category=\"general\";'
        cursor.execute(query)
        result = cursor.fetchall()
    # Randomly pick fact from the list of facts (need [0] since fetchall() returns list of tuples)
    number = random.randint(0, len(result) - 1)
    print(bot_prompt, result[number][0])
    # increment counter
    counter += 1
    # after giving 4 facts about the same phone in a row, if don't have users preference on this phone, get it
    if counter == 4 and not has_preference(conn):
        get_preference(conn)


def chat(conn):
    just_reacted = True
    while True:
        # get user response
        response = input(user_prompt).lower()
        category = get_category(response)
        reaction = bot_reaction(response)
        # first check if it matches a special query
        if special_queries(conn, response):
            just_reacted = True
        # if bot is able to react to user's response
        elif reaction and not just_reacted:
            print(bot_prompt, reaction)
            just_reacted = True
        # user wants to change topic, give general fact about new topic
        elif check_topic_change(response):
            just_reacted = False
            # if user wants to change topic and wants a specific category
            if category:
                get_fact(conn, category)
            # if user wants to change topic and wants the bots opinion
            elif opinion_requested(response):
                get_opinion()
            else:
                get_fact(conn, 'general')
        # determine if user is asking for a specific category of facts
        elif category:
            get_fact(conn, category)
            just_reacted = False
        # determine if user is asking for the bots opinion
        elif opinion_requested(response):
            get_opinion()
            just_reacted = False
        # give a general fact about current topic
        else:
            get_fact(conn, 'general')
            just_reacted = False


def check_topic_change(response):
    global topic
    global counter
    topic_changed = False
    # user wants to talk about the Samsung Galaxy Fold
    if ('galaxy' in response or 'samsung' in response or 'the fold' in response) and topic != 'galaxy_fold':
        topic = 'galaxy_fold'
        topic_changed = True
    # user wants to talk about a TCL phone
    elif 'tcl' in response and topic != 'tcl':
        topic = 'tcl'
        topic_changed = True
    # user wants to talk about the Huawei Mate X
    elif ('huawei' in response or 'mate' in response) and topic != 'mate_x':
        topic = 'mate_x'
        topic_changed = True
    # user wants to talk about the Microsoft Duo
    elif ('microsoft' in response or 'duo' in response) and topic != 'duo':
        topic = 'duo'
        topic_changed = True
    # user wants to talk about a possible Google folding phone
    elif ('google' in response or 'pixel' in response) and topic != 'google':
        topic = 'google'
        topic_changed = True
    # user wants to talk about a possible folding iPhone
    elif ('apple' in response or 'iphone' in response) and topic != 'apple':
        topic = 'apple'
        topic_changed = True
    # reset counter when the topic changes
    if topic_changed:
        counter = 0
    return topic_changed


def get_category(response):
    # check if user is requesting a fact about the cameras, display, or how the phone handles apps
    if 'display' in response or 'screen' in response:
        return 'display'
    elif 'camera' in response:
        return 'camera'
    elif 'apps' in response:
        return 'apps'
    else:
        return None


def opinion_requested(response):
    # check if user is requesting an opinion from the bot
    if 'you think' in response or 'your opinion' in response or 'you like' in response or 'you feel' in response:
        return True
    return False


def get_opinion():
    # 3 opinion options for each phone so that it feels less robotic
    opinion = ''
    if topic == 'galaxy_fold':
        opinions = ['I really like it!', 'If robots could have smartphones, I would buy this one!',
                    'I think its a good start, and I\'m excited for future generations of this phone!']
        number = random.randint(0, len(opinions) - 1)
        opinion = opinions[number]
    elif topic == 'tcl':
        opinions = ['It seems pretty cool!', 'I\'m interested to see how well they make use of having two folds.',
                    'The more screen space the better!']
        number = random.randint(0, len(opinions) - 1)
        opinion = opinions[number]
    elif topic == 'mate_x':
        opinions = ['I don\'t like that when it\'s folded the screen is on the outside.', 'It\'s alright.',
                    'I feel like it will be easy to damage the screen since its always exposed.']
        number = random.randint(0, len(opinions) - 1)
        opinion = opinions[number]
    elif topic == 'duo':
        opinions = ['It\'s a pretty cool idea, but I don\'t think it\'s for me.', 'It\'s a decent phone.',
                    'I think it would be better if it had an outside screen, like the Galaxy Fold.']
        number = random.randint(0, len(opinions) - 1)
        opinion = opinions[number]
    elif topic == 'google':
        opinions = ['We don\'t really have much to go on right now.', 'I\'m sure it will have a great camera!',
                    'Google phones usually have some hardware problems, so my expectations aren\'t too high.']
        number = random.randint(0, len(opinions) - 1)
        opinion = opinions[number]
    # topic == 'apple'
    else:
        opinions = ['Apple usually makes great hardware, so my hopes are high.', 'I hope it won\'t be too expensive!',
                    'I\'m excited to see what innovations Apple brings to folding phones!.']
        number = random.randint(0, len(opinions) - 1)
        opinion = opinions[number]
    print(bot_prompt, opinion)


def found_user(conn, name):
    # check if database has entry for this user
    found = False
    cursor = conn.cursor()
    query = 'SELECT name FROM users WHERE name=?;'
    query_tuple = (name,)
    cursor.execute(query, query_tuple)
    result = cursor.fetchall()
    # no entry for this user, it's their first time talking to foldy
    if len(result) == 0:
        # since name is user input, use parameterized query to avoid SQL injection
        query = """INSERT INTO users (name) VALUES (?)"""
        name_tuple = (name,)
        # add entry for user
        cursor.execute(query, name_tuple)
        conn.commit()
    else:
        found = True
    return found


def bot_reaction(response):
    # If user responds positively or negatively to a fact, the bot will give a reaction
    reaction = None
    analyzer = SentimentIntensityAnalyzer()
    scores = analyzer.polarity_scores(response)
    # Use compound score since it is more of an overall measure
    comp = scores['compound']
    # Positive response
    if comp > 0.2:
        reactions = ['I\'m glad you feel that way.', 'I like that too!', 'I know, right?',
                     'That\'s something I really love about it!', 'You have good taste.',
                     'It\'s so cool!', 'I love it!', 'Yeah, it\'s really awesome!', 'They really nailed that!',
                     'Yeah, I can\'t wait to see what they do with the next version!']
        # Pick random response
        number = random.randint(0, len(reactions) - 1)
        reaction = reactions[number]
    # Negative response
    if comp < -0.2:
        reactions = ['Yeah, I get that.', 'I know what you mean.', 'I feel the same way.',
                     'Yeah, it\'s kinda disappointing.', 'They had so much potential.',
                     'I know, why would they do that?', 'It\'s definitely an interesting choice.',
                     'Sometimes compromises need to be made.', 'I hope the next version is better.']
        # Pick random response
        number = random.randint(0, len(reactions) - 1)
        reaction = reactions[number]
    return reaction


def get_preference(conn):
    # ask user for their opinion
    print(bot_prompt, 'Do you like this phone?')
    response = input(user_prompt).lower()

    analyzer = SentimentIntensityAnalyzer()
    scores = analyzer.polarity_scores(response)
    cursor = conn.cursor()
    # Use compound score since it is more of an overall measure
    comp = scores['compound']
    # Positive response ('I do' not picked up by sentiment analyzer)
    if comp > 0 or ('i do' in response and 'i don\'t know' not in response):
        query = """INSERT INTO user_preferences (name, phone, preference) VALUES(?, ?, ?)"""
        query_tuple = (user_name, topic, 'like')
        # add preference entry for user
        cursor.execute(query, query_tuple)
        conn.commit()
        print(bot_prompt, 'Thank you! I like hearing your opinions!')
    # Negative response ('I don't not picked up by sentiment analyzer)
    elif comp < 0 or ('i don\'t' in response and 'i don\'t know' not in response):
        query = """INSERT INTO user_preferences (name, phone, preference) VALUES(?, ?, ?)"""
        query_tuple = (user_name, topic, 'dislike')
        # add preference entry for user
        cursor.execute(query, query_tuple)
        conn.commit()
        print(bot_prompt, 'Thank you! I like hearing your opinions!')
    else:
        print(bot_prompt, 'Okay, I\'ll ask again later.')


def has_preference(conn):
    # check if we have users preference on phone for current topic
    cursor = conn.cursor()
    query = """SELECT * FROM user_preferences WHERE name=? AND phone=?;"""
    query_tuple = (user_name, topic)
    cursor.execute(query, query_tuple)
    result = cursor.fetchall()
    # No preference for this phone
    if len(result) == 0:
        return False
    return True


def get_comment(conn):
    global topic
    cursor = conn.cursor()
    name_tuple = (user_name,)
    # check if we know that the user likes a phone
    query = """SELECT phone FROM user_preferences WHERE name=? AND preference="like";"""
    cursor.execute(query, name_tuple)
    result = cursor.fetchall()
    # if they do like a phone, pick one to talk about
    if len(result) > 0:
        number = random.randint(0, len(result) - 1)
        phone_topic = result[number][0]
        phone_name = topic_to_name[phone_topic]
        topic = phone_topic
        return 'Would you like to talk about ' + phone_name + ' some more?'
    # check if we know that the user dislikes a phone
    query = """SELECT phone FROM user_preferences WHERE name=? AND preference="dislike";"""
    cursor.execute(query, name_tuple)
    result = cursor.fetchall()
    # if we know they don't like a phone, make a comment about it
    if len(result) > 0:
        number = random.randint(0, len(result) - 1)
        phone_topic = result[number][0]
        phone_name = topic_to_name[phone_topic]
        return 'I guessing you don\'t want to talk about ' + phone_name + '.'
    # no comment can be made about the users preferences
    return ''


def special_queries(conn, response):
    cursor = conn.cursor()
    name_tuple = (user_name,)
    # 'goodbye' : quits the program
    if 'goodbye' in response:
        print(bot_prompt, 'Goodbye! It was nice talking to you.')
        quit()

    # 'what phones do i like' : can be used for testing purposes, or if user wants to see what bot knows
    elif 'what phones do i like' in response:
        # get list of phones that the user likes
        query = """SELECT phone FROM user_preferences WHERE name=? AND preference="like";"""
        cursor.execute(query, name_tuple)
        result = cursor.fetchall()
        if len(result) == 0:
            print(bot_prompt, 'I don\'t know yet!')
        else:
            print(bot_prompt, 'If I recall correctly, these are the phones that you like:')
            # print out each phone that user likes
            for i in result:
                phone_topic = i[0]
                phone_name = topic_to_list_name[phone_topic]
                print(phone_name)
        return True

    # 'what phones do i dislike' : can be used for testing purposes, or if user wants to see what bot knows
    elif 'what phones do i dislike' in response or 'what phones do i not like' in response:
        # list off phones that the user dislikes
        query = """SELECT phone FROM user_preferences WHERE name=? AND preference="dislike";"""
        cursor.execute(query, name_tuple)
        result = cursor.fetchall()
        if len(result) == 0:
            print(bot_prompt, 'I don\'t know yet!')
        else:
            print(bot_prompt, 'I believe that these are the phones that you dislike:')
            # print out each phone that user likes
            for i in result:
                phone_topic = i[0]
                phone_name = topic_to_list_name[phone_topic]
                print(phone_name)
        return True

    # 'what is your favorite folding phone' : adds some personality to the bot
    elif 'what is your favorite folding phone' in response or 'what is your favorite phone' in response:
        print(bot_prompt, 'My favorite is the Galaxy Fold. It just seems so cool!')
        return True

    # 'what is your least favorite folding phone' : adds some personality to the bot
    elif 'what is your least favorite folding phone' in response or 'what is your least favorite phone' in response:
        print(bot_prompt, 'Of the ones that have been released so far, I\'d say the Duo is my least favorite.')
        return True

    # 'what is your name' : adds some personality to the bot
    elif 'what is your name' in response:
        print(bot_prompt, 'My name is Foldy! Isn\'t that a really creative name?')
        return True

    # 'you just said that' : adds some personality to the bot
    elif 'you just said that' in response or 'you already said that' in response:
        print(bot_prompt, 'Whoops! I don\'t remember that. I must have some faulty RAM.')
        return True
    return False


if __name__ == '__main__':
    connection = None
    try:
        connection = sqlite3.connect('facts.db')
    except Error as e:
        print('Error connecting to SQLite database. Make sure facts.db is in the same folder as the .py file')
        quit()

    get_name(connection)
    if len(topic) == 0:
        get_initial_topic(connection)
    chat(connection)