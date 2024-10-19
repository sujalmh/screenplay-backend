from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# Define the Story model
class Story(db.Model):
    __tablename__ = 'story'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # Relationship with scenes
    scenes = db.relationship('Scene', backref='story', lazy=True, cascade="all, delete")

    def __repr__(self):
        return f"<Story {self.title}>"

# Define the Scene model
class Scene(db.Model):
    __tablename__ = 'scene'

    id = db.Column(db.Integer, primary_key=True)
    story_id = db.Column(db.Integer, db.ForeignKey('story.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)  # Scene content (includes setting)
    current_version_id = db.Column(db.Integer, db.ForeignKey('scene_version.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # Relationship with versions
    versions = db.relationship('SceneVersion', backref='scene', lazy=True, cascade="all, delete")

    def __repr__(self):
        return f"<Scene {self.title}>"

# Define the SceneVersion model
class SceneVersion(db.Model):
    __tablename__ = 'scene_version'

    id = db.Column(db.Integer, primary_key=True)
    scene_id = db.Column(db.Integer, db.ForeignKey('scene.id'), nullable=False)
    version_number = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<SceneVersion {self.version_number} for Scene {self.scene_id}>"
