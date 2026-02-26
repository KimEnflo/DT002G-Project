import spacy
import re

nlp = spacy.load("en_core_web_lg")

def tokenize(comments):
    """Tokenize the data and map it to a dictionary"""
    dictionary = {}
    for index, comment in enumerate(comments):
        clean_comment = clean_text(comment["body"])
        doc = nlp(clean_comment)
        dictionary[index] = doc

    print("Cleaned data" + str(len(dictionary)))
    return dictionary

def clean_text(comment):
    """clean the comment by removing whitespaces and urls"""
    comment = re.sub(r"http\S+", " ", comment)
    comment = re.sub(r"\s+", " ", comment.strip())

    return comment

