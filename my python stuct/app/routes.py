from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, 
    jwt_required, 
    get_jwt_identity
)
from .models import db, User
from datetime import datetime, timedelta

auth = Blueprint('auth', __name__)

@auth.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Validate input
    if not all(key in data for key in ['first_name', 'last_name', 'email', 'password']):
        return jsonify({"error": "Missing required fields"}), 400

    # Check if user already exists
    existing_user = User.query.filter_by(email=data['email']).first()
    if existing_user:
        return jsonify({"error": "Email already registered"}), 409

    # Create new user
    new_user = User(
        first_name=data['first_name'],
        last_name=data['last_name'],
        email=data['email']
    )
    new_user.set_password(data['password'])
    
    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({
            "message": "User registered successfully",
            "user": new_user.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@auth.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    # Validate input
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"error": "Missing email or password"}), 400

    # Find user
    user = User.query.filter_by(email=data['email']).first()
    
    # Validate credentials
    if not user or not user.check_password(data['password']):
        return jsonify({"error": "Invalid credentials"}), 401

    # Update last login
    user.last_login = datetime.utcnow()
    db.session.commit()

    # Create access token
    access_token = create_access_token(
        identity=user.uuid,
        expires_delta=timedelta(hours=2)
    )

    return jsonify({
        "access_token": access_token,
        "user": user.to_dict()
    }), 200

@auth.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    current_user_uuid = get_jwt_identity()
    user = User.query.filter_by(uuid=current_user_uuid).first()
    
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify(user.to_dict()), 200