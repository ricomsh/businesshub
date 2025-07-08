import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Set Flask configuration from .env file."""

    # General Config
    SECRET_KEY = os.environ.get('SECRET_KEY')
    FLASK_APP = os.environ.get('FLASK_APP')
    FLASK_DEBUG = os.environ.get('FLASK_DEBUG')

    # Database Config
    MONGO_URI = os.environ.get('MONGO_URI')
    MONGO_DB_NAME = os.environ.get('MONGO_DB_NAME')
    
    # SQL Server Config
    SQL_SERVER_DRIVER = os.environ.get('SQL_SERVER_DRIVER')
    SQL_SERVER_HOST = os.environ.get('SQL_SERVER_HOST')
    SQL_SERVER_DATABASE = os.environ.get('SQL_SERVER_DATABASE')
    SQL_SERVER_USER = os.environ.get('SQL_SERVER_USER')
    SQL_SERVER_PASSWORD = os.environ.get('SQL_SERVER_PASSWORD')
    
    # Email Config
    SMTP_SERVER = os.environ.get('SMTP_SERVER')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
    SMTP_USER = os.environ.get('SMTP_USER')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD')

    # Microsoft SSO Config
    MS_CLIENT_ID = os.environ.get('MS_CLIENT_ID')
    MS_CLIENT_SECRET = os.environ.get('MS_CLIENT_SECRET')
    MS_TENANT_ID = os.environ.get('MS_TENANT_ID')
    if MS_TENANT_ID:
        MS_SERVER_METADATA_URL = f"https://login.microsoftonline.com/{MS_TENANT_ID}/v2.0/.well-known/openid-configuration"
    else:
        MS_SERVER_METADATA_URL = ''
