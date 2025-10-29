"""
This script initializes and configures a Flask application
for handling search and recommendation
functionalities. It preloads data to optimize
performance and registers blueprints for modular routing.
The app serves static files, dynamically preloaded content,
and provides an index page locally at 127.0.0.1:5000.

To use the recommendation functionality, the
Jena Fuseki server must be started. Refer to the README file
for setup instructions and additional details.
"""
import os
from flask import Flask, send_from_directory, render_template
from model.local_graph.init import init
from controller.search_controller import search_blueprint
from controller.recommend_controller import recommend_blueprint

app = Flask(
    __name__,
    template_folder='view',
    static_folder='view/static',
    static_url_path='/static'
    )

with app.app_context():

    # Preload the required data for the search module to avoid unnecessary delays during runtime.
    # This initialization prevents the need to repeatedly send SPARQL queries to the Fuseki server
    # by loading the graph and searchable entities (movies, actors, directors) into memory.
    # These preloaded data structures are registered globally in Flask's app config for easy access
    # throughout the application.

    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":

        graph,searchable_movies,searchable_actors,searchable_directors = init()

        app.config['LOCAL_GRAPH'] = graph
        app.config['SEARCHABLE_MOVIES'] = searchable_movies
        app.config['SEARCHABLE_ACTORS'] = searchable_actors
        app.config["SEARCHABLE_DIRECTORS"] = searchable_directors


app.register_blueprint(search_blueprint)
# Registers the 'search_blueprint' to handle routes related to search functionality.
# POST /search

app.register_blueprint(recommend_blueprint)
# Registers the 'register_blueprint' to handle routes related to recommend functionality.
# POST /recommend

@app.route('/node_modules/<path:filename>')
def serve_node_modules(filename):
    """
    Serves files from the 'node_modules' directory to allow the frontend
    to access libraries such as Bootstrap and Gridstack.
    Files can be accessed via the '/node_modules/<path:filename>' URL pattern.
    """
    return send_from_directory('node_modules', filename)

@app.route('/', methods=['GET'])
def home():
    """
    Handles GET requests to the root URL ('/') by rendering the 'index.html' template.
    The 'index.html' file is located in the 'view' directory ('view/index.html').
    """
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
