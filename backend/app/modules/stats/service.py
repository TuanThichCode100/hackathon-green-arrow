from sqlalchemy.orm import Session

def calc_overview(db: Session, time_range: str):
    return {
        "total_pop": 642000,
        "recv_rate": 0.85,
        "not_responded": 96300,
        "headmen_confirmed": 210,
        "active_alerts": 3
    }
