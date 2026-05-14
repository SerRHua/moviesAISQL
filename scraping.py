import requests

BASE_URL = "https://raw.githubusercontent.com/prust/wikipedia-movie-data/master/movies.json"

GENRE_SYNONYMS = {
    "funny": "comedy",
    "scary": "horror",
    "romantic": "romance",
    "space": "sci-fi",
    "suspense": "thriller",
    "detective": "crime"
}

GENRES = [
    "action","adventure","animation","comedy","crime","drama",
    "fantasy","horror","romance","sci-fi","thriller","mystery"
]

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


def get_movies_imdb(genres, max_results=12):

    if not genres:
        return ["No genres detected"], []

    data = requests.get(BASE_URL, timeout=10).json()

    movies = []

    for m in data:
        movie_genres = [g.lower() for g in m.get("genres", [])]

        if any(g in movie_genres for g in genres):
            movies.append({
                "title": m["title"],
                "year": m.get("year", "")
            })

        if len(movies) >= max_results:
            break

    if not movies:
        return [{"title": "No movies found", "year": ""}], []

    return movies, []