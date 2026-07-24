import streamlit as st
import requests
import json
from datetime import datetime
import time
import os

# ---------- CONFIG ----------
API_BASE = os.environ.get("API_BASE_URL", "http://localhost:8000")

# ---------- SESSION STATE ----------
if "token" not in st.session_state:
    st.session_state.token = None
if "profile_complete" not in st.session_state:
    st.session_state.profile_complete = False
if "messages" not in st.session_state:
    st.session_state.messages = []
if "settings" not in st.session_state:
    st.session_state.settings = {
        "fear_reframing": True,
        "triad_mode": False,
        "clarifying_questions": True
    }
if "threads" not in st.session_state:
    st.session_state.threads = []
if "current_thread_id" not in st.session_state:
    st.session_state.current_thread_id = None
if "history_loaded" not in st.session_state:
    st.session_state.history_loaded = False

# ---------- API HELPERS ----------
def api_request(method, endpoint, data=None, headers=None):
    url = f"{API_BASE}{endpoint}"
    if headers is None:
        headers = {}
    if st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=headers)
        else:
            return None, "Unsupported method"
        return response, None
    except Exception as e:
        return None, str(e)

# ---------- THREAD MANAGEMENT ----------
def load_threads():
    response, err = api_request("GET", "/chat/threads")
    if err:
        st.error(f"Failed to load threads: {err}")
        return
    if response.status_code == 200:
        st.session_state.threads = response.json()
        st.session_state.history_loaded = True
    else:
        st.error(f"Failed to load threads (status {response.status_code})")

def load_thread_messages(thread_id):
    response, err = api_request("GET", f"/chat/threads/{thread_id}/messages")
    if err:
        st.error(f"Failed to load messages: {err}")
        return
    if response.status_code == 200:
        history = response.json()
        messages = []
        for conv in history:
            messages.append({"role": "user", "content": conv["message"]})
            messages.append({"role": "assistant", "content": conv["response"]})
        st.session_state.messages = messages
        st.session_state.current_thread_id = thread_id

def create_new_thread():
    response, err = api_request("POST", "/chat/threads")
    if err:
        st.error(f"Failed to create thread: {err}")
        return
    if response.status_code == 200:
        thread = response.json()
        st.session_state.threads.insert(0, thread)
        st.session_state.current_thread_id = thread["id"]
        st.session_state.messages = []
        st.rerun()
    else:
        st.error(f"Failed to create thread (status {response.status_code})")

def switch_thread(thread_id):
    if thread_id != st.session_state.current_thread_id:
        load_thread_messages(thread_id)
        st.rerun()

# ---------- AUTH / PROFILE ----------
def login(username, password):
    response, err = api_request("POST", "/login", {"username": username, "password": password})
    if err:
        return None, err
    if response.status_code == 200:
        data = response.json()
        st.session_state.token = data["access_token"]
        # Fetch profile
        prof_resp, _ = api_request("GET", "/user/profile")
        if prof_resp and prof_resp.status_code == 200:
            st.session_state.profile = prof_resp.json()
            if st.session_state.profile and st.session_state.profile.get("full_name"):
                st.session_state.profile_complete = True
            else:
                st.session_state.profile_complete = False
        # Load threads and messages
        load_threads()
        if st.session_state.threads:
            st.session_state.current_thread_id = st.session_state.threads[0]["id"]
            load_thread_messages(st.session_state.current_thread_id)
        return data, None
    else:
        try:
            err_msg = response.json().get("detail", "Login failed")
        except:
            err_msg = "Login failed"
        return None, err_msg

def register(username, email, password):
    response, err = api_request("POST", "/register", {"username": username, "email": email, "password": password})
    if err:
        return None, err
    if response.status_code == 200:
        return response.json(), None
    else:
        try:
            err_msg = response.json().get("detail", "Registration failed")
        except:
            err_msg = "Registration failed"
        return None, err_msg

def save_profile(profile_data):
    response, err = api_request("PUT", "/user/profile", profile_data)
    if err:
        return None, err
    if response.status_code == 200:
        st.session_state.profile = response.json()["profile"]
        st.session_state.profile_complete = True
        return response.json(), None
    else:
        try:
            err_msg = response.json().get("detail", "Profile update failed")
        except:
            err_msg = "Profile update failed"
        return None, err_msg

def send_message(message, settings):
    if st.session_state.current_thread_id is None:
        response, err = api_request("POST", "/chat/threads")
        if err:
            st.error(f"Failed to create thread: {err}")
            return None, "Thread creation failed"
        if response.status_code == 200:
            thread = response.json()
            st.session_state.current_thread_id = thread["id"]
            st.session_state.threads.insert(0, thread)
            st.session_state.messages = []
        else:
            st.error("Failed to create thread")
            return None, "Thread creation failed"

    params = f"?ask_clarifying={str(settings['clarifying_questions']).lower()}&triad_mode={str(settings['triad_mode']).lower()}"
    params += f"&thread_id={st.session_state.current_thread_id}"
    payload = {
        "message": message,
        "fear_reframing": settings["fear_reframing"]
    }
    response, err = api_request("POST", f"/chat{params}", payload)
    if err:
        return None, err
    if response.status_code == 200:
        return response.json(), None
    elif response.status_code == 401:
        st.session_state.token = None
        st.session_state.profile_complete = False
        st.warning("Session expired. Please log in again.")
        return None, "Session expired"
    else:
        try:
            err_msg = response.json().get("detail", "Chat failed")
        except:
            err_msg = "Chat failed"
        return None, err_msg

# ---------- CUSTOM CSS ----------
st.set_page_config(page_title="Junior - Your Trusted Friend", layout="wide")

st.markdown("""
<style>
    /* Force sidebar to be always visible */
    section[data-testid="stSidebar"] {
        display: flex !important;
        width: 300px !important;
        min-width: 300px !important;
        max-width: 300px !important;
        flex: 0 0 300px !important;
        position: relative !important;
        overflow: visible !important;
        visibility: visible !important;
        opacity: 1 !important;
    }
    section[data-testid="stSidebar"] > div {
        display: flex !important;
        flex-direction: column !important;
        height: 100vh !important;
        overflow-y: auto !important;
        width: 100% !important;
        visibility: visible !important;
        opacity: 1 !important;
    }
    /* Override any media queries that hide sidebar */
    @media (max-width: 768px) {
        section[data-testid="stSidebar"] {
            display: flex !important;
            width: 300px !important;
            min-width: 300px !important;
            max-width: 300px !important;
            flex: 0 0 300px !important;
        }
    }
    /* Also fix the hamburger menu if it appears */
    button[data-testid="baseButton-header"] {
        display: none !important; /* optional – hides the toggle if you don't need it */
    }
</style>
""", unsafe_allow_html=True)

# ---------- MAIN UI ----------
st.title("🌸 Junior - Your Always-There Friend")

# ---------- SIDEBAR ----------
with st.sidebar:
    st.header("⚙️ Settings")
    st.session_state.settings["fear_reframing"] = st.checkbox("Fear Reframing", value=st.session_state.settings["fear_reframing"])
    st.session_state.settings["triad_mode"] = st.checkbox("Triad Mode (Thoughts → Emotions → Behaviors)", value=st.session_state.settings["triad_mode"])
    st.session_state.settings["clarifying_questions"] = st.checkbox("Ask Clarifying Questions", value=st.session_state.settings["clarifying_questions"])

    # History – only shown when logged in
    if st.session_state.token is not None:
        st.markdown("---")
        st.subheader("📜 History")
        if st.button("➕ New Chat", use_container_width=True, key="new_chat_btn"):
            create_new_thread()

        if st.session_state.threads:
            for thread in st.session_state.threads:
                title = thread["title"] or "New Chat"
                is_current = thread["id"] == st.session_state.current_thread_id
                if st.button(title[:35], key=f"thread_{thread['id']}", use_container_width=True, type="primary" if is_current else "secondary"):
                    switch_thread(thread["id"])
        else:
            st.info("No conversations yet. Start a new chat!")

        # User info + logout at bottom of sidebar
        st.markdown("---")
        col1, col2 = st.columns([1, 4])
        with col1:
            username = st.session_state.profile.get("full_name", "U") if st.session_state.profile else "U"
            st.markdown(f"<div class='avatar'>{username[0].upper()}</div>", unsafe_allow_html=True)
        with col2:
            display_name = st.session_state.profile.get("full_name", "User") if st.session_state.profile else "User"
            st.write(display_name)
            if st.button("Logout", use_container_width=True, key="logout_btn"):
                st.session_state.token = None
                st.session_state.profile_complete = False
                st.session_state.messages = []
                st.session_state.threads = []
                st.session_state.current_thread_id = None
                st.rerun()

        # Sidebar footer
        st.markdown("""
        <div class="sidebar-footer">
            <p>© 2026 WaldisOne Tech Hub</p>
            <p>Powered by <strong>AMD</strong></p>
        </div>
        """, unsafe_allow_html=True)

# ---------- MAIN CONTENT ----------
if st.session_state.token is None:
    tab1, tab2 = st.tabs(["Login", "Register"])
    with tab1:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Log in")
            if submitted:
                data, err = login(username, password)
                if err:
                    st.error(err)
                else:
                    st.success("Logged in successfully!")
                    # Let Streamlit rerun naturally
    with tab2:
        with st.form("register_form"):
            reg_username = st.text_input("Username")
            reg_email = st.text_input("Email (optional)")
            reg_password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Create account & Login")
            if submitted:
                if not reg_username or not reg_password:
                    st.error("Username and password required")
                else:
                    data, err = register(reg_username, reg_email, reg_password)
                    if err:
                        st.error(err)
                    else:
                        login_data, login_err = login(reg_username, reg_password)
                        if login_err:
                            st.error(login_err)
                        else:
                            st.success("Account created and logged in!")
                            st.rerun()
else:
    # Check profile completion
    if not st.session_state.profile_complete:
        st.subheader("🎯 Let's get to know you better")
        st.write("Hi, I'm Junior. The junior version of you, to learn and grow with you. "
                 "Please tell me about yourself so I can serve you better. "
                 "Your data will be used only to personalise your experience. Please provide valid information to enjoy the Junior version of you in life.")
        with st.form("onboarding_form"):
            full_name = st.text_input("Full Name")
            dob = st.date_input("Date of Birth", min_value=datetime(1920,1,1), max_value=datetime.today())
            sex = st.selectbox("Sex", ["Select", "Male", "Female", "Other", "Prefer not to say"])
            career = st.text_input("Career Path (or unemployed)")
            likes = st.text_area("Likes (e.g., hobbies, people, places)")
            dislikes = st.text_area("Dislikes")
            interests = st.text_area("Interests")
            submitted = st.form_submit_button("Start my journey")
            if submitted:
                if not full_name:
                    st.error("Full name is required.")
                else:
                    profile_data = {
                        "full_name": full_name,
                        "date_of_birth": dob.isoformat(),
                        "sex": sex if sex != "Select" else None,
                        "career_path": career,
                        "likes": likes,
                        "dislikes": dislikes,
                        "interests": interests
                    }
                    data, err = save_profile(profile_data)
                    if err:
                        st.error(err)
                    else:
                        st.success("Profile saved! Welcome aboard.")
                        st.rerun()
    else:
        # Chat interface
        st.subheader("💬 Chat with Junior")
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                with st.chat_message("user"):
                    st.write(msg["content"])
            else:
                with st.chat_message("assistant"):
                    st.write(msg["content"])

        user_input = st.chat_input("Type your message...")
        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.write(user_input)

            with st.chat_message("assistant"):
                placeholder = st.empty()
                placeholder.markdown("⏳ *Junior is thinking...*")
                data, err = send_message(user_input, st.session_state.settings)
                if err:
                    if "Session expired" in err:
                        st.session_state.token = None
                        st.rerun()
                    else:
                        placeholder.error(f"Error: {err}")
                else:
                    assistant_reply = data["response"]
                    full_response = ""
                    delay = 0.02 if len(assistant_reply) < 200 else 0.01
                    for char in assistant_reply:
                        full_response += char
                        placeholder.markdown(full_response + "▌")
                        time.sleep(delay)
                    placeholder.markdown(full_response)
                    st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
                    load_threads()