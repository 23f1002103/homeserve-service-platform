from app import create_app
from app.seed import ensure_admin_exists


app = create_app()


if __name__ == "__main__":
    with app.app_context():
        ensure_admin_exists()

    app.run(debug=True, host="127.0.0.1", port=5000)

