# DT002G-Project

## Persona parser

This program analyzes Reddit threads and classifies comments into predefined personas using keyword rules and sentiment analysis. Results are exported as structured JSON data.

## Limitations:
In the current state, the tool will break at around 1,500-comment threads due to Reddit’s API throttling the requests
for additional children. To ensure no loss of data, try to keep it to 1,000-comment threads or fewer.

## Reddit Scraper – Quick Usage Guide

### 1. Install Python 3.12

1. Install Python 3.12
   Download and install Python 3.12 from https://www.python.org/downloads/release/python-3120/

### 2. Create a virtual environment:
The current version of spacy isn't compatible with the newest version of python in the current state.
Because of that a virtual environment is needed to run this script, so from the script folder run these following commands.

   Windows cmd:
   - py -3.12 -m venv venv
   - .\venv\Scripts\activate

   macOS / Linux terminal:
   - python 3.12 -m venv venv
   - source venv/bin/activate


### 3. Install dependencies
      - pip install --upgrade pip setuptools wheel
      - pip install -r requirements.txt
      - pip install -m spacy download en_core_web_sm

### 4. Define persona specification
Create the persona of your choice in the /resources/persona_specifications.json file.

Persona specifications structure:

`{  
  "Name of the persona": {  
    "keywords": ["apple","pear","orange"] 
  }
}`
    
### 5. Run the scraper
    python persona_parser.py <parser> <URL>
   Example:
       python persona_parser.py reddit https://reddit.com/r/python/comments/id/titlename
   - <parser> – the parser to use (reddit for Reddit threads)
   - <URL> – the URL of the Reddit thread you want to scrape

    `python persona_parser.py reddit https://reddit.com/r/python/comments/xyz`
 
