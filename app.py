from flask import Flask, request, jsonify
from models import db, Story, Scene, SceneVersion
from datetime import datetime
from ai import rate_screenplay, convert_to_screenplay
from dotenv import load_dotenv
import os
load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///stories.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['API_KEY'] = os.environ.get("API_KEY")

db.init_app(app)

@app.before_first_request
def create_tables():
    db.create_all()

@app.route('/api/stories', methods=['POST'])
def create_story():
    data = request.get_json()
    story_title = data.get('title')

    if not story_title:
        return jsonify({'error': 'Story title is required'}), 400

    new_story = Story(title=story_title)
    db.session.add(new_story)
    db.session.commit()

    return jsonify({'message': 'Story created successfully', 'story': {'id': new_story.id, 'title': new_story.title}}), 201

@app.route('/api/stories/<int:story_id>/scenes', methods=['POST'])
def create_scene(story_id):
    data = request.get_json()
    scene_title = data.get('title')
    scene_content = data.get('content')

    if not scene_title or not scene_content:
        return jsonify({'error': 'Scene title and content are required'}), 400

    story = Story.query.get(story_id)
    if not story:
        return jsonify({'error': 'Story not found'}), 404

    new_scene = Scene(story_id=story_id, title=scene_title, content=scene_content)
    db.session.add(new_scene)
    db.session.commit()

    return jsonify({'message': 'Scene created successfully', 'scene': {'id': new_scene.id, 'title': new_scene.title, 'content': new_scene.content}}), 201

@app.route('/api/scenes/<int:scene_id>', methods=['PUT', 'PATCH'])
def edit_scene(scene_id):
    data = request.get_json()
    scene = Scene.query.get(scene_id)
    if not scene:
        return jsonify({'error': 'Scene not found'}), 404

    scene.title = data.get('title', scene.title)
    scene.content = data.get('content', scene.content)

    db.session.commit()

    return jsonify({'message': 'Scene updated successfully', 'scene': {'id': scene.id, 'title': scene.title, 'content': scene.content}}), 200

@app.route('/api/convert_to_screenplay', methods=['POST'])
def convert_to_screenplay_route():
    data = request.get_json()
    text_content = data.get('text-content')
    screenplay = convert_to_screenplay(text_content, app.config['API_KEY'])
    return jsonify({'screenplay': screenplay})

@app.route('/api/score_screenplay', methods=['POST'])
def score_screenplay_route():
    data = request.get_json()
    screenplay = data.get('screenplay')
    score = rate_screenplay(screenplay, app.config['API_KEY'])
    return score

if __name__ == '__main__':
    app.run(debug=True)
    