from app import app, db
import models

with app.app_context():
    db.create_all()
    print("Tables created successfully!")
