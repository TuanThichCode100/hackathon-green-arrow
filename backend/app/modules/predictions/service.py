from sqlalchemy.orm import Session
from app.modules.predictions.models import Prediction

def get_latest_predictions(db: Session):
    # simplistic query for hackathon
    return db.query(Prediction).order_by(Prediction.predicted_at.desc()).limit(50).all()
