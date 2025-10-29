import time
from SPARQLWrapper import SPARQLWrapper, JSON
from rdflib import Graph, URIRef, Literal, Namespace, RDF, RDFS
from rdflib.plugins.sparql import prepareQuery

# Load RDF graph
print("Loading graph...")
g = Graph()

files = ["movies.ttl", "movies_with_actors.ttl", "movies_with_directors.ttl", "movies_with_genres.ttl", "movies_with_mainsubjects.ttl", "movies_with_publicationdates.ttl" ]
for file_path in files:
    g.parse(file_path, format="turtle")
    print("Loaded graph " + file_path)

#save the complete graph
output_file = "wikidata_derived_graph.ttl"
g.serialize(destination=output_file, format="turtle")
print(f"Extended graph saved to '{output_file}'.")
