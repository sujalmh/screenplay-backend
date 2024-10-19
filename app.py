from flask import Flask, request, jsonify
from models import db, Story, Scene, SceneVersion
from datetime import datetime
from ai import rate_screenplay, convert_to_screenplay
from dotenv import load_dotenv
import os
load_dotenv()

# Initialize the Flask app and configure the database
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///stories.db'  # Example SQLite DB
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['API_KEY'] = os.environ.get("API_KEY")

# Initialize SQLAlchemy with the app
db.init_app(app)

# Create database tables (if they don't exist)
@app.before_first_request
def create_tables():
    db.create_all()

# Route to create a new story
@app.route('/api/stories', methods=['POST'])
def create_story():
    data = request.get_json()

    # Extract story title from the request data
    story_title = data.get('title')

    if not story_title:
        return jsonify({'error': 'Story title is required'}), 400

    # Create new story
    new_story = Story(title=story_title)
    db.session.add(new_story)
    db.session.commit()

    return jsonify({'message': 'Story created successfully', 'story': {'id': new_story.id, 'title': new_story.title}}), 201

# Route to create a new scene for a specific story
@app.route('/api/stories/<int:story_id>/scenes', methods=['POST'])
def create_scene(story_id):
    data = request.get_json()

    # Extract scene title and content from the request data
    scene_title = data.get('title')
    scene_content = data.get('content')

    if not scene_title or not scene_content:
        return jsonify({'error': 'Scene title and content are required'}), 400

    # Ensure the story exists
    story = Story.query.get(story_id)
    if not story:
        return jsonify({'error': 'Story not found'}), 404

    # Create new scene
    new_scene = Scene(story_id=story_id, title=scene_title, content=scene_content)
    db.session.add(new_scene)
    db.session.commit()

    return jsonify({'message': 'Scene created successfully', 'scene': {'id': new_scene.id, 'title': new_scene.title, 'content': new_scene.content}}), 201

# Route to edit an existing scene (update title or content)
@app.route('/api/scenes/<int:scene_id>', methods=['PUT', 'PATCH'])
def edit_scene(scene_id):
    data = request.get_json()

    # Find the scene by ID
    scene = Scene.query.get(scene_id)
    if not scene:
        return jsonify({'error': 'Scene not found'}), 404

    # Update scene title and content
    scene.title = data.get('title', scene.title)
    scene.content = data.get('content', scene.content)

    db.session.commit()

    return jsonify({'message': 'Scene updated successfully', 'scene': {'id': scene.id, 'title': scene.title, 'content': scene.content}}), 200

@app.route('/api/convert_to_screenplay', methods=['POST'])
def convert_to_screenplay_route():
    data = request.get_json()

    # Extract scene title and content from the request data
    text_content = data.get('text-content')
    screenplay = convert_to_screenplay(text_content, app.config['API_KEY'])
    return jsonify({'screenplay': screenplay})

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
    