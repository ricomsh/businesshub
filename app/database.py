# FILE: app/database.py

import os
from flask import g, current_app
from pymongo import MongoClient
import pyodbc
import logging

logger = logging.getLogger(__name__)

def get_mongo_db():
    """
    Connects to the MongoDB database.
    Uses the Flask application context 'g' to store the connection,
    ensuring it's created only once per request.
    """
    if 'mongo_client' not in g:
        mongo_uri = current_app.config['MONGO_URI']
        db_name = current_app.config['MONGO_DB_NAME']
        if not mongo_uri or not db_name:
            raise ValueError("MONGO_URI and MONGO_DB_NAME must be set in the application config.")
        
        logger.info("Connecting to primary database: MongoDB")
        g.mongo_client = MongoClient(mongo_uri)
        g.mongo_db = g.mongo_client[db_name]
        logger.info("✅ MongoDB connection successful.")

    return g.mongo_db

def get_sql_conn():
    """
    Connects to the SQL Server database.
    Uses the Flask application context 'g' to store the connection,
    ensuring it's created only once per request.
    """
    if 'sql_conn' not in g:
        logger.info("Attempting to connect to source database: SQL Server")
        driver = current_app.config['SQL_SERVER_DRIVER']
        server = current_app.config['SQL_SERVER_HOST']
        database = current_app.config['SQL_SERVER_DATABASE']
        username = current_app.config['SQL_SERVER_USER']
        password = current_app.config['SQL_SERVER_PASSWORD']

        conn_str = f'DRIVER={{{driver}}};SERVER={server};DATABASE={database};UID={username};PWD={password}'
        g.sql_conn = pyodbc.connect(conn_str)
        logger.info("✅ SQL Server connection successful.")

    return g.sql_conn

def close_connections(exception=None):
    """
    Closes all database connections stored in the application context 'g'.
    This function is called automatically at the end of each request.
    """
    mongo_client = g.pop('mongo_client', None)
    if mongo_client:
        mongo_client.close()
        logger.info("MongoDB connection closed.")

    sql_conn = g.pop('sql_conn', None)
    if sql_conn:
        sql_conn.close()
        logger.info("SQL Server connection closed.")

