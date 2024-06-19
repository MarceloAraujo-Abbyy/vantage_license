import streamlit as st
import string
import random
import hashlib
import base64
import requests 
from streamlit_cookies_controller import CookieController

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



st.title("ABBYY Vantage OAuth2 Authentication")

controller = CookieController()

# OAuth2 client setup
client_id = st.secrets["VANTAGE_CLIENT_ID"]
client_secret = st.secrets["VANTAGE_SECRET_ID"]
authorization_base_url = 'https://vantage-us.abbyy.com/auth2/connect/authorize'
token_url = 'https://vantage-us.abbyy.com/auth2/04db7530-dc41-4ae2-9194-a18d786eb877/connect/token'
redirect_uri = 'https://vantageaccess.streamlit.app'
scope = "openid permissions global.wildcard offline_access"
grant_type = "authorization_code"
product_id= "a8548c9b-cb90-4c66-8567-d7372bb9b963"

if 'code' not in st.query_params:

    if 'verifier' not in st.session_state:
        st.session_state.verifier =  string_num_generator(56)
#        controller.set('streamlit-verifier', st.session_state.verifier)
    
    state = string_num_generator(20)
    challenger = pkce_challenge_from_verifier(st.session_state.verifier)
    verifier =  st.session_state.verifier

    st.write("state: " + state)
    st.write("verifier: " + verifier )
    st.write("challenger: " + challenger)

    auth_link = authorization_base_url+"?client_id="+client_id+"&redirect_uri="+redirect_uri+"&response_type=code&scope="+scope+"&state="+state+"&code_challenge="+challenger+"&code_challenge_method=S256&productId="+product_id

    st.write(f'<a href="'+auth_link+'"><Button>Login Vantage oAuth</Button></a>',unsafe_allow_html=True)
    #st.write(auth_link)

else:
    verifier = controller.get('streamlit-verifier')
    """
    st.write("authorization_response_code: " + st.query_params['code']) 
    st.write("authorization_response_scope: " + st.query_params['scope']) 
    st.write("authorization_response_state: " + st.query_params['state']) 
    st.write("verifier: " + verifier )
    st.write("authorization_response_session_state: " + st.query_params['session_state']) 
    """

    data = {

        'code_verifier':  st.session_state.verifier,
        'grant_type': grant_type,
        'client_id': client_id,
        'client_secret': client_secret,
        'code': st.query_params['code'],
        'redirect_uri': redirect_uri,
        'scope':  st.query_params['scope']
    }

    st.write(data)

    response = requests.post(token_url, data=data, headers={'accept': '*/*', 'Content-Type': 'application/x-www-form-urlencoded'})
    if response.status_code == 200:
        response_data = response.json()
        token = response_data['access_token']
        st.write("Authentication successful!")
        st.write(token)
    else:
        st.write("Erro logging: " + response.text) 
