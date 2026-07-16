import os
from app import create_app

app = create_app()

# Auto-initialize and safely seed database on startup
with app.app_context():
    try:
        from scripts.seed import seed_database
        seed_database(drop_tables=False)
    except Exception as e:
        print(f"Database initialization error on startup: {e}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
