from scraping import get_movies_imdb, extract_genres

# -------------------
# TOOLS
# -------------------

def search_movies(query):
    return get_movies_imdb(query)

def recommend_movies(query):
    return get_movies_imdb(query)


TOOLS = {
    "search": search_movies,
    "recommend": recommend_movies
}


# -------------------
# AGENT (decision layer)
# -------------------

def movie_agent(user_input):

    q = user_input.lower()

    if "like" in q or "similar" in q:
        return TOOLS["recommend"](q)

    if any(g in q for g in [
        "action","comedy","horror","drama",
        "romance","thriller","sci-fi"
    ]):
        return TOOLS["recommend"](q)

    return TOOLS["search"](q)


# -------------------
# SMART RECOMMENDER (FIX FOR REPETITION)
# -------------------

def smart_recommend(history):

    all_genres = []

    for h in history:
        all_genres.extend(extract_genres(h))

    top_genres = list(set(all_genres))

    movies, _ = get_movies_imdb(top_genres)

    # ranking + dedup
    ranked = []
    seen = set()

    for m in movies:
        movie_genres = m.get("genres", [])

        score = len(set(top_genres) & set(movie_genres))

        if m["title"] not in seen:
            ranked.append((score, m))
            seen.add(m["title"])

    ranked.sort(reverse=True, key=lambda x: x[0])

    return [m for _, m in ranked]