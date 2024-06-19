import streamlit as st
import string
import random
from requests_oauthlib import OAuth2Session

def string_num_generator(size):
    chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
    return ''.join(random.choice(chars) for _ in range(size))

# OAuth2 client setup
client_id = st.secrets["VANTAGE_CLIENT_ID"]
client_secret = st.secrets["VANTAGE_SECRET_ID"]
authorization_base_url = 'https://vantage-us.abbyy.com/auth2/connect/authorize'
token_url = 'https://vantage-us.abbyy.com/auth2//v1/token'
redirect_uri = 'http://localhost:8501/callback'  # This should be the same as set in your OAuth provider settings

# Create an OAuth2 session
oauth = OAuth2Session(client_id, redirect_uri=redirect_uri)

# Streamlit app logic
st.title("ABBYY Vantage OAuth2 Authentication")

authorization_url, state = oauth.authorization_url("https://vantage-us.abbyy.com/auth2/connect/authorize?client_id=y4YezWk2yfEA3oJVRVZfhCLemQPBLz&redirect_uri=https://vantagelicense.streamlit.app&response_type=code&scope=openid%20permissions%20global.wildcard%20offline_access&state=0l1IKffI1JB1mvCUBmO5lwmi&code_challenge=H3C6mgp0CdWPTQS1XjS6C4qmmf8TYTQcCBrp8wkj8dc&code_challenge_method=S256&productId=a8548c9b-cb90-4c66-8567-d7372bb9b963")
st.write(f"[Authorize with ABBYY Vantage]({authorization_url})")