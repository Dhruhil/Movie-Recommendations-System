# SemanticProject

Movie Recommendation System

A movie recommendation system that utilizes a knowledge graph fetched from Wikidata, comprising over ___270k movies___ and ___3m+ triples___. The knowledge graph is hosted locally on a Jena Fuseki Server, which is then SPARQL queried from the Flask webapp using RDFLib. It infers relationships and scores movies based on a grading system, offering a user-friendly interface that provides insightful recommendations to users, and also provides recommendation insights.

![SystemOverview (7)](https://github.com/user-attachments/assets/4416abaa-dd25-499a-8004-d8bfde8fc5e1)

# Running Instructions

All these commands should be executed inside the top-level folder `SemanticProject`.

## Step 1: Setup Jena Fuseki Server

Make sure you have Java and JDK23 installed

```bash
java --version
```

If not, install [Java](https://www.java.com/sv/download/) and [Java Development Kit 23](https://www.oracle.com/java/technologies/downloads/).

Then run the commands to start the Jena Fuseki Server for hosting the local knowledge graph. This command will load and export the already existing `.ttl` file into a TDB2 format, which is a high-performance storage format used by Apache Jena for persisting RDF data.

```bash
java -cp jena-fuseki-server-5.2.0.jar tdb2.tdbloader --loc=tdb2 model/local_graph/wikidata_graph_builder/wikidata_derived_graph.ttl
```

Start Jena Fuseki Server and load the TDB2 dataset

```bash
java -jar jena-fuseki-server-5.2.0.jar --loc=tdb2 /dataset
```

## Step 2: Install Python and Dependencies

Download [Python](https://www.python.org/downloads/) if you don't already have it, Run the command below. This command will install the required dependencies for this project using `pip`.

```bash
python -m pip install -r requirements.txt
```

## Step 3: Start the Flask Webapp
```bash
python app.py
```



