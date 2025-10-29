from flask import Blueprint, request, jsonify, current_app
from model.recommend.calculate_movie_points import calculate_movie_points
from model.recommend.combine_recommendation_data import combine_recommendation_data
from model.search.main import search,add_movie_metadata,add_person_metadata
import json
import time

def _map_metadata_to_recommended_movies(recommended_movies, recommended_movies_metadata):
    metadata_mapping = {meta["uri"]: meta for meta in recommended_movies_metadata}

    for movie in recommended_movies:
        movie_uri = movie["movie_uri"]
        movie["metadata"] = metadata_mapping.get(movie_uri, None)  #attach metadata or none shouldnt happen but justincase

    return recommended_movies

def extract_id_from_uri(uri):
    return uri.split("/")[-1]

recommend_blueprint = Blueprint('recommend', __name__)

@recommend_blueprint.route('/recommend', methods=['POST'])
def recommend():
    data = request.get_json()
    #movies = data.get('movies', [])

    #num moviesquentin
    #movies_count = len(movies)
    #print("Received Metadata:", movies)
    #print("Total Movies:", movies_count)
 
    print(data)

    movie_ids = []
    actor_ids = []
    director_ids = []
    for media in data["allMetadata"]:
        print(media)
        if media["type"] == "movie":
            movie_ids.append(extract_id_from_uri(media["uri"]))
        elif media["type"] == "actor":
            actor_ids.append(extract_id_from_uri(media["uri"]))
        elif media["type"] == "director":
            director_ids.append(extract_id_from_uri(media["uri"]))

    print(movie_ids)
    print(actor_ids)
    print(director_ids)

    shared_results, movie_data_for_target_movies = combine_recommendation_data(movie_ids, actor_ids, director_ids, current_app.config['LOCAL_GRAPH'])


    print("Calculating movie points...")
    recommended_movies = calculate_movie_points(shared_results, movie_data_for_target_movies) # !!!!!!
    recommended_movies = recommended_movies[:200] #start with 200 best


    fetch_movie_metadata_for_this = []
    for movie in recommended_movies:
        fetch_movie_metadata_for_this.append({"uri": movie["movie_uri"], "imdb": movie["imdbId"]})
    
    print("Getting movie metadata....")
    recommended_movies_metadata = add_movie_metadata(fetch_movie_metadata_for_this) # !!!!!!


    recommended_movies = _map_metadata_to_recommended_movies(recommended_movies, recommended_movies_metadata)
 
    #with open("johan_recommended_with_metadata.json", "w", encoding="utf-8") as file:
        #json.dump(recommended_movies, file, ensure_ascii=False, indent=2)

    #time.sleep(999999999)

    #now we got everything, imdb ratings, recommmended score, everything
    #TODO IS TO DO A FINAL POLISH ON THE SCORE AND LOWER SCORES WITH BAD IMDB RATINGS
    #adjust_score_based_on_imdb_ratings()


    def adjust_score_based_on_imdb_ratings(recommended_movies):
        baseline_rating = 7.0
        low_rating_threshold = 5.0

        for movie in recommended_movies:
            metadata = movie.get("metadata", None)
            if metadata and "ratings" in metadata:
                imdb_rating = metadata["ratings"]
                imdb_rating = float(imdb_rating)
                # Calculate multiplier
                if imdb_rating < low_rating_threshold:
                    multiplier = imdb_rating / 10.0  # Strong penalty
                else:
                    multiplier = imdb_rating / baseline_rating  # Normalization
                # Adjust points
                original_points = movie["points"]
                adjusted_points = original_points * multiplier
                movie["points"] = adjusted_points

                # Add to point breakdown
                if "point_breakdown" not in movie:
                    movie["point_breakdown"] = {}

                movie["point_breakdown"]["imdb_adjustment"] = {
                    "original_points": original_points,
                    "imdb_rating": imdb_rating,
                    "multiplier": multiplier,
                    "adjusted_points": adjusted_points
                }
            else:
                # No adjustment if no metadata or ratings
                if "point_breakdown" not in movie:
                    movie["point_breakdown"] = {}
                movie["point_breakdown"]["imdb_adjustment"] = "No IMDb rating available"

        return recommended_movies


    # Example Usage
    recommended_movies_adjusted = adjust_score_based_on_imdb_ratings(recommended_movies)
    recommended_movies_adjusted.sort(key=lambda x: x["points"], reverse=True)  #sort again
    recommended_movies_adjusted = recommended_movies_adjusted[:100] #discard the rest of the 100 potential shit movies

    #with open("johan_recommended_with_metadata_adjusted.json", "w", encoding="utf-8") as file:
        #json.dump(recommended_movies_adjusted, file, ensure_ascii=False, indent=2)

    #time.sleep(99999999)

    return json.dumps(recommended_movies_adjusted)



