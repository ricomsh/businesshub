import os
from pymongo import MongoClient
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

def create_initial_users():
    """Connects to MongoDB and creates initial users and collections."""
    load_dotenv()
    
    mongo_uri = os.environ.get('MONGO_URI')
    db_name = os.environ.get('MONGO_DB_NAME')
    
    if not mongo_uri or not db_name:
        print("Error: MONGO_URI and MONGO_DB_NAME must be set in your .env file.")
        return

    client = MongoClient(mongo_uri)
    db = client[db_name]
    
    # --- Initialize Collections ---
    print(f"Ensuring collections exist in database: '{db_name}'...")
    users_collection = db.users
    slips_collection = db.slips

    # Create indexes to optimize queries and enforce uniqueness where needed
    users_collection.create_index('email', unique=True)
    slips_collection.create_index('slip_id', unique=True, sparse=True)
    slips_collection.create_index('slip_type')
    print("Collections and indexes are ready.")

    # --- User Data with Specific Roles ---
    users = [
        {
            'email': 'ricardo.williams@hcaircon.com', 
            'name': 'Ricardo Williams',
            'roles': ['admin', 'sales'], 
            'password': 'Password123'
        },
        {
            'email': 'comfort.motebejane@hcaircon.com', 
            'name': 'Comfort Motebejane',
            'roles': ['qc'], 
            'password': 'Password123'
        },
        {
            'email': 'eric.mashau@hcaircon.com',
            'name': 'Eric Mashau',
            'roles': ['admin'],
            'password': 'Password123'
        },
        {
            'email': 'dispatch.user@yourapp.com', 
            'name': '[Dispatch Name]',
            'roles': ['dispatch'], 
            'password': 'Password123'
        },
        {
            'email': 'ir.user@yourapp.com', 
            'name': '[IR User Name]',
            'roles': ['ir'], 
            'password': 'Password123'
        }
    ]

    print("\nSeeding database with initial users...")
    for user_data in users:
        # Check if user already exists
        if users_collection.find_one({'email': user_data['email']}):
            print(f"User {user_data['email']} already exists. Updating roles and name.")
            users_collection.update_one(
                {'email': user_data['email']},
                {'$set': {'roles': user_data['roles'], 'name': user_data['name']}}
            )
            continue

        # Hash the password
        user_data['password'] = generate_password_hash(user_data['password'])
        
        # Insert the new user
        users_collection.insert_one(user_data)
        print(f"Created user: {user_data['email']} with roles: {user_data['roles']}")

    print("\nDatabase seeding complete.")
    client.close()

if __name__ == '__main__':
    create_initial_users()
