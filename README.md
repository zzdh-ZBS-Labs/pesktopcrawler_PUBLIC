# Pesktop Crawler

Pesktop Crawler is a focused Python scraper designed to extract malicious advertisement/download URLs from Pesktop software pages, and to store the results in a structured CSV format. The project is tailored for use in research, automation, or security-focused workflows where insight into the regularly changing malicious download link is required.  This link appears to change regularly with updated malware. 

---

## Features

- Sends HTTP requests with realistic, browser-like headers to reduce basic bot detection.
- Parses the raw HTML/JavaScript source of a Pesktop page as plain text.
- Uses regular expressions to locate JavaScript variables
- Extracts and validates discovered URLs, ignoring placeholders (e.g., "#", "null", "javascript:void(0)").
- Attempts to extract the software/page title from the HTML source.
- Saves all collected data (URL, title, ad URL, and timestamps) to a CSV file.
- Includes debug logging that prints source snippets and regex match context for easier troubleshooting.

---

## Project Structure

- `pesktop_crawler.py`  
  Main script containing:
  - HTTP request logic and headers.
  - Plain-text parsing and regex extraction functions.
  - CSV-writing and basic orchestration code.

(If you add more modules or support files, list and describe them here.)

---

## Requirements

- Python 3.8 or newer

Python standard library modules used (no installation required):
- `re`
- `csv`
- `time`
- `random`
- `datetime`
- `os`
- `urllib.parse`

Third-party dependencies:
- `requests`
- `beautifulsoup4` (currently optional, but included/imported for HTML parsing needs)

Install external dependencies with:

    pip install requests beautifulsoup4

---

## Configuration

### Base URL

The target Pesktop page is defined near the top of `pesktop_crawler.py`:

    BASE_URL = "<INSERTBASECRAWLURLHERE>"

Change this value to point to any other supported Pesktop software page, for example:

    BASE_URL = "<INSERTBASECRAWLURLHERE>"

### HTTP Headers

A realistic header set is defined in `HEADERS` to mimic a common browser:

    HEADERS = {
        "User-Agent": "...",
        "Accept": "...",
        "Accept-Language": "...",
        ...
    }

You can modify these headers if the site’s behavior changes or additional headers are needed.

### Output

The script writes results to a CSV file (e.g., in the current working directory).  
If you want a specific output location or filename pattern, adjust the relevant code where the CSV path/filename is created.

---

## Usage

1. Clone the repository:

       git clone https://github.com/zzdh-ZBS-Labs/pesktopcrawler_PUBLIC.git
       cd pesktop-crawler

2. Install dependencies:

       pip install requests beautifulsoup4

3. (Optional) Edit `BASE_URL` in `pesktop_crawler.py` to the Pesktop page you want to process.

4. Run the crawler:

       python pesktop_crawler.py

5. After execution, open the generated CSV file to inspect:
   - Page/Software title
   - Base URL
   - Extracted ad URL (download/redirect endpoint)
   - Timestamp and any other
