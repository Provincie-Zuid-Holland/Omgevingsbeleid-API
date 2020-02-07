from elasticsearch_dsl import Index, Keyword, Mapping, Nested, TermsFacet, connections, Search
from elasticsearch import Elasticsearch
from datamodel import dimensies_and_feiten
import logging
from datetime import datetime
import json
import os
import pyodbc
from globals import db_connection_string, db_connection_settings

# Filenames to store the date and logs
LOGGING_FILE = 'search-index.log'
DATE_FILE = 'search-date.json'
IX_POST = '_dev'

logging.basicConfig(format='%(asctime)s : %(message)s', filename=LOGGING_FILE, level=logging.INFO)


def main():
    scriptdate = datetime.now()
    logging.info('Starting indexing')
    # if we can't find a DATE_FILE we assume Unix timestamp minimum
    last_datetime = datetime(1970, 1, 1, 0, 0, 0, 0)
    if not (os.path.exists(DATE_FILE)):
        logging.info('No previous search date found, assuming first run')
    else:
        with open(DATE_FILE, 'r') as datefile:
            try:
                last_datetime = datetime.fromtimestamp(json.load(datefile)['last_datetime'])
                logging.info(f'Last run at {last_datetime}')
            except json.decoder.JSONDecodeError:
                logging.info(f'DATE_FILE seems corrupt, assuming first run')
    es = Elasticsearch()
    connections.create_connection(hosts=['localhost:9200'], timeout=20)
    logging.info(f'Checking existing indices')
    for dimensie in dimensies_and_feiten():
        ix = Index(dimensie['slug'] + IX_POST)
        fields = dimensie["schema"]().declared_fields
        search_fields = [field for field in fields if 'search_field'in fields[field].metadata and fields[field].metadata['search_field'] == "text"]
        search_fields += ["UUID", "ID"]
        if not ix.exists():
            logging.info(f'Index not found for {dimensie["slug"]}, creating index')
            ix.create()
            m = Mapping()
            for field in search_fields:
                if field == 'ID':
                    field = '_ID'
                m.field(field, 'text', analyzer='dutch')
            m.field('type', 'text')
            print(m)
            m.save(dimensie['slug'] + IX_POST)
            logging.info(f'Mapping created for {dimensie["slug"]}')

        logging.info(f'Index found for {dimensie["slug"]}, populating with objects')
        # Add objects here
        query = f"SELECT {', '.join(search_fields)} from {dimensie['tablename']} WHERE modified_date > '{last_datetime}' AND UUID != '00000000-0000-0000-0000-000000000000'"

        with pyodbc.connect(db_connection_settings) as connection:
            cursor = connection.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            
            for row in rows:
                rowdict = dict(zip([t[0] for t in row.cursor_description], row))
                rowdict['_ID'] = rowdict.pop('ID')
                rowdict['type'] = dimensie['plural']
                es.index(
                    index=dimensie['slug'] + IX_POST,
                    body=rowdict)
                logging.info(f"Added document with UUID {rowdict['UUID']} to index {dimensie['slug']}")

    with open(DATE_FILE, 'w') as datefile:
            json.dump({'last_datetime': datetime.timestamp(scriptdate.replace(microsecond=0))}, datefile)
    logging.info('Done filling search indices')


if __name__ == "__main__":
    main()