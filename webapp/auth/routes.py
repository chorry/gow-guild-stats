from flask import Blueprint, render_template

# Set up a Blueprint
auth_bp = Blueprint('auth_bp', __name__,
                        template_folder='templates',
                        static_folder='static')

@auth_bp.route('/', methods=['GET'])
def index():
    return render_template('index.html')