# DT002G-Project
Project for DT002G


Reddit Scraper – Quick Usage Guide

1. Install Python 3.12
   Download and install Python 3.12 from https://www.python.org/downloads/release/python-3120/

2. Create a virtual environment:  
   Windows:
   - py -3.12 -m venv venv
   - .\venv\Scripts\activate

   macOS / Linux:
   - python3.12 -m venv venv
   - source venv/bin/activate


3. Install dependencies
       pip install --upgrade pip setuptools wheel
       pip install -r requirements.txt


4. Run the scraper
       python persona_parser.py <parser> <URL>
   Example:
       python persona_parser.py reddit https://reddit.com/r/python/comments/xyz
   - <parser> – the parser to use (reddit for Reddit threads)
   - <URL> – the URL of the Reddit thread you want to scrape
