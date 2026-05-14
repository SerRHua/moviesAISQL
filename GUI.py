import streamlit as st
import sqlite3
from scraping import get_movies_imdb, extract_genres
from datetime import date

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

if "genres" not in st.session_state:
    st.session_state["genres"] = []


# -------------------
# LOAD USERS
# -------------------
c.execute("SELECT name FROM users ORDER BY name COLLATE NOCASE ASC")
users = [row[0] for row in c.fetchall()]

if not st.session_state["name"] and users:
    st.session_state["name"] = users[0]


# -------------------
# USER GENRE HISTORY
# -------------------
def get_user_top_genres(username):
    c.execute("SELECT genre FROM movies WHERE username=?", (username,))
    rows = [r[0] for r in c.fetchall()]

    freq = {}

    for r in rows:
        for g in extract_genres(r):
            freq[g] = freq.get(g, 0) + 1

    return sorted(freq, key=freq.get, reverse=True)[:2]


# -------------------
# SIDEBAR
# -------------------
st.sidebar.header("User")

new_user = st.sidebar.text_input("Create user")
selected_user = st.sidebar.selectbox("Select user", [""] + users)
delete_user = st.sidebar.selectbox("Delete user", [""] + users)


# DELETE USER
if delete_user and st.sidebar.button("Delete"):
    c.execute("DELETE FROM users WHERE name=?", (delete_user,))
    c.execute("DELETE FROM movies WHERE username=?", (delete_user,))
    conn.commit()

    if st.session_state["name"] == delete_user:
        st.session_state["name"] = ""
        st.session_state["movies"] = []

    st.rerun()


# CREATE / SELECT USER
if new_user:
    st.session_state["name"] = new_user
    c.execute("INSERT OR IGNORE INTO users VALUES (?)", (new_user,))
    conn.commit()

elif selected_user:
    st.session_state["name"] = selected_user

    # reset results when switching users
    st.session_state["movies"] = []


# -------------------
# MAIN APP
# -------------------
if st.session_state["name"]:

    st.title(f"Hello {st.session_state['name']}")
    st.write(f"Today: {date.today().strftime('%B %d, %Y')}")

    user_input = st.text_input("Enter movie preference (e.g. Interstellar, funny movie)")

    col1, col2 = st.columns(2)

    # -------------------
    # SEARCH
    # -------------------
    if col1.button("Search"):

        query = user_input.strip().lower()

        c.execute("INSERT INTO movies VALUES (?,?)",
                  (st.session_state["name"], query))
        conn.commit()

        movies, _ = get_movies_imdb(query)

        st.session_state["movies"] = movies


    # -------------------
    # RECOMMEND
    # -------------------
    if col2.button("Recommend for me"):

        top_genres = get_user_top_genres(st.session_state["name"])

        if not top_genres:
            st.warning("No history yet")
        else:
            query = " ".join(top_genres)

            movies, _ = get_movies_imdb(query)

            st.session_state["movies"] = movies


    # -------------------
    # DISPLAY RESULTS
    # -------------------
    if st.session_state["movies"]:

        st.subheader("Recommendations")

        for movie in st.session_state["movies"]:
            st.markdown(f"### {movie['title']}")
            st.write(movie.get("year", ""))
            st.markdown("---")


    # -------------------
    # HISTORY
    # -------------------
    st.subheader("History")

    c.execute("SELECT genre FROM movies WHERE username=?", (st.session_state["name"],))
    for row in c.fetchall():
        st.write(row[0])

else:
    st.title("Create or select a user from the sidebar")

conn.close()