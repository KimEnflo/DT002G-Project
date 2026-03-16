# DT002G-Project
Project for DT002G

Limitations:
In the current state, the tool will break at around 1,500-comment threads due to Reddit’s API throttling the requests
for additional children. To ensure no loss of data, try to keep it to 1,000-comment threads or fewer.

Reddit Scraper – Quick Usage Guide

## 1. Install Python 3.12

1. Install Python 3.12
   Download and install Python 3.12.13 from [https://www.python.org/downloads/release/python-3120/](https://www.python.org/downloads/release/python-31213/)

## 2. Create a virtual environment:
The current version of spacy isn't compatible with the newest version of python in the current state.
Because of that a virtual environment is needed to run this script.

   Windows cmd:
   - py -3.12.13 -m venv venv
   - .\venv\Scripts\activate

   macOS / Linux terminal:
   - python3.12.13 -m venv venv
   - source venv/bin/activate


## 3. Install dependencies
      - pip install --upgrade pip setuptools wheel
      - pip install -r requirements.txt

## 4. Define persona specification
Persona specifications structure:

`{  
  "Name of the persona": {  
    "keywords": ["apple","pear","orange"] 
  }
}`
    
## 5. Run the scraper
    python persona_parser.py <parser> <URL>
   Example:
       python persona_parser.py reddit https://reddit.com/r/python/comments/id/titlename
   - <parser> – the parser to use (reddit for Reddit threads)
   - <URL> – the URL of the Reddit thread you want to scrape

    `python persona_parser.py reddit https://reddit.com/r/python/comments/xyz`
 
