import json
import hashlib
import redshift_connector
import psycopg2
import configparser
from psycopg2 import sql
import sys
import pathlib
from psycopg2.extras import execute_values

parser = configparser.ConfigParser()
script_path = pathlib.Path(__file__).parent.resolve()
parser.read(f"{script_path}/configuration.conf")

USERNAME = parser.get("aws_config", "redshift_username")
PASSWORD = parser.get("aws_config", "redshift_password")
HOST = parser.get("aws_config", "redshift_hostname")
PORT = parser.get("aws_config", "redshift_port")
REDSHIFT_ROLE = parser.get("aws_config", "redshift_role")
DATABASE = parser.get("aws_config", "redshift_database")
BUCKET_NAME = parser.get("aws_config", "bucket_name")
ACCOUNT_ID = parser.get("aws_config", "account_id")
TABLE_NAME = "HousePrices"


role_string = f"arn:aws:iam::{ACCOUNT_ID}:role/{REDSHIFT_ROLE}"


sql_create_view = sql.SQL("""
create or replace view houseprices_view as
SELECT id, 
price, 
subarea,
zipcode, 
address, 
current_Date - cast(dateposted as integer) as dateposted ,
buildingtype,
rooms, 
den, 
bathrooms, 
case when hydro = 'Yes' and heat = 'Yes' and water ='Yes' then 'yes' else 'no' end all_utilties,
hydro, 
heat, 
water, 
laundry_in_building, 
laundary_in_unit,
dishwasher, 
fridge_freezer, 
concierge, 
twenty_four_hour_security,
storage_space, 
elevator_in_building,
gym,
bicycle_parking,
pool, 
parking_included,
move_in_date,
"size",
furnished,
air_conditioning
FROM public.houseprices;
""")

sql_create_table = sql.SQL(
    """CREATE TABLE IF NOT EXISTS {table}
               (id bigint, 
                price INTEGER,
                SubArea VARCHAR,
                ZipCode VARCHAR,
                Address VARCHAR,
                DatePosted VARCHAR,
                BuildingType VARCHAR,
                Rooms FLOAT,
                Den CHAR(3),
                Bathrooms FLOAT,
                Hydro CHAR(3),
                Heat CHAR(3),
                Water CHAR(3),
                Laundry_in_building CHAR(3),
                Laundary_in_unit CHAR(3),
                Dishwasher CHAR(3),
                Fridge_Freezer CHAR(3),
                Concierge CHAR(3),
                Twenty_Four_Hour_Security CHAR(3),
                Storage_Space CHAR(3),
                Elevator_in_building CHAR(3),
                Gym CHAR(3),
                Bicycle_Parking CHAR(3),
                Pool CHAR(3),
                Parking_Included CHAR(3),
                Move_in_date DATE,
                Size INTEGER,
                Furnished CHAR(3),
                Air_conditioning CHAR(3),
                primary key(id),
                UNIQUE (id,price,SubArea,ZipCode,Address,DatePosted)            
                );
                        """
).format(table=sql.Identifier(TABLE_NAME))

create_temp_table = sql.SQL(
    "CREATE TABLE staging_table (LIKE {table});"
).format(table=sql.Identifier(TABLE_NAME))


delete_from_table = sql.SQL(
    "DELETE FROM {table} USING staging_table WHERE ({table}.id = staging_table.id and {table}.price = staging_table.price and {table}.SubArea = staging_table.SubArea and {table}.ZipCode = staging_table.ZipCode and {table}.Address = staging_table.Address and {table}.DatePosted = staging_table.DatePosted);"
).format(table=sql.Identifier(TABLE_NAME))

insert_into_table = sql.SQL(
    "INSERT INTO {table} SELECT * FROM staging_table;"
).format(table=sql.Identifier(TABLE_NAME))

drop_temp_table = "DROP TABLE staging_table;"

class Load:
    def __init__(self) -> None:
        pass

    def connect_to_redshift(self):
        """Connect to Redshift instance"""
        try:
            self.rs_conn = psycopg2.connect(
            dbname=DATABASE, user=USERNAME, password=PASSWORD, host=HOST, port=PORT
            )
        
        except Exception as e:
            print(f"Unable to connect to Redshift. Error {e}")
            sys.exit(1) 
        finally:
            return self.rs_conn   

    def loadValues(self,filename):

        cursor = self.rs_conn.cursor() 
        keep = ['id', 'price','SubArea','ZipCode','Address','HoursPostedBack','BuildingType','Rooms','Den','Bathrooms','Hydro','Heat','Water','Laundry_in_bulding','Laundry_in_unit','Dishwasher','Fridge_Freezer','Concierge',
                       '24 Hour Security','Storage Space','Elevator in Building','Gym','Bicycle Parking', 'Pool','Parking Included',
                       'MoveInDateFormatted','Size (sqft)','Furnished','Air Conditioning']
        
        columns = ['id', 'price','SubArea','ZipCode','Address','DatePosted','BuildingType','Rooms','Den','Bathrooms','Hydro','Heat','Water','Laundry_in_building'
                   ,'Laundary_in_unit','Dishwasher','Fridge_Freezer','Concierge',
                       'twenty_four_hour_security','Storage_Space','Elevator_in_building','Gym','Bicycle_Parking', 'Pool','Parking_Included',
                       'Move_in_date','Size','Furnished','Air_Conditioning']
        

        dataset = json.load(open(filename))

        query = "INSERT INTO staging_table ({}) VALUES %s".format(','.join(columns))
        
        dict = [{}]

        for i in range(0,len(dataset)):
            dict.append({key: dataset[i][key] for key in keep})

        for i in range(0,len(dict)):
            index_map = {v: i for i, v in enumerate(keep)}
            sorted(dict[i].items(), key=lambda pair: index_map[pair[0]])
        
        # # convert dic values to list of lists
        values = [[value for key,value in dict[i].items() ] for i in range(0,len(dict))]
    
        del values[0]

        execute_values(cursor, query, values)
        self.rs_conn.commit()


def createTables():
    L = Load()
    conn = L.connect_to_redshift()  
    """Load data from S3 into Redshift"""
    with conn:
        cur = conn.cursor()
        cur.execute(sql_create_table)
        cur.execute(sql_create_view)
        cur.execute(create_temp_table)

    conn.commit()
    conn.close()    


def load(filename):
    L = Load()
    conn = L.connect_to_redshift()  
    """Load data from S3 into Redshift"""
    with conn:
        L.loadValues(filename=filename)

    conn.commit()
    conn.close()

def insertIntoFinal():

    L = Load()
    conn = L.connect_to_redshift()
    with conn: 
        cur = conn.cursor()
        cur.execute(delete_from_table)
        cur.execute(insert_into_table)
        cur.execute(drop_temp_table)
    
    conn.commit()
    conn.close()
  








