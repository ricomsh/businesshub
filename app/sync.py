# app/sync.py

import pyodbc
import logging
from app.database import get_mongo_db, get_sql_conn
from flask import current_app

# Configure logging to provide visibility into the sync process
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def sync_data_from_sql():
    """
    Connects to the SQL Server database, fetches data from specified tables,
    and upserts it into corresponding MongoDB collections.
    This function is designed to be run as a scheduled task or manually.
    """
    logger.info("Starting data synchronization from SQL Server to MongoDB.")
    
    db = get_mongo_db()
    sql_conn = None  # Initialize sql_conn to None to ensure it's available in 'finally'

    try:
        # Establish connection to the SQL Server
        sql_conn = get_sql_conn()
        cursor = sql_conn.cursor()
        
        # --- Sync 'Part' table ---
        logger.info("Starting 'Part' table sync...")
        
        # =================================== FIX ===================================
        # The SQL query is now updated to use the correct column names 'ID' and 'DESCRIPTION'
        # from your PART table, based on the detailed query you provided.
        # =========================================================================
        sql_query_parts = "SELECT ID, DESCRIPTION FROM PART"
        
        cursor.execute(sql_query_parts)
        
        parts_collection = db.parts
        synced_parts_count = 0
        
        # Iterate over the fetched rows
        for row in cursor.fetchall():
            part_data = {
                # =================================== FIX ===================================
                # The code now maps the correct columns to the MongoDB document fields.
                # 'ID' is used as the stock_code and 'DESCRIPTION' is used for both description fields.
                # =========================================================================
                'stock_code': row.ID,
                'description': row.DESCRIPTION,
                'long_description': row.DESCRIPTION,
            }
            
            # Upsert the part data into MongoDB.
            parts_collection.update_one(
                {'stock_code': part_data['stock_code']},
                {'$set': part_data},
                upsert=True
            )
            synced_parts_count += 1
            
        logger.info(f"Successfully synced {synced_parts_count} documents into the 'parts' collection.")

        # You can add sync logic for other tables here following the same pattern.

        cursor.close()
        logger.info("Data synchronization completed successfully.")

    except pyodbc.Error as ex:
        # Catch specific database errors
        sqlstate = ex.args[0]
        logger.error(f"Database error during sync: {sqlstate}", exc_info=True)
        # Provide a helpful message if the column name is wrong
        if 'Invalid column name' in str(ex):
            logger.error(
                "Sync failed: A column name in the SQL query is incorrect. "
                "Please check that the column names in 'app/sync.py' exist in your 'Part' table."
            )
        
    except Exception as e:
        # Catch any other unexpected errors
        logger.error(f"An unexpected error occurred during data synchronization: {e}", exc_info=True)

    finally:
        # Ensure the SQL connection is always closed
        if sql_conn:
            sql_conn.close()
            logger.info("SQL Server connection closed.")
