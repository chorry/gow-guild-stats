from webapp import create_app
from webapp.models import db

app = create_app()
db.app = app
db.init_app(app)
db.create_all()
