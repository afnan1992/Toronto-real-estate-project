from airflow.decorators import dag, task
from airflow.operators.python_operator import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow import DAG
from datetime import datetime, timedelta

from src.main import extract,transform,uploadRawtoS3,uploadTransformedtos3,insertIntoStage,createRedShiftTables,insertIntoFinalRedshiftTable


dag = DAG(
    'toronto_real_estate_etl',
    # These args will get passed on to each operator
    # You can override them on a per-task basis during operator initialization
  
    description='ETL DAG',
    start_date=datetime(2023, 9, 1),
    max_active_runs= 1
    
) 

ScrapeListings = PythonOperator(
dag=dag,
task_id="Extract",
python_callable=extract,
provide_context=True,
)

UploadRawtoS3 = PythonOperator(

    dag = dag,
    task_id = 'RawToS3',
    python_callable = uploadRawtoS3,
    provide_context=True,
)

createTables = PythonOperator(
dag = dag,
task_id = 'createTables',
python_callable = createRedShiftTables,
provide_context=True,
)

Transform = PythonOperator(
dag=dag,
task_id="Transform",
python_callable=transform,
provide_context=True,

)

ToStage = PythonOperator(
dag = dag,
task_id = "ToStageTable",
python_callable = insertIntoStage,
provide_context=True,
)

StagetoFinal = PythonOperator(
dag = dag,
task_id = "StagetoFinal",
python_callable = insertIntoFinalRedshiftTable,
provide_context=True,

)

# UploadTransformedtoS3 = PythonOperator(
# dag=dag,
# task_id="TransformedToS3",
# python_callable=uploadTransformedtos3,

# )

ScrapeListings >> UploadRawtoS3 >> createTables >> Transform  >> ToStage >> StagetoFinal