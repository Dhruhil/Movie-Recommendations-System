import requests
import json
import time
#from fuzzywuzzy import fuzz
from rapidfuzz import fuzz
from concurrent.futures import ThreadPoolExecutor, as_completed


#perhaps fix so that if we get less than 30 search results, redo the search without the initials and lower the penalty of length
#example of this Top Gun (top gun shows not Top Gun Maverick)
#Harry Potter (no harry potter movie shows up because the length of the harry potter titles is much larger)
#Search the datadump, fuzz allows typos
def search( query,searchable_data, threshold=70, limit=30, minChar=3):
    

    results = []

    if len(query) < minChar:
        return "Query must contain at least 3 characters."

    print("Searching....")
    for entry in searchable_data:
        #if c == limit:
            #break

        try:
            name = entry["name"]
            uri = entry["uri"] #wikidata uri
        except:
            continue

        try:
            imdb = entry["imdb"]
        except:
            imdb = None

        #fuzzy matching
        #similarity_score = fuzz.partial_ratio(query.lower(), name.lower())
        similarity_score = fuzz.token_set_ratio(query.lower(), name.lower())

        #threshold for inclusivity (100 perfect match etc...)
        length_penalty = (abs(len(query) - len(name)) / max(len(query), len(name))) * 0.5
        adjusted_score = similarity_score * (1 - length_penalty)
        if adjusted_score > threshold:
            results.append({"name": name, "score": adjusted_score, "uri": uri, "imdb": imdb})
                    

    #sort results by similarity score in descending order
    results = sorted(results, key=lambda x: x["score"], reverse=True)

    return results[:limit]


def extract_id_from_uri(uri):
    return uri.split("/")[-1]


#Appends movie poster image path, ratings (TMDB ratings), media_type 
#fetch TMDB metadata
def _fetch_tmdb_data(entry, session):
    wikidata_id = extract_id_from_uri(entry["uri"])
    url = f"https://api.themoviedb.org/3/find/{wikidata_id}?external_source=wikidata_id"
    try:
        response = session.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()

        if data["movie_results"]:
            movie = data["movie_results"][0]
            poster_path = movie.get("poster_path")
            backdrop_path = movie.get("backdrop_path")
            entry.update({
                "ratings": movie.get("vote_average", "0"),
                "media_type": movie.get("media_type", "movie"),
                "popularity": movie.get("popularity", 0),
                "backdrop": f"https://image.tmdb.org/t/p/original/{backdrop_path}",
                "overview": movie.get("overview", ""),
                "imdb": entry["imdb"], 
                "poster": (f"https://image.tmdb.org/t/p/original/{poster_path}"
                           if poster_path else 
                           "https://media.istockphoto.com/id/995815438/vector/"
                           "movie-and-film-modern-retro-vintage-poster-background.jpg?"
                           "s=612x612&w=0&k=20&c=UvRsJaKcp0EKIuqDKp6S7Dwhltt0D5rbegPkS-B8nDQ=")
            })
        else:
            raise ValueError("No movie results found")

    except Exception as e:
        #fallback values if TMDB fetch fails
        entry.update({
            "ratings": "0",
            "media_type": "movie",
            "popularity": 0,
            "poster": "https://media.istockphoto.com/id/995815438/vector/"
                      "movie-and-film-modern-retro-vintage-poster-background.jpg?"
                      "s=612x612&w=0&k=20&c=UvRsJaKcp0EKIuqDKp6S7Dwhltt0D5rbegPkS-B8nDQ="
        })
        print(f"TMDB fetch error for {wikidata_id}: {e}")

    return entry


#fetch IMDb ratings
def _fetch_omdb_data(entry, session):

    imdb_id = entry.get("imdb")
    #print(imdb_id)
    if not imdb_id:
        #if there is no imdb
        return entry

    try:
        url = f"https://www.omdbapi.com/?i={imdb_id}&apikey=bbe16d5f"
        response = session.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        imdb_rating = data.get("imdbRating")  # e.g. "7.3"
        entry.update({"imdb_ratings": imdb_rating})
        #print(imdb_rating)
    except Exception as e:
        entry.update({"imdb_ratings": None})
        print(f"Error fetching IMDb rating for {imdb_id}: {e}")

    return entry


#main function: add_movie_metadata (+ 2 helper functions fetch_omdb_data and fetch_tmdb_data)
def add_movie_metadata(search_results):
    #create a session for TMDB
    tmdb_session = requests.Session()
    tmdb_session.headers.update({
        "accept": "application/json",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI4N2NhYWVlZjk5OTRlZTIxNDk3ZDA1Mzc0ZTg1ODdiYSIsIm5iZiI6MTczNTU3NDYwMy44OTQsInN1YiI6IjY3NzJjNDRiNjIzNGMxYjQ2ZjYxNGU3ZiIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.7jM6UhZJFYPblmV8e-UE5QzvjT8Nl1TA5jvebToAZFg"
    })

    #fetch TMDB data in parallel using 30 workers
    tmdb_fetched_results = []
    with ThreadPoolExecutor(max_workers=30) as executor:
        futures = {
            executor.submit(_fetch_tmdb_data, entry, tmdb_session): entry
            for entry in search_results
        }
        for future in as_completed(futures):
            tmdb_fetched_results.append(future.result())

    #fetch IMDb ratings in parallel using another 30 workers
    imdb_session = requests.Session()
    omdb_fetched_results = []
    with ThreadPoolExecutor(max_workers=30) as executor:
        futures = {
            executor.submit(_fetch_omdb_data, entry, imdb_session): entry
            for entry in tmdb_fetched_results
        }
        for future in as_completed(futures):
            omdb_fetched_results.append(future.result())

    #sort by popularity decending order (from tmdb)
    omdb_fetched_results.sort(key=lambda x: x.get("popularity", 0), reverse=True)
    #print(omdb_fetched_results)
    return omdb_fetched_results


def add_person_metadata(search_results):
    # TMDB API
    session = requests.Session()  #session (faster than reopening the connection each time)
    session.headers.update({
        "accept": "application/json",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI4N2NhYWVlZjk5OTRlZTIxNDk3ZDA1Mzc0ZTg1ODdiYSIsIm5iZiI6MTczNTU3NDYwMy44OTQsInN1YiI6IjY3NzJjNDRiNjIzNGMxYjQ2ZjYxNGU3ZiIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.7jM6UhZJFYPblmV8e-UE5QzvjT8Nl1TA5jvebToAZFg"
    })

    def fetch_person_data(entry):
        wikidata_id = extract_id_from_uri(entry["uri"])
        url = f"https://api.themoviedb.org/3/find/{wikidata_id}?external_source=wikidata_id"
        try:
            response = session.get(url)
            response.raise_for_status()
            data = response.json()
            
            if data["person_results"]:
                person = data["person_results"][0]
                profile_path = person.get("profile_path")
                entry.update({
                    "popularity": person.get("popularity", 0),
                    "profile": f"https://image.tmdb.org/t/p/original/{profile_path}" if profile_path else "https://upload.wikimedia.org/wikipedia/commons/b/bc/Unknown_person.jpg"
                })
            else:
                raise ValueError("No actor results found")
        except Exception as e:
            entry.update({
                "popularity": 0,
                "profile": "https://upload.wikimedia.org/wikipedia/commons/b/bc/Unknown_person.jpg"
            })
            print(e)
        return entry

    new_search_results = []
    with ThreadPoolExecutor(max_workers=30) as executor:
        futures = {executor.submit(fetch_person_data, entry): entry for entry in search_results}
        for future in as_completed(futures):
            new_search_results.append(future.result())

    #sort by popularity
    new_search_results.sort(key=lambda x: x.get("popularity", 0), reverse=True)
    return new_search_results


#Example usage
#query = "avengers"
#search_results = search(query)
#add_move_metadata(search_results)

"""
{
  "movie_results": [
    {
      "backdrop_path": "/hpQ7dLKEdIsztIIFUMzrgVZMkls.jpg",
      "id": 42756,
      "title": "Angels Over Broadway",
      "original_title": "Angels Over Broadway",
      "overview": "Small-time businessman Charles Engle is threatened with exposure for embezzling $3,000 for his free-spending wife. Deciding on suicide, he scribbles a note, stuffs it in his pocket and goes for one last night on the town. He is pulled into a poker game by conman Bill O'Brien and singer Nina Barone, but when they discover the dropped note, they resolve to turn the tables, get Engle his $3,000 and save his life.",
      "poster_path": "/nee1LVYfgKE6fWrXNzi94fl2PAR.jpg",
      "media_type": "movie",
      "adult": false,
      "original_language": "en",
      "genre_ids": [
        18,
        80
      ],
      "popularity": 3.521,
      "release_date": "1940-10-02",
      "video": false,
      "vote_average": 5.8,
      "vote_count": 27
    }
  ],
  "person_results": [],
  "tv_results": [],
  "tv_episode_results": [],
  "tv_season_results": []
}
"""