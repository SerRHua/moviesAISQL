import requests

BASE_URL = "https://raw.githubusercontent.com/prust/wikipedia-movie-data/master/movies.json"

GENRES = [
    "action","adventure","animation","comedy","crime","drama",
    "fantasy","horror","romance","sci-fi","thriller","mystery"
]

GENRE_SYNONYMS = {
    "funny": "comedy",
    "scary": "horror",
    "romantic": "romance",
    "space": "sci-fi",
    "suspense": "thriller",
    "detective": "crime"
}


# ----------------------------
# Helpers
# ----------------------------

def extract_genres(query: str):
    q = query.lower()
    found = set()

    for g in GENRES:
        if g in q:
            found.add(g)

    for k, v in GENRE_SYNONYMS.items():
        if k in q:
            found.add(v)

    return list(found)


def find_exact_movie(title, dataset):
    t = title.lower().strip()

    for m in dataset:
        if m["title"].lower() == t:
            return m

    return None


def get_movie_genres(movie):
    return [g.lower() for g in movie.get("genres", [])]


# ----------------------------
# Main recommendation engine
# ----------------------------

def get_movies_imdb(query, max_results=10):

    data = requests.get(BASE_URL, timeout=10).json()

    results = []
    used = set()

    query_lower = query.lower().strip()

    # 1. check exact movie match
    seed_movie = find_exact_movie(query_lower, data)

    if seed_movie:
        results.append(seed_movie)
        used.add(seed_movie["title"])
        target_genres = get_movie_genres(seed_movie)
    else:
        target_genres = extract_genres(query)

    # 2. fallback if no genres found
    if not target_genres:
        return [{"title": "No movies found", "year": ""}], []

    # 3. recommend similar movies
    for m in data:

        if len(results) >= max_results:
            break

        if m["title"] in used:
            continue

        movie_genres = [g.lower() for g in m.get("genres", [])]

        if any(g in movie_genres for g in target_genres):
            results.append(m)
            used.add(m["title"])

    return results, []