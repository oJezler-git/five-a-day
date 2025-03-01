import requests
from bs4 import BeautifulSoup
import json
import re
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='scraper.log'
)

def extract_date(text):
    months = {
        'January': '01', 'Jan': '01',
        'February': '02', 'Feb': '02',
        'March': '03', 'Mar': '03',
        'April': '04', 'Apr': '04',
        'May': '05',
        'June': '06', 'Jun': '06',
        'July': '07', 'Jul': '07',
        'August': '08', 'Aug': '08',
        'September': '09', 'Sept': '09', 'Sep': '09',
        'October': '10', 'Oct': '10',
        'November': '11', 'Nov': '11',
        'December': '12', 'Dec': '12'
    }
    
    pattern = r'^\s*(\d+)(?:st|nd|rd|th)?\s+(\w+)'
    match = re.search(pattern, text.strip(), re.IGNORECASE)
    
    if match:
        day = match.group(1).zfill(2)
        month_text = match.group(2).capitalize()
        
        try:
            month = months[month_text]
            date_key = f"{day}-{month}"
            logging.debug(f"Extracted date '{date_key}' from text: '{text}'")
            return date_key
        except KeyError:
            logging.warning(f"Unrecognized month format: {month_text} in text: {text}")
            return None
    
    logging.debug(f"No date match found in text: '{text}'")
    return None

def scrape_gcse_worksheets(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        worksheets_data = {}
        
        paragraphs = soup.find_all('p')
        
        for p in paragraphs:
            text = p.get_text(strip=True)
            if not text:
                continue
                
            date = extract_date(text)
            if date:
                links = p.find_all('a')
                worksheet_links = []
                
                for link in links:
                    href = link.get('href', '')
                    if href and href.lower().endswith('.pdf'):
                        title = link.get_text(strip=True)
                        worksheet_links.append([title, href])
                
                if worksheet_links:
                    if date in worksheets_data:
                        logging.warning(f"Duplicate date found: {date}")
                        logging.warning(f"Original text: '{text}'")
                        logging.warning(f"Existing worksheets: {worksheets_data[date]['GCSE']['worksheets']}")
                        logging.warning(f"New worksheets: {worksheet_links}")
                    else:
                        worksheets_data[date] = {
                            "GCSE": {
                                "worksheets": worksheet_links,
                                "answers": []
                            },
                            "Further Maths": {
                                "worksheets": [],
                                "answers": []
                            }
                        }
                        logging.info(f"Added worksheets for date: {date}")
        
        return worksheets_data
    except requests.RequestException as e:
        logging.error(f"Error scraping GCSE worksheets: {str(e)}")
        return {}

def scrape_answers(url, worksheets_data):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        answer_links = soup.find_all('h4')
        for h4 in answer_links:
            a_tag = h4.find('a')
            if a_tag and 'Answers' in a_tag.text:
                try:
                    answer_page = requests.get(a_tag['href'])
                    answer_page.raise_for_status()
                    answer_soup = BeautifulSoup(answer_page.text, 'html.parser')
                    
                    answer_spans = answer_soup.find_all('span', class_='s1')
                    
                    for span in answer_spans:
                        text = span.get_text(strip=True)
                        date = extract_date(text)
                        
                        if date and date in worksheets_data:
                            links = span.find_all('a')
                            answer_links = []
                            
                            for link in links:
                                href = link.get('href', '')
                                if href and href.lower().endswith('.pdf'):
                                    title = link.get('title', link.get_text(strip=True))
                                    answer_links.append([title, href])
                            
                            if answer_links:
                                worksheets_data[date]["GCSE"]["answers"] = answer_links
                                logging.info(f"Added answers for date: {date}")
                
                except requests.RequestException as e:
                    logging.error(f"Error fetching answers page: {str(e)}")
    
    except requests.RequestException as e:
        logging.error(f"Error accessing main GCSE page: {str(e)}")

def scrape_further_maths(url, worksheets_data):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        paragraphs = soup.find_all('p', class_='p2')
        
        for p in paragraphs:
            text = p.get_text(strip=True)
            date = extract_date(text)
            
            if date:
                links = p.find_all('a')
                if len(links) >= 2:
                    if date not in worksheets_data:
                        worksheets_data[date] = {
                            "GCSE": {
                                "worksheets": [],
                                "answers": []
                            },
                            "Further Maths": {
                                "worksheets": [],
                                "answers": []
                            }
                        }
                    
                    worksheets_data[date]["Further Maths"]["worksheets"] = [
                        ["Further Maths", links[0]['href']]
                    ]
                    worksheets_data[date]["Further Maths"]["answers"] = [
                        ["Answers", links[1]['href']]
                    ]
                    logging.info(f"Added Further Maths content for date: {date}")
    
    except requests.RequestException as e:
        logging.error(f"Error scraping Further Maths page: {str(e)}")

def save_to_js(data):
    try:
        sorted_data = dict(sorted(data.items()))
        
        js_content = f"const worksheetData = {json.dumps(sorted_data, indent=2)};"
        
        with open('worksheets.js', 'w') as f:
            f.write(js_content)
        
        logging.info("Successfully saved data to worksheets.js")
        
        logging.info(f"Total number of dates: {len(sorted_data)}")
        for date in sorted_data:
            worksheet_count = len(sorted_data[date]["GCSE"]["worksheets"])
            answer_count = len(sorted_data[date]["GCSE"]["answers"])
            fm_worksheet_count = len(sorted_data[date]["Further Maths"]["worksheets"])
            fm_answer_count = len(sorted_data[date]["Further Maths"]["answers"])
            logging.info(f"Date {date}: GCSE - {worksheet_count} worksheets, {answer_count} answers, FM - {fm_worksheet_count} worksheets, {fm_answer_count} answers")
    
    except Exception as e:
        logging.error(f"Error saving data to file: {str(e)}")

def main():
    logging.info("Starting scraper")
    
    worksheets_data = {}
    
    gcse_url = 'https://corbettmaths.com/5-a-day/gcse/'
    worksheets_data.update(scrape_gcse_worksheets(gcse_url))
    
    scrape_answers(gcse_url, worksheets_data)
    
    further_maths_url = 'https://corbettmaths.com/5-a-day/further-maths/'
    scrape_further_maths(further_maths_url, worksheets_data)
    
    save_to_js(worksheets_data)
    
    logging.info("Scraping completed")

if __name__ == "__main__":
    main()
