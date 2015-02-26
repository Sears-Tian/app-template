#!/usr/bin/env python

import app_config
import json
import os
import static

from app_config import authomatic
from authomatic.adapters import WerkzeugAdapter
from etc.oauth import oauth_required, get_credentials, save_credentials
from flask import Flask, make_response, render_template
from etc.gdocs import GoogleDoc
from render_utils import make_context, smarty_filter, urlencode_filter
from werkzeug.debug import DebuggedApplication

app = Flask(__name__)
app.debug = app_config.DEBUG

app.add_template_filter(smarty_filter, name='smarty')
app.add_template_filter(urlencode_filter, name='urlencode')

# Example application views
@app.route('/')
@oauth_required
def index():
    """
    Example view demonstrating rendering a simple HTML page.
    """
    context = make_context()

    with open('data/featured.json') as f:
        context['featured'] = json.load(f)

    return render_template('index.html', **context)

@app.route('/comments/')
def comments():
    """
    Full-page comments view.
    """
    return render_template('comments.html', **make_context())

@app.route('/widget.html')
def widget():
    """
    Embeddable widget example page.
    """
    return render_template('widget.html', **make_context())

@app.route('/test_widget.html')
def test_widget():
    """
    Example page displaying widget at different embed sizes.
    """
    return render_template('test_widget.html', **make_context())

@app.route('/oauth/')
def oauth():
    """
    Show an OAuth alert to start authentication process.
    """
    context = make_context()

    credentials = get_credentials()
    if credentials:
        resp = authomatic.access(credentials, 'https://www.googleapis.com/oauth2/v1/userinfo?alt=json')
        if resp.status == 200:
            context['email'] = resp.data['email']

    return render_template('oauth.html', **context)

@app.route('/authenticate/', methods=['GET', 'POST'])
def authenticate():
    """
    Run OAuth workflow.
    """
    from flask import request
    response = make_response()
    context = make_context()
    result = authomatic.login(WerkzeugAdapter(request, response), 'google')

    if result:
        context['result'] = result

        if not result.error:
            save_credentials(result.user.credentials)
            doc = {
                'key': app_config.COPY_GOOGLE_DOC_KEY,
                'file_path': app_config.COPY_PATH,
                'credentials': result.user.credentials,
                'authomatic': app_config.authomatic,
            }
            g = GoogleDoc(**doc)
            g.get_document()

        return render_template('authenticate.html', **context)

    return response

app.register_blueprint(static.static)

# Enable Werkzeug debug pages
if app_config.DEBUG:
    wsgi_app = DebuggedApplication(app, evalex=False)
else:
    wsgi_app = app

# Catch attempts to run the app directly
if __name__ == '__main__':
    print 'This command has been removed! Please run "fab app" instead!'
