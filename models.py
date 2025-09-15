from .app import db

class Jewelry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    collection = db.Column(db.String(100), nullable=False)
    image_url = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return f'<Jewelry {self.name}>'
