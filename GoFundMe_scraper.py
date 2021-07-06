import time, requests
from bs4 import BeautifulSoup
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementClickInterceptedException

__author__ =  'Shengjun Wang'
__version__=  '0.1.2'
__maintainer__ = "Shengjun Wang"
__email__ = "sw3231@columbia.edu"

def ShowMore_clicker(driver, t_seconds = 2**2):
    start_clicking_time = time.time()
    i=0
    while True:
        i = i + 1
        try:
            start_loading_time = time.time()
            button = driver.find_element_by_link_text('Show More')
            #button.click()
            driver.execute_script("arguments[0].click();", button)
            WebDriverWait(driver, t_seconds, 0.001).until(EC.element_to_be_clickable((By.LINK_TEXT, 'Show More')))
            loading_time = time.time() - start_loading_time
            print(i,", loading succeeded", ", using %s seconds" % loading_time)
        except (NoSuchElementException, TimeoutException, ElementClickInterceptedException) as e:
            # NoSuchElementException - happens when the page does not have the button at all
            # TimeoutException - happens when the button is clicked multiple times, and do not show up anymore
            # ElementClickInterceptedException - is this a control from page developer side?
            page_source_lxml = BeautifulSoup(driver.page_source,'lxml')
            num_supply = len(set([x.get('href') for x in page_source_lxml.find_all('a') if "https://www.gofundme.com/" in x.get('href')]))
            try:
                num_demand = int(page_source_lxml.find('div', class_="heading-3").text.split(' results')[0])
            except:
                num_demand = 1000
            if num_demand == num_supply:
                loading_time = time.time() - start_loading_time
                print(i,", no more buttons", ", using %s seconds" % loading_time)
                print(repr(e))
                break
            else:
                #time.sleep(0)
                loading_time = time.time() - start_loading_time
                print(i,", loading failed", ", using %s seconds" % loading_time)
                print(repr(e))
                break
    time_in_total = time.time() - start_clicking_time
    print("--- %s seconds in total ---" % time_in_total)
    return driver


class MyWebScraper(object):
    def __init__(self, url):

        self.search_link = url
        self.search_term = self.topic_generator()
        self.search_tuple = '_'.join(self.search_term)

        prefs={"profile.managed_default_content_settings.images": 2}
        self.chromeOptions = webdriver.ChromeOptions()
        self.chromeOptions.add_experimental_option("prefs", prefs)

        driver = webdriver.Chrome(ChromeDriverManager().install(), options=self.chromeOptions)
        driver.get(self.search_link)
        print(self.search_term)

        init_page_source = BeautifulSoup(driver.page_source,'lxml')
        num_benchmark = self.num_obs(init_page_source)
        # setting below is based on empirical evidence,
        # which is highly dependent on your working environment
        if int(num_benchmark) <= 400:
            t_seconds = 2**2
        elif (int(num_benchmark) > 400) and (int(num_benchmark) <= 800):
            t_seconds = 2**3
        else:
            t_seconds = 2**5

        driver = ShowMore_clicker(driver, t_seconds)
        self.page_source = BeautifulSoup(driver.page_source,'lxml')
        driver.close()

        self.num_demand = self.num_obs(self.page_source)
        self.fundraisers_links = self.fundraiser_hunting()
        self.num_supply = len(self.fundraisers_links)

    def topic_generator(self):
        sub_url = self.search_link.split("/")[-1]
        if "-" in sub_url:
            return sub_url.split("-")[0]
        elif "=" in sub_url:
            return sub_url.split("=")[1].split("%20")
        else:
            return "unknown"

    def num_obs(self, x):
        try:
            num_obs_should_have = x.find('div', class_="heading-3").text.split(' results')[0]
            return int(num_obs_should_have)
        except:
            return 1000 # or "did not show up"; 1k is the maximum by website design

    def fundraiser_hunting(self):
        fundraisers_links_list = [x.get('href') for x in self.page_source.find_all('a')
                                  if "https://www.gofundme.com/" in x.get('href')]
        fundraisers_links_list = list(set(fundraisers_links_list))
        return fundraisers_links_list


def profile_reader(profile):
    try:
        soup = BeautifulSoup(requests.get(profile).text, "lxml")
        ##### title #####
        try:
            title = soup.find('h1', class_="a-campaign-title").text
        except(AttributeError, IndexError) as e:
            title = None
        ##### created_date #####
        try:
            created_date = soup.find('span', class_="m-campaign-byline-created a-created-date").text
            created_date = created_date.split("Created ",1)[1]
        except(AttributeError, IndexError) as e:
            created_date = None
        ##### tag #####
        try:
            tag = soup.find_all('a',
                  class_="m-campaign-byline-type divider-prefix meta-divider flex-container align-middle color-dark-gray hrt-tertiary-button hrt-base-button hrt-link hrt-link--unstyled")[0].text
        except(AttributeError, IndexError) as e:
            tag = None
        ##### location #####
        try:
            location = soup.find_all('div', class_="text-small")[1].text
        except(AttributeError, IndexError) as e:
            location = None
        ##### text #####
        try:
            text = soup.find('div', class_="o-campaign-story mt3x").text
            text = text.replace('\n','').replace('\xa0','')
        except(AttributeError, IndexError) as e:
            text = None
        ##### status #####
        try:
            status = soup.find('h2', class_="m-progress-meter-heading").text
        except(AttributeError, IndexError) as e:
            status = None
        ##### current_amount #####
        try:
            current_amount = soup.find('script').string.split('"current_amount":',1)[1].split(',',1)[0]
        except(AttributeError, IndexError) as e:
            current_amount = None
        ##### goal_amount #####
        try:
            goal_amount = soup.find('script').string.split('"goal_amount":',1)[1].split(',',1)[0]
        except(AttributeError, IndexError) as e:
            goal_amount = None
    except:
        title, created_date, tag, location, text, status, current_amount, goal_amount = None, None, None, None, None, None, None, None

    return title, created_date, tag, location, text, status, current_amount, goal_amount
