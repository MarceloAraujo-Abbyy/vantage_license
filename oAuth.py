import streamlit as st
import string
import random
import hashlib
import base64
from requests_oauthlib import OAuth2Session


def string_num_generator(size):
    chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
    return ''.join(random.choice(chars) for _ in range(size))

def base64urlencode(a):
    # Codifica em base64url
    return base64.urlsafe_b64encode(a).decode('utf-8').strip('=')

def sha256(plain):
    # Calcula o hash SHA-256 da string
    return hashlib.sha256(plain.encode()).digest()

def pkce_challenge_from_verifier(v):
    hashed = sha256(v)
    base64encoded = base64urlencode(hashed)
    return base64encoded

# OAuth2 client setup
client_id = st.secrets["VANTAGE_CLIENT_ID"]
client_secret = st.secrets["VANTAGE_SECRET_ID"]
authorization_base_url = 'https://vantage-us.abbyy.com/auth2/connect/authorize'
token_url = 'https://vantage-us.abbyy.com/auth2//v1/token'
redirect_uri = 'https://vantageaccess.streamlit.app'  # This should be the same as set in your OAuth provider settings
scope = "openid permissions global.wildcard offline_access"
state = string_num_generator(20)
verifier = string_num_generator(56)
challenger = pkce_challenge_from_verifier(verifier)

# Create an OAuth2 session
oauth = OAuth2Session(client_id, redirect_uri=redirect_uri)

# Streamlit app logic
st.title("ABBYY Vantage OAuth2 Authentication")

auth_link = "https://vantage-us.abbyy.com/auth2/connect/authorize?client_id="+client_id+"&redirect_uri="+redirect_uri+"&response_type=code&scope="+scope+"&state="+state+"&code_challenge"+challenger+"&code_challenge_method=S256&productId=a8548c9b-cb90-4c66-8567-d7372bb9b963"
st.write("auth_link => "+ auth_link)

authorization_url, state = oauth.authorization_url(auth_link)
st.write(f"[Authorize with ABBYY Vantage]({authorization_url})")