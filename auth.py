# # import os

# # import requests
# # from dotenv import load_dotenv
# # from msal import ConfidentialClientApplication

# # load_dotenv()

# # CLIENT_ID = os.getenv("CLIENT_ID")
# # CLIENT_SECRET = os.getenv("CLIENT_SECRET")
# # TENANT_ID = os.getenv("TENANT_ID")
# # REDIRECT_URI = os.getenv("REDIRECT_URI")

# import os

# import requests
# import streamlit as st

# from dotenv import load_dotenv
# from msal import ConfidentialClientApplication

# load_dotenv()

# def get_setting(name):

#     # Streamlit Cloud
#     if name in st.secrets:

#         return st.secrets[name]

#     # Local .env
#     return os.getenv(name)


# CLIENT_ID = get_setting("CLIENT_ID")

# CLIENT_SECRET = get_setting("CLIENT_SECRET")

# TENANT_ID = get_setting("TENANT_ID")

# REDIRECT_URI = get_setting("REDIRECT_URI")

# AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"

# SCOPES = [
#     "User.Read",
#     "GroupMember.Read.All"
# ]

# def build_msal_app():
#     return ConfidentialClientApplication(
#         CLIENT_ID,
#         authority=AUTHORITY,
#         client_credential=CLIENT_SECRET
#     )


# def get_auth_url():
#     app = build_msal_app()

#     return app.get_authorization_request_url(
#         scopes=SCOPES,
#         redirect_uri=REDIRECT_URI,
#         prompt="select_account"
#     )
# #-----------------------------------------------------------
# def process_login():

#     import streamlit as st

#     if st.session_state.get("authenticated"):
#         return

#     query_params = st.query_params


#     if "code" not in query_params:
#         return

#     user = authenticate_user(query_params["code"])

#     if user is None:

#         st.error("Microsoft login failed.")

#         st.stop()

#     st.session_state.authenticated = True

#     st.session_state.user_email = user["email"]

#     st.session_state.user_id = user["id"]

#     st.session_state.groups = user["groups"]

#     st.query_params.clear()
# #-----------------------------------------------------------

# def get_token_from_code(code):
#     app = build_msal_app()

#     result = app.acquire_token_by_authorization_code(
#         code=code,
#         scopes=SCOPES,
#         redirect_uri=REDIRECT_URI
#     )

#     return result


# def get_user_info(access_token):

#     response = requests.get(
#         "https://graph.microsoft.com/v1.0/me",
#         headers={
#             "Authorization": f"Bearer {access_token}"
#         }
#     )

#     if response.status_code != 200:
#         return None

#     user = response.json()

#     return {
#         "id": user.get("id"),
#         "display_name": user.get("displayName"),
#         "email": (
#             user.get("mail")
#             or user.get("userPrincipalName")
#         )
#     }

# def get_user_groups(access_token):

#     response = requests.get(
#         "https://graph.microsoft.com/v1.0/me/memberOf?$select=id",
#         headers={
#             "Authorization": f"Bearer {access_token}"
#         }
#     )

#     if response.status_code != 200:
#         return []

#     data = response.json()

#     groups = []

#     for item in data.get("value", []):

#         if "@odata.type" in item:

#             if item["@odata.type"] == "#microsoft.graph.group":

#                 groups.append(item["id"])

#     return groups

# def authenticate_user(code):

#     token = get_token_from_code(code)

#     if "access_token" not in token:
#         return None

#     user = get_user_info(token["access_token"])

#     if user is None:
#         return None

#     groups_response = requests.get(
#         "https://graph.microsoft.com/v1.0/me/memberOf?$select=id",
#         headers={
#             "Authorization": f"Bearer {token['access_token']}"
#         }
#     )

#     groups = []

#     if groups_response.status_code == 200:

#         groups = [
#             g["id"]
#             for g in groups_response.json()["value"]
#         ]

#     user["groups"] = groups

#     return user
