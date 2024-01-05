from selenium import webdriver 
from selenium.webdriver.common.by import By 
from selenium.webdriver.chrome.service import Service as ChromeService 
from webdriver_manager.chrome import ChromeDriverManager 
import json


'''
Embed user parameters into filters
'''
def filterBuilder():

    filters = []
    regions = ["Stockholm"]
    region_filter = {
        "key": "deal.location.regionName",
        "values": regions,
        "type":"nested"
        }
    filters.append(region_filter)

    gears = ["Automat"]
    gear_filter={
        "key":"car.details.gearbox",
        "values": gears,
        "type":"string"
        }
    filters.append(gear_filter)

    fuels = ["El"]
    fuel_filter = {
        "key":"car.details.mainPropellant.fuel",
        "values": fuels,
        "type":"string"
        }
    filters.append(fuel_filter)

    makes = ["Nissan", "Wolkswagen"]
    make_filter = {
        "key": "car.details.makeModel.make",
        "values" : makes,
        "type" :"nested"
        }
    filters.append(make_filter)

    models = ["ID.3","Leaf","i3","i3s"]
    model_filter = {
        "key":"car.details.makeModel.model",
        "values": models,
        "type":"nested"
        }
    filters.append(model_filter)

    year_start = "2018"
    year_end = ""
    year_filter = {
        "key":"car.details.vehicleModelYear",
        "range":{"start":year_start,"end":year_end},
        "type":"int"
        }
    filters.append(year_filter)

    price_min = "100000"
    price_max = "300000"
    price_filter={
        "key":"deal.price",
        "range":{"start":price_min,"end":price_max},
        "type":"int"
        }
    filters.append(price_filter)

    # filters = [region_filter, gear_filter, fuel_filter, make_filter, model_filter, year_filter, price_filter]
    return filters

'''
Convert filters into HTTP GET request parameters
Format is: filter=<filter in json object>&filter=<another filter in json object> ...
'''
def urlParamBuilder(filters):

    combined_filters = "&".join(["filter=" + json.dumps(i) for i in filters])
    print('[+] URL parameter: ' + combined_filters)

    return combined_filters

'''
URL
''' 
def urlBuilder(filter):

    endpoint = "https://www.blocket.se/motor-lp/sok?"
    final_url = endpoint + filter
    
    return final_url

'''
HTTP GET request
'''
def scraper(url):
    
    options = webdriver.ChromeOptions() 
    options.headless = True 
    with webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options) as driver: 
        driver.get(url) 
    
        print("[+] Page URL:", driver.current_url) 
        print("[+] Page Title:", driver.title)

filters = filterBuilder()
combined_filters = urlParamBuilder(filters)
final_url = urlBuilder(combined_filters)
scraper(final_url)