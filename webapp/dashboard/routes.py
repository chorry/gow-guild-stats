import os
import uuid

from flask import Blueprint, send_from_directory
from flask import current_app as app
from flask import render_template, request
from flask import session
# Set up a Blueprint
from werkzeug.utils import secure_filename

from webapp import db
from webapp.models import Uploads, RecognitionJob

dashboard_bp = Blueprint('dashboard_bp', __name__,
                        template_folder='templates',
                        static_folder='static')


@dashboard_bp.route('/', methods=['GET'])
def upload():
    return render_template('upload.html')