import time
from SPARQLWrapper import SPARQLWrapper, JSON
from rdflib import Graph, URIRef, Literal, Namespace, RDF, RDFS
from rdflib.plugins.sparql import prepareQuery
#P57 Director 
#P161 Cast Member 
#P136 Genre 
#P577 Publication Date
#P162 Producer
#P1431 Executive Producer
#P58 Screenwriter
#P144 Based On
#P495 Country Of Origin
#P915 Filming Location
#P840 Narrative Location
#P344 Director of Photography
#P345 IMDB ID
#P2408 Set in period
#P2047 Duration
#P1040 Film editor
#P921 Main subject 
#P750 Distributed by
#P2515 Costume designer
#P2554 Production Designer
#P2142 Box office
#P2208 Average shot length
#P2755 Exploitation Mark Number
#P3803 Original Film Format
#P3816 Film Script
#P1476 Title
#P676 lyricist
#P364 Original Language 
#P166 Award Received
#P8345 Media Franchise
#P179 Part of the series
#P2769 Budget
#P272 Production Company
#P4805 Make up artist
#P2130 Capital cost
#P462 Color
#P1258 Rotten Tomatoes ID
#P1411 Nominated for
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
    SELECT DISTINCT ?targetMovie ?mainsubject ?mainsubjectLabel WHERE {{
        VALUES ?targetMovie {{ {movie_filter} }}
        ?targetMovie wdt:P921 ?mainsubject .
        OPTIONAL {{ ?mainsubject rdfs:label ?mainsubjectLabel . FILTER(LANG(?mainsubjectLabel) = "en") }}
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
                mainsubject_uri = URIRef(result["mainsubject"]["value"])
                mainsubject_name = Literal(result["mainsubjectLabel"]["value"], lang="en") if "mainsubjectLabel" in result else Literal("Unknown", lang="en")

                # Add mainsubject triples to the graph
                #g.add((mainsubject_uri, RDF.type, entities.Q5))  # Instance of human
                g.add((mainsubject_uri, RDFS.label, mainsubject_name))
                g.add((movie_uri, properties.P921, mainsubject_uri))  #mainsubject relationship
            
            print(f"Successfully processed batch {i // batch_size + 1}.")
            break  # Exit retry loop if successful
        except Exception:
            attempts += 1
            print(f"Retrying batch {i // batch_size + 1} (Attempt {attempts}/{retry_attempts})...")
            time.sleep(10)  # Wait before retrying
    
    if attempts == retry_attempts:
        print(f"Failed to process batch {i // batch_size + 1} after {retry_attempts} attempts. Skipping...")

# Save the updated graph
output_file = "movies_with_mainsubjects.ttl"
g.serialize(destination=output_file, format="turtle")
print(f"Extended graph saved to '{output_file}'.")
