import streamlit as st
from supabase import create_client
import os
import time

# 1. Config
st.set_page_config(page_title="86 Items", page_icon="🍔")

# 2. Connect to Supabase
# In Docker, we read from os.environ, not st.secrets
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

if not url or not key:
    st.error("❌ Missing Supabase Credentials in environment variables.")
    st.stop()

@st.cache_resource
def init_connection():
    return create_client(url, key)

supabase = init_connection()

def login_form():
    st.title("🔒 Login")

    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Sign In")

        if submit:
            try:
                response = supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })

                st.session_state["user"] = response.user
                st.success("Login successful!")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Login failed: {e}")

def logout():
    supabase.auth.sign_out()
    st.session_state["user"] = None
    st.rerun()


def main_dashboard():
    user = st.session_state["user"]

# 3. Handle 'Restock' Action
    if "mark_stocked" in st.session_state:
        try:
            supabase.table("Eighty Sixed").update({"resolved": 'True', "resolved_at": "now()", "resolved_by": user.email}).eq("id", st.session_state["mark_stocked"]).execute()
            st.success("Item restocked!")
            del st.session_state["mark_stocked"]
        except Exception as e:
            st.error(f"Error: {e}")

# 4. Fetch Data
    response = supabase.table("Eighty Sixed").select("*").eq("resolved", 'False').order("location", desc=True).execute()
    items = response.data

# 5. Display Table
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

if "user" not in st.session_state:
    st.session_state["user"] = None

if st.session_state['user']:
    main_dashboard()
else:
    login_form()
