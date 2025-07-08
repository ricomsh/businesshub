from app import create_app
import os

app = create_app()

# This block allows you to run the app directly with 'python run.py'
if __name__ == "__main__":
    # --- SSL Configuration Placeholder ---
    # To enable HTTPS for production, you need an SSL certificate.
    # 1. Place your certificate file (e.g., 'cert.pem') and your private key file (e.g., 'key.pem')
    #    in the root directory of this project.
    # 2. Uncomment the 'ssl_context' line below.
    # For local development, you can generate a self-signed certificate.
    # -----------------------------------------------------------------

    # ssl_context = ('cert.pem', 'key.pem')

    # To run WITH SSL for production, change the line below to:
    # app.run(host='0.0.0.0', port=5000, ssl_context=ssl_context)
    
    # Run WITHOUT SSL for local development
    # The debug=True flag enables auto-reloading when you save a file.
    app.run(host='0.0.0.0', port=5000, debug=True)
