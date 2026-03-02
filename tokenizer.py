
import spacy

nlp = spacy.load("en_core_web_lg")

def tokenize(comments):
    """Tokenize the data and map it to a dictionary"""
    for index, comment in enumerate(comments):
        nlp(comments[comment]["text"])

    print("Cleaned data" + str(len(comments)))
    return comments