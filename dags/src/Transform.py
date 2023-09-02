import json
import re
from datetime import  datetime as dt
import time
import logging
import os

class Transform:

    def __init__(self,filename) -> None:
        self.filename = filename
        self.dataset = json.load(open(filename))
        self.TorontoAreasList = ['Old Toronto', 'East York', 'North York', 'York', 'Etobicoke', 'Scarborough','Markham','Toronto']

    
    def transform(self):
        for item in self.dataset:
             item['id'] = int(item['id'])
             item['HoursPostedBack'] = self.WrangleDatePosted(item)
             item['price'] = self.WranglePriceColumn(item)
             item['SubArea'] = self.ReturnSubArea(item)
             item['ZipCode'] = self.ReturnZipCode(item)
             item['Address'] = self.ReturnAddress(item)
             item['Rooms'],item['Den'] = self.WrangleBedrooms(item)
             item['Bathrooms'] = self.WrangleBathrooms(item)
             item['Hydro'],item['Heat'],item['Water'] = self.WrangleUtilities(item)
             item['Laundry_in_bulding'],item['Laundry_in_unit'],item['Dishwasher'],item['Fridge_Freezer'] = self.WrangleAppliances(item)
             item['Concierge'], item['24 Hour Security'], item['Storage Space'], item['Elevator in Building'], item['Gym'], item['Bicycle Parking'], item['Pool'] = self.WrangleAmenities(item)
             item['MoveInDateFormatted'] = self.WrangeMoveInDate(item)  
             
             try: 
                item['Size (sqft)'] = int('0') if item['Size (sqft)'] == 'Not Available' else int(item['Size (sqft)'].replace(",",""))
             except KeyError:
                 item['Size (sqft)'] = int('0')

             item['Parking Included'] = item['Parking Included'] if 'Parking Included' in item else 'No'
             item['Furnished'] = item['Furnished'] if 'Furnished' in item else 'No'
             item['Air Conditioning'] = item['Air Conditioning'] if 'Air Conditioning' in item else 'No'

    def saveToJson(self,date):
        if not os.path.exists('transformed/'+date):
            os.makedirs('/opt/airflow/dags/transformed/'+date)

        basefile=os.path.basename(self.filename)
        dir = '/opt/airflow/dags/transformed/'+date+'/'
        filename = dir+basefile
        logging.info(filename)
        with open(filename, 'w+') as fp:
            json.dump(self.dataset, fp,indent=True)
        fp.close()


    def WrangleDatePosted(self,item):
        chunkedList = item['DatePosted'].split(" ")
        try:
            if chunkedList[0].lower() != 'about':
                item['HoursPostedBack'] = str(24*int(chunkedList[0]))
            elif chunkedList[1].lower() == 'an':
                item['HoursPostedBack'] = "1"
            else:
                item['HoursPostedBack'] = chunkedList[1]
        except ValueError:
            item['HoursPostedBack'] = "1"

        return item['HoursPostedBack']
    
    def WrangeMoveInDate(self,item):
        if 'Move-In Date' in item:
            item['MoveInDateFormatted']  = str(dt.strptime(item['Move-In Date'], "%B %d, %Y").date())  
        else:
            item['MoveInDateFormatted'] = str('1900-01-01')
            
        return item['MoveInDateFormatted']

    def WranglePriceColumn(self,item):
        if item['price'] == 'Please Contact':
                item['price'] = None
        else:
            item['price'] = item['price'].replace("$","").replace(",","")
        
        return item['price']
    
    def ReturnSubArea(self,item):
        splitList = item['location'].split(",")
        for i,element in enumerate(splitList):
            if splitList[i].strip() in self.TorontoAreasList:
                item['SubArea'] = element
            else:
                item['SubArea'] = 'Not Available'

        return item['SubArea']   

    def ReturnZipCode(self,item): 
        splitList = item['location'].split(",")
        for i,element in enumerate(splitList):
            if re.search('[A-Z][0-9][A-Z]\s[0-9][A-Z][0-9]',splitList[i].strip()):
                item['ZipCode'] = element
            else:
                item['ZipCode'] = 'Not Available'

        return item['ZipCode']
    
    def ReturnAddress(self,item):
        splitList = item['location'].split(",")
        
        if splitList[0].strip() not in self.TorontoAreasList:
            item['Address'] = splitList[0]
        else:
            item['Address'] = 'Not Available'

        return item['Address']
    
    def WrangleBedrooms(self,item):
        try:
            splitList = item['Bedrooms'].split(":")
            
            if re.search('[a-zA-Z]', splitList[1]):
                NoOfRooms = splitList[1].split("+")
                
                if len(NoOfRooms) == 2:
                    item['Rooms'] = NoOfRooms[0].strip()
                    item['Den'] = 'Yes' if NoOfRooms[1].strip().lower() == 'den' else 'No'
                else:
                    item['Rooms'] = 0
                    item['Den'] = 'No'
            
            else:
                item['Rooms'] = splitList[1].strip()
                item['Den'] = 'No'
        
        except IndexError as ie:
            item['Rooms'] = 0
            item['Den'] = 'No'

        return item['Rooms'],item['Den']
    
    def WrangleBathrooms(self,item):
        splitList = item['Bathrooms'].split(":")
        item['Bathrooms'] = splitList[1] if len(splitList) == 2 else '0'

        return item['Bathrooms']
    
    def WrangleUtilities(self,item):
        try:
            if len(item['Utilities Included']):  
                for utility in item['Utilities Included']:
                    split = utility.split(':')
                    if split[0] == 'Yes':
                        item[split[1].strip()] = split[0]
                    else:
                        item[split[1].strip()] = split[0]
            else:
                item['Hydro'],item['Heat'],item['Water'] = 'No','No','No'
        except KeyError as KE:
            item['Hydro'],item['Heat'],item['Water'] = 'No','No','No'

        return item['Hydro'],item['Heat'],item['Water']


    def WrangleAppliances(self,item):
        try: 
            if len(item['Appliances']) > 0:
                for appliance in item['Appliances']:
                    if appliance == 'Laundry (In Building)':
                        item['Laundry_in_bulding'] = 'Yes'
                    elif appliance == 'Laundry (In Unit)':
                        item['Laundry_in_unit'] = 'Yes'
                    elif appliance == 'Dishwasher':
                        item['Dishwasher'] = 'Yes'
                    elif appliance == 'Fridge / Freezer':
                        item['Fridge_Freezer'] = 'Yes'
                    
            
            if 'Laundry_in_bulding' not in item:
                item['Laundry_in_bulding'] = 'No'
                
            if 'Laundry_in_unit' not in item:
                item['Laundry_in_unit'] = 'No'
                
            if 'Dishwasher' not in item: 
                item['Dishwasher'] ='No'

            if 'Fridge_Freezer' not in item:     
                item['Fridge_Freezer'] = 'No'
        except KeyError as ke:
            item['Laundry_in_bulding'] = 'No'
            item['Laundry_in_unit'] = 'No'
            item['Dishwasher'] ='No'
            item['Fridge_Freezer'] = 'No'


        return item['Laundry_in_bulding'],item['Laundry_in_unit'],item['Dishwasher'],item['Fridge_Freezer']
    
    def WrangleAmenities(self,item):
        amenities = ['Concierge', '24 Hour Security', 'Storage Space', 'Elevator in Building', 'Gym', 'Bicycle Parking', 'Pool']
        if 'Amenities' in item:
            for a in item["Amenities"]:
                    if a in amenities:
                        item[a] = 'Yes'

        for a in amenities:
            if a not in item:
                item[a] = 'No'   
                    
        return item['Concierge'], item['24 Hour Security'], item['Storage Space'], item['Elevator in Building'], item['Gym'], item['Bicycle Parking'], item['Pool']


# t = Transform('result.json')
# t.transform()
# t.saveToJson()