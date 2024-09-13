from flask import Flask, render_template
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re

app = Flask(__name__)


def remove_ordinal_indicator(date_text):
    return re.sub(r'\b(\d+)(st|nd|rd|th)\b', r'\1', date_text).strip()


def normalise_month(month):
    month_map = {
        'Jan': 'January', 'Feb': 'February', 'Mar': 'March', 'Apr': 'April',
        'May': 'May', 'Jun': 'June', 'Jul': 'July', 'Aug': 'August',
        'Sep': 'September', 'Sept': 'September', 'Oct': 'October',
        'Nov': 'November', 'Dec': 'December'
    }
    return month_map.get(month, month)


def parse_date(date_text):
    date_text = remove_ordinal_indicator(date_text)
    # normalise month names
    date_text_parts = date_text.split(' ')
    if len(date_text_parts) > 1:
        date_text_parts[1] = normalise_month(date_text_parts[1])
    normalised_date_text = ' '.join(date_text_parts)

    print(f"Cleaned and normalised date text: '{normalised_date_text}'")  # Debugging

    date_formats = [
        '%d %B', '%d %b',        # e.g., 31 January, 31 Jan
        '%B %d', '%b %d',        # e.g., January 31, Jan 31
        '%d-%m-%Y', '%m-%d-%Y',  # e.g., 31-09-2024, 09-31-2024
        '%Y-%m-%d',              # e.g., 2024-01-31
        '%d %B %Y', '%d %b %Y',  # e.g., 31 January 2024, 31 Jan 2024
        '%B %d %Y', '%b %d %Y'   # e.g., January 31 2024, 31 12 2024
    ]

    for date_format in date_formats:
        try:
            return datetime.strptime(normalised_date_text, date_format).replace(year=datetime.now().year)
        except ValueError:
            continue

    print(f"Date parsing error: Unable to parse date '{normalised_date_text}'")  # Debugging
    return None


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

            # extract worksheets and answers
            if category == 'GCSE':
                for entry in soup.find_all('span', style="line-height: 1.5;"):
                    date_text = entry.text.strip().split(' ', 2)[:2]
                    date_text = " ".join(date_text)
                    print(f"{category} Extracted date text: {date_text}")  # Debugging

                    date = parse_date(date_text)
                    if date:
                        worksheet_links = [(link.text.strip(), link['href']) for link in entry.find_all('a', href=True)]
                        if date.date() in worksheets[category]:
                            worksheets[category][date.date()].extend(worksheet_links)
                        else:
                            worksheets[category][date.date()] = worksheet_links

            elif category == 'Further Maths':
                for entry in soup.find_all('span', class_="s1"):
                    date_text = entry.text.strip().split(' ', 2)[:2]
                    date_text = " ".join(date_text)
                    print(f"{category} Extracted date text: {date_text}")  # Debugging

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

    # fetch GCSE answers index page
    answers_index_url = 'https://corbettmaths.com/5-a-day/gcse/'
    print(f"Fetching answers index from: {answers_index_url}")
    response = requests.get(answers_index_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        link_text = 'September Answers – click here'
        answers_link = None
        for h4 in soup.find_all('h4'):
            a_tag = h4.find('a', href=True)
            if a_tag and link_text in a_tag.text:
                answers_link = a_tag['href']
                break

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


@app.route('/')
def index():
    worksheets, answers = get_worksheets_and_answers()
    current_date = datetime.now().date()
    formatted_date = current_date.strftime('%d-%m-%Y')  # Format date as dd-mm-yyyy
    gcse_links = worksheets['GCSE'].get(current_date, "No GCSE worksheets found for today")
    further_maths_links = worksheets['Further Maths'].get(current_date, "No Further Maths worksheets found for today")
    gcse_answers = answers['GCSE'].get(current_date, "No GCSE answers found for today")
    further_maths_answers = answers['Further Maths'].get(current_date, "No Further Maths answers found for today")
    return render_template('index.html', date=formatted_date, gcse_links=gcse_links,
                           further_maths_links=further_maths_links, gcse_answers=gcse_answers,
                           further_maths_answers=further_maths_answers)


if __name__ == '__main__':
    app.run(debug=True)
