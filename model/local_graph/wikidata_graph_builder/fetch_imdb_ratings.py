import time
from SPARQLWrapper import SPARQLWrapper, JSON
from rdflib import Graph, URIRef, Literal, Namespace, RDF, RDFS
from rdflib.plugins.sparql import prepareQuery
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# Ladda RDF-graf
print("Loading graph...")
g = Graph()
file_path = "model/graph/local_graph/movies.ttl"
g.parse(file_path, format="turtle")
print("Loaded graph")

# Definiera SPARQL-frågan
local_query = prepareQuery("""
    PREFIX wdt: <http://www.wikidata.org/prop/direct/>
    PREFIX wd: <http://www.wikidata.org/entity/> 
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>    

    SELECT ?movie ?label ?imdb WHERE {
        ?movie rdfs:label ?label .
        ?movie wdt:P345 ?imdb .
    }
""")

# Funktion för att extrahera ID från URI
def extract_id_from_uri(uri):
    """Extract the movie ID from a URI."""
    return uri.split("/")[-1]

# Funktion för att hämta IMDb-ID:n från grafen
def fetch_ids(query):
    """Fetch movie and IMDb IDs from the RDF graph."""
    movie_and_IMDB_ids = []
    for row in g.query(query):
        movie_and_IMDB_ids.append({
            "movieid": extract_id_from_uri(str(row.movie)),
            "imdbid": str(row.imdb)
        })
    return movie_and_IMDB_ids

# Funktion för att hämta IMDb-ratings
def fetch_IMDB_ratings_optimized(movie_and_IMDB_ids):
    properties = Namespace("http://www.wikidata.org/prop/direct/")
    graph = Graph()

    def fetch_data(row, session):
        """Fetch IMDb rating for a single movie."""
        try:
            url = f"https://www.omdbapi.com/?i={row['imdbid']}&apikey=bbe16d5f"
            response = session.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            return row["movieid"], data.get("imdbRating")
        except Exception as e:
            print(f"Error fetching data for IMDb ID {row['imdbid']}: {e}")
            return row["movieid"], None

    start_time = time.time()

    # Use ThreadPoolExecutor for concurrent requests
    with requests.Session() as session, ThreadPoolExecutor(max_workers=100) as executor:
        future_to_row = {executor.submit(fetch_data, row, session): row for row in movie_and_IMDB_ids}

        for i, future in enumerate(as_completed(future_to_row), start=1):
            movieid, imdb_rating = future.result()
            if imdb_rating is not None:
                movie_uri = URIRef(f"http://www.wikidata.org/entity/{movieid}")
                graph.add((movie_uri, properties.P5201, Literal(imdb_rating)))

            # Print progress
            if i % 100 == 0 or i == len(movie_and_IMDB_ids):
                elapsed = time.time() - start_time
                print(f"Processed {i}/{len(movie_and_IMDB_ids)} movies in {elapsed:.2f} seconds")

    return graph

# Hämta data från SPARQL och processa IMDb-ratings
movie_and_IMDB_ids = fetch_ids(local_query)
rdf_graph = fetch_IMDB_ratings_optimized(movie_and_IMDB_ids)

# Spara RDF-grafen till en fil
output_file = "movies_with_imdbRatings_optimized.ttl"
rdf_graph.serialize(destination=output_file, format="turtle")
print(f"Extended graph saved to '{output_file}'.")
