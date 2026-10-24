from app import create_app
from app.seed import ensure_admin_exists


app = create_app()

# The function is idempotent: restarting the web service will not duplicate
# the administrator account.
with app.app_context():
    ensure_admin_exists()
