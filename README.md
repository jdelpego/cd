# CD Scraper Project 
This project inolves scraping the site Chief Delphi in order to get listings about the robotics community and send those notices to slack using webhooks. 


Scrapes using pyppeteer python library -> transforms data and loads into Json file -> compares to existing file and if there is a new listing -> ping slack via webhook.
