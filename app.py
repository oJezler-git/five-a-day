# IMPORTS

# Flask for web app
from flask import Flask, render_template, jsonify

# Requests to be able to scrape the corbettmaths website
import requests

# BeautifulSoup to parse the HTML content
from bs4 import BeautifulSoup

# Datetime to get the current date
from datetime import datetime

# Holidays to get the current holiday
import holidays

# Regular expressions to clean and normalise the date text
import re
######################################################################################################

# create the Flask app
app = Flask(__name__)

# function to remove ordinal indicators from date text (e.g 31st, 1st, 2nd, 3rd, 4th)
def remove_ordinal_indicator(date_text):
    return re.sub(r'\b(\d+)(st|nd|rd|th)\b', r'\1', date_text).strip()

# function to normalise month names (e.g Jan -> January, Sept -> September)
def normalise_month(month):
    month_map = {
        'Jan': 'January', 
        'Feb': 'February', 
        'Mar': 'March', 
        'Apr': 'April',
        'May': 'May', 
        'Jun': 'June', 
        'Jul': 'July', 
        'Aug': 'August',
        'Sep': 'September', 
        'Sept': 'September', 
        'Oct': 'October',
        'Nov': 'November', 
        'Dec': 'December'
    }
    return month_map.get(month, month)

# function to parse date text and return a datetime object (or None if parsing fails)
def parse_date(date_text):
    date_text = remove_ordinal_indicator(date_text)
    # normalise month names
    date_text_parts = date_text.split(' ')
    if len(date_text_parts) > 1:
        date_text_parts[1] = normalise_month(date_text_parts[1])
    normalised_date_text = ' '.join(date_text_parts)

    print(f"Cleaned and normalised date text: '{normalised_date_text}'")  # debugging
    # date formats to try
    date_formats = [
        '%d %B',        # e.g 31 January, 31 Jan
        '%d %b',        # e.g 31 January, 31 Jan
        '%B %d',        # e.g January 31, Jan 31
        '%b %d',        # e.g January 31, Jan 31
        '%d-%m-%Y',     # e.g 31-09-2024, 09-31-2024
        '%m-%d-%Y',     # e.g 31-09-2024, 09-31-2024
        '%Y-%m-%d',     # e.g 2024-01-31
        '%d %B %Y',     # e.g 31 January 2024, 31 Jan 2024
        '%d %b %Y',     # e.g 31 January 2024, 31 Jan 2024
        '%B %d %Y',     # e.g January 31 2024, 31 12 2024
        '%b %d %Y'      # e.g January 31 2024, 31 12 2024
    ]

    # try parsing the date text with each date format
    for date_format in date_formats:
        try:
            return datetime.strptime(normalised_date_text, date_format).replace(year=datetime.now().year)
        except ValueError:
            continue

    # if parsing fails
    print(f"Date parsing error: Unable to parse date '{normalised_date_text}'")  # debugging
    return None

# function to get the worksheets and answers from the corbettmaths website
def get_worksheets_and_answers():
    urls = {
        'GCSE': 'https://corbettmaths.com/5-a-day/gcse/',
        'Further Maths': 'https://corbettmaths.com/5-a-day/further-maths/'
    }
    worksheets = {'GCSE': {}, 'Further Maths': {}}
    answers = {'GCSE': {}, 'Further Maths': {}}

    for category, url in urls.items():
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            if category == 'GCSE':
                # find worksheets
                for p in soup.find_all(['p', 'div']):
                    text = p.get_text().strip()
                    if text and any(month in text for month in ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']):
                        date_text = ' '.join(text.split()[:2])
                        date = parse_date(date_text)
                        if date:
                            worksheet_links = [(link.text.strip(), link['href']) for link in p.find_all('a', href=True)]
                            if worksheet_links:
                                if date.date() in worksheets[category]:
                                    worksheets[category][date.date()].extend(worksheet_links)
                                else:
                                    worksheets[category][date.date()] = worksheet_links

                # find answers link
                current_month = datetime.now().strftime('%B')
                answers_link = None
                for a in soup.find_all('a', href=True):
                    if f'{current_month} Answers' in a.text:
                        answers_link = a['href']
                        break
                
                # find answers
                if answers_link:
                    answers_response = requests.get(answers_link)
                    if answers_response.status_code == 200:
                        answers_soup = BeautifulSoup(answers_response.text, 'html.parser')
                        for span in answers_soup.find_all('span', class_='s1'):
                            text = span.get_text().strip()
                            if text:
                                date_text = ' '.join(text.split()[:2])
                                date = parse_date(date_text)
                                if date:
                                    answer_links = [(link.text.strip(), link['href']) for link in span.find_all('a', href=True)]
                                    if answer_links:
                                        if date.date() in answers['GCSE']:
                                            answers['GCSE'][date.date()].extend(answer_links)
                                        else:
                                            answers['GCSE'][date.date()] = answer_links

            # find worksheets and answers for further maths
            elif category == 'Further Maths':
                for entry in soup.find_all('span', class_="s1"):
                    date_text = entry.text.strip().split(' ', 2)[:2]
                    date_text = " ".join(date_text)
                    print(f"{category} Extracted date text: {date_text}")  # debugging

                    # parse the date text
                    date = parse_date(date_text)
                    if date:
                        worksheet_links = [(link.text.strip(), link['href']) for link in entry.find_all('a', href=True)]
                        if date.date() in worksheets[category]:
                            worksheets[category][date.date()].extend(worksheet_links)
                        else:
                            worksheets[category][date.date()] = worksheet_links

                        answer_links = [(link.text.strip(), link['href']) for link in entry.find_all('a', href=True) if 'Answer' in link.text]
                        if answer_links:
                            if date.date() in answers[category]:
                                answers[category][date.date()].extend(answer_links)
                            else:
                                answers[category][date.date()] = answer_links

    # fetch answers index page
    answers_index_url = 'https://corbettmaths.com/5-a-day/gcse/'
    print(f"Fetching answers index from: {answers_index_url}")
    response = requests.get(answers_index_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')

        current_month_name = datetime.now().strftime('%B')
        link_text = f'{current_month_name} Answers – click here'

        # find the correct answers link
        answers_link = None
        for h4 in soup.find_all('h4'):
            a_tag = h4.find('a', href=True)
            if a_tag and link_text in a_tag.text:
                answers_link = a_tag['href']
                break

        # fetch answers page
        if answers_link:
            print(f"Found answers page URL: {answers_link}")
            response = requests.get(answers_link)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                for p in soup.find_all('p', class_='p2'):
                    span = p.find('span', class_='s1')
                    if span:
                        date_text = span.text.strip().split(' ', 2)[:2]
                        date_text = " ".join(date_text)
                        print(f"Extracted answer date text: {date_text}")
                        date = parse_date(date_text)
                        if date:
                            answer_links = [(link.text.strip(), link['href']) for link in p.find_all('a', href=True)]
                            if date.date() in answers['GCSE']:
                                answers['GCSE'][date.date()].extend(answer_links)
                            else:
                                answers['GCSE'][date.date()] = answer_links
            else:
                print(f"Failed to fetch answers page with status code {response.status_code}.")
        else:
            print(f"Could not find the answers link with text '{link_text}'.")
    else:
        print(f"Failed to fetch answers index with status code {response.status_code}.")

    print("Worksheets dictionary:", worksheets)
    print("Answers dictionary:", answers)
    return worksheets, answers


@app.route('/fetch_data')
def fetch_data():
    worksheets, answers = get_worksheets_and_answers()
    current_date = datetime.now().date()

    gcse_links = worksheets['GCSE'].get(current_date, "No GCSE worksheets found for today")
    further_maths_links = worksheets['Further Maths'].get(current_date, "No Further Maths worksheets found for today")
    gcse_answers = answers['GCSE'].get(current_date, "No GCSE answers found for today")
    further_maths_answers = answers['Further Maths'].get(current_date, "No Further Maths answers found for today")

    return jsonify({
        'gcse_links': gcse_links,
        'further_maths_links': further_maths_links,
        'gcse_answers': gcse_answers,
        'further_maths_answers': further_maths_answers
    })

@app.route('/')
def index():
    current_date = datetime.now().date()
    formatted_date = current_date.strftime('%d-%m-%Y')

    custom_holiday_messages = {
        "Christmas Day": "Merry Christmas!",
        "New Year's Day": "Happy New Year!",
        "Good Friday": "Happy Easter!",
        "May Day": "Happy May Day!",
        "Spring Bank Holiday": "Happy Bank Holiday!",
        "New Year's Day": "Happy New Year!",
    }

    country_holidays = holidays.CountryHoliday('UK')
    holiday_name = country_holidays.get(current_date, '')

    if holiday_name:
        custom_message = custom_holiday_messages.get(holiday_name, holiday_name)
        display_date = f"{formatted_date} ({custom_message})"
    else:
        display_date = formatted_date

    return render_template('index.html', date=display_date)

if __name__ == '__main__':
    app.run(debug=True)
