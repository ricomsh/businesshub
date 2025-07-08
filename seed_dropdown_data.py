from app.database import get_mongo_db
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_dropdowns():
    """
    Populates the 'dropdown_options' collection with initial data
    for various dropdowns in the application.
    """
    load_dotenv()
    
    try:
        db = get_mongo_db()
        collection = db.dropdown_options
        logger.info("Connected to MongoDB and accessed 'dropdown_options' collection.")

        # --- Data for Production Managers Dropdown (Updated) ---
        production_managers = {
            '_id': 'production_managers',
            'list_name': 'Production Managers',
            'options': [
                {'name': 'Daniel Maleka – Commercial Final Assembly', 'email': 'daniel.maleka@hcaircon.com'},
                {'name': 'Macdonald Moabi – Industrial Final Assembly', 'email': 'macdonald.moabi@hcaircon.com'},
                {'name': 'Collen Sondlo – HVAC', 'email': 'collen.sondlo@hcaircon.com'},
                {'name': 'Andrew Botha – Welding', 'email': 'andrew.botha@hcaircon.com'},
                {'name': 'Norman Dixon – Coil Shop', 'email': 'norman.dixon@hcaircon.com'},
                {'name': 'Chelsea Owen – Sheet Metal', 'email': 'chelsea.owen@hcaircon.com'},
                {'name': 'Deen Motani – Electrical', 'email': 'deen.motani@hcaircon.com'},
                {'name': 'Jacques Botha – Electrical', 'email': 'jacques.botha@hcaircon.com'}
            ]
        }

        # Use replace_one with upsert=True to insert or update the document
        collection.replace_one({'_id': production_managers['_id']}, production_managers, upsert=True)
        logger.info(f"Upserted '{production_managers['list_name']}' list.")

        # The qc_users list has been removed as it is no longer needed.

        logger.info("✅ Dropdown data seeding complete.")

    except Exception as e:
        logger.error(f"❌ An error occurred during seeding: {e}")

if __name__ == '__main__':
    seed_dropdowns()
