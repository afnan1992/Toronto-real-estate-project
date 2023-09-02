from bs4 import BeautifulSoup
import requests
import re
import csv
import os
import json
import random
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class Scrape:
    def __init__(self,link) -> None:
        self.link = link
        self.overViewDict = {}
        self.userAgentList =  [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_4_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1',
    'Mozilla/4.0 (compatible; MSIE 9.0; Windows NT 6.1)',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36 Edg/87.0.664.75',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 Edge/18.18363',
]
        self.soup = BeautifulSoup()

    def createSession(self):
        headers = requests.utils.default_headers()

        headers.update(
        {
        'User-Agent': self.userAgentList[random.randint(0, len(self.userAgentList)-1)],
        }
        )

        session = requests.Session()
        retry = Retry(connect=3, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)

        self.r =session.get(self.link,headers=headers)

    def checkIfFieldIsNone(self,Field,returnType):
        if Field is not None:
            self.overViewDict[str(Field).lower] = Field.text
        else:
            'NA' if returnType == 'text' else '0'
                


    def getHeaderDetails(self) -> None:
        
        self.soup = BeautifulSoup(self.r.content, 'html.parser')
        
        chunkedList = self.link.split("/")
        self.overViewDict['id'] = chunkedList[-1]
        
        div = self.soup.find('div',attrs={'class':re.compile("^realEstateTitle-\d+")})
         
        innerSoup = BeautifulSoup(str(div), 'html.parser')

        Title= innerSoup.find('h1',attrs={'class':re.compile("^title-\d+")})
        if Title is not None:
            self.overViewDict['title'] = Title.text
        else:
            self.overViewDict['title'] = 'NA'
        
        OuterPriceTag = innerSoup.find('div',attrs={'class':re.compile("^priceWrapper-\d+")})
        if OuterPriceTag is not None:
            Price = OuterPriceTag.find("span")
            if Price is not None:
                self.overViewDict['price'] = Price.text
            else:
                self.overViewDict['price'] = '0'
        
        else:
            self.overViewDict['price'] = '0'
        
        try:
            Location = innerSoup.find('div',attrs={'class':re.compile("^locationContainer-\d+")}).find("span")
            
            self.overViewDict['location'] = Location.text
                 
        except AttributeError as noLocation:
            self.overViewDict['location'] = 'NA'

        
        try:
            DatePosted = innerSoup.find('div',attrs={'class':re.compile("^datePosted-\d+")}).find("time")
        
            self.overViewDict['DatePosted'] = DatePosted.text
        except AttributeError as noDatePosted:
            self.overViewDict['DatePosted'] = 'NA'

        try:
            BedroomandBathroom = innerSoup.find('div',attrs={'class':re.compile("^titleAttributes-\d+")})
            values = BedroomandBathroom.findAll("span")
        
            BuildingType = values[0]
            Bedrooms = values[1]
            Bathrooms =values[2]
        
            self.overViewDict['BuildingType'] = BuildingType.text
            self.overViewDict['Bedrooms'] = Bedrooms.text
            self.overViewDict['Bathrooms'] = Bathrooms.text
            

        except AttributeError as NoAttribute:
            self.overViewDict['BuildingType'] = 'NA'
            self.overViewDict['Bedrooms'] = '0'
            self.overViewDict['Bathrooms'] = '0'

            


    def getOverviewDetails(self) -> None:

        div = self.soup.find('div',attrs={'class':re.compile("^itemAttributeCards-\d+")})
        innerSoup = BeautifulSoup(str(div), 'html.parser')
        
        keys = innerSoup.findAll('li',attrs={'class':re.compile("^attributeGroupContainer-\d+")})

        for key in keys:
            if key.find('ul').findAll('li') is None:
                self.overViewDict[str(key.find('h4').text)] = key.find('ul').text  
            elif key.find('h4').text == 'Utilities Included':
                keyTitle = key.find('h4').text
                listedItems = key.find('ul').findAll('li')
                
                if listedItems is None:
                    self.overViewDict[keyTitle] = "Not Included"
                else:
                    concatedList = []
                    for a in listedItems:
                        concatedList.append(a.find('svg')['aria-label'])
                    self.overViewDict[keyTitle] =concatedList

            else:
                keyTitle = key.find('h4').text
                listedItems = key.find('ul').findAll('li')
                concatedList = []
                for a in listedItems:
                    concatedList.append(a.text)
                self.overViewDict[keyTitle] =concatedList 
            


        keys = innerSoup.findAll('li',attrs={'class':re.compile("^twoLinesAttribute-\d+")})

        for key in keys:
            self.overViewDict[key.find('dt').text] = key.find('dd').text


    def returnOverviewDict(self):
        return self.overViewDict


    def savetoCSV(self):
        with open('toronto.csv', 'a',newline='') as f:  
             w = csv.DictWriter(f, self.overViewDict.keys())
             if os.path.getsize('toronto.csv') == 0:
                 w.writeheader()
             w.writerow(self.overViewDict)
        f.close()

    

        
# s= Scrape('https://www.kijiji.ca/v-apartments-condos/city-of-toronto/3-bedroom-2-level-penthouse-yonge-davisville/1663034997')
# s.getHeaderDetails()
# s.getOverviewDetailsv2()
# print(s.returnOverviewDict())