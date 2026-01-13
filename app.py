import streamlit as st
from supabase import create_client
import os
import extra_streamlit_components as stx
import time
import datetime

# 1. Config
st.set_page_config(page_title="86 Items", page_icon="🍔")

# 2. Connect to Supabase
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

if not url or not key:
    st.error("❌ Missing Supabase Credentials in environment variables.")
    st.stop()

@st.cache_resource
def init_connection():
    return create_client(url, key)

supabase = init_connection()

# --- 3. Cookie Manager Setup ---
# Initialize directly (no cache) to avoid the widget error
cookie_manager = stx.CookieManager()

# --- 4. Session Management ---
def check_session():
    """Checks for existing cookies and restores session if found."""
    if "user" in st.session_state and st.session_state["user"] is not None:
        return

    time.sleep(0.1)
    
    # .get() reads from the initial load, so it doesn't need unique keys usually
    access_token = cookie_manager.get("sb_access_token")
    refresh_token = cookie_manager.get("sb_refresh_token")

    if access_token and refresh_token:
        try:
            response = supabase.auth.set_session(access_token, refresh_token)
            st.session_state["user"] = response.user
            st.session_state["session"] = response
        except Exception as e:
            # Clean up invalid tokens
            # We add unique keys here just to be safe
            cookie_manager.delete("sb_access_token", key="clean_at")
            cookie_manager.delete("sb_refresh_token", key="clean_rt")

def login_form():
    st.title("Sign In")
    
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Log In")

        if submit_button:
            try:
                response = supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })
                
                st.session_state["session"] = response.session
                st.session_state["user"] = response.user
                
                # FIXED: Added unique 'key' arguments to prevent "multiple elements with same key" error
                expires = datetime.datetime.now() + datetime.timedelta(days=30)
                
                cookie_manager.set("sb_access_token", 
                                 response.session.access_token, 
                                 expires_at=expires, 
                                 key="set_access_token") # <--- Unique Key
                                 
                cookie_manager.set("sb_refresh_token", 
                                 response.session.refresh_token, 
                                 expires_at=expires, 
                                 key="set_refresh_token") # <--- Unique Key
                
                st.success("Logged in successfully!")
                time.sleep(1)
                st.rerun()
                
            except Exception as e:
                st.error(f"Login failed: {e}")

def logout():
    supabase.auth.sign_out()
    st.session_state.clear()
    
    # FIXED: Added unique keys here too
    cookie_manager.delete("sb_access_token", key="delete_access_token")
    cookie_manager.delete("sb_refresh_token", key="delete_refresh_token")
    
    st.rerun()

# --- 5. Main Application ---
def main_dashboard():
    user = st.session_state["user"]

    st.title("QED Coffee - 86d")
    st.write(f"You're logged in as: {user.email}")
    
    if st.button("Sign out"):
        logout()

    options_list = ['Location', 'Items', 'Created At', 'Reported By']
    sort_by = st.selectbox("Sort By", options_list, index=0)

    if "mark_stocked" in st.session_state:
        try:
            supabase.table("Eighty Sixed").update({
                "resolved": 'True', 
                "resolved_at": "now()", 
                "resolved_by": user.email
            }).eq("id", st.session_state["mark_stocked"]).execute()
            
            st.success("Item restocked!")
            del st.session_state["mark_stocked"]
        except Exception as e:
            st.error(f"Error: {e}")

    query = supabase.table("Eighty Sixed").select("*").eq("resolved", 'False')
    
    if sort_by == "Items":
        query = query.order("item_name", desc=True)
    elif sort_by == "Location":
        query = query.order("location", desc=True)
    elif sort_by == "Created At":
        query = query.order("created_at", desc=True)
    else:
        query = query.order("created_by", desc=True)
        
    response = query.execute()
    items = response.data

    if not items:
        st.info("✅ Everything is in stock!")
    else:
        c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
        c1.markdown("#### Location")
        c2.markdown("#### Item")
        c3.markdown("#### Reported By")
        c4.markdown("#### Action")
        st.divider()

        for item in items:
            c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
            c1.write(f"{item['location']}")
            c2.write(f"**{item['item_name']}**")
            c3.caption(item['created_by'])
            
            def restock(id_to_remove):
                st.session_state["mark_stocked"] = id_to_remove
                
            c4.button("Restock", key=item['id'], on_click=restock, args=(item['id'],))
            st.divider()

# --- Entry Point ---
if "user" not in st.session_state:
    st.session_state["user"] = None

check_session()

if st.session_state['user']:
    main_dashboard()
else:
    login_form()
