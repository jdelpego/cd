# CD Scraper Project 
This project inolves scraping the site Chief Delphi in order to get listings about the robotics community and send those notices to slack using webhooks. 


Scrapes using pyppeteer python library -> transforms data and loads into Json file -> compares to existing file and if there is a new listing -> ping slack via webhook.

Features: 
- Python Web scraper using Puppeteer and Beautiful Soup. 
- Bypasses CloudFlare Anti-Bot detection with 99% success rate. 
- Sends 100% of targeted robotics posts to Slack Bot via Webhooks API. 
- Stores all pre-existing keyword posts in JSON to check for updates. 

<img width="863" alt="CD Scraper" src="https://github.com/user-attachments/assets/412d50c7-e846-4183-95d0-5e5787cc052d">
