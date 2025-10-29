import json
import time


def calculate_movie_points(movie_data, movie_data_for_target_movies):
    # Define weights
    WEIGHTS = {
        "actors": 10,
        "genres": 5,
        "directors": 15,
        "wishedActor": 30,
        "wishedDirector": 30,
        "actor_director_combo": 50  #extra points for wishedActor and wishedDirector in the same movie
    }

    #extract publication years of target movies
    target_years = [
        int(movie_data_for_target_movies[movie]["publicationDate"].split("-")[0])
        for movie in movie_data_for_target_movies
    ]

    def calculate_proximity_bonus(publication_year):
        #award points based on closeness to target years
        proximity_points = 0
        for target_year in target_years:
            year_difference = abs(publication_year - target_year)
            if year_difference <= 5:  #close within 5 years gets higher points
                proximity_points += 20 - year_difference * 2  #linear decrease
        return proximity_points

    recommended_movies = []

    for movie_uri, details in movie_data.items():
        points = 0
        point_breakdown = {}  #record of why points were awarded

        for shared_entry in details.get("shared_result", []):
            shared_movies = shared_entry["sharedMovies"]
            common = shared_entry["common"]

            #check for regular categories like actors, genres, etc.
            for category, items in common.items():
                if category in WEIGHTS:
                    multiplier = max(len(shared_movies), 1)  #át least 1 multiplier even if sharedMovies is empty
                    category_points = len(items) * WEIGHTS[category] * multiplier
                    points += category_points

                    # Record the contribution of this category
                    point_breakdown[category] = {
                        "items": items,
                        "shared_movies": shared_movies,
                        "weight": WEIGHTS[category],
                        "points_awarded": category_points
                    }

            #check for wishedActor and wishedDirector interaction
            if "wishedActor" in common and "wishedDirector" in common:
                interaction_points = WEIGHTS["actor_director_combo"] * max(len(shared_movies), 1)
                points += interaction_points

                #record the interaction points
                point_breakdown["actor_director_combo"] = {
                    "wishedActor": common["wishedActor"],
                    "wishedDirector": common["wishedDirector"],
                    "shared_movies": shared_movies,
                    "points_awarded": interaction_points
                }

        #calculate proximity bonus
        try:
            publication_year = int(details.get("publicationDate", "0").split("-")[0])
            proximity_points = calculate_proximity_bonus(publication_year)
            points += proximity_points

            #record proximity bonus
            point_breakdown["proximity_bonus"] = {
                "publication_year": publication_year,
                "target_years": target_years,
                "points_awarded": proximity_points
            }
        except ValueError:
            point_breakdown["proximity_bonus"] = "Invalid or missing publication year"

        recommended_movies.append({
            "title": details.get("title"),
            "imdbId": details.get("imdbId"),
            "movie_uri": movie_uri,
            "points": points,
            "point_breakdown": point_breakdown,
            "shared_result": details.get("shared_result"),
            "publicationDate": details.get("publicationDate")
        })

    #sort movies by points (descending)
    recommended_movies.sort(key=lambda x: x["points"], reverse=True)

    return recommended_movies