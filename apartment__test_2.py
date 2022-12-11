from selenium import common
from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement as Element
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait as Wait
from selenium.webdriver.support import expected_conditions as EC
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]
credentials = ServiceAccountCredentials.from_json_keyfile_name("apartments-370403-3f8382015e32.json", scopes)
file = gspread.authorize(credentials)
sheet = file.open('Stupid')
sheet = sheet.sheet1 



# apartments.com url is specific for each filter applied so url determines what kind of apartment 
# listings the program looks for
url = 'https://www.apartments.com/apartments/austin-tx/min-3-bedrooms-under-2500/' 
browser = webdriver.Chrome()
browser.set_window_size(1200, 800)
browser.get(url)
# depending on how slow or fast WIFI/user's computer is, the wait time can be shortened or lengthened
# 1 second was chosen arbitrarily
# will perform testing to determine shortest possible wait time and if the wait is necessary
wait = Wait(browser, 0.15)


def format_num(text):  
    rev_text = text.replace('$', '').replace('\n', '').replace(',', '')
    return rev_text

def format_address(address):
    neighborhood = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'span.neighborhoodAddress > a'))).text
    address = address.replace('\n', '').replace(neighborhood, '')
    return address

# func. below finds the total number of apt. complexes that have at least one listing that meets the criteria
def find_total_count():   
    count_text = browser.find_element(By.ID, 'mapResultBox').text
    count = format_num(count_text)
    cut = count.find(' ')
    final_count = count[:cut]
    return int(final_count)

# func. below finds the number of unique apt. types for each complex.
# since each matching apt. type is a child of the same parent
# the func. looks for all of the children until it times out and then returns the number of matches
def find_apt_count():   
    try:
        i = 1
        while True:            
            css_selector_units = f'div.tab-section.active > div:nth-child({i}) > div.priceGridModelWrapper.js-unitContainer.mortar-wrapper > div.availability'
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, css_selector_units)))
            i += 1
    except common.exceptions.TimeoutException:
        return i-1 

def find_reviews():
    try:
        review = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'span.reviewRating'))).text
        if review != '':
            return review
        else:
            review = 'Na'
            return review    
    except common.exceptions.TimeoutException:
        review = 'Na'
        return review

def find_url():
    try:
        url = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#officeHoursSection > div > div > div:nth-child(1) > div.mortar-wrapper > a')))
        url = url.get_dom_attribute('href')
        return url
    except common.exceptions.TimeoutException:
        url = 'Na'
        return url


# def scroll_down(apt_num):
#     if apt_num >= 12:
#         browser.execute_script(f'window.scrollTo(0, {3000 + apt_num*400})')

# func. below finds all important criteria for the specific apt. type

def find_apt_criteria(apt_num):
    complex_name = browser.find_element(By.ID, 'propertyName').text
    address = browser.find_element(By.CLASS_NAME, 'propertyAddressContainer').text
    address = format_address(address)

    review = find_reviews()
    url = find_url()

    css_selector_price = f'div:nth-child({apt_num}) > div.unitGridContainer.mortar-wrapper > div > ul > li:nth-child(1) > div.grid-container.js-unitExtension > div.pricingColumn.column > span:nth-child(2)'
    css_selector_sq_ft = f'div:nth-child({apt_num}) > div.unitGridContainer.mortar-wrapper > div > ul > li:nth-child(1) > div.grid-container.js-unitExtension > div.sqftColumn.column > span:nth-child(2)'
    css_selector_floor_plan = f'div:nth-child({apt_num}) > div.priceGridModelWrapper.js-unitContainer.mortar-wrapper > div.row > div.column1 > div > h3 > span.modelName'
    sq_ft = browser.find_element(By.CSS_SELECTOR, css_selector_sq_ft).text
    sq_ft = format_num(sq_ft)
    price = browser.find_element(By.CSS_SELECTOR, css_selector_price).text
    price = format_num(price)
    floor_plan = browser.find_element(By.CSS_SELECTOR, css_selector_floor_plan).text

    return (complex_name, address, price, sq_ft, url, floor_plan, review)


# func. below finds important amenities by searching for key words on the webpage
def find_amenity(amenity): 
    try:
        if wait.until(EC.text_to_be_present_in_element((By.CLASS_NAME, 'sectionContainer'), amenity)):
            answer = 'Yes'
            return answer
        else:  
            answer = 'No'
            return answer   
    except common.exceptions.TimeoutException:
        answer = 'No'
        return answer             

# stops creating entries after 6 unique apt. types sinces that's kinda unnecessary
def write_into_sheets(apt_num):
    if apt_num <= 6:
        complex_name, address, price, sq_ft, url, floor_plan, review = find_apt_criteria(apt_num+1)
        washer, gym = find_amenity('Washer'), find_amenity('Fitness Center')
        sheet.append_row([complex_name, floor_plan, address, price, sq_ft, washer,
        '', '', '', '', '', gym, review, url], value_input_option='USER_ENTERED')

def compile_data():
    try:
        sheet.batch_clear(['A2:AA1000'])
        total_count = find_total_count()
        browser.find_element(By.CLASS_NAME, 'property-link').click()    
        for i in range(0, total_count):
            apt_count = find_apt_count()
            for j in range(0, apt_count):
                write_into_sheets(j)
            browser.find_element(By.CSS_SELECTOR, 'a.prevNext.next.profileButton').click()
    # except common.exceptions.NoSuchElementException:
    #     print("The stupid computer couldn't find the damn element")
    # except:
    #     print('The test is done')
    finally: 
        print('uhhh')


compile_data()