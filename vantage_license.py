

import streamlit as st
import pandas as pd
import json
import requests
import numpy as np
import datetime
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from io import StringIO
from dateutil.relativedelta import relativedelta


###   streamlit run C:\Users\marceloraraujo\Documents\vantage_license\vantage-license\vantage_license.py

# Login Vantage
def login_vantage(tenant_name,tenant_id,username,password,client_id,client_secret,register):
    if username != "" and password != "":
        url = st.secrets["VANTAGE_BASE_URL"] + "auth2/" + tenant_id + "/connect/token"
        payload = 'grant_type=password&scope=openid permissions global.wildcard&username='+username+'&password='+password+'&client_id='+client_id+'&client_secret='+client_secret
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        response = requests.request("POST", url, headers=headers, data=payload)
        obj = json.loads(response.text)
        if "access_token" in obj:
            accessToken = "Bearer " + str(obj["access_token"])
            st.session_state['token'] = accessToken
            st.session_state['status'] = "🟢 Logged in " + tenant_name
            if register==True:
                st.markdown(st.session_state['status'], unsafe_allow_html=True)
            return(accessToken)
        else:
            st.session_state['token'] = ""
            st.session_state['status'] = "🔴 Error to logging in " + tenant_name
            if register==True:
                st.markdown(st.session_state['status'], unsafe_allow_html=True)
            return("Error to login!")
        
def login_vantage_client(tenant_id,client_id,client_secret):

    url = st.secrets["VANTAGE_BASE_URL"] + "auth2/" + tenant_id + "/connect/token"
    payload = 'grant_type=client_credentials&scope=openid permissions global.wildcard&client_id='+client_id+'&client_secret='+client_secret
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    response = requests.request("POST", url, headers=headers, data=payload)
    obj = json.loads(response.text)
    accessToken = "Bearer " + str(obj["access_token"])
    return(accessToken)

def get_skill_name(skill,tenant_name):
    tenant_list = json.loads(tenants)
    for tenant in tenant_list:
        if tenant['tenant_name'] == tenant_name:
            #accessToken = login_vantage(tenant['tenant_name'], tenant["tenant_id"], tenant["user"], tenant["pwd"], tenant["client_id"], tenant["client_secret"], False)       
            accessToken = login_vantage_client( tenant["tenant_id"],  tenant["client_id"], tenant["client_secret"])       
            if accessToken.startswith("Bearer"):
                url = st.secrets["VANTAGE_BASE_URL"] + "api/publicapi/v1/skills/"+skill
                headers = {'Authorization': accessToken, 'Accept': '*/*'}
                payload = {}
                response = requests.request("GET", url, headers=headers, data=payload)
                if response.status_code == 200:
                    obj = json.loads(response.text)
                    return obj['name']
                else:
                    return skill

def get_skill_id(skill_name,tenant_name):
    tenant_id, client_id, client_secret = get_tenant_data(tenant_name)
    accessToken = login_vantage_client(tenant_id, client_id, client_secret)       
    url = st.secrets["VANTAGE_BASE_URL"] + "api/publicapi/v1/skills"
    headers = {'Authorization': accessToken, 'Accept': 'text/plain'}
    payload = {}
    response = requests.request("GET", url, headers=headers, data=payload)
    if response.status_code == 200:
        data = json.loads(response.text)
        skill =  [item["id"] for item in data if item["name"] == skill_name]
        print("SKILL ID: " + skill[0])
        return skill[0]
                    
@st.cache_data            
def replaceSkillName(df):
    
    skill_cache = {}
    
    def get_skill_name_cached(row):
        skill_id=row['skill']
        tenant_name=row['tenant_name']
        cache_key = (skill_id, tenant_name)
        if cache_key in skill_cache:
            return skill_cache[cache_key]
        
        skill_name = get_skill_name(skill_id,tenant_name)
        skill_cache[cache_key] = skill_name
        return skill_name
    
    df['skill_name'] = df.apply(get_skill_name_cached, axis=1)
    skill_col_index = df.columns.get_loc('skill')
    df = df.drop(columns=['skill'])
    cols = list(df.columns)
    cols.insert(skill_col_index, cols.pop(cols.index('skill_name')))
    df = df[cols]
    
    return df

def read_data_cons(json_cons):

    data_list = json.loads(json_cons)
    tenants = []
    transactions = []
    createds = []
    skills = []
    pages = []
    docs = []
    for tenant_data in data_list:
            tenant_name = tenant_data['tenant']
            for item in tenant_data['data']:
                transaction= item["transactionId"]
                created= item["createTimeUtc"]
                skill= item["skillId"]
                page= item["pageCount"]
                doc= item["documentCount"]

                tenants.append(tenant_name)
                transactions.append(transaction)
                createds.append(created)
                skills.append(skill)
                pages.append(page)
                docs.append(doc)

    df = pd.DataFrame({
        'tenant_name': tenants,
        'transaction': transactions,
        'created': createds,
        'skill': skills,
        'page': pages,
        'doc': docs
    })
    
    return df

def read_data_usr(json_array):
    data_list = json.loads(json_array)
    tenant_names = []
    user_names = []
    user_emails = []
    user_roles = []
    for data in data_list:
        tenant_name = data['tenant']
        for user in data['data']['items']:
            user_name = user['displayName']
            user_email = user['email']
            for role in user['roles']:
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
    skill_types = []
    skill_counters = []
    skill_limits = []
    skill_remains = []
    
    for data in data_list:
        tenant_name = data['tenant']
        serial_number = data['data']['serialNumber']
        expire_date = data['data']['expireDate']
        
        for skill in data['data']['skills']:
            if skill['name'] == "General":
                skill_type = "Core Cognitive" 
            elif skill['name'] == "ABBYY.Ocr": 
                skill_type = "Ocr Skill"
            else: 
                skill_type = "Production Skill"

            tenant_names.append(tenant_name)
            serial_numbers.append(serial_number)
            expire_dates.append(expire_date)
            skill_names.append(skill['name'])
            skill_types.append(skill_type)
            skill_counters.append(skill['counter'])
            skill_limits.append(skill['limit'])
            skill_remains.append(skill['limit'] - skill['counter'])
    
    df = pd.DataFrame({
        'tenant_name': tenant_names,
        'serialNumber': serial_numbers,
        'expireDate': expire_dates,
        'skills_name': skill_names,
        'skills_type': skill_types,
        'skills_counter': skill_counters,
        'skills_limit': skill_limits,
        'skills_remain': skill_remains
    })
    
    return df

@st.cache_data
def get_data(tenants):

    tenant_list = json.loads(tenants)
    lic_data = []
    usr_data = []
    cons_data = []

    for item in tenant_list:
        accessToken = login_vantage(item['tenant_name'], item["tenant_id"], item["user"], item["pwd"], item["client_id"], item["client_secret"], True)
        #accessToken = login_vantage_client( item["tenant_id"],  item["client_id"], item["client_secret"])       
        if accessToken.startswith("Bearer"):
            #read license
            url = st.secrets["VANTAGE_BASE_URL"] + "api/workspace/subscriptions/me"
            headers = {'Authorization': accessToken, 'Accept': '*/*'}
            payload = {}
            response = requests.request("GET", url, headers=headers, data=payload)
            obj = json.loads(response.text)
            lic_data.append({"tenant": item["tenant_name"], "data": obj})
            #read users
            url = st.secrets["VANTAGE_BASE_URL"] + "api/adminapi2/v1/tenants/"+item["tenant_id"]+"/users?includeRoles=true"
            headers = {'Authorization': accessToken, 'Accept': '*/*'}
            payload = {}
            response = requests.request("GET", url, headers=headers, data=payload)
            obj = json.loads(response.text)
            usr_data.append({"tenant": item["tenant_name"], "data": obj})
            #read completed transactions loop using Limit and offset
            all_items = []
            offset = 0
            limit = 1000
            total_items_retrieved = 0
            while True:
                url = st.secrets["VANTAGE_BASE_URL"] + "api/publicapi/v1/transactions/completed?offset="+str(offset)+"&Limit="+str(limit)
                headers = {'Authorization': accessToken, 'Accept': '*/*'}
                payload = {}
                response = requests.request("GET", url, headers=headers, data=payload)
                if response.status_code != 200:
                    break
                obj = response.json()
                items = obj.get('items',[])
                all_items.extend(items)
                total_items_retrieved += len(items)
                total_item_count = obj.get('totalItemCount', 0)
                print("total_items_retrieved:" + str(total_items_retrieved) + " - total_item_count:" + str(total_item_count))
                if total_items_retrieved >= total_item_count:
                    break
                offset += limit
            cons_data.append({"tenant": item["tenant_name"], "data": all_items})

    json_lic = json.dumps(lic_data)
    json_usr = json.dumps(usr_data)
    json_cons = json.dumps(cons_data)

    return json_lic, json_usr, json_cons

def highlight_less_than(val,ref):
    color = 'red' if int(val) < int(ref) else ''
    return f'background-color: {color}'

def get_tenant_names(): 
    tenant_list =  json.loads(st.secrets["VANTAGE_TENANTS"])
    tenants = []
    for item in tenant_list:
        tenants.append(item['tenant_name'])
    return tenants

def get_tenant_data(tenant):
    tenant_list =  json.loads(st.secrets["VANTAGE_TENANTS"])
    tenant_id, client_id, client_secret = "", "",""
    for item in tenant_list:
        if item['tenant_name'] == tenant:
            tenant_id = item['tenant_id']
            client_id = item['client_id']
            client_secret = item['client_secret']
            break
    return tenant_id, client_id, client_secret

def get_proc_skill_names(tenant_name):
    tenant_id, client_id, client_secret = get_tenant_data(tenant_name)
    accessToken = login_vantage_client(tenant_id,client_id,client_secret)
    url = st.secrets["VANTAGE_BASE_URL"] + "api/publicapi/v1/skills"
    headers = {'Authorization': accessToken, 'Accept': 'text/plain'}
    payload = {}
    response = requests.request("GET", url, headers=headers, data=payload)
    data = json.loads(response.text)
    filtered_data = [ item["name"] for item in data if item["type"] == "Process"]
    return(filtered_data)

def get_transaction_data(accessToken, start_date, end_date):
    url = st.secrets["VANTAGE_BASE_URL"] + "api/reporting/v1/transaction-steps?startDate="+start_date.strftime('%Y-%m-%dT%H:%M:%S')+"&endDate="+end_date.strftime('%Y-%m-%dT%H:%M:%S')
    headers = {'Authorization': accessToken, 'Accept': '*/*'}
    payload = {}
    response = requests.request("GET", url, headers=headers, data=payload)
    if response.status_code == 200:
        csv_data = StringIO(response.text)
        df = pd.read_csv(csv_data)
        return df
    else:
        print("Erro ao acessar a API")
        data=[]
        df =pd.DataFrame(data)
        return df

def get_field_data(tenant_name, process_skill_name):
    date_14_days_ago = datetime.now() - relativedelta(days=13)
    print(date_14_days_ago)
    formatted_date = date_14_days_ago.strftime('%Y-%m-%dT%H:%M:%SZ')
    process_skill_id = get_skill_id(process_skill_name, tenant_name)
    tenant_id, client_id, client_secret = get_tenant_data(tenant_name)
    accessToken = login_vantage_client(tenant_id, client_id, client_secret)
    url = st.secrets["VANTAGE_BASE_URL"] + "api/reporting/v1/qa/process-skills/fields?startDate="+formatted_date+"&processSkillId="+process_skill_id
    headers = {'Authorization': accessToken, 'Accept': '*/*'}
    payload = {}
    response = requests.request("GET", url, headers=headers, data=payload)
    print("URL: "+ url)
    print("accessToken: "+ accessToken)
    print("response: "+ response.text)
    if response.status_code == 200:
        csv_data = StringIO(response.text)
        print(response.text)
        df = pd.read_csv(csv_data)
        return df
    else:
        print("Erro ao acessar a API")
        data=[]
        df =pd.DataFrame(data)
        return df

def get_avg_pages_tenant(tenant):
    return st.session_state['tenant_avg_pages'].get(tenant, 1)

@st.cache_data
def get_transactions(tenant, start_date, end_date, step_days):
    tenant_list = json.loads(st.secrets["VANTAGE_TENANTS"])
    for item in tenant_list:
        if item['tenant_name']==tenant:
           #accessToken = login_vantage(item['tenant_name'], item["tenant_id"], item["user"], item["pwd"], item["client_id"], item["client_secret"], False) 
           accessToken = login_vantage_client( item["tenant_id"],  item["client_id"], item["client_secret"])       
           break
    if accessToken.startswith("Bearer"):
        all_data = []
        current_start = start_date
        while current_start < end_date:
            current_end = current_start + relativedelta(days=step_days)
            if current_end > end_date:
                current_end = end_date
            df = get_transaction_data(accessToken, current_start, current_end)
            if df.shape[0]>0:
                all_data.append(df)
            #get_data(current_start, current_end)
            current_start = current_end
        if all_data!=[]:
            final_df = pd.concat(all_data,ignore_index=True)
            return final_df
    return None

st.set_page_config(layout="wide")

if 'token' not in st.session_state:
    st.session_state['token'] = ""
if 'status' not in st.session_state:
    st.session_state['status'] = "🟠 Disconnected "
if 'tenant_avg_pages' not in st.session_state:
    st.session_state['tenant_avg_pages'] = ""

with st.sidebar:
    st.image("abbyy.png")
    st.title("Vantage Login")
    tenant = st.selectbox("Tenant", get_tenant_names())
    username = st.text_input("Email")
    password = st.text_input("Password",type="password")
    tenant_id, client_id, client_secret = get_tenant_data(tenant)
    st.button("Login", on_click=login_vantage, args=[tenant,tenant_id,username,password,client_id,client_secret,False] )
    status = st.text_input("Status", value=st.session_state['status'], disabled=True)

# Initialize APP
st.title("ABBYY Vantage License Monitor")
st.write("Author: marcelo.araujo@abbyy.com")

if  st.session_state["token"] != "":

    conn_tab, cons_tab, lic_tab, user_tab, trans_tb, field_tb = st.tabs(["Connections", "License Consumption", "Subscription Data", "Users Report", "Transaction History", "Field Accuracy"])

    with conn_tab: 
        tenants = st.secrets["VANTAGE_TENANTS"]   
        lic_data, usr_data, cons_data = get_data(tenants)
        cons_df = read_data_cons(cons_data)
        cons_df = replaceSkillName(cons_df)
        lic_df = read_data_lic(lic_data)
        usr_df = read_data_usr(usr_data)

    with cons_tab: 
 
        total_trans = cons_df.shape[0]
        total_pages =  cons_df['page'].sum()
        total_docs =  cons_df['doc'].sum()
        value_counts = cons_df['page'].value_counts()
        values = value_counts.index.to_numpy()
        weights = value_counts.to_numpy()
        print("values " + str(values))
        print("weights " + str(weights))
        
        pages_average = np.average(values, weights=weights)
        st.session_state['tenant_avg_pages'] = pages_average

        st.header("🎯 Performance Measures") 
        cm1,cm2,cm3,cm4 = st.columns(4)
        with cm1:
            st.metric("Total Transactions", total_trans, help="Total of transactions last 14 days.")
        with cm2:
            st.metric("Total Documents", total_docs, help="Total of documents processed last 14 days.")
        with cm3:
            st.metric("Total Pages", total_pages, help="Total of documents processed last 14 days.")
        with cm4:
            st.metric("Average Pages by Transaction", "{:.2f}".format(pages_average), help="Weighted Average of the number of pages processed by the transactions during the last 14 days. " )
            

        st.header("Consumption by Tenant last 14 Days")
        df_cons_tenant = cons_df.groupby(["tenant_name"]).agg(transaction=('transaction', 'count'),page=('page','sum'),doc=('doc','sum')).reset_index()
        df_cons_tenant.columns = ["Tenant", "Transactions", "Pages Used", "Documents"]
        df_cons_tenant['Average Pages Transac'] = (df_cons_tenant['Pages Used'] / df_cons_tenant['Transactions'])
        df_cons_tenant['Average Pages Transac'] = df_cons_tenant['Average Pages Transac'].round(2)
        df_cons_tenant = df_cons_tenant.sort_values(by=["Tenant"], ascending=True)

        skill_avg_pages_dict = df_cons_tenant.groupby('Tenant')['Average Pages Transac'].mean().round(2).to_dict()
        st.session_state['tenant_avg_pages'] = skill_avg_pages_dict

        ctcol1, ctcol2 = st.columns(2)
        with ctcol1:
            st.dataframe(df_cons_tenant, hide_index=True)
        with ctcol2:
            st.bar_chart(df_cons_tenant, x=("Tenant"), y=("Pages Used", "Documents"), stack=False)

        st.header("Consumption by Skill last 14 Days")
        df_cons_skill = cons_df.groupby(["tenant_name","skill_name"]).agg(transaction=('transaction', 'count'),page=('page','sum'),doc=('doc','sum')).reset_index()
        df_cons_skill.columns = ["Tenant", "Skill Name", "Transactions", "Pages Used", "Documents"]
        df_cons_skill = df_cons_skill.sort_values(by=["Tenant", "Pages Used"], ascending=False)
        
        tenants = df_cons_skill['Tenant'].unique()
        for tenant in tenants:
            st.write("Tenant: "+ tenant)
            tenant_df = df_cons_skill[df_cons_skill['Tenant'] == tenant]
            cscol1, cscol2 = st.columns(2)
            with cscol1:
                st.dataframe(tenant_df, hide_index=True)
            with cscol2:
                st.bar_chart(tenant_df, x=("Skill Name"), y=("Pages Used", "Documents"), stack=False,  horizontal=True, x_label="Pages")

        st.header("Consumption Data")
        cons_df.columns = ["Tenant", "Transaction", "Created", "Skill Name", "Pages Used", "Document"]
        st.dataframe(cons_df, hide_index=True, use_container_width=True)
        
    with lic_tab:  

        st.header("📈 Licenses by Type")
        df_totals_tenant = lic_df.groupby(["tenant_name",'skills_type']).agg({'skills_counter':sum, 'skills_limit':sum, 'skills_remain': sum}).reset_index()
        df_totals_tenant.columns = ["Tenant", "Type", "Pages Used", "Page Limit", "Pages Left"]
        df_totals_tenant = df_totals_tenant.sort_values(by=["Tenant",'Type'], ascending=True)
        tcol1, tcol2 = st.columns(2)
        with tcol1:
            st.caption("Real-time information from the subscription page.")
            st.dataframe(df_totals_tenant, hide_index=True)
        with tcol2:
            st.bar_chart(df_totals_tenant, x=("Type"), y=("Pages Used","Pages Left"))
            

        # Licenses by Tenant Dash
        st.header("📈 Licenses by Tenant")
        st.caption("Real-time information from the subscription page.")
        df_totals = lic_df.groupby(["tenant_name",'skills_type']).agg({'skills_counter':sum, 'skills_limit':sum, 'skills_remain': sum}).reset_index()
        df_totals.columns = ["Tenant", "Type", "Pages Used", "Page Limit", "Pages Left"]
        df_totals = df_totals.sort_values(by="Pages Used", ascending=True)
        tenants = df_cons_skill['Tenant'].unique()
        for tenant in tenants:
            st.write("Tenant: "+ tenant)
            tenant_df = df_totals[df_totals['Tenant'] == tenant]
            vcol1, vcol2 = st.columns(2)
            with vcol1:
                st.dataframe(tenant_df, hide_index=True)
            with vcol2:
                st.bar_chart(tenant_df, x="Type", y=("Pages Used","Pages Left"))

        # Licenses complete data
        st.header("Licenses Data")
        lic_df.columns = ["Tenant", "Serial", "Expire Date", "Skill", "Type", "Pages Used", "Page Limit", "Pages Left"]
        styled_df = lic_df.style.applymap(lambda x: highlight_less_than(x,1000),subset=["Pages Left"])
        st.dataframe(styled_df, hide_index=True, use_container_width=True)
        st.markdown('<span style="color: red;">(*) Less than 1000 pages left</span>',unsafe_allow_html=True)
        st.header("")

    with user_tab: 

        st.header("🙋🏻‍♂️ Users by Tenant")
        st.caption("Total number of users.")
        df_user_tenant = usr_df.drop_duplicates(subset='email')
        df_user_tenant = df_user_tenant.groupby("tenant")['email'].count().reset_index()
        df_user_tenant.columns = ["Tenant", "Users Count"]
        ucol1, ucol2 = st.columns([0.3,0.7])
        with ucol1:
            st.dataframe(df_user_tenant, hide_index=True)
        with ucol2:
            st.bar_chart(df_user_tenant, x="Tenant", y="Users Count")

        # Users by Roles Dash
        st.header("🙋🏻‍♂️ Users by Roles")
        st.caption("Total number of users by Roles.")
        df_roles_tenant = usr_df.groupby(["tenant", "role"]).agg({'email': 'count'}).reset_index().rename(columns={"email":"count"})
        df_roles_tenant.columns = ["Tenant", "Role" ,"Users Count"]
        
        tenants = df_cons_skill['Tenant'].unique()
        for tenant in tenants:
            st.write("Tenant: " + tenant)
            tenant_df = df_roles_tenant[df_roles_tenant['Tenant'] == tenant]
            rcol1, rcol2 = st.columns([0.4,0.6])
            with rcol1:
                st.dataframe(tenant_df, hide_index=True)
            with rcol2:
                st.bar_chart(tenant_df, x="Role", y="Users Count")

        # Uses complete data 
        st.header("Users Data")
        usr_df.columns = ["Tenant", "User Name", "E-mail", "Role"]
        st.dataframe(usr_df, hide_index=True,use_container_width=True)
        
    with trans_tb:

        c1,c2,c3,c4 = st.columns(4)
        with c1:
            tenant_trans = st.selectbox("Tenant for Report", get_tenant_names())
        with c2:
            start_date = st.date_input(label="Start Date", value=datetime.today() - relativedelta(days=5), min_value=datetime.today() - relativedelta(days=365), max_value=datetime.today() )
        with c3:
            end_date = st.date_input(label="End Date", value=datetime.today(), min_value=datetime.today() - relativedelta(days=365), max_value=datetime.today())
        with c4:
            step_days = st.slider("Split requests in N Days", min_value=1, max_value=30, step=1, value=5, help="The request will be splited N times based on step value")
        
        with st.spinner('Be patient, it may take some minutes!!!'):
            final_df = get_transactions(tenant_trans, start_date, end_date, step_days)

        if final_df is None:
            st.write("No transactions founded to selected period. ")
        else:
            transactions_df = final_df[final_df['StepName'] == "Input"]
            transactions_df['StartedUtc'] = pd.to_datetime(transactions_df['StartedUtc'], format='%m/%d/%Y %H:%M:%S')
            transactions_df["Date"] = transactions_df['StartedUtc'].dt.strftime("%Y-%m")#to_period('M')
            
            months = relativedelta(end_date, start_date).months + (relativedelta(end_date, start_date).years * 12) +1
            total_trans = transactions_df.shape[0]
            avg_pages_tenant = get_avg_pages_tenant(tenant_trans)
            estimate_pages = round(total_trans * avg_pages_tenant)
            trans_by_months = round(total_trans / months)
            skills_used =  transactions_df['SkillName'].nunique()
            stp_df = transactions_df[transactions_df['ManualReviewOperatorName'] != ""]
            transactions_with_mr = stp_df['TransactionId'].nunique()
            stp_average = str(  "{:.2f}".format( 100 - (transactions_with_mr * 100) / total_trans) ) +"%"
            st.header("🎯 Performance Measures") 
            m1,m2,m3,m4 = st.columns(4)
            with m1:
                st.metric("Total Transactions", total_trans, help="Total of transactions during the period.")
            with m2:
                st.metric("Average Transactions Month", trans_by_months, help="Average of transactions by month during the period.")
            with m3:
                st.metric("Estimated Number of Pages (*)", estimate_pages, help="Estimated number of pages consumed based on average consumption over the last 14 days")
            with m4:
                st.metric("STP Average", stp_average, help="STP - Straight-through processing means transactions with out Manual Review Step")

            st.header("Transactions by Month")
            tmcol1, tmcol2 = st.columns([0.3,0.7])
            with tmcol1:
                transactions_date_df = transactions_df.groupby(["Date"]).size().reset_index(name="count")
                transactions_date_df = transactions_date_df.sort_values(by=["Date"], ascending=True)
                st.dataframe(transactions_date_df, hide_index=True)
            with tmcol2:
                st.bar_chart(transactions_date_df, x="Date", y="count")
            
            st.header("Transactions by Skill")
            tscol1, tscol2 = st.columns([0.3,0.7])
            with tscol1:
                transactions_skill_df = transactions_df.groupby([ "SkillName"]).size().reset_index(name="count")
                transactions_skill_df = transactions_skill_df.sort_values(by=["count"], ascending=False)
                st.dataframe(transactions_skill_df, hide_index=True)
            with tscol2:
                st.bar_chart(transactions_skill_df, x="SkillName", y="count")
        
            st.header("Transactions Data")
            restricted = ["SkillName", "TransactionId", "StepName", "StepType", "ManualReviewOperatorName", "ManualReviewOperatorEmail", "StartedUtc", "CompletedUtc", "Duration", "document_SourceFileName" ]
            df_restricted = final_df[restricted]
            st.dataframe(df_restricted, hide_index=True,use_container_width=True)

    with field_tb:
         
        f1,f2,f3 = st.columns(3)
        
        with f1:
            tenant_field = st.selectbox("Tenant for Accuracy Report", get_tenant_names())
        with f2:
            process_skill_field = st.selectbox("Skill for Accuracy Report", get_proc_skill_names(tenant_field))
   
        with st.spinner('Be patient, it may take some minutes!!!'):
            fields_df = get_field_data(tenant_field, process_skill_field)

        if fields_df.empty:
            st.warning("📌There is no data for this process skill. Please select another one with processing in the las 14 days.")
        else:
            st.write("")
            st.caption("The data below is based only on the last 14 days.")
            fg1,fg2 = st.columns(2)
            with fg1:
                # Donut Chart for Accuracy
                total_fields = fields_df.shape[0]
                correct_fields = fields_df[fields_df['Correct'] == True].shape[0]
                accuracy_percentage = (correct_fields / total_fields) * 100
                st.subheader(f"🎯 Overall Field Accuracy: {accuracy_percentage:.2f}%")
                st.caption("This chart shows the percentage of fields with no modification on Manual Review.")
                fig_accuracy = go.Figure(data=[go.Pie(
                    labels=['Correct', 'Incorrect'],
                    values=[correct_fields, total_fields - correct_fields],
                    hole=0.5,
                    marker_colors=['#1f77b4', '#aec7e8']
                )])
                #fig_accuracy.update_layout(title_text=f"Overall Accuracy: {accuracy_percentage:.2f}%")
                st.plotly_chart(fig_accuracy)
                
            with fg2:
                # Analysis 2: Manual vs. Automatic Review Distribution
                manual_review_counts = fields_df['HasManualReview'].value_counts(normalize=True) * 100
                manual_review_percentage = manual_review_counts[True] if True in manual_review_counts.index else 0
                st.subheader(f"✍️ Manual Review Distribution: {manual_review_percentage:.2f}% ")
                st.caption("This chart shows the percentage of fields reviewed manually versus automatically. Process with Manual Review Stage.")
                fig_review = px.bar(
                    manual_review_counts,
                    x=manual_review_counts.index,
                    y=manual_review_counts.values,
                    labels={'x': 'Manual Review', 'y': 'Percentage'},
                    color=manual_review_counts.index,
                    color_discrete_sequence=['#1f77b4', '#aec7e8']
                )
                fig_review.update_layout(yaxis_title="Percentage (%)", xaxis_title="Review Type")
                st.plotly_chart(fig_review)
                st.write("")

            fg3,fg4 = st.columns(2)
            with fg3:
                # Analysis 3: Top 10 Fields Needing Training (Percentage)
                st.subheader("🔧 Top 10 Fields Needing Training")
                st.caption("Fields with higher correction percentages represent opportunities for training improvements.")
                if 'Correct' in fields_df.columns and 'FieldName' in fields_df.columns:
                    fields_corrected = fields_df[fields_df['Correct'] == False]['FieldName'].value_counts(normalize=True) * 100
                    fig_corrected = px.bar(
                        fields_corrected.head(10),
                        y=fields_corrected.head(10).index,
                        x=fields_corrected.head(10).values,
                        orientation='h',
                        labels={'x': 'Correction Percentage (%)', 'y': 'Field Name'},
                        color=fields_corrected.head(10).values,
                        color_continuous_scale="Blues"
                    )
                    fig_corrected.update_layout(title="Top 10 Fields Needing Training", xaxis_title="Correction Percentage (%)")
                    st.plotly_chart(fig_corrected)
                
            with fg4:

                # Analysis 4: Top 10 Undetected Fields (Percentage)
                if 'NotDetected' in fields_df.columns and 'FieldName' in fields_df.columns:
                    undetected_fields = fields_df[fields_df['NotDetected'] == True]['FieldName'].value_counts(normalize=True).head(10) * 100
                    
                    if not undetected_fields.empty:
                        st.subheader("🚫 Top 10 Undetected Fields")
                        st.caption("Fields with a high undetected rate may require further recognition improvements or additional training.")
                        df_undetected = undetected_fields.reset_index()
                        df_undetected.columns = ['FieldName', 'Undetected Percentage']

                        fig_undetected = px.bar(
                            df_undetected,
                            y='FieldName',
                            x='Undetected Percentage',
                            orientation='h',
                            labels={'Undetected Percentage': 'Undetected Percentage (%)', 'FieldName': 'Field Name'},
                            color='Undetected Percentage',
                            color_continuous_scale="Blues"
                        )
                        fig_undetected.update_layout(title="Top 10 Undetected Fields", xaxis_title="Undetected Percentage (%)")
                        st.plotly_chart(fig_undetected)
                        
                    else:
                        st.info("No undetected fields found.")
                else:
                    st.info("Undetected fields data is not available.")
                    
    
            
