from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from pytz import timezone
from sqlalchemy import PickleType

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone("Asia/Kolkata")))

    def __repr__(self):
        return f"<User {self.username}>"


class Story(db.Model):
    __tablename__ = 'story'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    image_link = db.Column(db.String(700), nullable=True)
    title = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone("Asia/Kolkata")))
    updated_at = db.Column(db.DateTime, onupdate=datetime.now(timezone("Asia/Kolkata")))
    description = db.Column(db.Text, nullable=False)

    scenes = db.relationship('Scene', backref='story', lazy=True, cascade="all, delete")

    def __repr__(self):
        return f"<Story {self.title}>"

class Scene(db.Model):
    __tablename__ = 'scene'

    id = db.Column(db.Integer, primary_key=True)
    story_id = db.Column(db.Integer, db.ForeignKey('story.id'), nullable=False)
    current_version_id = db.Column(db.Integer, db.ForeignKey('scene_version.id'))
    created_at = db.Column(db.DateTime, default=datetime.now(timezone("Asia/Kolkata")))
    updated_at = db.Column(db.DateTime, onupdate=datetime.now(timezone("Asia/Kolkata")))
    plot = db.Column(db.Integer, nullable=True)
    character_development = db.Column(db.Integer, nullable=True)
    dialogue = db.Column(db.Integer, nullable=True)
    originality = db.Column(db.Integer, nullable=True)
    theme = db.Column(db.Integer, nullable=True)
    emoji = db.Column(PickleType, nullable=True)
    emoji_name = db.Column(PickleType, nullable=True)
    sentiment_desc = db.Column(db.Text, nullable=True)
    summary = db.Column(db.Text, nullable=True)
    
    versions = db.relationship('SceneVersion', backref='scene', lazy=True, cascade="all, delete", foreign_keys='SceneVersion.scene_id')
    
    def __repr__(self):
        return f"<Scene {self.id}>"

class SceneVersion(db.Model):
    __tablename__ = 'scene_version'

    id = db.Column(db.Integer, primary_key=True)
    scene_id = db.Column(db.Integer, db.ForeignKey('scene.id'), nullable=False)
    version_number = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    formatted = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone("Asia/Kolkata")))

    def __repr__(self):
        return f"<SceneVersion {self.version_number} for Scene {self.scene_id}>"

class Conversation(db.Model):
    __tablename__ = 'conversations'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50),db.ForeignKey('user.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f"<Conversation {self.id} - {self.user_id} - {self.role}>"
