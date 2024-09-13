import asyncio
from collections import defaultdict
from datetime import datetime
import json
from pyppeteer import launch
from bs4 import BeautifulSoup
import re
import requests
import json


main_url = 'https://www.chiefdelphi.com/search?q=5137%20order%3Alatest'
referer_url = 'https://www.chiefdelphi.com/'
database_path = 'tracked_threads.json'
with open('config.json', 'r') as config_file:
    config = json.load(config_file)
slack_webhook = config['Webhook']
keywords = ['5137', 'Iron Kodiaks']

async def set_up_browser():
    browser = await launch(headless=False)  # Set headless=True if you want to run it headlessly
    return browser

# Get a soup of a webpage using the page url and referring url
async def get_soup(browser, url, referer):
    page = await browser.newPage()
    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    
    # Open the referer URL to set any necessary cookies
    await page.goto(referer)
    await asyncio.sleep(5)

    # Perform some human-like interactions
    await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
    await asyncio.sleep(2)

    # Open the target URL
    await page.goto(url)
    await asyncio.sleep(10)

    # Simulate more scrolling and interaction
    await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
    await asyncio.sleep(5)

    # Get the page content and parse it with BeautifulSoup
    content = await page.content()
    soup = BeautifulSoup(content, 'html.parser')
    return soup

# Converts date string to datetime
def parse_date(date_str):
    # Define the format of the date string
    date_format = "%b %d, %Y %I:%M %p"
    # Parse the date string into a datetime object
    date_obj = datetime.strptime(date_str, date_format)
    return date_obj

# Get all threads on a CD Page
def find_all_threads(soup):
    postings = soup.find_all('div', class_='fps-result')
    all_threads = defaultdict(dict)
    for thread in postings:
        id = thread.find("div", class_='fps-topic')['data-topic-id']
        title = thread.find("span", class_='topic-title').get_text().strip()
        date = thread.find("span", class_='relative-date')['title']
        href = thread.find("a", class_='search-link')['href']
        all_threads[id] = {
            'title': title,
            'date': date,
            'href': href
        }
    return all_threads

# Returns a list of threads that are not yet present or matching in the database
def find_updated_threads(database_path, posts):
    with open(database_path, 'r') as file:
            tracked_threads = json.load(file)
    new_posts = defaultdict(dict)
    for id in posts:
        if(id not in tracked_threads):
            new_posts[id] = posts[id]
        elif(posts[id]['date'] != tracked_threads[id]['date']):
            new_posts[id] = posts[id]
    return new_posts

# Adds threads to existing file
def add_threads(database_path, posts):
    # Gets existing file data
    with open(database_path, 'r') as file:
        data = json.load(file)
    # Updates with new data
    data.update(posts)
    # Writes to file
    with open(database_path, 'w') as file:
        json.dump(data, file, indent=4)

async def send_posts(browser, database_path, threads):
    with open(database_path, 'r') as file:
        tracked_threads = json.load(file)
    for thread in threads:
        link = f"https://www.chiefdelphi.com{threads[thread]['href']}"
        soup = await get_soup(browser, link, referer_url)
        posts = soup.find_all("div", class_='topic-post')
        if(thread in tracked_threads):
            last_scrape_date = parse_date(tracked_threads[thread]['date'])
        else:
            last_scrape_date = datetime(1960,1,1)
        for post in posts:
            post_date = parse_date(post.find("span", class_='relative-date')['title'])
            if(post_date > last_scrape_date):
                post_text = post.get_text().strip()
                thread_title = threads[thread]['title']
                if("5137" in post_text or "5137" in thread_title):
                    author = post.find("span", class_=['first', 'username']).get_text().strip()
                    raw_text = post.find("div", class_='cooked').get_text().strip()
                    text = re.sub(r'\s+', ' ', raw_text).strip() # Removes excessive whitespace
                    image_container = post.find("a", class_='trigger-user-card')
                    image = image_container.find("img", class_='avatar')['src']
                    ping_slack(thread_title, text, post_date.date(), author, link, image)

def ping_slack(title, text, date, author, link, image):
    headers = {
        'Content-Type': 'application/json',
    }
    data = {
        "blocks": [
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{title}*"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "text": "*New Post *  |  Tagged as \"5137\"",
                        "type": "mrkdwn"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{text[:250]}...\n\n*Date:*\n{date}\n\n*Author:*\n{author}\n\n<{link}|*| View Post |*>"
                },
                "accessory": {
                    "type": "image",
                    "image_url": f"https://www.chiefdelphi.com/{image}",
                    "alt_text": "computer thumbnail"
                }
            },
		    {
			    "type": "divider"
		    }
        ]
    }
    response = requests.post(slack_webhook, headers=headers, data=json.dumps(data))
    
    if response.status_code != 200:
        raise ValueError(f"Request to Slack returned an error {response.status_code}, the response is:\n{response.text}")

async def main():
    browser = await set_up_browser()
    soup = await get_soup(browser, main_url, referer_url)
    all_threads = find_all_threads(soup)
    updated_threads = find_updated_threads(database_path, all_threads)
    await send_posts(browser, database_path, updated_threads)
    add_threads(database_path, updated_threads)
    await browser.close()

asyncio.get_event_loop().run_until_complete(main())