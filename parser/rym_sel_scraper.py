import csv
import logging
import re
import time
from typing import Any

import numpy as np
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

from bs4 import BeautifulSoup
import cld3

CLEAN = re.compile("<.*?>")  # regex for removing html tags

logging.basicConfig(level=logging.INFO, filename='log.log', filemode='w',
                    format="%(asctime)s - %(levelname)s - %(message)s")


def remove_html_tags(text: str) -> str:
    """Remove html tags from a string"""
    return re.sub(CLEAN, ' ', text)


def reviews_filter(tag: BeautifulSoup) -> bool:
    """ Function that filters reviews return True if filter found reviews false otherwise"""
    return True if tag.parent.name == 'p' and tag.has_attr('class') and tag.name == 'span' else False


def rating_filter(tag: BeautifulSoup) -> bool:
    """ Function that filters rating return True if filter found rating false otherwise"""
    return True if tag.parent.name == 'td' and tag.name == 'p' and not tag.parent.has_attr('colspan') else False


def get_page_data(soup: BeautifulSoup) -> list[tuple[Any, ...]]:
    if isinstance(soup, BeautifulSoup):
        reviews_list = [remove_html_tags(str(review)) for review in soup.find_all(reviews_filter)]

        album_names = []
        for el in soup.find_all('a', 'album'):
            album_names.append(el.get_text())

        artist_names = []
        for el in soup.find_all('a', 'artist'):
            artist_names.append(el.get_text())

        album_rating = []
        for element in soup.find_all(rating_filter):
            try:
                album_rating.append(element.img['title'])
            except TypeError:
                album_rating.append('no_rating')

        dates_list = [remove_html_tags(str(date)) for date in soup.find_all('div', attrs={'class': 'small'})]

        users = []
        for el in soup.find_all('a', attrs={'class': 'user'}):
            users.append(el.get_text())

        reviews_lang = []
        for review in reviews_list:
            lang = cld3.get_language(review).language
            reviews_lang.append(lang)

        return list(zip(artist_names, album_names, reviews_list, dates_list, album_rating, users, reviews_lang))


def write_data(page_soup: BeautifulSoup, file: str = 'rym_data.csv') -> None:
    """ Function that takes in file and soup object, parses data and writes it to the file"""
    with open(file, 'a', encoding="utf-8") as f:
        write = csv.writer(f)
        if get_page_data(page_soup):
            for elem in get_page_data(page_soup):
                write.writerow(elem)
        else:
            pass


def scrape_data(max_pages):
    pages_scraped = 0
    url = 'https://rateyourmusic.com/latest?offset=2010'
    driver = webdriver.Firefox()
    driver.get(url)
    delay = 5  # seconds
    
    try:

        username = driver.find_element(By.ID, value='username')
        password = driver.find_element(By.ID, value='password')
        login = driver.find_element(By.ID, value='login_submit')
        username.send_keys('*****') #your credentials here
        password.send_keys('*****') #your credentials here
        login.click()
        driver.implicitly_wait(10)
        all_reviews = driver.find_element(By.XPATH, "//a[contains(text(), '[+all reviews]')]")
        driver.execute_script("arguments[0].scrollIntoView();", all_reviews)
        driver.execute_script("arguments[0].click();", all_reviews)
    except NoSuchElementException:
        pass

    url = 'https://rateyourmusic.com/latest?offset=15'
    driver.get(url)
    delay = 5  # seconds
    
    while pages_scraped < max_pages:
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        write_data(soup)

        try:
            next_page = WebDriverWait(driver, delay).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Next 15')]")))
            next_page.click()
        except NoSuchElementException as e:
            logging.error(e)
        except TimeoutException as e:
            logging.error('Timed out with exception  %s' % e, exc_info=True)

        time.sleep(np.random.random_sample() + np.random.randint(5, 10))
        pages_scraped += 1
        logging.info('Finished scraping page# %s' % pages_scraped)

    logging.info('Total scraped pages: %s' % pages_scraped)


if __name__ == "__main__":
    scrape_data(10)
