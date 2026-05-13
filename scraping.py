import requests
from bs4 import BeautifulSoup

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

def extract_genres(query: str) -> list:
    query_lower = query.lower()
    found = set()
    for genre in GENRES:
        if genre in query_lower:
            found.add(genre)
    for syn, genre in GENRE_SYNONYMS.items():
        if syn in query_lower:
            found.add(genre)
    return list(found)

def build_url(genres: list) -> str:
    if not genres:
        return ""
    return f"https://www.imdb.com/search/title/?genres={','.join(genres)}&sort=moviemeter,asc"

def get_movies_imdb(genres: list, max_results=10):
    if not genres:
        return ["No genres detected"], []

    url = build_url(genres)

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html"
    }

    r = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")

    movies = []
    posters = []

    title_tags = soup.select("a.ipc-title-link-wrapper")
    poster_tags = soup.select("img.ipc-image")

    for i in range(min(max_results, len(title_tags))):

        movies.append(title_tags[i].text.strip())

        if i < len(poster_tags):
            posters.append(poster_tags[i].get("src"))
        else:
            posters.append(None)

    if not movies:
        return ["No movies found"], []

    return movies, posters

def main():
    genres = extract_genres("I want to watch a funny and scary movie")
    print("Extracted genres:", genres)

    movies, posters = get_movies_imdb(genres)
    print("Recommended movies:", movies)
    print("Poster URLs:", posters)

if __name__ == "__main__":
    main()