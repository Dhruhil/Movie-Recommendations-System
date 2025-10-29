import time
from SPARQLWrapper import SPARQLWrapper, JSON
from rdflib import Graph, URIRef, Literal, Namespace, RDF, RDFS
from rdflib.plugins.sparql import prepareQuery

# Load RDF graph
print("Loading graph...")
g = Graph()
file_path = "movies.ttl"
g.parse(file_path, format="turtle")
print("Loaded graph")

# Define the local SPARQL query
local_query = prepareQuery("""
    PREFIX wdt: <http://www.wikidata.org/prop/direct/>
    PREFIX wd: <http://www.wikidata.org/entity/> 
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>    

    SELECT ?movie ?label ?imdb WHERE {
        ?movie rdfs:label ?label .
        ?movie wdt:P345 ?imdb .
    }
""")

# Extract movie IDs from the graph
def extract_id_from_uri(uri):
    return uri.split("/")[-1]

movie_ids = []
for row in g.query(local_query):
    movie_ids.append(extract_id_from_uri(str(row.movie)))

print(f"Fetched {len(movie_ids)} movies from the local graph.")

# SPARQL endpoint setup
sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
sparql.setMethod("POST")
sparql.setReturnFormat(JSON)

# Define batch processing
batch_size = 5000
retry_attempts = 5  # Number of retries per batch

def process_batch(batch):
    movie_filter = " ".join(f"wd:{movie}" for movie in batch)
    query = f"""
    SELECT DISTINCT ?targetMovie ?director ?directorLabel WHERE {{
        VALUES ?targetMovie {{ {movie_filter} }}
        ?targetMovie wdt:P57 ?director .
        OPTIONAL {{ ?director rdfs:label ?directorLabel . FILTER(LANG(?directorLabel) = "en") }}
    }}
    """
    sparql.setQuery(query)
    try:
        ret = sparql.queryAndConvert()
        return ret["results"]["bindings"]
    except Exception as e:
        print(f"Error querying batch: {e}")
        raise

# Process all batches
for i in range(0, len(movie_ids), batch_size):
    batch = movie_ids[i:i + batch_size]
    print(f"Processing batch {i // batch_size + 1} with {len(batch)} movies...")
    
    attempts = 0
    while attempts < retry_attempts:
        try:
            time.sleep(5)
            results = process_batch(batch)
            properties = Namespace("http://www.wikidata.org/prop/direct/")
            entities = Namespace("http://www.wikidata.org/entity/")
            
            for result in results:
                movie_uri = URIRef(result["targetMovie"]["value"])
                director_uri = URIRef(result["director"]["value"])
                director_name = Literal(result["directorLabel"]["value"], lang="en") if "directorLabel" in result else Literal("Unknown", lang="en")

                # Add director triples to the graph
                g.add((director_uri, RDF.type, entities.Q5))  # Instance of human
                g.add((director_uri, RDFS.label, director_name))
                g.add((movie_uri, properties.P57, director_uri))  #director relationship
            
            print(f"Successfully processed batch {i // batch_size + 1}.")
            break  # Exit retry loop if successful
        except Exception:
            attempts += 1
            print(f"Retrying batch {i // batch_size + 1} (Attempt {attempts}/{retry_attempts})...")
            time.sleep(10)  # Wait before retrying
    
    if attempts == retry_attempts:
        print(f"Failed to process batch {i // batch_size + 1} after {retry_attempts} attempts. Skipping...")

# Save the updated graph
output_file = "movies_with_directors.ttl"
g.serialize(destination=output_file, format="turtle")
print(f"Extended graph saved to '{output_file}'.")
