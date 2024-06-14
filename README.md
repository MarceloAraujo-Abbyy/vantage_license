# Vantage License Manager

This application helps manager license in different Vantage Tenants.

Install dependencies.

```python
pip install -r requirements.txt
```

## Usage

You'll need to set up your ABBYY Vantage tenant and a JSON with the tenant information you want to manager. 

When create your streamlit app, set the secrets with the according information: 

```python
VANTAGE_CLIENT_ID = "" 
VANTAGE_SECRET_ID = ""
VANTAGE_TENANT_ID = "" 
VANTAGE_TENANTS = "[ {tenant_name: "", user: "", pwd: "", client_id: "", secret_id: "" } ]" 
