from model.recommend.infer import infer_shared_actors, infer_shared_genres, fetch_and_map_actor_metadata, filter_actor_popularity, fetch_and_map_director_metadata, infer_shared_directors, fetch_movie_data, fetch_movies_from_actors, fetch_movies_from_directors


def extract_id_from_uri(uri):
    return uri.split("/")[-1]
def combine_recommendation_data(list_of_movies, list_of_actors, list_of_directors, g):
    # Fetch and process data for shared actors

    actor_movies = fetch_movies_from_actors(list_of_actors,g)

    director_movies = fetch_movies_from_directors(list_of_directors,g)

    print("Infering actors....")
    shared_actor_data = filter_actor_popularity(
        fetch_and_map_actor_metadata(infer_shared_actors(list_of_movies,g)),
        threshold=30
    )

    print("Infering directors...")
    shared_director_data = fetch_and_map_director_metadata(
        infer_shared_directors(list_of_movies,g)
    )
    print("Infering shared genres..")
    shared_genre_data = infer_shared_genres(list_of_movies,g)

    shared_results = {}

    def normalize_shared_movies(shared_movies):
        return tuple(sorted(shared_movies))

    def add_shared_result(movie_uri, shared_movies, common_data):
        shared_movies_key = normalize_shared_movies(shared_movies)

        if movie_uri not in shared_results:
            shared_results[movie_uri] = {
                #"title": None, 
                "shared_result": []
            }

        for result in shared_results[movie_uri]["shared_result"]:
            if result["sharedMovies"] == list(shared_movies_key):
                for key, value in common_data.items():
                    result["common"].setdefault(key, []).extend(value)
                return

        shared_results[movie_uri]["shared_result"].append({
            "sharedMovies": list(shared_movies_key),
            "common": common_data
        })

    for movie_uri, data in shared_actor_data.items():
        shared_movies = [extract_id_from_uri(uri) for uri in data.get("sharedMovieUris", [])]
        actors = [actor["name"] for actor in data.get("actors", [])]
        if shared_movies:
            add_shared_result(movie_uri, shared_movies, {"actors": actors})

    for movie_uri, data in shared_director_data.items():
        shared_movies = [extract_id_from_uri(uri) for uri in data.get("sharedMovieUris", [])]
        directors = [director["name"] for director in data.get("directors", [])]
        if shared_movies:
            add_shared_result(movie_uri, shared_movies, {"directors": directors})

    for movie_uri, data in shared_genre_data.items():
        shared_movies = [extract_id_from_uri(uri) for uri in data.get("sharedMovieUris", [])]
        genres = [genre["name"] for genre in data.get("genres", [])]
        if shared_movies:
            add_shared_result(movie_uri, shared_movies, {"genres": genres})


    #WISHED ACTORS
    for movie_uri, data in actor_movies.items():
        wished_actors = data.get("wishedActors", [])
        if not wished_actors:
            continue

        if movie_uri not in shared_results:
            shared_results[movie_uri] = {"shared_result": []}

        for wished_actor in wished_actors:
            add_shared_result(
                movie_uri,
                [movie_uri],  # Only include the specific movie as shared
                {
                    "wishedActor": [wished_actor["wishedActorName"]],
                    "wishedActorUri": [wished_actor["wishedActorUri"]],
                },
            )

    for movie_uri, data in director_movies.items():
        wished_directors = data.get("wishedDirectors", [])
        if not wished_directors:
            continue

        if movie_uri not in shared_results:
            shared_results[movie_uri] = {"shared_result": []}

        for wished_director in wished_directors:
            add_shared_result(
                movie_uri,
                [movie_uri],  # Only include the specific movie as shared
                {
                    "wishedDirector": [wished_director["wishedDirectorName"]],
                    "wishedDirectorUri": [wished_director["wishedDirectorUri"]],
                },
            )


    new_list_of_movies = []
    for uri, data in shared_results.items():
        new_list_of_movies.append(extract_id_from_uri(uri))

    print("Fetch other moviedata (titel,publicationdate etc....)")
    movie_data = fetch_movie_data(new_list_of_movies,g) 

    for uri, data in shared_results.items():
        try:
            shared_results[uri]["title"] = movie_data[uri]["title"]
            shared_results[uri]["publicationDate"] = movie_data[uri]["publicationDate"]
            shared_results[uri]["imdbId"] = movie_data[uri]["imdbId"]
        except:
            pass

    movie_data_for_target_movies = fetch_movie_data(list_of_movies,g) 


    return shared_results, movie_data_for_target_movies
  
    #with open("reccomendation_data_dump.json", "w", encoding="utf-8") as file:
        #json.dump(shared_results, file, ensure_ascii=False, indent=2)