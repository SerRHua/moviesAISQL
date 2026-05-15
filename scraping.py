import requests

BASE_URL = "https://raw.githubusercontent.com/prust/wikipedia-movie-data/master/movies.json"

GENRES = [
    "action",
    "adventure",
    "animation",
    "comedy",
    "crime",
    "drama",
    "fantasy",
    "horror",
    "romance",
    "sci-fi",
    "thriller",
    "mystery"
]

GENRE_SYNONYMS = {
    "funny": "comedy",
    "scary": "horror",
    "romantic": "romance",
    "space": "sci-fi",
    "suspense": "thriller",
    "detective": "crime",
    "superhero": "action"
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


def get_movies_imdb(query, max_results=20):

    if isinstance(query, list):
        query = " ".join(query)

    query_lower = query.lower().strip()

    # -----------------------------
    # LOAD MOVIE DATA
    # -----------------------------
    data = requests.get(BASE_URL, timeout=10).json()

    # -----------------------------
    # FIND MOVIE TITLE
    # -----------------------------
    matched_movie = None

    # exact title matches
    exact_matches = []

    for m in data:

        title = m.get("title", "").lower().strip()

        if title == query_lower:
            exact_matches.append(m)

    # choose newest exact match
    if exact_matches:

        matched_movie = max(
            exact_matches,
            key=lambda x: x.get("year", 0)
        )

    # partial title matches
    if not matched_movie:

        partial_matches = []

        for m in data:

            title = m.get("title", "").lower().strip()

            # ignore tiny titles like "Ma"
            if len(title) < 4:
                continue

            # exact phrase matching
            if f" {title} " in f" {query_lower} ":
                partial_matches.append(m)

        # choose newest match
        if partial_matches:

            matched_movie = max(
                partial_matches,
                key=lambda x: x.get("year", 0)
            )

    # -----------------------------
    # GET TARGET GENRES
    # -----------------------------
    target_genres = extract_genres(query)

    # use movie genres if title matched
    if matched_movie:

        target_genres = [
            g.lower()
            for g in matched_movie.get("genres", [])
        ]

        print("Matched:", matched_movie["title"])
        print("Year:", matched_movie["year"])
        print("Genres:", target_genres)

    # no genres found
    if not target_genres:

        return [{
            "title": "No movies found",
            "year": "",
            "genres": []
        }], []

    # -----------------------------
    # SCORE MOVIES
    # -----------------------------
    scored = []

    for m in data:

        title = m.get("title", "")

        # skip same movie
        if matched_movie and title == matched_movie["title"]:
            continue

        movie_genres = [
            g.lower()
            for g in m.get("genres", [])
        ]

        overlap = len(
            set(movie_genres) & set(target_genres)
        )

        # require at least 1 shared genre
        if overlap < 1:
            continue

        year = m.get("year", 0)

        # remove ancient movies
        if isinstance(year, int) and year < 1980:
            continue

        # -----------------------------
        # SCORING
        # -----------------------------
        score = overlap * 100

        title_lower = title.lower()

        # boost superhero/action titles
        boost_words = [
            "man",
            "avengers",
            "marvel",
            "captain",
            "thor",
            "spider",
            "guardian",
            "robot",
            "future",
            "iron"
        ]

        for word in boost_words:
            if word in title_lower:
                score += 200

        # prefer newer movies
        if isinstance(year, int):
            score += year

        scored.append((score, m))

    # -----------------------------
    # SORT BEST MATCHES
    # -----------------------------
    scored.sort(
        key=lambda x: x[0],
        reverse=True
    )

    # -----------------------------
    # BUILD FINAL RESULTS
    # -----------------------------
    results = []
    seen = set()

    for score, m in scored:

        title = m["title"]

        if title in seen:
            continue

        results.append({
            "title": title,
            "year": m.get("year", ""),
            "genres": [
                g.lower()
                for g in m.get("genres", [])
            ]
        })

        seen.add(title)

        if len(results) >= max_results:
            break

    # fallback
    if not results:

        return [{
            "title": "No similar movies found",
            "year": "",
            "genres": target_genres
        }], target_genres

    return results, target_genres