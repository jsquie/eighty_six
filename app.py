import streamlit as st
from supabase import create_client
import os

# 1. Config
st.set_page_config(page_title="86 Items", page_icon="🍔")

# 2. Connect to Supabase
# In Docker/Streamlit Cloud, we read from os.environ
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

if not url or not key:
    st.error("❌ Missing Supabase Credentials in environment variables.")
    st.stop()

@st.cache_resource
def init_connection():
    return create_client(url, key)

supabase = init_connection()

# --- 2. Authentication Flow (Email + Password) ---
def login_form():
    st.title("Sign In")
    
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Log In")

        if submit_button:
            try:
                # Attempt to sign in with email and password
                response = supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })

                # If successful, store session and reload
                st.session_state["session"] = response.session
                st.session_state["user"] = response.user
                st.success("Logged in successfully!")
                st.rerun()
                
            except Exception as e:
                st.error(f"Login failed: {e}")

def logout():
    supabase.auth.sign_out()
    st.session_state.clear()
    st.rerun()

# --- 3. Main Application ---
def main_dashboard():
    user = st.session_state["user"]

    st.title("QED Coffee - 86d")

    st.write(f"You're logged in as: {user.email}")
    
    if st.button("Sign out"):
        logout()

    options_list = ['Location', 'Items', 'Created At', 'Reported By']

    sort_by = st.selectbox(
        "Sort By",
        options_list,
        index=0
    )

    # Handle 'Restock' Action
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

    # Fetch Data
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

    # Display Table
    if not items:
        st.info("✅ Everything is in stock!")
    else:
        # Header
        c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
        c1.markdown("#### Location")
        c2.markdown("#### Item")
        c3.markdown("#### Reported By")
        c4.markdown("#### Action")
        st.divider()

        # Rows
        for item in items:
            c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
            c1.write(f"{item['location']}")
            c2.write(f"**{item['item_name']}**")
            c3.caption(item['created_by'])
            
            # Callback wrapper
            def restock(id_to_remove):
                st.session_state["mark_stocked"] = id_to_remove
                
            c4.button("Restock", key=item['id'], on_click=restock, args=(item['id'],))
            st.divider()

# --- Entry Point ---
if "user" not in st.session_state:
    st.session_state["user"] = None

if st.session_state['user']:
    main_dashboard()
else:
    login_form()
