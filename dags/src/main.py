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
import configparser
from src.Upload import upload_to_s3
from src.Scrape import Scrape
from src.Load import Load,createTables,load,insertIntoFinal
from src.Extract import Extract

parser = configparser.ConfigParser()
script_path = pathlib.Path(__file__).parent.resolve()
parser.read(f"{script_path}/configuration.conf")

toronto_url = parser.get("url_config", "toronto_url")


def extract(** context):
    date = context['ds']
    print(date)
    
    print("toronto_url "+toronto_url)
    e = Extract(toronto_url)
    e.getListings(2,str(date))
    logging.info("Scraping listings was successfull")
    

def uploadRawtoS3(** context):
    date = context['ds']
    dir = '/opt/airflow/dags/data/'+ str(date)
    files = os.listdir(dir)
    for file in files:
        filepath = dir+"/"+file
        upload_to_s3(filepath,str(date))


def transform(** context):
    date = context['ds']
    dir = '/opt/airflow/dags/data/'+str(date)    
    files = os.listdir(dir)

    for file in files:
        filepath = dir+"/"+file
        t = Transform(filepath)
        t.transform()
        t.saveToJson(date)

def createRedShiftTables():
    createTables()

def insertIntoStage(** context):
    date = context['ds']
    dir = '/opt/airflow/dags/transformed/'+ str(date)
    files = os.listdir(dir)
    for file in files:
        filepath = dir+"/"+file
        load(filepath)          

def insertIntoFinalRedshiftTable():
    insertIntoFinal()

def uploadTransformedtos3():
    dir = '/opt/airflow/dags/transformed' 
    files = os.listdir(dir)
    for file in files:
        filepath = dir+"/"+file
        
        upload_to_s3(filepath,'transformed')        
           




        

