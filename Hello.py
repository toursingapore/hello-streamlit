import streamlit as st
from streamlit.logger import get_logger

import pandas as pd
import datetime
import csv
import glob
import pygwalker as pyg
import json
import uuid
import random
import gspread 
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
import httplib2
import os, sys
from json2table import convert

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
import cloudscraper 
from bs4 import BeautifulSoup
import time
import urllib.parse
import urllib.request
import re

from airtable import airtable
import requests
import matplotlib.pyplot as plt
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

import base64
import translators as ts
from requests_toolbelt.multipart.encoder import MultipartEncoder             

from PIL import Image, ImageDraw
from collections import defaultdict
from ultralytics import YOLO
import cv2
from pathlib import Path

from huggingface_hub import InferenceClient
from huggingface_hub.utils import hf_raise_for_status, HfHubHTTPError
import tempfile
from gtts import gTTS
from langdetect import detect

from pytube import YouTube, extract
import speech_recognition as sr
from pydub import AudioSegment
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import SRTFormatter

import openai
import httpx 

LOGGER = get_logger(__name__)

HF_API_TOKEN = "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"
HUB_ULTRALYTICS_API_KEY = "8f402dc7ca8f6866b12da635eb99dacc38c3ec6484"
LEPTON_API_TOKEN = "Idts8YzDtSJSFXrpOlwbxJr7Y1Gx60Os"
ROBOFLOW_API_KEY = 'Fh4GjyJACeJLvWa4r2vN'

# Function to authorize credentials
def authorize_credentials(API_Path):
    SCOPES = ["https://www.googleapis.com/auth/webmasters", "https://www.googleapis.com/auth/webmasters.readonly"]
    #credentials = ServiceAccountCredentials.from_json_keyfile_name(API_Path, scopes=SCOPES)
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(API_Path, scopes=SCOPES)
    http = credentials.authorize(httplib2.Http())
    return http

# Function to inspect URL
def inspect_url(http, URL):
    ENDPOINT = "https://searchconsole.googleapis.com/v1/urlInspection/index:inspect"
    split_url = URL.split('/')
    siteURL = '/'.join(split_url[:3]) + '/'
    content = str({'inspectionUrl': URL, 'siteUrl': siteURL, 'languageCode': 'en'})
    response, content = http.request(ENDPOINT, method="POST", body=content)
    return response, content

def submit_url_google_indexing_api(json_contents, URL):
    try:
        # Load Google API key from apikey.json
        SCOPES = ['https://www.googleapis.com/auth/indexing']
        credentials = ServiceAccountCredentials.from_json_keyfile_dict(json_contents, scopes=SCOPES)
        # Create a service object for interacting with the Google Indexing API
        service = build('indexing', 'v3', credentials=credentials)
        # Send indexing request
        request = {
            'url': URL,
            'type': 'URL_UPDATED'
        }
        result = service.urlNotifications().publish(body=request).execute()
        with st.expander("Click here to view data"):
            st.write(result)       
        st.success('URL has been submitted and Please wait in 24 hours for Googlebot take to crawl the page.')                          
    except Exception as e:
        st.error(f'Error indexing URL: {e}')

def upload_text_file(uploaded_file):
    links = None
    if uploaded_file is not None:
        links = uploaded_file.read().decode().splitlines()
        with st.expander("Click here to view data"):
            st.write(links)
    return links

def upload_json_file(uploaded_file_json):
    json_contents = None
    if uploaded_file_json is not None:
        if uploaded_file_json.type in ["application/json"]:
            json_contents_raw = uploaded_file_json.read()
            json_contents = json.loads(json_contents_raw)
            with st.expander("Click here to view data"):
                st.write(json_contents)
                # st.dataframe(json_contents, use_container_width=True) #Show long data
    return json_contents

def upload_csv_file(uploaded_file_csv):
    df_value = None
    if uploaded_file_csv is not None:
        # Read CSV file into pandas DataFrame
        df_value = pd.read_csv(uploaded_file_csv, encoding='utf8')
        with st.expander("Click here to view data"):
            st.write(df_value)
    return df_value    

# Function to generate unique widget key
def generate_widget_key(widget_id):
    return f"{widget_id}_{hash(widget_id)}"


def run():
    st.set_page_config(
        page_title="SEO TOOLS",
        page_icon=":star:",
    )

    st.write("# Welcome to SEO Applications!")
    st.sidebar.info("Select tool below:")
    # Using "with" notation
    with st.sidebar:
        #add_radio = st.radio(
        #    "Choose a tool below",
        #    ("URL INSPECTION TOOL", "GOOGLE INDEXING API")
        #)
        #st.write(f'You selected {add_radio}')     

        #Navigate to element in current page   
        st.markdown(f"<a href='#search-console-url-inspection-tool'>URL INSPECTION TOOL</a>", unsafe_allow_html=True)
        st.markdown(f"<a href='#submit-links-via-google-indexing-api'>GOOGLE INDEXING API</a>", unsafe_allow_html=True)       
        st.markdown(f"<a href='#keyword-rank-checker'>KEYWORD RANK CHECKER</a>", unsafe_allow_html=True)      
        st.markdown(f"<a href='#keyword-density-checker'>KEYWORD DENSITY CHECKER</a>", unsafe_allow_html=True)
        st.markdown(f"<a href='#auto-post-wordpress-sites'>AUTO POST WORDPRESS SITES</a>", unsafe_allow_html=True)    
        st.markdown(f"<a href='#ask-bot'>ASK BOT</a>", unsafe_allow_html=True)            
        st.markdown(f"<a href='#image-extract-masks-from-image'>IMAGE - EXTRACT MASKS FROM IMAGE</a>", unsafe_allow_html=True)    
        st.markdown(f"<a href='#video-text-to-speech-vice-versa'>VIDEO - TEXT TO SPEECH & VICE VERSA</a>", unsafe_allow_html=True)        
        st.markdown(f"<a href='#visual-analysis-for-csv-file'>VISUAL ANALYSIS FOR CSV FILE</a>", unsafe_allow_html=True)       

    st.markdown(
        """
        We provide best SEO services. **Select a tool from the sidebar** to see more services of what you can do!
        """
    )


    #B1:-- SEARCH CONSOLE URL INSPECTION API  --
    with st.container(border=True):    
        st.write(
        """ 
            ## SEARCH CONSOLE URL INSPECTION TOOL 
            Upload **'API_Key.json'** and **'urls.txt'** files containing URLs (max 20 per file) to inspect urls indexed or not.
        """
        )

        #mỗi lần dùng widget st.file_uploader thì add key unique mới được, nếu ko sẽ bị error
        uploaded_file = st.file_uploader("Upload .txt file with links", type=["txt"], key="1")
        links = upload_text_file(uploaded_file)

        uploaded_file_json = st.file_uploader("Upload .json file with links", type=["json"], key="2")
        json_contents_from_API_key = upload_json_file(uploaded_file_json)

        if links and json_contents_from_API_key:
            st.info("Uploaded .txt and .json files")    
            
        button = st.button("Submit", type="primary", key="3")
        if button and links and json_contents_from_API_key:
            with st.spinner('Wait for it...'): #Show thanh progress khi xử lý code        
              authorized = authorize_credentials(json_contents_from_API_key)
              #st.write(authorized)   
              st.write("Credentials Successfully Authorized!")

              for URL in links:
                  st.write(URL)
                  #URL = 'https://toursingapore.c1.is/hoan-thue-tai-singapore-3tr995/'
                  response, content = inspect_url(authorized, URL)

                  with st.expander("Click here to view data"): 
                      #st.write(content)
                      response_json_contents = json.loads(content) #chứa value json chuẩn            
                      st.write(response_json_contents)

                      #Convert json to table
                      build_direction = "LEFT_TO_RIGHT"
                      table_attributes = {"style" : "width:100%", "border":"1", "border-collapse":"collapse"}
                      html=convert(json.loads(content), build_direction=build_direction, table_attributes=table_attributes)
                      #st.write(html) #get raw html
                      #st.markdown(html, unsafe_allow_html=True)
                      st.components.v1.html(html,height=400,scrolling=True)

    st.divider()

    #B2:-- SUBMIT URLS WITH GOOGLE INDEXING API --
    with st.container(border=True): 
        st.write(
        """ 
            ## SUBMIT LINKS VIA GOOGLE INDEXING API 
            Upload **'API_Key.json'** and **'urls.txt'** files containing URLs (max 20 per file) to inspect urls indexed or not.
        """
        )

        uploaded_file = st.file_uploader("Upload .txt file with links", type=["txt"], key="4")
        links = upload_text_file(uploaded_file)

        uploaded_file_json = st.file_uploader("Upload .json file with links", type=["json"], key="5")
        json_contents_from_API_key = upload_json_file(uploaded_file_json)

        if links and json_contents_from_API_key:
            st.info("Uploaded .txt and .json files")    
            
        button = st.button("Submit", type="primary", key="6")
        if button and links and json_contents_from_API_key:
            with st.spinner('Wait for it...'): #Show thanh progress khi xử lý code              
              authorized = authorize_credentials(json_contents_from_API_key)
              #st.write(authorized)   
              st.write("Credentials Successfully Authorized!")

              for URL in links:
                  st.write(URL)
                  submit_url_google_indexing_api(json_contents_from_API_key, URL)

    st.divider()

    #B3:-- KEYWORD RANK CHECKER --
    #pip install cloudscraper  #HD HERE - https://github.com/VeNoMouS/cloudscraper
    #BYPASS ANTI-BOT, CLOUDFLARE WITH CLOUDSCRAPER - cái này chỉ get souce html, chứ ko click được. Muốn click thì dùng seleniumbase ở trên
    with st.container(border=True): 
        st.write(
        """ 
            ## KEYWORD RANK CHECKER 
            To check the keyword rank in Google ranking, use our free Keyword Position Checker. Just enter the domain name, keywords and search engine and click the blue ‘SUBMIT’ button.
        """
        )    

        website = st.text_input("Enter your website", value='https://www.dulichsingaporegiare.com/', placeholder='https://bot.sannysoft.com/', key="7")     

        #Check multiple keywords
        keyword = st.text_area("Enter your keywords (max 5 keywords)", value="có được mang trái cây vào singapore không \ndu lịch singapore tháng nào đẹp nhất \nmùa mưa ở Singapore là tháng mấy \nnhững thực phẩm không được mang vào singapore \nbộ luật hình sự singapore", placeholder='keyword1 \nkeyword2 \nkeyword3 \nmax 5 keywords')
        #Append keywords to array and remove whitespace dư, empty line
        keyword_Arr = []
        keyword_Arr = [line.strip() for line in keyword.split('\n') if line.strip()]          

        #Check one keyword
        #keyword = st.text_input("Enter your keyword", value="có được mang trái cây vào singapore không", placeholder="cheapest iphone at istore", key="8")        

        device = st.selectbox(
            "Device",
            ("Mobile - Android", "Mobile - iOS", "Desktop - Windows", "Desktop - Linux", "Desktop - macOS"),
            index=0,
            key="9"
        )
        #st.write('You selected:', device)
        #List all SERP countries code - https://www.scaleserp.com/docs/search-api/reference/google-countries - Json api; https://assets.api-cdn.com/scaleserp/scaleserp_google_countries.json
        countries = {
            "Afghanistan": "af",
            "Albania": "al",
            "Algeria": "dz",
            "American Samoa": "as",
            "Andorra": "ad",
            "Angola": "ao",
            "Anguilla": "ai",
            "Antarctica": "aq",
            "Antigua and Barbuda": "ag",
            "Argentina": "ar",
            "Armenia": "am",
            "Aruba": "aw",
            "Ascension Island": "ac",
            "Australia": "au",
            "Austria": "at",
            "Azerbaijan": "az",
            "Bahamas": "bs",
            "Bahrain": "bh",
            "Bangladesh": "bd",
            "Barbados": "bb",
            "Belarus": "by",
            "Belgium": "be",
            "Belize": "bz",
            "Benin": "bj",
            "Bermuda": "bm",
            "Bhutan": "bt",
            "Bolivia": "bo",
            "Bonaire": "bq",
            "Bosnia and Herzegovina": "ba",
            "Botswana": "bw",
            "Bouvet Island": "bv",
            "Brazil": "br",
            "Brunei Darussalam": "bn",
            "Bulgaria": "bg",
            "Burkina Faso": "bf",
            "Burundi": "bi",
            "Cambodia": "kh",
            "Cameroon": "cm",
            "Canada": "ca",
            "Cape Verde": "cv",
            "Catalonia": "cat",
            "Cayman Islands": "ky",
            "Central African Republic": "cf",
            "Chad": "td",
            "Chile": "cl",
            "China": "cn",
            "Christmas Island": "cx",
            "Cocos (Keeling) Islands": "cc",
            "Colombia": "co",
            "Comoros": "km",
            "Congo": "cg",
            "Cook Islands": "ck",
            "Costa Rica": "cr",
            "Cote D'ivoire": "ci",
            "Croatia": "hr",
            "Cuba": "cu",
            "Curaçao": "cw",
            "Cyprus": "cy",
            "Czech Republic": "cz",
            "Democratic Rep Congo": "cd",
            "Denmark": "dk",
            "Djibouti": "dj",
            "Dominica": "dm",
            "Dominican Republic": "do",
            "Ecuador": "ec",
            "Egypt": "eg",
            "El Salvador": "sv",
            "Equatorial Guinea": "gq",
            "Eritrea": "er",
            "Estonia": "ee",
            "Ethiopia": "et",
            "Falkland Islands (Malvinas)": "fk",
            "Faroe Islands": "fo",
            "Fiji": "fj",
            "Finland": "fi",
            "France": "fr",
            "French Guiana": "gf",
            "French Polynesia": "pf",
            "French Southern Territories": "tf",
            "Gabon": "ga",
            "Gambia": "gm",
            "Georgia": "ge",
            "Germany": "de",
            "Ghana": "gh",
            "Gibraltar": "gi",
            "Greece": "gr",
            "Greenland": "gl",
            "Grenada": "gd",
            "Guadeloupe": "gp",
            "Guam": "gu",
            "Guatemala": "gt",
            "Guernsey": "gg",
            "Guinea": "gn",
            "Guinea-Bissau": "gw",
            "Guyana": "gy",
            "Haiti": "ht",
            "Heard Island and Mcdonald Islands": "hm",
            "Holy See (Vatican City State)": "va",
            "Honduras": "hn",
            "Hong Kong": "hk",
            "Hungary": "hu",
            "Iceland": "is",
            "India": "in",
            "Indian Ocean Territory": "io",
            "Indonesia": "id",
            "Iran, Islamic Republic of": "ir",
            "Iraq": "iq",
            "Ireland": "ie",
            "Isle of Man": "im",
            "Israel": "il",
            "Italy": "it",
            "Jamaica": "jm",
            "Japan": "jp",
            "Jersey": "je",
            "Jordan": "jo",
            "Kazakhstan": "kz",
            "Kenya": "ke",
            "Kiribati": "ki",
            "Korea": "kr",
            "Kosovo": "xk",
            "Kuwait": "kw",
            "Kyrgyzstan": "kg",
            "Lao": "la",
            "Latvia": "lv",
            "Lebanon": "lb",
            "Lesotho": "ls",
            "Liberia": "lr",
            "Libyan Arab Jamahiriya": "ly",
            "Liechtenstein": "li",
            "Lithuania": "lt",
            "Luxembourg": "lu",
            "Macao": "mo",
            "Macedonia, the Former Yugosalv Republic of": "mk",
            "Madagascar": "mg",
            "Malawi": "mw",
            "Malaysia": "my",
            "Maldives": "mv",
            "Mali": "ml",
            "Malta": "mt",
            "Marshall Islands": "mh",
            "Martinique": "mq",
            "Mauritania": "mr",
            "Mauritius": "mu",
            "Mayotte": "yt",
            "Mexico": "mx",
            "Micronesia, Federated States of": "fm",
            "Moldova, Republic of": "md",
            "Monaco": "mc",
            "Mongolia": "mn",
            "Montserrat": "ms",
            "Morocco": "ma",
            "Mozambique": "mz",
            "Myanmar": "mm",
            "Namibia": "na",
            "Nauru": "nr",
            "Nepal": "np",
            "Netherlands": "nl",
            "Netherlands Antilles": "an",
            "New Caledonia": "nc",
            "New Zealand": "nz",
            "Nicaragua": "ni",
            "Niger": "ne",
            "Nigeria": "ng",
            "Niue": "nu",
            "Norfolk Island": "nf",
            "Northern Mariana Islands": "mp",
            "Norway": "no",
            "Oman": "om",
            "Pakistan": "pk",
            "Palau": "pw",
            "Palestinian Territory, Occupied": "ps",
            "Panama": "pa",
            "Papua New Guinea": "pg",
            "Paraguay": "py",
            "Peru": "pe",
            "Philippines": "ph",
            "Pitcairn": "pn",
            "Poland": "pl",
            "Portugal": "pt",
            "Puerto Rico": "pr",
            "Qatar": "qa",
            "Reunion": "re",
            "Romania": "ro",
            "Russian Federation": "ru",
            "Rwanda": "rw",
            "Saint Helena": "sh",
            "Saint Kitts and Nevis": "kn",
            "Saint Lucia": "lc",
            "Saint Martin": "mf",
            "Saint Pierre and Miquelon": "pm",
            "Saint Vincent": "vc",
            "Samoa": "ws",
            "San Marino": "sm",
            "Sao Tome and Principe": "st",
            "Saudi Arabia": "sa",
            "Senegal": "sn",
            "Serbia and Montenegro": "rs",
            "Seychelles": "sc",
            "Sierra Leone": "sl",
            "Singapore": "sg",
            "Sint Maarten": "sx",
            "Slovakia": "sk",
            "Slovenia": "si",
            "Solomon Islands": "sb",
            "Somalia": "so",
            "South Africa": "za",
            "South Georgia and the South Sandwich Islands": "gs",
            "Spain": "es",
            "Sri Lanka": "lk",
            "Sudan": "sd",
            "Suriname": "sr",
            "Svalbard and Jan Mayen": "sj",
            "Swaziland": "sz",
            "Sweden": "se",
            "Switzerland": "ch",
            "Syrian Arab Republic": "sy",
            "Taiwan, Province of China": "tw",
            "Tajikistan": "tj",
            "Tanzania, United Republic of": "tz",
            "Thailand": "th",
            "Timor-Leste": "tl",
            "Togo": "tg",
            "Tokelau": "tk",
            "Tonga": "to",
            "Trinidad and Tobago": "tt",
            "Tunisia": "tn",
            "Turkey": "tr",
            "Turkmenistan": "tm",
            "Turks and Caicos Islands": "tc",
            "Tuvalu": "tv",
            "Uganda": "ug",
            "Ukraine": "ua",
            "United Arab Emirates": "ae",
            "United Kingdom": "uk",
            "United States": "us",
            "United States Minor Outlying Islands": "um",
            "Uruguay": "uy",
            "Uzbekistan": "uz",
            "Vanuatu": "vu",
            "Venezuela": "ve",
            "Viet Nam": "vn",
            "Virgin Islands, British": "vg",
            "Virgin Islands, U.S.": "vi",
            "Wallis and Futuna": "wf",
            "Western Sahara": "eh",
            "Yemen": "ye",
            "Zambia": "zm",
            "Zimbabwe": "zw"
        }        
        selected_country = st.selectbox("Pick a country", list(countries.keys()), index=240, key="10")
        #st.write(f"You selected: {selected_country} {countries[selected_country]}")
        # https://www.google.com/search?q=tour%20th%C3%A1i%20lan%20gi%C3%A1%20r%E1%BA%BB&gws_rd=ssl&gl=vn&num=100
        #st.write(f"https://www.google.com/search?q={keyword}&gws_rd=ssl&gl={countries[selected_country]}&num=100")        

        #tự tạo baseId đầu tiên như này để lấy baseId - https://airtable.com/appHrRNYkBMnQiQql/tblQt50ebaPQvsZrD/viwIaYWzAGr5sjUIe?blocks=hide
        PERSONAL_ACCESS_TOKEN = st.text_input("Enter PERSONAL_ACCESS_TOKEN of airtable.com", placeholder='pat13vN......', key="11")
        baseId = st.text_input("Enter baseId of airtable.com", placeholder='appHr......', key="12") 

        keywords_data = []
        myrank = ""
        mywebsite = ""              

        if 'button_clicked' not in st.session_state:
            st.session_state.button_clicked = False

        button = st.button("SUBMIT", type="primary", key="13")
        if button and website and keyword:
            st.session_state.button_clicked = True
            st.write(f"your website is {website}")

            #for loop get all keywords from arrya keyword_Arr để scrape one by one here
            for keyword in keyword_Arr:
                st.write(f"+++ {keyword}", key=f"{uuid.uuid4()}")
                keyword = urllib.parse.quote(keyword) #url encode keyword                
                       
                with st.spinner('Wait for it...'):
                    time.sleep(5)
    
                    if device == "Mobile - Android":
                        scraper = cloudscraper.create_scraper(
                            browser={
                                'browser': 'chrome', #firefox or chrome
                                'platform': 'android', #auto random user-agent: 'linux', 'windows', 'darwin', 'android', 'ios' bypass cloudflare rất ok
                                'desktop': False
                            },             
                            disableCloudflareV1=True  #Disable site có cloudflare           
                        )  # returns a CloudScraper instance
                    elif device == "Mobile - iOS":
                        scraper = cloudscraper.create_scraper(
                            browser={
                                'browser': 'chrome',
                                'platform': 'ios', 
                                'desktop': False
                            },             
                            disableCloudflareV1=True           
                        )    
                    elif device == "Desktop - Windows":
                        scraper = cloudscraper.create_scraper(
                            browser={
                                'browser': 'chrome',
                                'platform': 'windows', 
                                'desktop': True
                            },             
                            disableCloudflareV1=True           
                        )  
                    elif device == "Desktop - Linux":
                        scraper = cloudscraper.create_scraper(
                            browser={
                                'browser': 'chrome',
                                'platform': 'linux', 
                                'desktop': True
                            },             
                            disableCloudflareV1=True          
                        )    
                    else:
                        scraper = cloudscraper.create_scraper(
                            browser={
                                'browser': 'chrome',
                                'platform': 'darwin', 
                                'desktop': True
                            },             
                            disableCloudflareV1=True          
                        )                      
                    
                    # Or: scraper = cloudscraper.CloudScraper()  # CloudScraper inherits from requests.Session
                    #response = scraper.get("https://whoer.net/")
                    response = scraper.get(f"https://www.google.com/search?q={keyword}&gws_rd=ssl&gl={countries[selected_country]}&num=100")
                    html = response.text  # => scraper.get("https://bot.sannysoft.com/").text "<!DOCTYPE html><html><head>..."                    
                    #st.write(response.status_code) #status code với reCAPTCHA 429, còn 200 là OK
                    
                    if response.status_code == 200:
                        #Đưa vào BeautifulSoup cho dễ scrape elements
                        soup = BeautifulSoup(html,'html.parser')

                        #with st.expander("Click here to see more"):  
                            #st.write(response.status_code)
                            #st.code(html)  #bỏ vào html online mới lấy đúng element
                            #st.markdown(html, unsafe_allow_html=True) #load html and render it in streamlit page

                        #B1; Get all urls with device mobile
                        urls = soup.find_all('div', class_='egMi0 kCrYT')
                        found = False
                        all_urls = []
                        i = 1
                        for data in urls:
                            for a in data.find_all('a'):
                                #st.write(a.text) #for getting text between the link
                                href_full_url = a.get('href') #for getting link
                                href_full_url = href_full_url.replace('/url?q=', '')
                                href_full_url = href_full_url.replace('/url?esrc=s&q=&rct=j&sa=U&url=', '')
                                matches = href_full_url.split('&')
                                href = matches[0]              
                                all_urls.append(href)
                                #st.write(str(i) + ". " + href) #show all urls found here
                                i+=1
                                if website in href:
                                    st.write("Found position " + str(i-1) + " - " + urllib.parse.unquote(href) + " - " + datetime.date.today().strftime("%Y-%m-%d")) #url decode
                                    found = True
                                    myrank = str(i-1)
                                    mywebsite = urllib.parse.unquote(href)                            
        
                        if found == False:
                            myrank = "101"
                            mywebsite = "Not find your webiste in 100 SERP"                           
                            st.write("Not find " + website)
                        with st.expander("Click here to see more"):  
                                #st.write(all_urls)
                                count = 0
                                for url in all_urls:
                                    count += 1
                                    st.write(str(count) + ". " + urllib.parse.unquote(url)) 

                    else:
                        st.write("Displayed GOOGLE reCAPTCHA, xem get free 1000 proxy per month here - https://scrape.do/pricing/")
                        with st.expander("Click here to see more"):  
                            st.write(response.status_code) #status code 429 là reCAPTCHA 
                            #st.code(html)  #bỏ vào html online mới lấy đúng element
                            st.markdown(html, unsafe_allow_html=True) #load html and render it in streamlit page                   
                        #continue #bypass tới keyword tiếp theo
                        break   #exit for loop luôn                          
                        #HD Use proxy scrapeops.io for cloudscraper - https://scrapeops.io/python-web-scraping-playbook/python-cloudscraper/#:~:text=Using%20Proxies%20With%20CloudScraper%E2%80%8B&text=If%20you%20use%20proxies%20with,or%20ban%20the%20IP%20address.
                        #free proxy https://scrape.do/pricing/
                        #HD Use proxy scrapingbee.com for cloudscraper - https://www.scrapingbee.com/blog/how-to-scrape-websites-with-cloudscraper-python-example/


                time.sleep(10) #phải sleep mới hạn chế dính recaptcha
                keywords_data.append([datetime.date.today().strftime("%Y-%m-%d"),urllib.parse.unquote(keyword),myrank,mywebsite,device,selected_country])                            
                #keywords_data.append([date,keyword,rank,url,type])  

            df = pd.DataFrame(keywords_data, columns=['Date', 'Keyword', 'Rank', 'URL', 'Type', 'Country'])
            st.write(df)

            #Add info to airtable to track keywords
            st.write(
            """ 
                ##### Connect to airtable.com for tracking keywords and positions
            """
            )

            with st.expander("Click here to view data"):
                def create_records(baseId, tableIdOrName, PERSONAL_ACCESS_TOKEN, KEYWORD, RANK, URL, TYPE, COUNTRY):
                    headers = {
                        'Authorization': f'Bearer {PERSONAL_ACCESS_TOKEN}',
                        'Content-Type': 'application/json',
                    }
                    json_data = {
                        'records': [
                            {
                                'fields': {
                                    'DATE': f'{datetime.date.today().strftime("%Y-%m-%d")}',
                                    'KEYWORD': KEYWORD,
                                    'RANK': RANK,
                                    'URL': URL,
                                    'TYPE': TYPE,
                                    'COUNTRY': COUNTRY,
                                },
                            }
                        ],
                    }
                    response = requests.post(f'https://api.airtable.com/v0/{baseId}/{tableIdOrName}', headers=headers, json=json_data)
                    return response.json()

                #Modify thêm hàm này như create_records ở trên mới dùng được
                def update_record(baseId, tableIdOrName, recordId, field_name, new_value, PERSONAL_ACCESS_TOKEN):
                    headers = {
                        'Authorization': f'Bearer {PERSONAL_ACCESS_TOKEN}',
                        'Content-Type': 'application/json',
                    }
                    json_data = {
                        'records': [
                            {
                                'id': recordId,
                                'fields': {
                                    field_name: new_value
                                }
                            }
                        ]
                    }
                    response = requests.patch(f'https://api.airtable.com/v0/{baseId}/{tableIdOrName}', headers=headers, json=json_data)
                    return response.json()


                #B1; Phải tạo 1 Base trong UI mới được và có link này để lấy được baseId
                #VD - https://airtable.com/appHrRNYkBMnQiQql/tblW8q1RXyFpyXczf/viwCVSZcXJjfwcGjD?blocks=hide
                #baseId = 'appHrRNYkBMnQiQql'
                #tableIdOrName = 'tblW8q1RXyFpyXczf'
                #recordId = 'viwCVSZcXJjfwcGjD'            
                #PERSONAL_ACCESS_TOKEN = 'pat13vNx3AUeA3pp9.fbaac9659c518a0631dfa3558bdc71f7e3e0f1a525eb0e3383ccb5c942763074'


                #B2; Create a NEW table containing in baseId with colums; DATE,KEYWORD,RANK,URL,TYPE
                tableIdOrName = 'KEYWORD_RANK_TRACKER_TABLE'
                headers = {
                    'Authorization': f'Bearer {PERSONAL_ACCESS_TOKEN}',
                    'Content-Type': 'application/json',
                }
                json_data = {
                    'description': '',
                    'fields': [
                        {
                            'name': 'DATE',
                            #'type': 'singleLineText',
                            'options': {
                                'dateFormat': {
                                    'name': 'iso' #iso = "YYYY-MM-DD"
                                },
                            },                                                   
                            'type': 'date',
                        },
                        {
                            'name': 'KEYWORD',
                            'type': 'singleLineText',
                        },
                        {
                            'name': 'RANK',
                            'options': {
                                'precision': 0 #0 là sẽ 0 có số 0 sau số nguyên
                            },                                                   
                            'type': 'number',
                        },
                        {
                            'name': 'URL',
                            'type': 'url',
                        },
                        {
                            'name': 'TYPE',
                            'type': 'singleLineText',
                        },
                        {
                            'name': 'COUNTRY',
                            'type': 'singleLineText',
                        }                                      
                    ],
                    'name': f'{tableIdOrName}',
                }
                response = requests.post(f'https://api.airtable.com/v0/meta/bases/{baseId}/tables', headers=headers, json=json_data)
                if response.status_code == 200:
                    st.write(f"Table {tableIdOrName} created successfully.")
                    #st.write(response.json())
                elif response.status_code == 422:
                    st.write(f"Table {tableIdOrName} already exists with that name.")
                    #st.write(response.json())
                else:
                    st.write(f"Failed to create table. Status code: {response.status_code}")
                    st.write(response.text)


                #B3; Get all records id and values in the table                        
                response = requests.get(f'https://api.airtable.com/v0/{baseId}/{tableIdOrName}', headers=headers)
                st.write(response.json())

                #Append all records id vào data          
                data = response.json().get('records', [])
                #st.write(data[0]['fields']['DATE'])  #get data đầu tiên
                #st.write(data[-1]['fields']['KEYWORD']) #get data cuối cùng

                #Check last DATE and current_date
                current_date = str(datetime.date.today().strftime("%Y-%m-%d")) #YYYY-MM-DD
                #Decode json and convert all to a raw string, then use regular expression to extract target values
                string_data = json.dumps(response.json())
                #st.write(string_data)              

                #date_to_check = "2024-05-09"
                date_to_check = current_date
                pattern = fr'"DATE":\s*"{date_to_check}"'
                if re.search(pattern, string_data):
                    #st.write(f"Found 'DATE': {date_to_check} - Update records")
                    #Update records
                    st.write("Updated once per day only, therefore no need to update anymore.")
                    pass
                else:
                    #st.write(f"not find 'DATE': {date_to_check} - Create records")                    
                    #Create records
                    st.write("Created records in the table at airtable.com")
                    #response = create_records(baseId, tableIdOrName, PERSONAL_ACCESS_TOKEN, 'có được mang trái cây vào singapore không', '12', 'https://airtable.com/developers/web/api/field-model#multiple-3-url', 'Mobile - Android')
                    #st.write(response)
                    #Add all values in array keywords_data vào airtable
                    for myKeyword in keywords_data:
                        #st.write(myKeyword)
                        response = create_records(baseId, tableIdOrName, PERSONAL_ACCESS_TOKEN, myKeyword[1], int(myKeyword[2]), myKeyword[3], myKeyword[4], myKeyword[5])                    
                    pass
                      
        #SHOW KEYWORD RANK TRACKER CHART
        if st.session_state.button_clicked:
            #VD - https://airtable.com/appHrRNYkBMnQiQql/tblW8q1RXyFpyXczf/viwCVSZcXJjfwcGjD?blocks=hide
            #baseId = 'appHrRNYkBMnQiQql'
            #tableIdOrName = 'tblW8q1RXyFpyXczf'
            #recordId = 'viwCVSZcXJjfwcGjD'            
            #PERSONAL_ACCESS_TOKEN = 'pat13vNx3AUeA3pp9.fbaac9659c518a0631dfa3558bdc71f7e3e0f1a525eb0e3383ccb5c942763074'


            #B2; Create a NEW table containing in baseId with colums; DATE,KEYWORD,RANK,URL,TYPE
            tableIdOrName = 'KEYWORD_RANK_TRACKER_TABLE'
            headers = {
                'Authorization': f'Bearer {PERSONAL_ACCESS_TOKEN}',
                'Content-Type': 'application/json',
            }

            response = requests.get(f'https://api.airtable.com/v0/{baseId}/{tableIdOrName}', headers=headers)
            #st.write(response.json())

            data_array = {
                "KEYWORD": [
                    #"có được mang trái cây vào singapore không","có được mang trái cây vào singapore không","có được mang trái cây vào singapore không",
                ],
                "RANK": [
                    #44, 54,76,
                ],
                "DATE": [
                    #"2024-05-05","2024-05-06","2024-05-07"
                ]
            }

            #data_array = {
            #    "KEYWORD": ["có được mang trái cây vào singapore không", "có được mang trái cây vào singapore không", "có được mang trái cây vào singapore không", "mùa mưa ở Singapore là tháng mấy", "mùa mưa ở Singapore là tháng mấy", "mùa mưa ở Singapore là tháng mấy", "những thực phẩm không được mang vào singapore", "những thực phẩm không được mang vào singapore", "những thực phẩm không được mang vào singapore"],
            #    "RANK": [44, 54, 74, 43, 45, 74, 26, 24, 24],
            #    "DATE": ['2024-05-05', '2024-05-06', '2024-05-07', '2024-05-05', '2024-05-06', '2024-05-07', '2024-05-05', '2024-05-06', '2024-05-07']
            #}
            #st.write("dữ liệu data_array chuẩn phải như dưới")

            records = response.json().get('records', [])
            for data in records:
                # Appending values to arrays
                data_array["KEYWORD"].append(data["fields"]["KEYWORD"])
                data_array["RANK"].append(data["fields"]["RANK"])
                data_array["DATE"].append(data["fields"]["DATE"])                        

            #st.write(data_array)
            df = pd.DataFrame(data_array)
            clist = df["KEYWORD"].unique().tolist()

            selections = st.multiselect("Select keyword", clist)
            if selections:
                st.write("You selected: {}".format(", ".join(selections)))
                dfs = {selected: df[df["KEYWORD"] == selected].sort_values(by="DATE") for selected in selections} #sort data show chart by "DATE"


                fig = go.Figure()
                for selected, df in dfs.items():
                    fig.add_trace(go.Scatter(x=df["DATE"], y=df["RANK"], name=selected))
                    #fig.add_trace(go.Scatter(x=df["DATE"], y=df["RANK"], mode='markers', name=selected))

                fig.update_layout(yaxis=dict(autorange="reversed")) #invert y axis descending (trục y giảm dần)
                st.plotly_chart(fig)

    st.divider()

    #B5:-- KEYWORD DENSITY CHECKER --
    with st.container(border=True): 
        st.write(
        """ 
            ## KEYWORD DENSITY CHECKER 
            Use check density of keywords.
        """
        )

        website = st.text_input("Enter your website to crawl", placeholder="https://whoer.net/", key="14")
        button = st.button("SUBMIT", type="primary" , key="15")
        if button:
            st.write(f"your website is {website}")  
            with st.container():
                with st.spinner('Wait for it...'):
                    time.sleep(5)
                    def get_driver():
                        return webdriver.Chrome(
                            service=Service(
                                ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()
                            ),
                            options=options,
                        )

                    options = Options()
                    options.add_argument("--disable-gpu")
                    options.add_argument("--headless=new")
                    options.add_argument('--no-sandbox')
                    options.add_argument('--disable-dev-shm-usage')
                    options.add_argument("--enable-javascript")
                    options.add_argument("user-agent=Mozilla/5.0 (Linux; Android 13; SAMSUNG SM-G988B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/20.0 Chrome/106.0.5249.126 Mobile Safari/537.36")
                    #proxy = '23.23.23.23:3128'
                    #options.add_argument('--proxy-server='+proxy) #use proxy with --proxy-server=23.23.23.23:3128
                    #options.add_argument('--proxy-server=socks5://'+proxy) #use socks5 with --proxy-server=socks5://23.23.23.23:3128

                    driver = get_driver()
                    driver.get(website) #driver.get("https://vnexpress.net")

                    def wait_for_page_load(driver): 
                        return driver.execute_script('return document.readyState') == 'complete'             
                    
                    Page_Loaded = wait_for_page_load(driver)
                    if Page_Loaded:
                        #st.write(f"Page Loaded: {Page_Loaded}")

                        html = driver.page_source
                        #st.code(html) #show code html để user nhìn thấy
                        #st.markdown(html, unsafe_allow_html=True) #load html and render it in streamlit page

    st.divider()


    #B6:-- Auto get url, then translate to target languague and auto post wordpress sites --
    with st.container(border=True): 
        st.write(
        """ 
            ## AUTO POST WORDPRESS SITES 
            Use this tool to get content from url, then translate to target languague and auto post to multiple wordpress sites once.
        """
        )

        def upload_img_to_wp(wordpress_user, wordpress_application_password, website_wordpress, imgPath, img_alt=""):
            fileName = os.path.basename(imgPath)
            multipart_data = MultipartEncoder(
                fields={
                    # a file upload field
                    'file': (fileName, open(imgPath, 'rb'), 'image/jpg'),
                    # plain text fields
                    #'title': img_alt,
                    'alt_text': img_alt,
                    'caption': img_alt,
                    'description': img_alt
                }
            )
            response = requests.post(f'{website_wordpress}/wp-json/wp/v2/media', data=multipart_data,
                                    headers={'Content-Type': multipart_data.content_type},
                                    auth=(wordpress_user, wordpress_application_password))
            id = 0
            link = ''
            if response.status_code == 201:
                id = response.json()['id']
                link = response.json()['guid']["rendered"]
                #id may be used to set 'featured_media' field of created post
            else:
                st.write("Unexpected status code: {}".format(response.status_code))
            return id, link                                      

        def create_wordpress_post(wordpress_user, wordpress_application_password, website_wordpress, translated_title, translated_content, random_image_id=None):
            # Concatenate WordPress credentials
            wordpress_credentials = wordpress_user + ':' + wordpress_application_password
            wordpress_token = base64.b64encode(wordpress_credentials.encode())
            wordpress_header = {'Authorization': 'Basic ' + wordpress_token.decode('utf-8')}                            
            # API URL for creating post
            api_url = f'{website_wordpress}/wp-json/wp/v2/posts'                            
            # Data for the post
            data = {
                "title": translated_title,
                'content': '<!-- wp:html -->' + translated_content + '<!-- /wp:html -->',                      
                'status': 'publish',
                'excerpt': translated_title,
                'comment_status' : 'closed',
                #'featured_media': random_image_id, #select number in media library wp - vd 1 or 4 or 5 or chọn img đầu tiên image_list_array[0] làm featured_media
                #'ping_status' : 'open', #open, closed
                #'slug' : 'example-post-1',
                #'categories' : [1, 2],  # Category IDs
                #'tags' : ['tag1', 'tag2'],                                
            }
            #cho featured_media is optional
            if random_image_id is not None:
                data['featured_media'] = random_image_id #'featured_media': random_image_id, #select number in media library wp - vd 1 or 4 or 5 or chọn img đầu tiên image_list_array[0] làm featured_media

            # Send POST request to create the post
            response = requests.post(api_url, headers=wordpress_header, json=data)                            
            # Check the response status
            if response.status_code == 201:
                st.write("Post created successfully!")                                
                # Get latest post
                wpBaseURL = website_wordpress
                wp_posts_endpoint = f'{wpBaseURL}/wp-json/wp/v2/posts?per_page=1' # Get 1 latest post only                            
                posts = requests.get(wp_posts_endpoint)
                parse_posts_json = posts.json()                                
                # Extract relevant information from the latest post
                for post in parse_posts_json:
                    post_link = post['link']
                    post_id = post['id']
                    return post_link, post_id
            else:
                st.write("Error creating post:", response.text)  

        #Auto get url, then translate to target languague, then autopost wordpress
        website = st.text_input("Enter target url to get content", value="https://e.vnexpress.net/news/business/companies/billionaire-asplundh-family-s-95m-worker-exploitation-history-resurfaces-amid-in-law-s-bully-scandal-4744828.html", placeholder="https://www.neverendingfootsteps.com/cost-of-travel-singapore-budget/", key="16")       
        languages = {
            "English": "en",
            "Chinese": "zh",
            "Arabic": "ar",
            "Russian": "ru",
            "French": "fr",
            "German": "de",
            "Spanish": "es",
            "Portuguese": "pt",
            "Italian": "it",
            "Japanese": "ja",
            "Korean": "ko",
            "Greek": "el",
            "Dutch": "nl",
            "Hindi": "hi",
            "Turkish": "tr",
            "Malay": "ms",
            "Thai": "th",
            "Vietnamese": "vi",
            "Indonesian": "id",
            "Hebrew": "he",
            "Polish": "pl",
            "Mongolian": "mn",
            "Czech": "cs",
            "Hungarian": "hu",
            "Estonian": "et",
            "Bulgarian": "bg",
            "Danish": "da",
            "Finnish": "fi",
            "Romanian": "ro",
            "Swedish": "sv",
            "Slovenian": "sl",
            "Persian/Farsi": "fa",
            "Bosnian": "bs",
            "Serbian": "sr",
            "Fijian": "fj",
            "Filipino": "tl",
            "Haitian Creole": "ht",
            "Catalan": "ca",
            "Croatian": "hr",
            "Latvian": "lv",
            "Lithuanian": "lt",
            "Urdu": "ur",
            "Ukrainian": "uk",
            "Welsh": "cy",
            "Tahiti": "ty",
            "Tongan": "to",
            "Swahili": "sw",
            "Samoan": "sm",
            "Slovak": "sk",
            "Afrikaans": "af",
            "Norwegian": "no",
            "Bengali": "bn",
            "Malagasy": "mg",
            "Maltese": "mt",
            "Queretaro Otomi": "otq",
            "Klingon/Tlhingan Hol": "tlh",
            "Gujarati": "gu",
            "Tamil": "ta",
            "Telugu": "te",
            "Punjabi": "pa",
            "Amharic": "am",
            "Azerbaijani": "az",
            "Bashkir": "ba",
            "Belarusian": "be",
            "Cebuano": "ceb",
            "Chuvash": "cv",
            "Esperanto": "eo",
            "Basque": "eu",
            "Irish": "ga"
        }
        selected_language = st.selectbox("Pick a target language to translate", list(languages.keys()), index=17, key="17")
        #st.write(f"You selected: {selected_language} ({languages[selected_language]})")             
        website_wordpress = st.text_input("Enter your wordpress url to publish post", value="http://toursingapore.medianewsonline.com", placeholder="http://toursingapore.medianewsonline.com", key="18")                
        edit_content = st.checkbox("Customize body HTML before creating a post to wordpress")
        download_img_from_url_and_upload_to_wp_media = st.checkbox("Download images from target url and upload to wordpress media")
        
        #Free library textgenie - https://github.com/hetpandya/textgenie/blob/main/examples/basic.py , Parrot_Paraphraser - https://github.com/PrithivirajDamodaran/Parrot_Paraphraser/
        #Load pretrained model into streamlit - https://github.com/happilyeverafter95/ml-streamlit-demo
        #Load pretrained model into streamlit - https://www.youtube.com/watch?v=8hOzsFETm4I&list=PLHgX2IExbFosAKDJ6yuVjnQLRhoj_yc3g&ab_channel=1littlecoder
        #Load pretrained model NẶNG max 100GB vào https://www.comet.com/site/pricing/ , sau đó dùng API của nó connect model sẽ ok hơn - HD ở đây https://www.reddit.com/r/MachineLearning/comments/fbsi01/d_how_do_you_share_a_large_100mb_trained_model_on/
        #Free Train custom model YOLOv5 and YOLOv8 via Ultralytics HUB - https://hub.ultralytics.com/ và dùng model đó qua cloud api luôn - https://youtu.be/OpWpBI35A5Y?si=oIWqe7Zm0rt1cvcd ; Inference API Ultralytics HUB | Episode 32
        #Xem thêm dùng AI MODEL fairseq - https://github.com/facebookresearch/fairseq/tree/main/examples/paraphraser
        paraphrase = st.checkbox("Paraphrase content") 

        # http://toursingapore.medianewsonline.com/ | user wp; DipasiEdI | pass D1[yE7.7L6Gv2tO
        #Must Install plugin ‘Application Passwords Enable’ - https://wordpress.org/plugins/application-passwords-enable/ và config để lấy wordpress_application_password thì mới auto post được
        #wordpress_user = 'DipasiEdI'
        #wordpress_application_password = 'EuuI uyHa uI9e EUyw pm11 6Tji'
        wordpress_user = st.text_input("Enter wordpress_user", placeholder="stevejob", key="19")
        wordpress_application_password = st.text_input("Enter wordpress_application_password", placeholder="Kuei uyHa uI9e EUyw pm11 8Tmi", key="20")
        st.warning("You install 'Application Passwords Enable' plugin and get 'wordpress_application_password' - https://wordpress.org/plugins/application-passwords-enable/", icon=None)

        if 'button_clicked_2' not in st.session_state:
            st.session_state.button_clicked_2 = False

        button = st.button("SUBMIT", type="primary" , key="21")
        if button and website and selected_language and website_wordpress and wordpress_user and wordpress_application_password:
            st.session_state.button_clicked_2 = True

            with st.container():
                with st.spinner('Wait for it...'): #Show thanh progress khi xử lý code                        
                    #Step 1: Scrape URL
                    scraper = cloudscraper.create_scraper(
                        browser={
                            'browser': 'chrome', #firefox or chrome
                            'platform': 'android', #auto random user-agent: 'linux', 'windows', 'darwin', 'android', 'ios' bypass cloudflare rất ok
                            'desktop': False
                        },             
                        disableCloudflareV1=True  #Disable site có cloudflare           
                    )  # returns a CloudScraper instance                
                    params = {
                        'api': 'article',
                        'url': f'{website}',
                        'token': '',
                        'naturalLanguage': 'categories',
                    }

                    response = scraper.get('https://labs.diffbot.com/testdrive/article', params=params)
                    if response.status_code == 200:
                        response_json_raw = response.text
                        json_contents = json.loads(response_json_raw) #convert to value json chuẩn            
                        #st.write(json_contents)               

                        title = json_contents["objects"][0]["title"]
                        #st.write(title)

                        #content = json_contents["objects"][0]["text"]
                        #st.write(content)

                        html_content = json_contents["objects"][0]["html"]
                        #st.code(html_content)  #bỏ vào html online mới lấy đúng element
                        #st.markdown(html_content, unsafe_allow_html=True)

                        #Step 2: Auto-translate to target language & download from target url
                        ### List all translators (default bing or google, baidu, alibaba,...)
                        #st.write(ts.translators_pool)
                        #st.write(ts.translate_html(q_text, translator='google', from_language='auto', to_language='vi'))
                        #st.write(ts.translate_html(q_html, translator='alibaba')) #translate full html code - tested bị error ko được nên phải làm theo cách dưới

                        st.write("#### Content translated completely:")
                        # Translate title & body content
                        translated_title = ts.translate_text(title, translator='google', from_language='auto', to_language=languages[selected_language])
                        #st.write(f"TITLE: {translated_title}")
                        # write values to seession
                        st.session_state['data_title'] = translated_title                        

                        #Đưa vào BeautifulSoup để extract chỉ text in tag html, sau đó translate chúng rồi bỏ ngược lại vào trong tag html để được text đã translated và đặt trong code html
                        soup = BeautifulSoup(html_content,'html.parser')
                        #headings = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "a", "b", "strong", "i", "em", "li"])     
                        headings = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "img"])           
                        #headings = soup.find_all(re.compile("^h[1-6]$"))
                        translated_content_array = []
                        image_list_array = []
                        for heading in headings:
                            if heading.name.strip() == "img":
                                img_src = heading['src'] #Get img src of url post
                                img_alt = heading['alt'] #Get img alt of url post
                                #st.write(f"<{heading.name.strip()} alt='{heading['alt']}' src='{heading['src']}'>")
                                
                                if download_img_from_url_and_upload_to_wp_media == False:
                                    #Keep img src from orginal url post and put in html code
                                    translated_content_array.append(f"<{heading.name.strip()} alt='{heading['alt']}' src='{heading['src']}' style='height: 100%; width: 100%; object-fit: contain'>")
                                else:
                                    #Download image from URL
                                    path_to_current_folder = os.path.dirname(os.path.realpath(__file__))
                                    #st.write(f"Path to current directory: {path_to_current_folder}")
                                    #urllib.request.urlretrieve("http://www.gunnerkrigg.com//comics/00000001.jpg", "00000001.jpg")
                                    imgPath = f"{random.randrange(1,100)}.jpg"
                                    result = urllib.request.urlretrieve(img_src, imgPath)
                                    #st.write(result)

                                    #Upload images to wordpress media
                                    newID, link = upload_img_to_wp(wordpress_user, wordpress_application_password, website_wordpress, imgPath, img_alt)
                                    #st.write(f"ID: {newID} - link: {link}")
                                    image_list_array.append(newID)

                                    #Replace img src from orginal url post by img in wp and put in html code
                                    translated_content_array.append(f"<{heading.name.strip()} alt='{heading['alt']}' src='{link}' style='height: 100%; width: 100%; object-fit: contain'>")                                    

                            else:
                                #TRANSLATE LINE BY LINE mới được, vì nếu translate hơn 5000 ký tự sẽ bị error
                                content_translation = ts.translate_text(heading.text.strip(), translator='google', from_language='auto', to_language=languages[selected_language])
                                #st.write(f"<{heading.name.strip()}>{content_translation}</{heading.name.strip()}>")
                                translated_content_array.append(f"<{heading.name.strip()}>{content_translation}</{heading.name.strip()}>")
                        
                        translated_content = '\n'.join(translated_content_array)
                        st.code(translated_content)

                        random_image_id = ""
                        if image_list_array:
                            random_image_id = random.choice(image_list_array)
                            #st.write(random_image_id)

                        # write values to session
                        st.session_state['data_content'] = translated_content
                        st.session_state['data_random_image_id'] = random_image_id
                        
                        #Step 3: Auto-post to WordPress
                        #Must Install plugin ‘Application Passwords Enable’ - https://wordpress.org/plugins/application-passwords-enable/ và config để lấy wordpress_application_password thì mới auto post được
                        #post_link, post_id = create_wordpress_post(wordpress_user, wordpress_application_password, website_wordpress, translated_title, translated_content, random_image_id)
                        #st.write(f"POST ID: {post_id} - POST LINK: {post_link}")

                    else:
                        st.write('Error with request url') 

        if st.session_state.button_clicked_2:
            if edit_content:
                # read values from session
                data_title_from_session = st.session_state['data_title']
                data_content_from_session = st.session_state['data_content']
                data_random_image_id_from_session = st.session_state['data_random_image_id']            
                
                user_input = st.text_area("Customize body HTML after translated", value=f"{data_content_from_session}", height=400, key="22")
                st.write("### Preview HTML Viewer:")         
                with st.expander("Click here to view data"):
                    st.markdown(user_input, unsafe_allow_html=True)
                button = st.button("PUBLISH POST", type="primary" , key="23")
                if button:
                    translated_title = data_title_from_session
                    translated_content = user_input
                    random_image_id = data_random_image_id_from_session

                    #Step 3: Auto-post to WordPress
                    #Must Install plugin ‘Application Passwords Enable’ - https://wordpress.org/plugins/application-passwords-enable/ và config để lấy wordpress_application_password thì mới auto post được
                    post_link, post_id = create_wordpress_post(wordpress_user, wordpress_application_password, website_wordpress, translated_title, translated_content, random_image_id)
                    st.write(f"POST ID: {post_id} - POST LINK: {post_link}")

                    # Delete a single key-value pair
                    del st.session_state['data_title']
                    del st.session_state['data_content']
                    del st.session_state['data_random_image_id']

                    st.session_state.button_clicked_2 = False #chuyển về trạng thái lúc đầu khi chưa click button
            else:
                #Step 3: Auto-post to WordPress
                # read values from session
                translated_title = st.session_state['data_title']
                translated_content = st.session_state['data_content']
                post_link, post_id = create_wordpress_post(wordpress_user, wordpress_application_password, website_wordpress, translated_title, translated_content)
                st.write(f"POST ID: {post_id} - POST LINK: {post_link}") 

                # Delete a single key-value pair
                del st.session_state['data_title']
                del st.session_state['data_content']

                st.session_state.button_clicked_2 = False #chuyển về trạng thái lúc đầu khi chưa click button

    st.divider()

    #B7:-- Ask chatGPT3.5 VIA LEPTON API --
    with st.container():
        st.write("## ASK BOT")

        # Storing the chat
        if 'generated' not in st.session_state:
            st.session_state['generated'] = []
        if 'past' not in st.session_state:
            st.session_state['past'] = []         

        add_radio = st.radio(
            "ChatBot type",
            ["OpenChat 3.5", "Llama2 13b"],
            index=0,
        )
        #st.write("You selected:", add_radio)

        # User input
        user_input = st.text_area("You:", placeholder="What is your name and version", key="24", height=200)
        if user_input:
            api_base_url = ""
            api_model = ""
            if add_radio == "OpenChat 3.5":
                api_base_url="https://openchat-3-5.lepton.run/api/v1/"
                api_model="openchat-3-5"
            else:
                api_base_url="https://llama2-13b.lepton.run/api/v1/"
                api_model="llama2-13b"

            #LEPTON API - https://www.lepton.ai/playground/chat/openchat-3-5 - list all bot like chatGPT here
            client = openai.OpenAI(
                #base_url="https://openchat-3-5.lepton.run/api/v1/",
                base_url=api_base_url,
                api_key=LEPTON_API_TOKEN
            )
            completion = client.chat.completions.create(
                #model="openchat-3-5",
                model=api_model,
                messages=[
                    {"role": "user", "content": f"{user_input}"},
                ],
                max_tokens=128,
                stream=False, #PHẢI set stream=False mới get message.content được - default stream=True
            )
            #st.write(completion)
            bot_response = completion.choices[0].message.content
            #st.write(bot_response)           

            if bot_response:            
                # Store st.session_state
                st.session_state['past'].append(user_input)
                st.session_state['generated'].append(bot_response)
            else:
                st.write('Not receive bot_response yet')

        # Displaying the chat history
        if st.session_state['generated']:
            with st.expander("Click here to view conversation"):
                for i in range(len(st.session_state['generated']) - 1, -1, -1):
                    st.info(st.session_state['past'][i], icon=None)
                    st.success(st.session_state["generated"][i], icon=None)

    st.divider() 

    #B8:-- DEPLOY CUTOM MODEL VIA LEPTON API --
    with st.container():
        st.write(
        """ 
            ## CREATE PHOTONS WITH CUSTOM MODEL VIA COMMAND LINE LEPTON API
            + SEGMENT ANYTHING
        """
        )        

        # User input
        user_input = st.text_input("Command line:", value="pwd", placeholder="Example command line: pwd", key="25")
        button = st.button("SUBMIT", type="primary" , key="26")        
        if button and user_input:
            #os.system("ls -l") # Run command line linux
            #os.popen("ls -l").read() # This will run the command and return any output
            #return_command_line = []   
            return_command_line = os.popen(user_input).read()
            st.write(return_command_line)
            for line in return_command_line:
                print(line.strip())            

    st.divider()

    #B9:-- INFERENCE MODEL VIA HUGGINGFACE API --
    with st.container(border=True): 
        st.write(
        """ 
            ## IMAGE - EXTRACT MASKS FROM IMAGE
        """
        )

        user_input_arr = []
        img_path_arr = []

        add_radio = st.radio(
            "Image type",
            ["Generate image from prompt", "Change clothes from reference image", "Extract masks from uploaded image", "Extract masks from image URL"],
            index=0,
        )
        #st.write("You selected:", add_radio)
        if add_radio == "Generate image from prompt":
            user_input = st.text_input("Enter prompt", value='An astronaut riding a horse on the moon.', placeholder='your prompt') 
        elif add_radio == "Change clothes from reference image":
            user_input = st.file_uploader("Choose a model image...", type=["jpg", "png", "jpeg"])
            user_input_garment = st.file_uploader("Choose a garment image...", type=["jpg", "png", "jpeg"])                
        elif add_radio == "Extract masks from uploaded image":
            user_input = st.file_uploader("Choose images...", type=["jpg", "png", "jpeg"], accept_multiple_files=True)
        else:
            user_input = st.text_area("Enter image URL", value='https://cafefcdn.com/203337114487263232/2023/2/2/photo-1-16753281552041758342824.jpg \nhttps://img.baoninhbinh.org.vn/DATA/ARTICLES/2022/7/26/tran-thanh-toi-va-hari-won-khong-ly-di--29220.jpg', placeholder='https://path_to_image1.jpg \nhttps://path_to_image2.jpg', height=200)
            #Append keywords to array and remove whitespace dư, empty line
            user_input_arr = [line.strip() for line in user_input.split('\n') if line.strip()]

        button = st.button("SUBMIT", type="primary", key="27")
        if button and user_input:                   
            try:
                client = InferenceClient(
                    token=f"{HF_API_TOKEN}"
                )                
                match add_radio:
                    case "Generate image from prompt":
                        #st.stop()
                        #List all Hub API Endpoints - https://huggingface.co/docs/hub/api
                        #response = requests.get('https://huggingface.co/api/models?full=True')
                        #json_data = json.loads(response.text)
                        #st.write(json_data)

                        #Case1; text to image - tool online generate prompt from description - https://huggingface.co/spaces/doevent/Stable-Diffusion-prompt-generator 
                        PIL_image_response = client.text_to_image(
                            prompt=f"{user_input}, best quality, 8k.",
                            negative_prompt="low resolution, ugly, tiling, poorly drawn hands, poorly drawn feet, poorly drawn face, out of frame, extra limbs, disfigured, deformed, body out of frame, blurry, bad anatomy, blurred, watermark, grainy, signature, cut off, draft",
                            num_inference_steps=25,
                            #model="prompthero/openjourney-v4",
                            model="stabilityai/stable-diffusion-2-1",                     
                            #default model="stable-diffusion-v1-4" - https://api-inference.huggingface.co/models/CompVis/stable-diffusion-v1-4                    
                        )
                        st.image(PIL_image_response)
                        #st.code(PIL_image_response)                  
                        # Save the PIL image to a temporary file
                        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmpfile:
                            PIL_image_response.save(tmpfile, format="JPEG")
                            temp_filename_img_path = tmpfile.name             
                        #st.code(temp_filename_img_path, language="text")
                        img_path = temp_filename_img_path
                        img_path_arr.append(img_path)

                    case "Change clothes from reference image":
                        temp_dir_model = tempfile.mkdtemp()
                        path_model = os.path.join(temp_dir_model, user_input.name)
                        with open(path_model, "wb") as f:
                            f.write(user_input.getvalue())
                        st.image(path_model)

                        temp_dir_garment = tempfile.mkdtemp()
                        path_garment = os.path.join(temp_dir_garment, user_input_garment.name)
                        with open(path_garment, "wb") as f:
                            f.write(user_input_garment.getvalue())
                        st.image(path_garment)

                        #Get from this space - https://huggingface.co/spaces/levihsu/OOTDiffusion
                        from gradio_client import Client, file

                        client = Client("https://levihsu-ootdiffusion.hf.space/--replicas/6urx6/")
                        result = client.predict(
                                #"https://images2.thanhnien.vn/528068263637045248/2023/7/6/tom-cruise-the-uk-premiere-of-mission-impossible-dead-reckoning-part-one-2-16886333643941441581231.jpg",	# filepath  in 'Model' Image component
                                #"https://image.uniqlo.com/UQ/ST3/AsianCommon/imagesgoods/454485/sub/goods_454485_sub14.jpg",	# filepath  in 'Garment' Image component
                                path_model,
                                path_garment,
                                "Upper-body",	# Literal['Upper-body', 'Lower-body', 'Dress']  in 'Garment category (important option!!!)' Dropdown component
                                1,	# float (numeric value between 1 and 4) in 'Images' Slider component
                                20,	# float (numeric value between 20 and 40) in 'Steps' Slider component
                                1,	# float (numeric value between 1.0 and 5.0) in 'Guidance scale' Slider component
                                -1,	# float (numeric value between -1 and 2147483647) in 'Seed' Slider component
                                api_name="/process_dc"
                        )
                        #st.write(result)
                        response_image = result[0]["image"]
                        st.image(response_image)


                    case "Extract masks from uploaded image": #trường hợp này extract masks dùng pretrained model YOLOv8 segmentation
                        for uploaded_file in user_input:
                            with st.spinner('Wait for it...'): #Show thanh progress khi xử lý code 
                                #Case1; Detect objects
                                # Display uploaded image
                                image = Image.open(uploaded_file)
                                st.image(image, caption="Uploaded Image", use_column_width=True)

                                # Save uploaded image to temp directory
                                temp_jpg_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
                                temp_jpg_file.close()
                                #temp_jpg_path = temp_jpg_file.name
                                temp_jpg_path = uploaded_file.name  #keep image name               
                                #st.write(temp_jpg_path)
                                with open(temp_jpg_path, "wb") as f:
                                    image_bytes = uploaded_file.getvalue() #open file in temp_jpg_path and write image bytes to it
                                    f.write(image_bytes)
                                #st.image(temp_jpg_path)                

                                # Run inference on an image and Deploy pretrained model Yolov8 remote via Ultralytics HUB and detect objects
                                url = "https://api.ultralytics.com/v1/predict/qVwusF28GI44Jvh5E868"
                                headers = {"x-api-key": HUB_ULTRALYTICS_API_KEY}
                                data = {"size": 640, "confidence": 0.25, "iou": 0.45}
                                image_bytes = uploaded_file.getvalue()
                                response = requests.post(url, headers=headers, data=data, files={"image": image_bytes})
                                if response.status_code == 200:
                                    #st.write(json.dumps(response.json(), indent=2))                
                                    # Parse JSON response
                                    json_data = response.json()
                                    #st.write(json_data)
                                    #st.write(json_data["data"])

                                    # Draw bounding boxes
                                    draw = ImageDraw.Draw(image)
                                    
                                    # Dictionary to count instances of each class
                                    class_count = defaultdict(int)
                                    # Dictionary to map class names to outline colors
                                    class_color_map = {
                                        "person": "red",
                                        "handbag": "blue",
                                        "cell phone": "green",
                                        # Add more classes and corresponding colors as needed - https://stackoverflow.com/questions/77477793/class-ids-and-their-relevant-class-names-for-yolov8-model
                                    }

                                    for bbox_data in json_data["data"]:
                                        xcenter = bbox_data["xcenter"] * image.width
                                        ycenter = bbox_data["ycenter"] * image.height
                                        width = bbox_data["width"] * image.width
                                        height = bbox_data["height"] * image.height

                                        # Calculate bounding box coordinates
                                        x1 = xcenter - width / 2
                                        y1 = ycenter - height / 2
                                        x2 = xcenter + width / 2
                                        y2 = ycenter + height / 2

                                        # Draw bounding box 1 color only
                                        #draw.rectangle([x1, y1, x2, y2], outline="red", width=2)
                                        
                                        # Increment class count
                                        class_name = bbox_data["name"]
                                        class_count[class_name] += 1

                                        # Draw bounding box with class-specific outline color
                                        outline_color = class_color_map.get(class_name, "yellow")  # Default to yellow if class not found
                                        draw.rectangle([x1, y1, x2, y2], outline=outline_color, width=2)

                                    # Display image with bounding boxes
                                    st.image(image, caption="Objects detected with Bounding Boxes", use_column_width=True)
                            
                                    # Display class counts
                                    st.write("Detected objects:")
                                    for class_name, count in class_count.items():
                                        st.write(f"{class_name}: {count}")

                                    #Case2; Extract masks from image
                                    # https://docs.ultralytics.com/hub/inference-api/#segmentation
                                    temp_dir_path = tempfile.mkdtemp()
                                    #st.write(temp_dir_path) 

                                    # Load a model - https://docs.ultralytics.com/vi/tasks/segment/#export
                                    # inference-arguments - https://docs.ultralytics.com/modes/predict/#inference-arguments
                                    model = YOLO("models/yolov8x-seg.pt")  # load an official model 
                                    #model = YOLO("path/to/best.pt")  # load a custom model
                                    # Predict with the model and named folder is 'image_predicted_folder' and Save annotated frames to the output directory
                                    #results = model(["https://ultralytics.com/images/bus.jpg","https://wallpapercave.com/wp/wp6715217.jpg"], save=True, project=temp_dir_path) # predict on an image
                                    #results = model(["im1.jpg", "im2.jpg"], save=True, project=temp_dir_path, name='image_predicted_folder', stream=True)  # return a generator of Results objects
                                    results = model(temp_jpg_path, save=True, project=temp_dir_path, name='image_predicted_folder') #default tham số image size width 640px -> imgsz=[480, 640]                    
                                    #st.write(results) # results in JSON format

                                    st.write(f"Total mask of objects = {len(results[0].masks)}")
                                    #st.write(results[0].masks) #get all bbox points of masks
                                    #st.write(results[0].boxes) #get all bbox points
                                    #st.write(results[0].save_dir) #get directory where save images

                                    _ = """
                                    st.write('Extract second mask in image')
                                    #Extract mask thứ 2 masks[1] trong ảnh
                                    mask = results[0].masks[1].data[0].numpy()
                                    st.image(mask)

                                    #Draw polygon around mask of object
                                    polygon = results[0].masks[1].xy[0]
                                    #st.write(polygon)                    
                                    img = Image.open(temp_jpg_path)
                                    draw = ImageDraw.Draw(img)
                                    draw.polygon(polygon,outline=(0,255,0), width=3)
                                    st.image(img)
                                    """

                                    with st.expander("Click here to view data"):
                                        i = 1              
                                        for mask in results[0].masks:
                                            st.write(f"------------ mask{i} ------------")
                                            mymask = mask.data[0].numpy()
                                            st.image(mymask)

                                            #Draw polygon around mask of object 
                                            polygon = mask.xy[0]
                                            #st.write(polygon)                    
                                            img = Image.open(temp_jpg_path)
                                            draw = ImageDraw.Draw(img)
                                            draw.polygon(polygon, outline=(0,255,0), width=3)
                                            st.image(img)
                                            i += 1

                                    #Case3; Change clothes

                    case _: #trường hợp còn lại extract masks dùng Huggingface Inference API
                        # Download the image                   
                        for user_input in user_input_arr:
                            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'}
                            response = requests.get(user_input.strip(), headers=headers)
                            if response.status_code == 200:
                                #st.write(user_input)
                                
                                # Save the downloaded image to a temporary file
                                with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmpfile:
                                    tmpfile.write(response.content)
                                    temp_filename_img_path = tmpfile.name

                                # Load the image using PIL for any further processing if needed
                                PIL_image_response = Image.open(temp_filename_img_path)
                                #st.image(PIL_image_response)
                                #st.code(PIL_image_response)                    
                                # Save the PIL image to a temporary file again if further processing is needed (optional)
                                with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmpfile:
                                    PIL_image_response.save(tmpfile, format="JPEG")
                                    temp_filename_img_path = tmpfile.name 
                                img_path = temp_filename_img_path
                                PIL_image_response = Image.open(img_path)
                                st.image(PIL_image_response)

                                #Case2; Image Classification
                                st.write("### IMAGE CLASSIFICATION")
                                image_classification_response = client.image_classification(
                                    image=img_path,
                                    model="microsoft/resnet-50", #default model
                                )
                                with st.expander("Click here to view data"):
                                    st.write(image_classification_response) #response json chuẩn

                                time.sleep(5)

                                #Case3; Image Segmentation
                                st.write("### MASKS IN IMAGE")
                                image_segmentation_response = client.image_segmentation(
                                    image=img_path,
                                    model="facebook/detr-resnet-50-panoptic", #default model
                                )
                                #st.write(image_segmentation_response)
                                #st.write(image_segmentation_response[0]["mask"])
                                with st.expander("Click here to view data"):
                                    for mask_image_segmentation in image_segmentation_response:
                                        st.write(mask_image_segmentation["mask"])                                 

                                time.sleep(5)

                                #Case4; paraphrase english only
                                st.write("### PARAPHRASE")
                                text = "I saw a puppy a cat and a raccoon during my bike ride in the park"
                                text_generation_response = client.text_generation(
                                    prompt=text,
                                    model="tuner007/pegasus_paraphrase", #default model
                                )
                                st.write(text)
                                st.write(text_generation_response)

                                #Case5; paraphrase vietnamese only
                                API_URL = "https://api-inference.huggingface.co/models/keepitreal/vietnamese-sbert"
                                headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
                                def query(payload):
                                    response = requests.post(API_URL, headers=headers, json=payload)
                                    return response.json()                       
                                output = query({
                                    "inputs": {
                                        "source_sentence": "That is a happy person",
                                        "sentences": [
                                            "That is a happy dog",
                                            "That is a very happy person",
                                            "Today is a sunny day"
                                        ]
                                    },
                                    "options": {
                                        "wait_for_model": True,
                                    },                        
                                })                  
                                st.write(output)


                                API_URL = "https://api-inference.huggingface.co/models/hetpandya/t5-small-tapaco"
                                headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}

                                def query(payload):
                                    response = requests.post(API_URL, headers=headers, json=payload)
                                    return response.json()
                                    
                                output = query({
                                    "inputs": "chào bạn rất vui làm quen",
                                    "options": {
                                        "wait_for_model": True,
                                    },                          
                                })
                                st.write(output)

                                time.sleep(5)

                                #or paraphrase multiple languagues - https://github.com/RasaHQ/paraphraser

                                #Case6; Change hair in image with HairFastGAN model
                                # https://youtu.be/_Yn4LrTuU64?si=e2QxZy3Jw_6lwO5P ; Xây dựng web đổi kiểu tóc với HairFastGAN, Streamlit và Colab - Mì AI
                                # https://github.com/AIRI-Institute/HairFastGAN/
                                # HD code here - https://blog.paperspace.com/face-verification-with-keras/ 
                                # keras-vggface - https://github.com/rcmalli/keras-vggface
                                # https://huggingface.co/inference-endpoints/dedicated
                                # Download model AI here - https://modelzoo.co/


                                #Case6; Dùng ROBOFLOW.com API
                                from inference_sdk import InferenceHTTPClient

                                #TEST predict API this pretrained model - https://universe.roboflow.com/myname-pfkdq/test-gp37s/model/3
                                CLIENT = InferenceHTTPClient(
                                    api_url="https://outline.roboflow.com",
                                    api_key=ROBOFLOW_API_KEY
                                )
                                result = CLIENT.infer(temp_filename_img_path, model_id="test-gp37s/3")
                                st.write(result)


                            else:
                                st.write(f"{user_input} - Error: {response.status_code}")

            except HfHubHTTPError as e:
                #hf_raise_for_status(response)
                st.write(f"{str(e)} - {str(e.request_id)} - {str(e.server_message)}")

    st.divider()

    #B9:-- TEXT TO SPEECH gTTT --
    with st.container(border=True): 
        st.write(
        """ 
            ## VIDEO - TEXT TO SPEECH & VICE VERSA
            + Convert text to speech
            + Extract mp3 audio from URL of youtube video, then follow steps below
                + B1: Convert mp3 audio to wav audio
                + B2: Convert wav audio to text and get transcription .srt file
                + B3: Translate .srt file to target languague
                + B4: Add .srt file again to get new video with translated transcription
        """
        )

        add_radio = st.radio(
            "Video type",
            ["Voice Cloning (English only)", "Extract audio from URL of YouTube video", "Extract audio from uploaded video"],
            index=0,
        )
        #st.write("You selected:", add_radio)

        user_input_arr = []

        if add_radio == "Voice Cloning (English only)":
            default_value = 'The average domestic airfare during the peak summer season between June and August has decreased with carriers rolling out discounts on night flights on popular routes.'
            user_input = st.text_area("Enter your text", value=default_value, height=200)
            #Append keywords to array and remove whitespace dư, empty line
            #user_input_arr = []
            #user_input_arr = [line.strip() for line in user_input.split('\n') if line.strip()]
            audio = st.file_uploader("Upload Reference Speaker (mp3 file)", type=["mp3"])
            if audio is not None:
                temp_reference_mp3_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
                temp_reference_mp3_file.close()
                temp_reference_mp3_path = temp_reference_mp3_file.name
                #st.write(temp_reference_mp3_path)

                temp_reference_wav_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
                temp_reference_wav_file.close()
                temp_reference_wav_path = temp_reference_wav_file.name
                #st.write(temp_reference_wav_path)

                # save as mp3 file
                with open(temp_reference_mp3_path, 'wb') as f:
                    audio_bytes_data = audio.getvalue()
                    f.write(audio_bytes_data) #write all audio_bytes_data to file mp3                        
                st.audio(temp_reference_mp3_path)

                # Convert mp3 to wav file                                                          
                audio_wav = AudioSegment.from_mp3(temp_reference_mp3_path)
                audio_wav.export(temp_reference_wav_path, format="wav")
                #st.audio(temp_reference_wav_path, format="audio/wav")              

        elif add_radio == "Extract audio from URL of YouTube video":
            user_input = st.text_area("Enter URL of YouTube video", value='https://www.youtube.com/watch?v=cNch6T4H8Hk \nhttps://www.youtube.com/watch?v=v5phuCoTCOM', placeholder='https://path_to_youtubevideo1.jpg \nhttps://path_to_youtubevideo2.jpg', height=200)
            #Append keywords to array and remove whitespace dư, empty line 
            user_input_arr = [line.strip() for line in user_input.split('\n') if line.strip()]
        else:
            user_input = st.file_uploader("Upload video mp4", type=["mp4"])

        button = st.button("SUBMIT", type="primary", key="28")
        if button and user_input:
            match add_radio:
                case "Voice Cloning (English only)":
                    #B1; Optional - Convert text to speech                        
                    #temp_wav_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
                    #temp_wav_file.close()
                    #temp_wav_path = temp_wav_file.name
                    #st.write(temp_wav_path)

                    # Detect the language of the user input
                    #language = 'en'                    
                    #language = detect(user_input) #auto detect languague code như; en, de, vi,...
                    #st.write(language) 

                    #tts = gTTS(text=user_input, lang=language, slow=False)
                    # Saving the converted audio in a wav file named sample
                    #tts.save(temp_wav_path) 
                    #st.write('Convert prompt to WAV audio')
                    #st.audio(temp_wav_path) # Display the audio in Streamlit 


                    #B2; Clone voice via Gradio API from Huggingface repo
                    with st.spinner('Wait for it...'):
                        try:                        
                            #Case1; Clone voice using coqui/XTTS-v2
                            from gradio_client import Client, file

                            #client = Client("abidlabs/my-private-space", hf_token="...") #Dùng cho my private space
                            client = Client("tonyassi/voice-clone")
                            result = client.predict(
                                    text=user_input,
                                    #audio=file('https://github.com/gradio-app/gradio/raw/main/test/test_files/audio_sample.wav'),
                                    audio=file(temp_reference_wav_path),
                                    api_name="/predict"
                            )
                            st.write('Voice cloned with XTTS-v2')
                            st.audio(result)
                        
                            #Case2; Clone voice using OpenVoice Version2 - https://huggingface.co/spaces/myshell-ai/OpenVoiceV2
                            client = Client("https://myshell-ai-openvoicev2.hf.space/--replicas/nx4jp/")
                            result = client.predict(
                                    #"Hello, nice to meet you!",	# str  in 'Text Prompt' Textbox component
                                    user_input,
                                    "en_default",	# str (Option from: ["en_default", "en_us", "en_br", "en_au", "en_in", "es_default", "fr_default", "jp_default", "zh_default", "kr_default"]) in 'Style' Dropdown component
                                    #"https://github.com/gradio-app/gradio/raw/main/test/test_files/audio_sample.wav",	# str (filepath on your computer (or URL) of file) in 'Reference Audio' Audio component
                                    temp_reference_mp3_path,
                                    True,	# bool  in 'Agree' Checkbox component
                                    fn_index=1
                            )
                            st.write('Voice cloned with OpenVoice - only supported languagues "en_us", "en_br", "en_au", "en_in", "es_default", "fr_default", "jp_default", "zh_default", "kr_default"')
                            #st.write(result)
                            Synthesised_audio = result[1]
                            #st.write(Synthesised_audio)
                            #Default volume nhỏ
                            #st.audio(Synthesised_audio)

                            #Dùng cái này boost tăng volume
                            audio = AudioSegment.from_file(Synthesised_audio)
                            louder_Synthesised_audio = audio + 6  
                            #save louder audio 
                            temp_audio_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
                            temp_audio_file.close()
                            temp_audio_path = temp_audio_file.name                            
                            #st.write(temp_audio_path)                            
                            louder_Synthesised_audio.export(temp_audio_path, format='wav')                   
                            st.audio(temp_audio_path)
                            
                        except Exception as e:
                            exc_type, exc_obj, exc_tb = sys.exc_info()
                            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                            #st.write(exc_type, fname, exc_tb.tb_lineno)
                            st.write(f"An error occurred: {e} - Error at line: {exc_tb.tb_lineno}")                                             

                case "Extract audio from URL of YouTube video":
                    for user_input in user_input_arr:
                        st.write(user_input)                        
                        try:
                            # Step 1: Create video and audio temporary file
                            temp_video_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                            temp_video_file.close()
                            temp_video_path = temp_video_file.name                            
                            #st.write(temp_video_path)

                            temp_audio_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
                            temp_audio_file.close()
                            temp_audio_path = temp_audio_file.name                            
                            #st.write(temp_audio_path)

                            temp_wav_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
                            temp_wav_file.close()
                            temp_wav_path = temp_wav_file.name
                            #st.write(temp_wav_path)

                            temp_mp3_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
                            temp_mp3_file.close()
                            temp_mp3_path = temp_mp3_file.name                            
                            #st.write(temp_mp3_path)                            

                            temp_srt_file = tempfile.NamedTemporaryFile(delete=False, suffix=".srt")
                            temp_srt_file.close()
                            temp_srt_path = temp_srt_file.name
                            #st.write(temp_srt_path)

                            yt = YouTube(user_input)
                            #st.write(f"{yt.title} \n\nThumbnail URL:{yt.thumbnail_url}")
                            #Optional: Download video mp4 from youtube and output video to temp directory
                            yt.streams.first().download(filename=temp_video_path)
                            st.video(temp_video_path)

                            # Step 2: Download default audio is wav from youtube and output audio to temp directory
                            yt.streams.filter(only_audio=True).first().download(filename=temp_audio_path)
                            #st.write("Origianal PCM WAV audio")
                            #st.audio(temp_audio_path)

                            # Step 3: Convert PCM WAV audio into stardard WAV audio
                            audio = AudioSegment.from_file(temp_audio_path)
                            #st.write(f"{len(audio)} - {audio.sample_width} - {audio.frame_rate} - {audio.frame_width}")
                            audio.export(temp_wav_path, format="wav")
                            st.write("WAV audio")
                            st.audio(temp_wav_path, loop=True)

                            # Optional: Convert stardard WAV audio into stardard MP3 audio
                            audio_mp3 = AudioSegment.from_wav(temp_wav_path)
                            #st.write(f"{len(audio)} - {audio.sample_width} - {audio.frame_rate} - {audio.frame_width}")
                            audio_mp3.export(temp_mp3_path, format="mp3")
                            st.write("MP3 audio")
                            st.audio(temp_mp3_path, format="audio/mpeg", loop=True)

                            # Step 4: Convert audio to text using SpeechRecognition
                            with st.spinner('Wait for it...'):
                                transcribe = ""
                                recognizer = sr.Recognizer()
                                with sr.AudioFile(temp_wav_path) as source:
                                    audio_data = recognizer.record(source)
                                    text = recognizer.recognize_google(audio_data)
                                    transcribe += text
                            st.write(transcribe)


                            #Convert transcript to substitle.srt file of substile
                            video_id=extract.video_id(user_input)
                            #st.write(video_id)
                            #video_id = 'cNch6T4H8Hk'
                            transcript = YouTubeTranscriptApi.get_transcript(video_id)
                            #st.write(transcript)                        

                            # Create an instance of SRTFormatter & Format the transcript in SRT
                            srt_formatter = SRTFormatter()
                            srt_formatted = srt_formatter.format_transcript(transcript)
                            st.write(f"#### .srt file")
                            st.write(srt_formatted)

                            # Export srt file to download
                            with open(temp_srt_path, 'w', encoding='utf-8') as file:
                                file.write(srt_formatted)
                                btn = st.download_button(
                                        label=f'Download .srt file',
                                        data=srt_formatted,
                                        file_name=temp_srt_path,
                                        mime="text/srt" #default mime="text/plain"
                                    )


                            #Auto translate transcript to target languague
                            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                            #st.write(transcript_list)
                            for transcript in transcript_list:
                                transcript.language_code
                                transcript.is_translatable
                                #st.write(
                                    #transcript.video_id,
                                    #transcript.language,
                                    #transcript.language_code,
                                    # whether it has been manually created or generated by YouTube
                                    #transcript.is_generated,
                                    # whether this transcript can be translated or not
                                    #transcript.is_translatable,
                                    # a list of languages the transcript can be translated to
                                    #transcript.translation_languages,
                                #)
                            
                            if transcript.is_translatable:
                                transcript = transcript_list.find_transcript([transcript.language_code])
                                #transcript = transcript_list.find_transcript(['en'])
                                translated_transcript = transcript.translate('vi') #translate to vietnameses
                                #st.write(translated_transcript.fetch())

                                srt_formatted = srt_formatter.format_transcript(translated_transcript.fetch())
                                st.write(f"#### .srt file translated to vn")
                                st.write(srt_formatted)

                                # Export srt file to download
                                with open(temp_srt_path, 'w', encoding='utf-8') as file:
                                    file.write(srt_formatted)
                                    btn = st.download_button(
                                            label=f'Download .srt file translated to vn',
                                            data=srt_formatted,
                                            file_name=temp_srt_path,
                                            mime="text/srt" #default mime="text/plain"
                                        )
                                #Upload .srt file to create substitles in video
                                st.video(temp_video_path, subtitles=temp_srt_path)                                 

                            else:
                                st.write('Unable to translate transcription')

                        except Exception as e:
                            exc_type, exc_obj, exc_tb = sys.exc_info()
                            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                            #st.write(exc_type, fname, exc_tb.tb_lineno)
                            st.write(f"An error occurred: {e} - Error at line: {exc_tb.tb_lineno}")
                            #Nếu bị error - 'NoneType' object has no attribute 'span' là do youtube đang update gì đó , đợi 24h nó update là xong or fix theo đây - https://github.com/pytube/pytube/issues/1498#issuecomment-1475993725

                        finally:
                            # Cleanup temporary files
                            if temp_video_path and os.path.exists(temp_video_path):
                                os.remove(temp_video_path)
                            if temp_audio_path and os.path.exists(temp_audio_path):
                                os.remove(temp_audio_path)
                            if temp_wav_path and os.path.exists(temp_wav_path):
                                os.remove(temp_wav_path)

                case _: #trường hợp còn lại
                    if user_input is not None:
                        #Clone Voice with OpenVoice - https://github.com/myshell-ai/OpenVoice/blob/main/docs/USAGE.md
                        #Clone Voice with OpenVoice colab - https://github.com/camenduru/OpenVoice-colab
                        #Demo HF - https://huggingface.co/myshell-ai/OpenVoice                        
                        # https://www.youtube.com/watch?v=1ec-jOlxt_E ; Unveiling the New AI Voice Cloner | OpenVoice
                        #st.write(user_input)
                        st.video(user_input)

                        #Python library - https://pypi.org/project/openvoice-cli/
                        from openvoice_cli import tune_batch

                        # Set parameters for batch processing
                        input_dir = 'path_to_input_directory'
                        ref_file = 'path_to_reference.wav'
                        output_dir = 'path_to_output_directory'
                        device = 'cuda'  # or 'cpu' for CPU processing
                        output_format = '.wav'  # could be .mp3 or other formats

                        # Convert the tone color of multiple audio files in a directory
                        output = tune_batch(input_dir=input_dir, ref_file=ref_file, output_dir=output_dir, device=device, output_format=output_format)                        

    st.divider()

    #B9:-- VISUAL ANALYSIS FOR CSV FILE --
    with st.container(border=True): 
        st.write(
        """ 
            ## VISUAL ANALYSIS FOR CSV FILE 
            Upload **'.csv'** files to turn datas into an interactive UI for visual analysis.
        """
        )

        with st.form(key='csv_upload_form'):
            # Add a file uploader to the form for CSV files
            uploaded_file = st.file_uploader("Choose a CSV file", type=['csv'])
            # Add a submit button to the form
            submit_button = st.form_submit_button("Submit")
        # Process the form submission
        if submit_button:
            if uploaded_file is not None:
                # Check if the uploaded file is a CSV
                if uploaded_file.type == 'text/csv':
                    # Use pandas to read the CSV file
                    df = pd.read_csv(uploaded_file)
                    st.write("CSV file uploaded successfully!")
                    st.write(df)  # Display the uploaded CSV data
                    #pyg_html = pyg.walk(df, return_html=True)
                    pyg_html = pyg.walk(df, env='Streamlit')
                    st.write(pyg_html, unsafe_allow_html=True)
                    from pygwalker.api.streamlit import StreamlitRenderer                    
                    pyg_app = StreamlitRenderer(df)
                    pyg_app.explorer() 
                                       
                else:
                    st.write("Please upload a CSV file.")

if __name__ == "__main__":
    run()