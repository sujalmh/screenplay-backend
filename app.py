from flask import Flask, session, request, jsonify
from flask_cors import CORS
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Story, Scene, SceneVersion, Conversation
from datetime import datetime, timedelta
from ai import generate_pitch_summary, generate_image, chatbot_chat, rate_screenplay, convert_to_screenplay, summarize_screenplay, clean_screenplay_text, convert_text_to_speech2, get_sentimental_analysis
from dotenv import load_dotenv
import json
import os
from pytz import timezone
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

@app.route('/api/register', methods=['POST'])
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

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()

    if not user or not check_password_hash(user.password, password):
        return jsonify({"message": "Invalid username or password"}), 401

    access_token = create_access_token(identity=user.id, expires_delta=timedelta(hours=1))

    return jsonify(access_token=access_token), 200

@app.route('/api/get_stories', methods=['GET'])
@jwt_required()
def get_stories():
    current_user_id = get_jwt_identity()
    user = db.session.get(User, current_user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    stories = Story.query.filter_by(user_id = current_user_id)
    scenes_data = []
    for story in stories:
        scenes_data.append({"title": story.title, "image_link": story.image_link, "created_at": story.created_at.strftime("%Y-%m-%d %H:%M:%S")
, "updated_at": story.updated_at, "description": story.description})
    return jsonify({"scenes_data": scenes_data}), 201

@app.route('/api/story/<int:story_id>/get_scenes', methods=['GET'])
@jwt_required()
def get_scenes(story_id):
    current_user_id = get_jwt_identity()
    user = db.session.get(User, current_user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    scenes = Scene.query.filter_by(story_id = story_id)
    scenes_data = []
    for scene in scenes:
        scene_version = db.session.get(SceneVersion, scene.current_version_id) 
        scenes.append({"title": scene_version.title})
    return jsonify({"scenes_data": scenes_data}), 201

@app.route('/api/add_story', methods=['POST'])
@jwt_required()
def create_story():
    current_user_id = get_jwt_identity()
    user = db.session.get(User, current_user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    data = request.get_json()
    story_title = data.get('title')
    desc = data.get('description')

    if not story_title:
        return jsonify({'error': 'Story title is required'}), 400

    new_story = Story(title=story_title, user_id=current_user_id, description=desc, image_link=generate_image(desc, app.config['API_KEY']))
    db.session.add(new_story)
    db.session.commit()

    return jsonify({'message': 'Story created successfully', 'story': {'id': new_story.id, 'title': new_story.title}}), 201

@app.route('/api/add_story/image/<int:story_id>', methods=['POST'])
@jwt_required()
def create_story_image(story_id):
    current_user_id = get_jwt_identity()
    user = db.session.get(User, current_user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    story = db.session.get(Story, story_id)

    story.image_link = generate_image(story.description, app.config['API_KEY'])
    db.session.commit()

    return jsonify({'message': 'Image created successfully'}), 201


@app.route('/api/story/<int:story_id>/add_scene', methods=['POST'])
@jwt_required()
def create_scene(story_id):
    current_user_id = get_jwt_identity()
    user = db.session.get(User, current_user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    data = request.get_json()
    scene_title = data.get('title')
    scene_content = data.get('content')

    if not scene_title or not scene_content:
        return jsonify({'error': 'Scene title and content are required'}), 400

    story = db.session.get(Story, story_id)
    if not story:
        return jsonify({'error': 'Story not found'}), 404

    new_scene = Scene(story_id=story_id)
    db.session.add(new_scene)
    db.session.flush()

    initial_version = SceneVersion(
        scene_id=new_scene.id,
        version_number=1,
        title=scene_title,
        content=scene_content
    )
    db.session.add(initial_version)
    db.session.flush()

    new_scene.current_version_id = initial_version.id
    db.session.commit()

    return jsonify({
        'message': 'Scene created successfully',
        'scene': {
            'id': new_scene.id,
            'title': initial_version.title,
            'content': initial_version.content,
            'version': initial_version.version_number
        }
    }), 201

@app.route('/api/story/<int:story_id>/edit_scene_formatted/<int:scene_id>', methods=['POST'])
@jwt_required()
def edit_scene_formatted(story_id, scene_id):
    current_user_id = get_jwt_identity()
    user = db.session.get(User, current_user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    data = request.get_json()
    scene_title = data.get('title')
    scene_formatted = data.get('content')

    scene = db.session.get(Scene, scene_id)

    if not scene_title or not scene_formatted:
        return jsonify({'error': 'Scene title and content are required'}), 400

    story = db.session.get(Story, story_id)
    if not story:
        return jsonify({'error': 'Story not found'}), 404

    new_version = SceneVersion(
        scene_id=scene_id,
        version_number=scene.current_version_id+1,
        title=scene_title,
        content=scene.content,
        formatted=scene_formatted
    )
    db.session.add(new_version)
    db.session.flush()

    scene.current_version_id = new_version.id
    db.session.commit()

    return jsonify({
        'message': 'Scene updated successfully',
        'scene': {
            'id': scene_id,
            'title': new_version.title,
            'formatted': new_version.scene_formatted,
            'version': new_version.version_number
        }
    }), 201

@app.route('/api/get_scene_formatted/scene/<int:scene_id>', methods=['GET'])
@jwt_required()
def get_scene_formatted(scene_id):
    current_user_id = get_jwt_identity()
    user = db.session.get(User, current_user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    scene = db.session.get(Scene, scene_id)
    scene_version = db.session.get(SceneVersion, scene.current_version_id)

    return jsonify({
        'formatted': scene_version.formatted
    }), 201


@app.route('/api/story/<int:story_id>/edit_scene_text/<int:scene_id>', methods=['POST'])
@jwt_required()
def edit_scene_text(story_id, scene_id):
    current_user_id = get_jwt_identity()
    user = db.session.get(User, current_user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    data = request.get_json()
    scene_title = data.get('title')
    scene_content = data.get('content')

    scene = db.session.get(Scene, scene_id)

    if not scene_title or not scene_content:
        return jsonify({'error': 'Scene title and content are required'}), 400

    story = db.session.get(Story, story_id)
    if not story:
        return jsonify({'error': 'Story not found'}), 404

    new_version = SceneVersion(
        scene_id=scene_id,
        version_number=scene.current_version_id+1,
        title=scene_title,
        content=scene_content
    )
    db.session.add(new_version)
    db.session.flush()

    scene.current_version_id = new_version.id
    db.session.commit()

    return jsonify({
        'message': 'Scene updated successfully',
        'scene': {
            'id': scene_id,
            'title': new_version.title,
            'content': new_version.content,
            'version': new_version.version_number
        }
    }), 201

@app.route('/api/convert_to_screenplay/scene/<int:scene_id>', methods=['POST'])
@jwt_required()
def convert_to_screenplay_route(scene_id):
    current_user_id = get_jwt_identity()
    user = db.session.get(User, current_user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    scene = db.session.get(Scene, scene_id)
    scene_version = db.session.get(SceneVersion, scene.current_version_id)

    text_content = scene_version.content
    screenplay = convert_to_screenplay(text_content, app.config['API_KEY'])
    scene_version.formatted = screenplay
    db.session.commit()
    return jsonify({'screenplay': screenplay})

@app.route('/api/score_screenplay/scene/<int:scene_id>', methods=['POST'])
@jwt_required()
def score_screenplay_route(scene_id):
    current_user_id = get_jwt_identity()
    user = db.session.get(User, current_user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    scene = db.session.get(Scene, scene_id)
    scene_version = db.session.get(SceneVersion, scene.current_version_id)
    screenplay = scene_version.content
    score = json.loads(rate_screenplay(screenplay, app.config['API_KEY']))
    scene.plot = score["Plot"] or 0
    scene.character_development = score["Character Development"] or 0
    scene.dialogue = score["Dialogue"] or 0
    scene.originality = score["Originality"] or 0
    scene.theme = score["Theme"] or 0
    db.session.commit()
    print(score, type(score))
    return {"message": "Successfully scored", "Plot": scene.plot, "Character Development": scene.character_development, "Dialogue": scene.dialogue, "Originality": scene.originality, "Theme": scene.theme}

@app.route('/api/get_score/scene/<int:scene_id>', methods=['GET'])
@jwt_required()
def get_score(scene_id):
    current_user_id = get_jwt_identity()
    user = db.session.get(User, current_user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    scene = db.session.get(Scene, scene_id)
    return {"scores": {"Plot": scene.plot, "Character Development": scene.character_development, "Dialogue": scene.dialogue, "Originality": scene.originality, "Theme": scene.theme}}

@app.route('/api/summarize_screenplay/scene/<int:scene_id>', methods=['POST'])
@jwt_required()
def summarize_screenplay_route(scene_id):
    current_user_id = get_jwt_identity()
    user = db.session.get(User, current_user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    scene = db.session.get(Scene, scene_id)
    screenplay = scene.formatted
    summary = summarize_screenplay(screenplay, app.config['API_KEY'])
    return summary

@app.route('/api/scene_to_voice', methods=['POST'])
@jwt_required()
def scene_to_voice_route():
    current_user_id = get_jwt_identity()
    user = db.session.get(User, current_user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    data = request.get_json()
    screenplay = data.get('screenplay')
    cleaned_text = clean_screenplay_text(screenplay,app.config['API_KEY'])
    convert_text_to_speech2(cleaned_text, "C:/Users/Acer/Desktop/screenplay_audio3.mp3")

    return jsonify({"asbcd": "abacd"})

@app.route('/api/sentiment_analysis/scene/<int:scene_id>', methods=['POST'])
@jwt_required()
def sentiment_analysis_route(scene_id):
    current_user_id = get_jwt_identity()
    user = db.session.get(User, current_user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    scene = db.session.get(Scene, scene_id)
    scene_version = db.session.get(SceneVersion, scene.current_version_id)
    screenplay = scene_version.formatted
    scene_emoji, scene_description = get_sentimental_analysis(screenplay, app.config['API_KEY'])
    emoji_list = []
    emojiNames_list = []
    for emoji_dict in scene_emoji:
        emoji_list.append(emoji_dict["emoji"].encode("utf-8").decode('utf-8'))
        emojiNames_list.append(emoji_dict["name"])
    scene.emoji = emoji_list
    scene.emoji_name = emojiNames_list
    scene.sentiment_desc = scene_description
    db.session.commit()    
    return jsonify({"emoji": scene_emoji, "desc": scene_description})

@app.route('/api/get_sentiment_analysis/scene/<int:scene_id>', methods=['GET'])
@jwt_required()
def get_sentiment_analysis(scene_id):
    current_user_id = get_jwt_identity()
    user = db.session.get(User, current_user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404
    scene = db.session.get(Scene, scene_id)
    emojis_data=[]
    for i in range(len(scene.emoji)):
        emojis_data.append({"emoji": scene.emoji[i], "emoji_name": scene.emoji_name[i]})  
    return jsonify({"emoji_data": emojis_data, "desc": scene.sentiment_desc})

@app.route('/api/generate_summary/scene/<int:scene_id>', methods=['POST'])
@jwt_required()
def generate_summary_route(scene_id):
    current_user_id = get_jwt_identity()
    user = db.session.get(User, current_user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404
    scene = db.session.get(Scene, scene_id)
    scene_version = db.session.get(SceneVersion, scene.current_version_id)
    summary = generate_pitch_summary(scene_version.formatted, app.config['API_KEY'])
    scene.summary = summary
    db.session.commit()
    print(summary)
    return jsonify({"summary": scene.summary})

@app.route('/api/get_summary/scene/<int:scene_id>', methods=['GET'])
@jwt_required()
def get_summary(scene_id):
    current_user_id = get_jwt_identity()
    user = db.session.get(User, current_user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404
    scene = db.session.get(Scene, scene_id)
    summary = json.loads(scene.summary)
    title = summary["Title"]
    logline = summary["Logline"]
    pitch_summary = summary["Pitch summary"]
    return jsonify({"Title": title, "Logline": logline, "Pitch summary": pitch_summary})

@app.route('/api/chat', methods=['POST'])
@jwt_required()
def chat():
    current_user_id = get_jwt_identity()
    user = db.session.get(User, current_user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404
    data = request.get_json()
    user_input = data.get('userInput')
    print(user_input)
    return chatbot_chat(current_user_id, user_input, app.config['API_KEY'])

@app.route('/api/get_chat', methods=['GET'])
@jwt_required()
def get_chat():
    current_user_id = get_jwt_identity()
    user = db.session.get(User, current_user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404
    chats = Conversation.query.filter_by(user_id=current_user_id)
    chats_data = []
    for chat in chats:
        chats_data.append({"id": chat.id, "role": chat.role, "content": chat.content})
    return jsonify(chats_data)


if __name__ == '__main__':
    app.run(debug=True)
    