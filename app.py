import streamlit as st
from supabase import create_client
import os

# 1. Config
st.set_page_config(page_title="86 Manager", page_icon="🍔")

# 2. Connect to Supabase
# In Docker, we read from os.environ, not st.secrets
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

if not url or not key:
    st.error("❌ Missing Supabase Credentials in environment variables.")
    st.stop()

supabase = create_client(url, key)

st.title("🍔 86 Manager")

# 3. Handle 'Restock' Action
if "delete_id" in st.session_state:
    try:
        supabase.table("Eighty Sixed").delete().eq("id", st.session_state["delete_id"]).execute()
        st.success("Item restocked!")
        del st.session_state["delete_id"]
    except Exception as e:
        st.error(f"Error: {e}")

# 4. Fetch Data
response = supabase.table("Eighty Sixed").select("*").order("created_at", desc=True).execute()
items = response.data

# 5. Display Table
if not items:
    st.info("✅ Everything is in stock!")
else:
    # Header
    c1, c2, c3 = st.columns([3, 2, 1])
    c1.markdown("### Item")
    c2.markdown("### Reported By")
    c3.markdown("### Action")
    st.divider()

    # Rows
    for item in items:
        c1, c2, c3 = st.columns([3, 2, 1])
        c1.write(f"🚫 **{item['item_name']}**")
        c2.caption(item['created_by'])
        
        # Callback wrapper
        def restock(id_to_remove):
            st.session_state["delete_id"] = id_to_remove
            
        c3.button("Restock", key=item['id'], on_click=restock, args=(item['id'],))
        st.divider()
