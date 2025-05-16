from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
import time
import csv

driver = webdriver.Chrome(service=Service('C:/Users/olariucr/Desktop/programming/RBS Tech Training - Python Course/Movie Picker Bot/Python-Project-Cristian/chromedriver.exe'))