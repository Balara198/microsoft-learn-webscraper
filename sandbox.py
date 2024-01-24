from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import requests as rq
from bs4 import BeautifulSoup

import os
import logging
import time

import Catalog

logging.basicConfig(level=logging.INFO)

service = Service()
options = webdriver.ChromeOptions()
driver = webdriver.Chrome(service=service, options=options)
driver.set_window_position(3000, 0)
driver.maximize_window()

ROOT_DIR = os.getcwd()

