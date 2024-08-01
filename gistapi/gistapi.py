"""
Exposes a simple HTTP API to search a users Gists via a regular expression.

Github provides the Gist service as a pastebin analog for sharing code and
other develpment artifacts.  See http://gist.github.com for details.  This
module implements a Flask server exposing two endpoints: a simple ping
endpoint to verify the server is up and responding and a search endpoint
providing a search across all public Gists for a given Github account.
"""
import re

import requests
from flask import Flask, jsonify, request

from utils import gists_for_user, gist_content

app = Flask(__name__)


@app.route("/ping")
def ping():
    """Provide a static response to a simple GET request."""
    return "pong"


@app.route("/api/v1/search", methods=['POST'])
def search():
    """Provides matches for a single pattern across a single users gists.

    Pulls down a list of all gists for a given user and then searches
    each gist for a given regular expression.

    Returns:
        A Flask Response object of type application/json.  The result
        object contains the list of matches along with a 'status' key
        indicating any failure conditions.
    """
    post_data = request.get_json()

    username = post_data['username']
    pattern = post_data['pattern']

    result = {
        'status': 'success',
        'username': username,
        'pattern': pattern,
        'matches': []
    }

    # Compile the pattern for better performance in loop
    regex = re.compile(pattern)

    gists = gists_for_user(username)
    if gists is None:
        result['status'] = 'error'
        result['message'] = 'Failed to fetch gists. Please check the username and try again.'
        return jsonify(result), 400

    for gist in gists:
        gist_details = gist_content(gist['url'])
        if gist_details is None:
            continue

        for filename, file_info in gist_details['files'].items():
            file_content = requests.get(file_info['raw_url']).text

            if regex.search(file_content):
                match_info = {
                    'gist_id': gist['id'],
                    'filename': filename,
                    'url': gist['html_url']
                }
                result['matches'].append(match_info)

    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=9876)
