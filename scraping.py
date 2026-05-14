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


def get_movies_imdb(query, max_results=30):

    if isinstance(query, list):
        query = " ".join(query)

    data = requests.get(BASE_URL, timeout=10).json()

    target_genres = extract_genres(query)

    if not target_genres:
        return [{"title": "No movies found", "year": "", "genres": []}], []

    results = []
    seen = set()

    for m in data:

        movie_genres = [g.lower() for g in m.get("genres", [])]

        if any(g in movie_genres for g in target_genres):

            if m["title"] in seen:
                continue

            results.append({
                "title": m["title"],
                "year": m.get("year", ""),
                "genres": movie_genres
            })

            seen.add(m["title"])

        if len(results) >= max_results:
            break

    return results, []