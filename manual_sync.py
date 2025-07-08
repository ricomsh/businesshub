from app.sync import sync_data_from_sql
from dotenv import load_dotenv

# Load environment variables so the script can connect to the DB
load_dotenv() 
print("Starting manual sync...")
sync_data_from_sql()
print("Manual sync finished.")