# Vantage License Manager

This application helps manager license in different Vantage Tenants.

Requirements:

Github user - To fork this repository

Streamlit user - To publish using Streamlit cloud. 




## Usage

You'll need to set up your ABBYY Vantage tenants information you want to manager. 

When create your streamlit app, set the secrets with the according information: 

```python
VANTAGE_BASE_URL = 'https://vantage-us.abbyy.com/'
VANTAGE_TENANTS = '[ {"tenant_name": "", "tenant_id": "", "user": "", "pwd": "", "client_id": "", "client_secret": "" }, ... ]'
