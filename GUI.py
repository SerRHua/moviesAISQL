import streamlit as st
import sqlite3
from datetime import date

from agent import movie_agent, smart_recommend

# -------------------
# DB SETUP
# -------------------
conn = sqlite3.connect("users.db", check_same_thread=False)
c = conn.cursor()

c.execute("CREATE TABLE IF NOT EXISTS users (name TEXT UNIQUE)")
c.execute("CREATE TABLE IF NOT EXISTS movies (username TEXT, genre TEXT)")
conn.commit()

# -------------------
# SESSION STATE
# -------------------
if "name" not in st.session_state:
    st.session_state["name"] = ""

if "movies" not in st.session_state:
    st.session_state["movies"] = []

# -------------------
# LOAD USERS
# -------------------
c.execute("SELECT name FROM users ORDER BY name")
users = [r[0] for r in c.fetchall()]

# -------------------
# SIDEBAR - USER MANAGEMENT
# -------------------
st.sidebar.header("User Management")

new_user = st.sidebar.text_input("Create user")
selected_user = st.sidebar.selectbox("Select user", [""] + users)
delete_user = st.sidebar.selectbox("Delete user", ["None"] + users)

# CREATE USER
if new_user:
    st.session_state["name"] = new_user
    st.session_state["movies"] = []
    c.execute("INSERT OR IGNORE INTO users VALUES (?)", (new_user,))
    conn.commit()

# SELECT USER
elif selected_user:
    st.session_state["name"] = selected_user
    st.session_state["movies"] = []

# DELETE USER
if delete_user != "None" and st.sidebar.button("Delete user"):

    c.execute("DELETE FROM users WHERE name=?", (delete_user,))
    c.execute("DELETE FROM movies WHERE username=?", (delete_user,))
    conn.commit()

    if st.session_state["name"] == delete_user:
        st.session_state["name"] = ""
        st.session_state["movies"] = []

    st.sidebar.success(f"Deleted {delete_user}")
    st.rerun()

# -------------------
# MAIN APP
# -------------------
if st.session_state["name"]:

    st.title(f"Movie Agent - {st.session_state['name']}")
    st.write(f"Today: {date.today().strftime('%B %d, %Y')}")

    # -------------------
    # TOP BAR (CLEAR HISTORY BUTTON)
    # -------------------
    top_left, top_right = st.columns([8, 2])

    with top_right:
        if st.button("Clear history"):
            c.execute(
                "DELETE FROM movies WHERE username=?",
                (st.session_state["name"],)
            )
            conn.commit()

            st.session_state["movies"] = []
            st.success("History cleared")
            st.rerun()

    user_input = st.text_input("Search movies")
    col1, col2 = st.columns(2)

    # -------------------
    # SEARCH (MCP AGENT)
    # -------------------
    if col1.button("Search") and user_input:

        movies, _ = movie_agent(user_input)

        st.session_state["movies"] = movies

        c.execute(
            "INSERT INTO movies VALUES (?,?)",
            (st.session_state["name"], user_input)
        )
        conn.commit()

    # -------------------
    # RECOMMEND (SMART SYSTEM)
    # -------------------
    if col2.button("Recommend for me"):

        c.execute(
            "SELECT genre FROM movies WHERE username=?",
            (st.session_state["name"],)
        )

        history = [r[0] for r in c.fetchall()]

        if history:
            movies = smart_recommend(history)
            st.session_state["movies"] = movies
        else:
            st.warning("No history yet")

    # -------------------
    # DISPLAY RESULTS
    # -------------------
    if st.session_state["movies"]:

        st.subheader("Results")

        for m in st.session_state["movies"]:
            st.markdown(f"### {m['title']}")
            st.write(m.get("year", ""))
            st.markdown("---")

    # -------------------
    # HISTORY
    # -------------------
    st.subheader("History")

    c.execute(
        "SELECT genre FROM movies WHERE username=?",
        (st.session_state["name"],)
    )

    for r in c.fetchall():
        st.write(r[0])

else:
    st.title("Create or select a user from the sidebar")

conn.close()