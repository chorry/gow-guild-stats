"""App entry point."""
from webapp import create_app

app = create_app()

if __name__ == "__main__":
    app.run('127.0.0.1', debug=True)
