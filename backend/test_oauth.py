import sys
import os
# Add the current directory to sys.path
sys.path.append(os.getcwd())

from gmail.gmail_auth import generate_oauth_url

try:
    url = generate_oauth_url("test-user")
    print(f"Generated URL: {url}")
except Exception as e:
    import traceback
    traceback.print_exc()
