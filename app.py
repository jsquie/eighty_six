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

# --- 2. Handle Auth Flow ---
def handle_auth():
    # Check if we are returning from Google with an auth code
    # Streamlit now uses st.query_params (replacing experimental_get_query_params)
    query_params = st.query_params
    auth_code = query_params.get("code")

    if auth_code:
        try:
            # Exchange the code for a session
            st.write("exchanging for a session")
            response = supabase.auth.exchange_code_for_session({"auth_code": auth_code})
            st.session_state["session"] = response.session
            st.session_state["user"] = response.user
            
            # Clear the code from the URL so a refresh doesn't trigger an error
            st.query_params.clear()
            st.rerun()
        except Exception as e:
            st.error(f"Login failed: {e}")

def login_form():
    st.title("Streamlit + Supabase OAuth")

    # Run the auth handler at the start of every run
    handle_auth()

    st.write("I'm here")

    # Check if user is logged in via session state
    if "session" in st.session_state:
        user_email = st.session_state["user"].email
        st.success(f"✅ Logged in as {user_email}")
        
        if st.button("Sign out"):
            supabase.auth.sign_out()
            st.session_state.clear()
            st.rerun()
    else:
        st.warning("Please log in to continue.")
        
        # --- Generate the Google OAuth URL ---
        # dynamic_redirect_url should match your Streamlit app's URL
        # For local dev, this is usually http://localhost:8501
        redirect_url = "https://qed-eighty-sixed.streamlit.app" 
        
        data = supabase.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {
                "redirect_to": redirect_url
            }
        })

        st.login_button("Sign in with Google", provider="google")


def logout():
    supabase.auth.sign_out()
    st.session_state["user"] = None
    st.rerun()


def main_dashboard():
    user = st.session_state["user"]

    st.title("QED Coffee - 86d")

    st.write(f"Youre logged in as: {st.session_state['user'].user_metadata['name']}")


    options_list = ['Location', 'Items', 'Created At', 'Reported By']

    sort_by = st.selectbox(
        "Sort By",
        options_list,
        index=0
    )


# 3. Handle 'Restock' Action
    if "mark_stocked" in st.session_state:
        try:
            supabase.table("Eighty Sixed").update({"resolved": 'True', "resolved_at": "now()", "resolved_by": user.email}).eq("id", st.session_state["mark_stocked"]).execute()
            st.success("Item restocked!")
            del st.session_state["mark_stocked"]
        except Exception as e:
            st.error(f"Error: {e}")

# 4. Fetch Data
    if sort_by == "Items":
        response = supabase.table("Eighty Sixed").select("*").eq("resolved", 'False').order("item_name", desc=True).execute()
    elif sort_by == "Location":
        response = supabase.table("Eighty Sixed").select("*").eq("resolved", 'False').order("location", desc=True).execute()
    elif sort_by == "Created At":
        response = supabase.table("Eighty Sixed").select("*").eq("resolved", 'False').order("created_at", desc=True).execute()
    else:
        response = supabase.table("Eighty Sixed").select("*").eq("resolved", 'False').order("created_by", desc=True).execute()

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
