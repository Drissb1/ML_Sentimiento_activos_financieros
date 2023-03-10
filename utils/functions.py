import numpy as np
import pandas as pd

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common import keys
from selenium import webdriver 
import chromedriver_autoinstaller
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.keys import Keys
import regex as re

import time
import datetime
from datetime import date, timedelta, datetime
from dateutil.relativedelta import relativedelta
import random

import yfinance as yf

# User agents aleatorios para scrapear evitando detección:

def rand_user_agent():

    user_agents = (["Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36",
                    "Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:24.0) Gecko/20100101 Firefox/24.0",
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.1 Safari/605.1.15",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0",
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36",
                    "Mozilla/5.0 (X11; Linux i586; rv:31.0) Gecko/20100101 Firefox/31.0",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36",
                    "Mozilla/5.0 (Windows Phone 10.0; Android 4.2.1; Microsoft; Lumia 640 XL LTE) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Mobile Safari/537.36 Edge/12.10166"])
    
    user_agent = random.choice(user_agents)
    return user_agent

# Yahoo Finance Crawling

def yf_crawling(tickers=[]):
    
    
    chromedriver_autoinstaller.install() 
    #Opciones driver para evitar detección.
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument('--start-maximized')
    options.add_experimental_option("excludeSwitches", ["enable-automation"]) 
    options.add_experimental_option("useAutomationExtension", False) 
    driver = webdriver.Chrome(options=options) 
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})") 

    # Función para tiempos de espera.
    def sleep(dur=''):
        if dur == 'long':
            time.sleep(np.random.uniform(low=5.12,high=8.324))
        elif dur == 'short':
            time.sleep(np.random.uniform(low=2.12,high=5.324))
        else:
            time.sleep(np.random.uniform(low=0.5,high=0.8))
    # Scroll
    def scroll_down():
        html = driver.find_element(By.TAG_NAME, 'html')
        html.send_keys(Keys.END)
        sleep()
    
    final_list = []
    
    for ticker in tickers:
        url = f'https://finance.yahoo.com/quote/{ticker}?p={ticker}&.tsrc=fin-srch'
        driver.execute_cdp_cmd("Network.setUserAgentOverride", {"userAgent": rand_user_agent()})
        driver.get(url)
        sleep('short')
        
        # Aceptar cookies
        try: 
            driver.find_element(By.XPATH,'//*[@id="consent-page"]/div/div/div/form/div[2]/div[2]/button').click()
            sleep('short')
            driver.find_element(By.XPATH,'//*[@id="myLightboxContainer"]/section/button[2]').click()
            sleep('long')
        except: pass
        sleep('short')
        
        # Scroll para cargar html     
        [scroll_down() for x in range(35)]

        # Data extraction
        
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        filter_a = soup.find_all('a')
        links = [link.get('href') for link in filter_a]
        links_filtered = [link for link in links if link != None and '/news/' in link]
        for link in links_filtered:
            link = link.replace('?.tsrc=fin-notif','')
            link = 'https://finance.yahoo.com/'+link
            if link != 'https://finance.yahoo.com//news/': final_list.append((ticker,link)) 
        
    to_DF = pd.DataFrame(final_list,columns=('ticker','link'))
    to_DF.to_csv('data/crawling.csv')

    driver.close()
    return to_DF
        
#Extracción artículo YF

def yf_scraping(df=None):

    articles = []
    for url in df.link:
        try:
            headers = {'User-Agent': rand_user_agent(),
                        'referer':'https://www.google.com/',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.5',
                        'DNT': '1',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                        }
            
            with requests.get(url) as response:
                soup = BeautifulSoup(response.text, 'html.parser')
                paragraph_texts = [p.text for p in soup.find_all('p')]
                clean_text = ' '.join(paragraph_texts)
                exclude = ['All rights reserved.',' Click here for the latest stock market news and in-depth analysis, including events that move stocks Read the latest financial and business news from Yahoo Finance Download the Yahoo Finance app for Apple or Android Follow Yahoo Finance on Twitter, Facebook, Instagram, Flipboard, LinkedIn, and YouTube Related Quotes','Join the most important conversation in crypto and web3! Secure your seat today ','Related Quotes','For the latest earnings reports and analysis, earnings whispers and expectations, and company earnings news, click here Read the latest financial and business news from Yahoo Finance Download the Yahoo Finance app for Apple or Android Follow Yahoo Finance on Twitter, Facebook, Instagram, Flipboard, LinkedIn, and YouTube']
                for text in exclude:
                    clean_text = clean_text.replace(text,'')
                    
                clean_text = clean_text.lstrip().rstrip()
                
                #Fecha artículo
                try:
                    date_and_time=soup.find_all('time')[0]
                    date_and_time=date_and_time['datetime']
                    date = date_and_time.split('T')[0]
                except: date = 'date_error'

            articles.append((clean_text,date))

        except (requests.exceptions.HTTPError, requests.exceptions.RequestException) as e:
            articles.append(f'Error: {e},{url}')
        
    return articles


# TICKERS YF para análisis

def precios(start=None,end=None,tickers=None):

    data = yf.Ticker(tickers[0]).history(start=start,end=end).reset_index()[['Date','Close']]
    data['Date'] = data['Date'].dt.date
    data.reset_index(inplace=True,drop=True)
    data.rename(columns={'Close':f'{tickers[0]}'},inplace=True)
    print(tickers[0:])
    
    for ticker in tickers[0:]:
           
        yf_ticker = yf.Ticker(ticker).history(start=start,end=end).reset_index()[['Date','Close']]
        yf_ticker['Date'] = yf_ticker['Date'].dt.date
        yf_ticker.reset_index(inplace=True,drop=True)
        
        yf_ticker.rename(columns={'Close':f'{ticker}'},inplace=True)      
        data = data.merge(yf_ticker)            
        
    # Ffill para reemplazar valores del fin de semana en finanza tradicional
    data.ffill(inplace=True)
    data.bfill(inplace=True)

    return data