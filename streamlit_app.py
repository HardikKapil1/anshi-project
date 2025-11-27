import os
import sqlite3
from datetime import datetime

import streamlit as st
from werkzeug.security import generate_password_hash, check_password_hash

# ---- Config ----
st.set_page_config(page_title="Campus Hub", page_icon="🎒", layout="wide")

BASE_DIR = os.getcwd()
DB_PATH = os.environ.get("DATABASE_PATH", os.path.join(BASE_DIR, "campus_hub.db"))
UPLOAD_DIR = os.environ.get("UPLOAD_FOLDER", os.path.join(BASE_DIR, "uploads"))
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ---- DB helpers ----
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS students (
            student_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            password_hash TEXT NOT NULL
        )
        """
    )

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS items (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            type TEXT NOT NULL,
            title TEXT NOT NULL,
            category TEXT,
            description TEXT,
            date TEXT,
            location TEXT,
            photo_path TEXT,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        )
        """
    )

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            date TEXT NOT NULL,
            venue TEXT NOT NULL,
            description TEXT,
            created_by INTEGER,
            FOREIGN KEY (created_by) REFERENCES students(student_id)
        )
        """
    )

    conn.commit()
    conn.close()


init_db()

# ---- Auth helpers ----
def login_user(email: str, password: str):
    conn = get_db()
    user = conn.execute("SELECT * FROM students WHERE email = ?", (email,)).fetchone()
    conn.close()
    if user and check_password_hash(user["password_hash"], password):
        return {"student_id": user["student_id"], "name": user["name"], "email": user["email"]}
    return None


def register_user(name: str, email: str, phone: str, password: str):
    conn = get_db()
    existing = conn.execute("SELECT 1 FROM students WHERE email = ?", (email,)).fetchone()
    if existing:
        conn.close()
        return False, "Email already registered"

    password_hash = generate_password_hash(password)
    conn.execute(
        "INSERT INTO students (name, email, phone, password_hash) VALUES (?, ?, ?, ?)",
        (name, email, phone, password_hash),
    )
    conn.commit()
    conn.close()
    return True, "Registered successfully. Please log in."


# ---- Sidebar: Auth ----
if "user" not in st.session_state:
    st.session_state.user = None

with st.sidebar:
    st.title("Campus Hub")

    if st.session_state.user:
        st.success(f"Logged in as {st.session_state.user['name']}")
        if st.button("Log out"):
            st.session_state.user = None
            st.rerun()
    else:
        tabs = st.tabs(["Login", "Register"])
        with tabs[0]:
            with st.form("login_form"):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Login")
            if submitted:
                u = login_user(email.strip(), password)
                if u:
                    st.session_state.user = u
                    st.success("Logged in")
                    st.rerun()
                else:
                    st.error("Invalid email or password")
        with tabs[1]:
            with st.form("register_form"):
                name = st.text_input("Name")
                remail = st.text_input("Email", key="reg_email")
                phone = st.text_input("Phone")
                rpassword = st.text_input("Password", type="password")
                submitted_r = st.form_submit_button("Register")
            if submitted_r:
                ok, msg = register_user(name.strip(), remail.strip(), phone.strip(), rpassword)
                st.success(msg) if ok else st.error(msg)

# ---- Main content ----
st.header("🎒 Campus Hub – Lost & Found + Events")

list_tab, add_item_tab, events_tab = st.tabs(["Browse Items", "Add Item", "Events"])

# Browse Items
with list_tab:
    col1, col2 = st.columns([2, 1])
    with col1:
        q = st.text_input("Search (title/location/category)", "")
    with col2:
        item_type = st.selectbox("Type", ["", "lost", "found"], index=0)

    query = "SELECT * FROM items WHERE status = 'active'"
    params = []
    if q.strip():
        query += " AND (title LIKE ? OR location LIKE ? OR category LIKE ?)"
        params.extend([f"%{q}%", f"%{q}%", f"%{q}%"])
    if item_type:
        query += " AND type = ?"
        params.append(item_type)
    query += " ORDER BY created_at DESC"

    conn = get_db()
    rows = conn.execute(query, params).fetchall()
    conn.close()

    if not rows:
        st.info("No items found.")
    else:
        for r in rows:
            with st.container(border=True):
                c1, c2 = st.columns([1, 3])
                with c1:
                    if r["photo_path"] and os.path.exists(r["photo_path"]):
                        st.image(r["photo_path"], width=160)
                    else:
                        st.write("No photo")
                with c2:
                    st.subheader(r["title"])  # type: ignore
                    st.write(
                        f"Type: {r['type']} | Category: {r['category'] or '-'} | Location: {r['location'] or '-'}"
                    )
                    st.caption(
                        f"Date: {r['date'] or '-'} | Status: {r['status']} | Posted: {r['created_at']}"
                    )

                # Owner-only: resolve item
                if (
                    st.session_state.user
                    and r["student_id"] == st.session_state.user.get("student_id")
                    and r["status"] != "resolved"
                ):
                    if st.button("Mark as resolved", key=f"resolve_{r['item_id']}"):
                        conn = get_db()
                        conn.execute("UPDATE items SET status = 'resolved' WHERE item_id = ?", (r["item_id"],))
                        conn.commit()
                        conn.close()
                        st.success("Item marked as resolved")
                        st.rerun()

# Add Item
with add_item_tab:
    if not st.session_state.user:
        st.warning("Please log in to add items.")
    else:
        with st.form("add_item_form"):
            itype = st.selectbox("Type", ["lost", "found"])
            title = st.text_input("Title")
            category = st.text_input("Category")
            description = st.text_area("Description")
            date = st.date_input("Date", value=datetime.today())
            location = st.text_input("Location")
            photo = st.file_uploader("Photo", type=["png", "jpg", "jpeg"]) 
            submitted = st.form_submit_button("Add Item")

        if submitted:
            photo_path = None
            if photo is not None:
                safe_name = os.path.basename(photo.name)
                photo_path = os.path.join(UPLOAD_DIR, safe_name)
                with open(photo_path, "wb") as f:
                    f.write(photo.getbuffer())

            conn = get_db()
            conn.execute(
                """
                INSERT INTO items (student_id, type, title, category, description, date, location, photo_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    st.session_state.user["student_id"],
                    itype,
                    title,
                    category,
                    description,
                    str(date),
                    location,
                    photo_path,
                ),
            )
            conn.commit()
            conn.close()
            st.success("Item added successfully!")
            st.rerun()

# Events
with events_tab:
    conn = get_db()
    evts = conn.execute("SELECT * FROM events ORDER BY date").fetchall()
    conn.close()

    st.subheader("Upcoming Events")
    if not evts:
        st.info("No events yet.")
    else:
        for e in evts:
            with st.container(border=True):
                st.write(f"📅 {e['date']} — {e['title']} @ {e['venue']}")
                if e["description"]:
                    st.caption(e["description"])  # type: ignore

    st.divider()
    if not st.session_state.user:
        st.info("Log in to add an event.")
    else:
        with st.form("add_event_form"):
            etitle = st.text_input("Event Title")
            edate = st.date_input("Event Date", value=datetime.today())
            evenue = st.text_input("Venue")
            edesc = st.text_area("Description")
            esub = st.form_submit_button("Add Event")
        if esub:
            conn = get_db()
            conn.execute(
                "INSERT INTO events (title, date, venue, description, created_by) VALUES (?, ?, ?, ?, ?)",
                (etitle, str(edate), evenue, edesc, st.session_state.user["student_id"]),
            )
            conn.commit()
            conn.close()
            st.success("Event added!")
            st.rerun()
