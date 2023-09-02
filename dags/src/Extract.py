from bs4 import BeautifulSoup
import requests
import pathlib
import re
from src.Transform import Transform
#from src.Load import Load
import time
import logging
import json
import random
import datetime
import os
from src.Upload import upload_to_s3
from src.Scrape import Scrape
import configparser

parser = configparser.ConfigParser()
script_path = pathlib.Path(__file__).parent.resolve()
parser.read(f"{script_path}/configuration.conf")

sub_url = parser.get("url_config", "sub_url")

class Extract:

    def __init__(self,landingURL) -> None:
        logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
        self.landingURL = landingURL
        self.jsonList = []

    def getListings(self,NoOfPages,run_date) -> None:
        NoOfLinks = 1

        for i in range(1,NoOfPages):
            
            chunkedUrl = self.landingURL.split("/")
            formattedUrl = chunkedUrl[0] + "//"+"/".join(chunkedUrl[2:4])+"/page-"+str(i)+"/"+chunkedUrl[5]
            logging.info(formattedUrl)


            r = requests.get(self.landingURL)
            soup = BeautifulSoup(r.content, 'html.parser')

            divs = soup.findAll("div", {"data-vip-url": True,"class":"search-item"})

            self.jsonList = []

            for div in divs:

                
                s = Scrape(sub_url+div["data-vip-url"])
                s.createSession()
                s.getHeaderDetails()
                s.getOverviewDetails()
                self.jsonList.append(s.returnOverviewDict())
                # logging.info("scraping listing number:"+str(NoOfLinks))
                # NoOfLinks +=1
                time.sleep(3)


        self.saveToJson(i,run_date)
            
    
    def saveToJson(self,page_number,run_date):

        if not os.path.exists('data/'+run_date):
            os.makedirs('/opt/airflow/dags/data/'+run_date)
 
        dir = '/opt/airflow/dags/data/'+run_date
        filename = dir+'/page_number_'+str(page_number)+".json"
        
        with open(filename, 'w+') as fp:
            json.dump(self.jsonList, fp,indent=True)
    
        fp.close()

