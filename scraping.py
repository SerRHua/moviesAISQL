import requests
from difflib import get_close_matches

BASE_URL = "https://raw.githubusercontent.com/prust/wikipedia-movie-data/master/movies.json"

# -----------------------------
# MAIN GENRES
# -----------------------------
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

# -----------------------------
# GENRE SYNONYMS
# -----------------------------
GENRE_SYNONYMS = {

    # ACTION
    "superhero": "action",
    "heroes": "action",
    "hero": "action",
    "fight": "action",
    "fighting": "action",
    "war": "action",
    "battle": "action",
    "explosion": "action",
    "guns": "action",
    "martial arts": "action",
    "marvel": "action",
    "dc": "action",

    # ADVENTURE
    "journey": "adventure",
    "explore": "adventure",
    "exploration": "adventure",
    "quest": "adventure",
    "treasure": "adventure",
    "survival": "adventure",

    # ANIMATION
    "cartoon": "animation",
    "animated": "animation",
    "pixar": "animation",
    "disney": "animation",

    # COMEDY
    "funny": "comedy",
    "humor": "comedy",
    "hilarious": "comedy",
    "laugh": "comedy",
    "parody": "comedy",

    # CRIME
    "detective": "crime",
    "mafia": "crime",
    "gangster": "crime",
    "police": "crime",
    "murder": "crime",
    "heist": "crime",
    "criminal": "crime",

    # DRAMA
    "emotional": "drama",
    "sad": "drama",
    "serious": "drama",
    "life": "drama",
    "family": "drama",

    # FANTASY
    "magic": "fantasy",
    "dragon": "fantasy",
    "wizard": "fantasy",
    "kingdom": "fantasy",
    "myth": "fantasy",
    "fairy": "fantasy",

    # HORROR
    "scary": "horror",
    "ghost": "horror",
    "monster": "horror",
    "zombie": "horror",
    "haunted": "horror",
    "demon": "horror",

    # ROMANCE
    "romantic": "romance",
    "love": "romance",
    "dating": "romance",
    "relationship": "romance",
    "couple": "romance",

    # SCI-FI
    "space": "sci-fi",
    "future": "sci-fi",
    "alien": "sci-fi",
    "robot": "sci-fi",
    "cyberpunk": "sci-fi",
    "technology": "sci-fi",
    "time travel": "sci-fi",

    # THRILLER
    "suspense": "thriller",
    "tense": "thriller",
    "psychological": "thriller",
    "mind game": "thriller",
    "spy": "thriller",

    # MYSTERY
    "investigation": "mystery",
    "clues": "mystery",
    "unknown": "mystery",
    "whodunit": "mystery"
}

# -----------------------------
# FRANCHISE KEYWORDS
# -----------------------------
FRANCHISE_KEYWORDS = {

    "marvel": [
        "avengers",
        "iron man",
        "thor",
        "spider-man",
        "captain america",
        "guardians",
        "doctor strange",
        "black panther",
        "hulk",
        "ant-man"
    ],

    "dc": [
        "batman",
        "superman",
        "joker",
        "wonder woman",
        "flash",
        "aquaman"
    ],

    "star wars": [
        "star wars"
    ],

    "harry potter": [
        "harry potter",
        "fantastic beasts"
    ]
}


# -----------------------------
# EXTRACT GENRES
# -----------------------------
def extract_genres(query: str):

    q = query.lower()
    found = set()

    # direct genre matching
    for g in GENRES:
        if g in q:
            found.add(g)

    # synonym matching
    for synonym, genre in GENRE_SYNONYMS.items():
        if synonym in q:
            found.add(genre)

    # fuzzy matching
    all_words = list(GENRE_SYNONYMS.keys()) + GENRES

    for word in q.split():

        matches = get_close_matches(
            word,
            all_words,
            n=1,
            cutoff=0.75
        )

        if matches:

            matched = matches[0]

            if matched in GENRES:
                found.add(matched)

            elif matched in GENRE_SYNONYMS:
                found.add(
                    GENRE_SYNONYMS[matched]
                )

    return list(found)


# -----------------------------
# MAIN MOVIE FUNCTION
# -----------------------------
def get_movies_imdb(query, max_results=20):

    if isinstance(query, list):
        query = " ".join(query)

    query_lower = query.lower().strip()

    # -----------------------------
    # LOAD DATA
    # -----------------------------
    data = requests.get(
        BASE_URL,
        timeout=10
    ).json()

    # -----------------------------
    # FIND FRANCHISE
    # -----------------------------
    matched_franchise = None

    for franchise in FRANCHISE_KEYWORDS:

        if franchise in query_lower:
            matched_franchise = franchise
            break

    # -----------------------------
    # FIND MOVIE TITLE
    # -----------------------------
    matched_movie = None

    # exact title matching
    exact_matches = []

    for m in data:

        title = m.get(
            "title",
            ""
        ).lower().strip()

        if title == query_lower:
            exact_matches.append(m)

    if exact_matches:

        matched_movie = max(
            exact_matches,
            key=lambda x: x.get("year", 0)
        )

    # partial matching
    if not matched_movie:

        partial_matches = []

        for m in data:

            title = m.get(
                "title",
                ""
            ).lower().strip()

            if len(title) < 4:
                continue

            if f" {title} " in f" {query_lower} ":
                partial_matches.append(m)

        if partial_matches:

            matched_movie = max(
                partial_matches,
                key=lambda x: x.get("year", 0)
            )

    # -----------------------------
    # TARGET GENRES
    # -----------------------------
    target_genres = extract_genres(query)

    # use movie genres if title matched
    if matched_movie:

        target_genres = [
            g.lower()
            for g in matched_movie.get(
                "genres",
                []
            )
        ]

        print("\nMatched:", matched_movie["title"])
        print("Year:", matched_movie.get("year"))
        print("Genres:", target_genres)

    # -----------------------------
    # NO GENRES FOUND
    # -----------------------------
    if not target_genres and not matched_franchise:

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

        title_lower = title.lower()

        movie_genres = [
            g.lower()
            for g in m.get("genres", [])
        ]

        overlap = len(
            set(movie_genres) &
            set(target_genres)
        )

        year = m.get("year", 0)

        # skip old movies
        if isinstance(year, int) and year < 1980:
            continue

        # require either:
        # genre overlap OR franchise match
        if overlap < 1 and not matched_franchise:
            continue

        # -----------------------------
        # BASE SCORE
        # -----------------------------
        score = overlap * 100

        # -----------------------------
        # FRANCHISE BOOST
        # -----------------------------
        if matched_franchise:

            keywords = FRANCHISE_KEYWORDS[
                matched_franchise
            ]

            for keyword in keywords:

                if keyword in title_lower:
                    score += 1000

        # -----------------------------
        # SMART TITLE BOOSTS
        # -----------------------------
        boost_words = {
            "avengers": 300,
            "marvel": 250,
            "thor": 400,
            "spider-man": 400,
            "iron man": 400,
            "captain america": 350,
            "guardian": 200,
            "matrix": 300,
            "mission impossible": 300,
            "batman": 400,
            "superman": 350
        }

        for word, points in boost_words.items():

            if word in title_lower:
                score += points

        # newer movies preferred
        if isinstance(year, int):
            score += year

        scored.append((score, m))

    # -----------------------------
    # SORT RESULTS
    # -----------------------------
    scored.sort(
        key=lambda x: x[0],
        reverse=True
    )

    # -----------------------------
    # FINAL RESULTS
    # -----------------------------
    results = []
    seen = set()

    for score, m in scored:

        title = m["title"]

        if title in seen:
            continue

        imdb_link = (
            "https://www.imdb.com/find?q="
            + title.replace(" ", "+")
        )

        trailer_link = (
            "https://www.youtube.com/results?search_query="
            + title.replace(" ", "+")
            + "+official+trailer"
        )

        results.append({
            "title": title,
            "year": m.get("year", ""),
            "genres": [
                g.lower()
                for g in m.get("genres", [])
            ],
            "imdb": imdb_link,
            "trailer": trailer_link
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