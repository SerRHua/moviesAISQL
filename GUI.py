import streamlit as st
import sqlite3
from scraping import get_movies_imdb, extract_genres
from datetime import date

# --- DB setup ---
conn = sqlite3.connect("users.db", check_same_thread=False)
c = conn.cursor()

c.execute("CREATE TABLE IF NOT EXISTS users (name TEXT UNIQUE)")
c.execute("CREATE TABLE IF NOT EXISTS movies (username TEXT, genre TEXT)")
conn.commit()

# --- session state ---
if "name" not in st.session_state:
    st.session_state["name"] = ""

if "movies" not in st.session_state:
    st.session_state["movies"] = []

if "posters" not in st.session_state:
    st.session_state["posters"] = []

if "genres" not in st.session_state:
    st.session_state["genres"] = []

# --- load users ---
c.execute("SELECT name FROM users ORDER BY name COLLATE NOCASE ASC")
users = [row[0] for row in c.fetchall()]

if not st.session_state["name"] and users:
    st.session_state["name"] = users[0]

# --- helper ---
def get_user_top_genres(username):
    c.execute("SELECT genre FROM movies WHERE username = ?", (username,))
    rows = [row[0] for row in c.fetchall()]

    freq = {}
    for r in rows:
        for g in extract_genres(r):
            freq[g] = freq.get(g, 0) + 1

    return sorted(freq, key=freq.get, reverse=True)[:2]


# --- sidebar ---
st.sidebar.header("User Selection")

new_name = st.sidebar.text_input("Enter new user")
selected_name = st.sidebar.selectbox("Select user", [""] + users)
delete_name = st.sidebar.selectbox("Delete user", [""] + users)

# --- delete ---
if delete_name and st.sidebar.button("Delete Selected User"):
    c.execute("DELETE FROM users WHERE name=?", (delete_name,))
    c.execute("DELETE FROM movies WHERE username=?", (delete_name,))
    conn.commit()

    if st.session_state["name"] == delete_name:
        st.session_state["name"] = ""
        st.session_state["movies"] = []
        st.session_state["posters"] = []
        st.session_state["genres"] = []

    st.rerun()

# --- create/select ---
if new_name:
    st.session_state["name"] = new_name
    c.execute("INSERT OR IGNORE INTO users VALUES (?)", (new_name,))
    conn.commit()

elif selected_name:
    st.session_state["name"] = selected_name

# reset UI when switching user
st.session_state["movies"] = []
st.session_state["posters"] = []
st.session_state["genres"] = []

# --- MAIN ---
if st.session_state["name"]:

    st.title(f"Hello {st.session_state['name']}! Today is {date.today().strftime('%B %d, %Y')}")

    what_to_do = st.text_input("What movies do you want?")

    col1, col2 = st.columns(2)

    # SEARCH
    if col1.button("Search"):
        query = what_to_do.strip().lower()

        c.execute("INSERT INTO movies VALUES (?,?)",
                  (st.session_state["name"], query))
        conn.commit()

        genres = extract_genres(query)
        movies, posters = get_movies_imdb(genres)

        st.session_state["movies"] = movies
        st.session_state["posters"] = posters
        st.session_state["genres"] = genres

    # RECOMMEND
    if col2.button("Recommend for me"):
        top_genres = get_user_top_genres(st.session_state["name"])

        if not top_genres:
            st.warning("No history yet")
        else:
            movies, posters = get_movies_imdb(top_genres)

            st.session_state["movies"] = movies
            st.session_state["posters"] = posters
            st.session_state["genres"] = top_genres

    # RESULTS
    st.subheader("Recommended Movies")

    for movie in st.session_state["movies"]:
        with st.container():
            st.markdown(f"""
            ### 🎬 {movie['title']}
            **Year:** {movie['year']}
            ---
            """)

    # HISTORY
    st.subheader("History")
    c.execute("SELECT genre FROM movies WHERE username=?", (st.session_state["name"],))
    for row in c.fetchall():
        st.write(row[0])

else:
    st.title("Welcome! Create or select a user from sidebar")

conn.close()