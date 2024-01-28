#!/usr/bin/env python
# coding: utf-8

import argparse

from time import time
import pandas as pd
from sqlalchemy import create_engine

def main(params):
    user = params.user
    password = params.password
    host = params.host
    port = params.port
    db = params.db
    table_name = params.table_name
    url = params.url

    # backup files are gzipped 
    csv_name = 'output.csv.gz' if url.endswith('.csv.gz') else 'output.csv'

    os.system(f'wget {url} -O {csv_name}')

    engine = create_engine(f'postgresql://{user}:{password}@{host}:{port}/{db}')
    
    if csv_name.endswith('.gz'):
        df_iter = pd.read_csv(f'{csv_name}', compression='gzip', iterator=True, chunksize=10000)
    else:
        df_iter = pd.read_csv(f'{csv_name}', iterator=True, chunksize=10000)
    df = next(df_iter)

    # chagne the format from char to timestemp
    df.lpep_pickup_datetime = pd.to_datetime(df.lpep_pickup_datetime)
    df.lpep_dropoff_datetime = pd.to_datetime(df.lpep_dropoff_datetime)

    df.head(n=0).to_sql(name=table_name, con=engine, if_exists='replace')
    df.to_sql(name=table_name, con=engine, if_exists='append')

    while True:
        try:
            t_start = time()

            df = next(df_iter)

            df.lpep_pickup_datetime = pd.to_datetime(df.lpep_pickup_datetime)
            df.lpep_dropoff_datetime = pd.to_datetime(df.lpep_dropoff_datetime)
            
            df.to_sql(name=table_name, con=engine, if_exists='append')

            t_end = time()

            print('inserted anoter chunk, took %.3f second' % (t_end-t_start))

        except StopIteration:
            print('Finished ingesting data into the postgres database')
            break



if __name__ == 'main':
    parser = argparse.ArgumentParser(descriptoin='Ingest CSV data to Postgres')
    parser.add_argument("--user", help="user name for Postgres")
    parser.add_argument("--password", help="password for Postgres")
    parser.add_argument("--host", help="host for Postgres")
    parser.add_argument("--port", help="port for Postgres")
    parser.add_argument("--db", help="database name for Postgres")
    parser.add_argument("--table_name", help="name of the table where we will write the results to")
    parser.add_argument("--url", help="url of the csv file")
    args = parser.parse_args()

    main(args)