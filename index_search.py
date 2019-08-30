from elasticsearch_dsl import Index, Keyword, Mapping, Nested, TermsFacet, connections, Search
from elasticsearch import Elasticsearch
from datamodel import dimensies, feiten
import logging
import datetime

logging.basicConfig(format='%(asctime)s : %(message)s',filename='search-index.log', level=logging.INFO)


def main():
    logging.info(f'Starting indexing')
    es = Elasticsearch()
    connections.create_connection(hosts=['localhost:9200'], timeout=20)
    logging.info(f'Checking existing indices')
    for dimensie in dimensies[:1]:
        ix = Index(dimensie['slug'])
        if not ix.exists():
            logging.info(f'Index not found for {dimensie["slug"]}, creating index')
            ix.create()
            m = Mapping()
            fields = dimensie["schema"]().declared_fields
            search_fields = [field for field in fields if 'search_field'in fields[field].metadata and fields[field].metadata['search_field'] == "text"]
            for field in search_fields:
                m.field(field, 'text')
            m.save(dimensie['slug'])
            logging.info(f'Mapping created for {dimensie["slug"]')
        
        logging.info(f'Index found for {dimensie["slug"]}, populating with objects')            

    existing_ixs = es.cat.indices(h='index')
    print(existing_ixs)


if __name__ == "__main__":
    main()