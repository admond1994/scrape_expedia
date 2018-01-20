import json
import requests
from lxml import html
from collections import OrderedDict
import argparse
import time 

from selenium import webdriver
#%%
'''
Scraping Logic:
    1. Construct the URL of the search results from Expedia
    2. Download HTML of the search result page using Python Requests.
    3. Parse the page using LXML – LXML lets you navigate the HTML Tree Structure using Xpaths. 
    We have predefined the XPaths for the details we need in the code.
    4. Save the data to a JSON file. You can later modify this to write to a database.

'''
#%%
def parse(source,destination,date):
    for i in range(5):
        try:
            # %2C - comma, %3A - colon :, %2F - slash / 
            
            url = "https://www.expedia.com/Flights-Search?trip=oneway&leg1=from:{0},to:{1},departure:{2}TANYT&passengers=adults:1,children:0,seniors:0,infantinlap:Y&options=cabinclass%3Aeconomy&mode=search&origref=www.expedia.com".format(source,destination,date)
           #%%
            # TEST URL FIRST 
            # url = "https://www.expedia.com/Flights-Search?trip=oneway&leg1=from:sin,to:kul,departure:02/20/2018TANYT&passengers=adults:1,children:0,seniors:0,infantinlap:Y&options=cabinclass%3Aeconomy&mode=search&origref=www.expedia.com"

            browser = webdriver.Chrome(executable_path=r'C:\Users\Admond\Downloads\chromedriver_win32\chromedriver.exe')
            browser.get(url)
            # Parse the html, returning a single element/document
            # use page.content rather than page.text because html.fromstring implicitly expects bytes as input
            tree = html.fromstring(browser.page_source)
            # tree now contains the whole HTML file in a nice tree structure
            json_data_xpath = tree.xpath("//script[@id='cachedResultsJson']//text()")
            
            raw_json =json.loads(json_data_xpath[0])
            flight_data = json.loads(raw_json["content"])

            flight_info  = OrderedDict() 
            lists=[]
            #%%
            for i in flight_data['legs'].keys():
                
                total_distance =  flight_data['legs'][i]["formattedDistance"]
                exact_price = flight_data['legs'][i]['price']['totalPriceAsDecimal']

                departure_location_airport = flight_data['legs'][i]['departureLocation']['airportCity']
                departure_location_city = flight_data['legs'][i]['departureLocation']['airportCity']
                departure_location_airport_code = flight_data['legs'][i]['departureLocation']['airportCode']
                
                arrival_location_airport = flight_data['legs'][i]['arrivalLocation']['airportCity']
                arrival_location_airport_code = flight_data['legs'][i]['arrivalLocation']['airportCode']
                arrival_location_city = flight_data['legs'][i]['arrivalLocation']['airportCity']
                airline_name = flight_data['legs'][i]['carrierSummary']['airlineName']
                
                no_of_stops = flight_data['legs'][i]["stops"]
                flight_duration = flight_data['legs'][i]['duration']
                flight_hour = flight_duration['hours']
                flight_minutes = flight_duration['minutes']
                flight_days = flight_duration['numOfDays']

                if no_of_stops==0:
                    stop = "Nonstop"
                else:
                    stop = str(no_of_stops)+' Stop'

                total_flight_duration = "{0} days {1} hours {2} minutes".format(flight_days,flight_hour,flight_minutes)
                departure = departure_location_airport+", "+departure_location_city
                arrival = arrival_location_airport+", "+arrival_location_city
                carrier = flight_data['legs'][i]['timeline'][0]['carrier']
                plane = carrier['plane']
                plane_code = carrier['planeCode']
                formatted_price = "{0:.2f}".format(exact_price)

                if not airline_name:
                    airline_name = carrier['operatedBy']
                
                timings = []
                for timeline in  flight_data['legs'][i]['timeline']:
                    if 'departureAirport' in timeline.keys():
                        departure_airport = timeline['departureAirport']['longName']
                        departure_time = timeline['departureTime']['time']
                        arrival_airport = timeline['arrivalAirport']['longName']
                        arrival_time = timeline['arrivalTime']['time']
                        flight_timing = {
                                            'departure_airport':departure_airport,
                                            'departure_time':departure_time,
                                            'arrival_airport':arrival_airport,
                                            'arrival_time':arrival_time
                        }
                        timings.append(flight_timing)

                flight_info={'stops':stop,
                    'ticket price':formatted_price,
                    'departure':departure,
                    'arrival':arrival,
                    'flight duration':total_flight_duration,
                    'airline':airline_name,
                    'plane':plane,
                    'timings':timings,
                    'plane code':plane_code
                }
                lists.append(flight_info)
            sortedlist = sorted(lists, key=lambda k: k['ticket price'],reverse=False)
            return sortedlist
        
        except ValueError:
            print("Retrying...") 
        return {"error":"failed to process the page",}
    browser.close()
#%%
if __name__=="__main__":
    argparser = argparse.ArgumentParser() # create an object 
    # fill with info about program arguments 
    argparser.add_argument('source',help = 'Source airport code')  # help --> A brief description of what the argument does
    argparser.add_argument('destination',help = 'Destination airport code')
    argparser.add_argument('date',help = 'MM/DD/YYYY')

    # parse arguments
    args = argparser.parse_args() # Convert argument strings to objects and assign them as attributes 
    print('args:{} \n'.format(args))
    source = args.source
    destination = args.destination
    date = args.date
    # check the input and its type
    print('source:{} , source type:{}\ndestination:{} , destination type:{}\ndata:{} , data type:{}\n'.format(source,type(source),destination,type(destination),date,type(date)))
    
    print("Fetching flight details...\n")
    
    scraped_data = parse(source,destination,date)
    print("Writing data to output file\n")
    with open('%s-%s-flight-results.json'%(source,destination),'w') as fp:
         json.dump(scraped_data,fp,indent = 4)