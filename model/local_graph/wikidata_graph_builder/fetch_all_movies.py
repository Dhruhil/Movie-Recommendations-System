import time
from SPARQLWrapper import SPARQLWrapper, JSON
from rdflib import Graph, URIRef, Literal, Namespace, RDF, RDFS

def fetch_movies_and_build_graph():
    sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
    sparql.setReturnFormat(JSON)
    query = """
     SELECT DISTINCT ?movie ?movieName ?imdb WHERE {
          ?movie wdt:P31 wd:Q11424. # Instance of a movie
          ?movie wdt:P345 ?imdb. #must have an imdb id
          
          #attempt to fetch the English label
          OPTIONAL { ?movie rdfs:label ?movieNameEn. FILTER(LANG(?movieNameEn) = "en") }
          
          #fallback to any available label
          OPTIONAL { ?movie rdfs:label ?movieNameFallback. }

          #prioritize English label if available, otherwise use fallback
          BIND(COALESCE(?movieNameEn, ?movieNameFallback) AS ?movieName)
        }
    """
    try:
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        ret = sparql.queryAndConvert()
        results = ret["results"]["bindings"]

        g = Graph()
        entities = Namespace("http://www.wikidata.org/entity/")
        g.bind("wd", entities)

        properties = Namespace("http://www.wikidata.org/prop/direct/")
        g.bind("wdt",properties)


        for result in results:
            movie_uri = URIRef(result["movie"]["value"])
            imdb_id = Literal(result["imdb"]["value"])
            if "movieName" in result:
                movie_name = Literal(result["movieName"]["value"], lang="en")
                g.add((movie_uri, RDFS.label, movie_name))
            else:
                movie_name = Literal("Unknown", lang="en")
                g.add((movie_uri, RDFS.label, movie_name))

            g.add((movie_uri, RDF.type, entities.Q11424))  # Instance of movie
            g.add((movie_uri, RDFS.label, movie_name))
            g.add((movie_uri, properties.P345, imdb_id))  # IMDB ID

        #serialize the graph to a Turtle file
        with open("movies.ttl", "wb") as f:
            g.serialize(destination=f, format="turtle")

        print("Graph successfully saved to 'movies.ttl'.")
    except Exception as e:
        #handle exceptions (e.g., too many requests, timeout)
        print("An error occurred:", e)

print("Starting movie graph creation...")
fetch_movies_and_build_graph()
