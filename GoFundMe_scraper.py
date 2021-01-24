import time, requests
from bs4 import BeautifulSoup
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, TimeoutException

__author__ =  'S. Wang'
__version__=  '20210124'

def ShowMore_clicker(driver, t_seconds = 2**2):
    start_clicking_time = time.time()

    i=0
    while True:
        i = i + 1

        try:
            button = driver.find_element_by_link_text('Show More')
            button.click()
            start_loading_time = time.time()
            try:
                WebDriverWait(driver, t_seconds, 0.001).until(EC.element_to_be_clickable((By.LINK_TEXT, 'Show More')))
                loading_time = time.time() - start_loading_time
                print(i,", loading succeeded", ", using %s seconds" % loading_time)
            except TimeoutException:
                page_source_lxml = BeautifulSoup(driver.page_source,'lxml')
                try:
                    num_demand = int(page_source_lxml.find('div', class_="heading-3").text.split(' results')[0])
                except:
                    num_demand = 1000
                num_supply = len(set([x.get('href') for x in page_source_lxml.find_all('a') if "https://www.gofundme.com/" in x.get('href')]))
                if num_demand == num_supply:
                    loading_time = time.time() - start_loading_time
                    print(i,", no more buttons", ", using %s seconds" % loading_time)
                    break
                else:
                    #time.sleep(0)
                    loading_time = time.time() - start_loading_time
                    print(i,", loading failed", ", using %s seconds" % loading_time)
                    break
        except NoSuchElementException:
            print(i,", no more buttons")
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
        if int(num_benchmark) <= 500:
            t_seconds = 2**2
        elif (int(num_benchmark) > 500) and (int(num_benchmark) <= 800):
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
            title = None #non-exist, fund-raiser not for people
        ##### created_date #####
        try:
            created_date = soup.find('span', class_="m-campaign-byline-created a-created-date").text
            created_date = created_date.split("Created ",1)[1]
        except(AttributeError, IndexError) as e:
            created_date = None
        ##### tag #####
        try:
            tag = soup.find_all('a',
                  class_="m-campaign-byline-type divider-prefix meta-divider flex-container align-middle color-dark-gray a-link--unstyled a-link")[0].text
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
            #text = soup.find('div', class_="o-campaign-story mt-three-halves").text
            text = text.replace('\n','').replace('\xa0','')
        except(AttributeError, IndexError) as e:
            text = None

    except:
        title, created_date, tag, location, text = None, None, None, None, None

    return title, created_date, tag, location, text
