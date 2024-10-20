from flask import Flask, session, request, jsonify
from flask_cors import CORS
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Story, Scene, SceneVersion
from datetime import datetime, timedelta
from ai import rate_screenplay, convert_to_screenplay, summarize_screenplay
from dotenv import load_dotenv
import os
load_dotenv()

app = Flask(__name__)
CORS(app, supports_credentials=True)

app.config['JWT_SECRET_KEY'] = 'Num3R0n4u7s!Num3R0n4u7s!'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=6)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///stories.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['API_KEY'] = os.environ.get("API_KEY")

db.init_app(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)

with app.app_context():
    db.create_all()

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    user_exists = User.query.filter((User.username == username)).first()
    if user_exists:
        return jsonify({"message": "User with that username or email already exists"}), 400
    print(password)
    hashed_password = generate_password_hash(password)
    user = User(username=username, password=hashed_password)
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "User registered successfully"}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()

    if not user or not check_password_hash(user.password, password):
        return jsonify({"message": "Invalid username or password"}), 401

    access_token = create_access_token(identity=user.id, expires_delta=timedelta(hours=1))

    return jsonify(access_token=access_token), 200

@app.route('/api/add_story', methods=['POST'])
@jwt_required()
def create_story():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    data = request.get_json()
    story_title = data.get('title')

    if not story_title:
        return jsonify({'error': 'Story title is required'}), 400

    new_story = Story(title=story_title, user_id=current_user_id)
    db.session.add(new_story)
    db.session.commit()

    return jsonify({'message': 'Story created successfully', 'story': {'id': new_story.id, 'title': new_story.title}}), 201

@app.route('/api/story/<int:story_id>/add_scene', methods=['POST'])
@jwt_required()
def create_scene(story_id):
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

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
@jwt_required()
def edit_scene(scene_id):
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    data = request.get_json()
    scene = Scene.query.get(scene_id)
    if not scene:
        return jsonify({'error': 'Scene not found'}), 404

    scene.title = data.get('title', scene.title)
    scene.content = data.get('content', scene.content)

    db.session.commit()

    return jsonify({'message': 'Scene updated successfully', 'scene': {'id': scene.id, 'title': scene.title, 'content': scene.content}}), 200

@app.route('/api/convert_to_screenplay', methods=['POST'])
@jwt_required()
def convert_to_screenplay_route():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    data = request.get_json()
    text_content = data.get('text-content')
    screenplay = convert_to_screenplay(text_content, app.config['API_KEY'])
    return jsonify({'screenplay': screenplay})

@app.route('/api/score_screenplay', methods=['POST'])
@jwt_required()
def score_screenplay_route():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    data = request.get_json()
    screenplay = data.get('screenplay')
    score = rate_screenplay(screenplay, app.config['API_KEY'])
    return score

@app.route('/api/summarize_screenplay', methods=['POST'])
@jwt_required()
def summarize_screenplay_route():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    data = request.get_json()
    screenplay = data.get('screenplay')
    summary = summarize_screenplay(screenplay, app.config['API_KEY'])
    return summary

if __name__ == '__main__':
    app.run(debug=True)
    