

import streamlit as st
import random
import time
import os
import pandas as pd
import json
import requests

###  streamlit run C:\Users\marceloraraujo\Documents\vantage_license\vantage-license\vantage_license.py

# Login Vantage
def login_vantage(tenant_name,tenant_id,username,password,client_id,secret_id):
    print("Login Vantage")
    if username != "" and password != "":
        url = "https://vantage-us.abbyy.com/auth2/"+tenant_id+"/connect/token"
        payload = 'grant_type=password&scope=openid permissions global.wildcard&username='+username+'&password='+password+'&client_id='+client_id+'&client_secret='+secret_id
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        response = requests.request("POST", url, headers=headers, data=payload)
        obj = json.loads(response.text)
        if "access_token" in obj:
            accessToken = "Bearer " + str(obj["access_token"])
            st.session_state['token'] = accessToken
            st.markdown("🟢 Logged with Success in " + tenant_name)
            return(accessToken)
        else:
            st.session_state['token'] = ''
            st.markdown("🔴 Error to login in " + tenant_name)
            return("Error to login!")

def read_data_usr(json_array):

    data_list = json.loads(json_array)

    tenant_names = []
    user_names = []
    user_emails = []
    user_roles = []
    
    #print("data_list " + json_array)
    
    for data in data_list:
        print("data " + str(data))
        tenant_name = data['tenant']

        for user in data['data']['items']:
            print("user " + str(user))
            user_name = user['displayName']
            user_email = user['email']
            
            for role in user['roles']:
                print("role " + str(role))
                user_role = role['name']

                tenant_names.append(tenant_name)
                user_names.append(user_name)
                user_emails.append(user_email)
                user_roles.append(user_role)
    
    df = pd.DataFrame({
        'tenant': tenant_names,
        'name': user_names,
        'email': user_emails,
        'role': user_roles
    })
    
    return df

def read_data_lic(json_array):

    data_list = json.loads(json_array)

    tenant_names = []
    serial_numbers = []
    expire_dates = []
    skill_names = []
    skill_counters = []
    skill_limits = []
    skill_remains = []
    
    #print("data_list " + json_array)
    
    for data in data_list:
        tenant_name = data['tenant']
        serial_number = data['data']['serialNumber']
        expire_date = data['data']['expireDate']
        
        for skill in data['data']['skills']:
            tenant_names.append(tenant_name)
            serial_numbers.append(serial_number)
            expire_dates.append(expire_date)
            skill_names.append(skill['name'])
            skill_counters.append(skill['counter'])
            skill_limits.append(skill['limit'])
            skill_remains.append(skill['limit'] - skill['counter'])
    
    df = pd.DataFrame({
        'tenant_name': tenant_names,
        'serialNumber': serial_numbers,
        'expireDate': expire_dates,
        'skills_name': skill_names,
        'skills_counter': skill_counters,
        'skills_limit': skill_limits,
        'skills_remain': skill_remains
    })
    
    return df

def get_data(tenants):

    tenant_list = json.loads(tenants)
    lic_data = []
    usr_data = []
    for item in tenant_list:
        accessToken = login_vantage(item['tenant_name'], item["tenant_id"], item["user"], item["pwd"], item["client_id"], item["secret_id"])
        #print("accessToken" + accessToken)
        if accessToken.startswith("Bearer"):
            #read license
            url = "https://vantage-us.abbyy.com/api/workspace/subscriptions/me"
            headers = {'Authorization': accessToken, 'Accept': '*/*'}
            payload = {}
            response = requests.request("GET", url, headers=headers, data=payload)
            #print("lic_data: " + response.text, response.status_code)
            obj = json.loads(response.text)
            lic_data.append({"tenant": item["tenant_name"], "data": obj})
            #print("Returned: " + json.dumps(lic_data))

            #read users
            url = "https://vantage-us.abbyy.com/api/adminapi2/v1/tenants/"+item["tenant_id"]+"/users?includeRoles=true"
            headers = {'Authorization': accessToken, 'Accept': '*/*'}
            payload = {}
            response = requests.request("GET", url, headers=headers, data=payload)
            #print("user_data: " + item["tenant_id"])#  + response.text, response.status_code)
            obj = json.loads(response.text)
            usr_data.append({"tenant": item["tenant_name"], "data": obj})
            #print("Returned: " + json.dumps(usr_data))

    json_lic = json.dumps(lic_data)
    json_usr = json.dumps(usr_data)
    return json_lic, json_usr


def highlight_less_than(val,ref):
    print(val,ref)
    color = 'red' if int(val) < int(ref) else ''
    return f'background-color: {color}'


st.set_page_config(layout="wide")

if 'token' not in st.session_state:
    st.session_state['token'] = ''

with st.sidebar:
    tenant = st.secrets["VANTAGE_TENANT_ID"]
    client_id = st.secrets["VANTAGE_CLIENT_ID"]
    secret_id = st.secrets["VANTAGE_SECRET_ID"]
    st.image("abbyy.png")
    st.title("Vantage Login")
    tenant = st.text_input("Tenant", tenant ,disabled=True)
    username = st.text_input("Email")
    password = st.text_input("Password",type="password")
    st.button("Login", on_click=login_vantage("", tenant,username,password,client_id,secret_id))

st.session_state['token'] = 'teste'

if  st.session_state["token"] != "":

    # Initialize APP
    st.title("ABBYY Vantage License Monitor")
    st.write("Author: marcelo.araujo@abbyy.com")
    
    
    st.header("Connecting to Tenants")
    tenants = st.secrets["VANTAGE_TENANTS"]    
    lic_data, usr_data = get_data(tenants)
    lic_df = read_data_lic(lic_data)
    usr_df = read_data_usr(usr_data)
    st.write("")


    df_totals_tenant = lic_df.groupby(["tenant_name",'skills_name']).agg({'skills_counter':sum, 'skills_limit':sum, 'skills_remain': sum}).reset_index()
    df_totals_tenant = df_totals_tenant.sort_values(by=["tenant_name",'skills_name'], ascending=True)
    st.header("Licenses by Tenant")
    tcol1, tcol2 = st.columns(2)
    with tcol1:
        st.dataframe(df_totals_tenant, hide_index=True)

    with tcol2:
        st.bar_chart(df_totals_tenant, x=("tenant_name"), y=("skills_counter","skills_remain"))

    st.header("Licenses by Skill")
    df_totals = lic_df.groupby("skills_name").agg({'skills_counter':sum, 'skills_limit':sum, 'skills_remain': sum}).reset_index()
    df_totals = df_totals.sort_values(by='skills_remain', ascending=True)
    vcol1, vcol2 = st.columns(2)
    with vcol1:
        st.dataframe(df_totals, hide_index=True)
    with vcol2:
        st.bar_chart(df_totals, x="skills_name", y=("skills_counter","skills_remain"))

    st.header("Licenses database")
    styled_df = lic_df.style.applymap(lambda x: highlight_less_than(x,1000),subset=['skills_remain'])
    st.dataframe(styled_df, hide_index=True,use_container_width=True)

    df_user_tenant = usr_df.drop_duplicates(subset='email')
    df_user_tenant = df_user_tenant.groupby("tenant")['email'].count().reset_index()
    df_user_tenant.columns = ["tenant", "count"]
    
    df_roles_tenant = usr_df.groupby(["tenant", "role"]).agg({'email': 'count'}).reset_index().rename(columns={"email":"count"})
    
    #df_totals_tenant = df_totals_tenant.sort_values(by=["tenant_name",'skills_name'], ascending=True)
  
    st.header("Users by Tenant")
    ucol1, ucol2 = st.columns(2)
    with ucol1:
        st.dataframe(df_user_tenant, hide_index=True)
    with ucol2:
        st.bar_chart(df_user_tenant, x="tenant", y="count")

    st.header("Roles by Tenant")
    rcol1, rcol2 = st.columns(2)
    with rcol1:
        st.dataframe(df_roles_tenant, hide_index=True)
    with rcol2:
        st.bar_chart(df_roles_tenant, x="tenant", y="count")

    st.header("Users & Roles database")
    st.dataframe(usr_df, hide_index=True,use_container_width=True)
    


