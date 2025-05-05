from app import create_app
from app import test_db_connection
app = create_app()

if __name__ == "__main__":
    app.run(debug=True)

    