import json
import os

from flask import Response

from v1 import app, common, db, models, password


@app.route('/login', methods=['POST'])
def login():
    username = os.getenv('USER_NAME')
    auth = common.authenticate(
        db,
        username,
        password,
        {})  # {} -> user_agent_env

    print(f"auth = {auth}")

    if not auth:
        response = {'message': 'Invalid username / password'}
        return Response(
            json.dumps(response),
            status=401,
            mimetype='application/json')

    response = {
        'message': 'Login successful',
        'user_id': auth
    }

    return Response(
        json.dumps(response),
        status=200,
        mimetype='application/json')
