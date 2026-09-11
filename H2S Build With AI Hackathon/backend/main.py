from fastapi import FastAPI, Depends # pyright: ignore[reportMissingImports]
from fastapi.middleware.cors import CORSMiddleware # pyright: ignore[reportMissingImports]
from sqlalchemy.orm import Session # pyright: ignore[reportMissingImports]
from sqlalchemy import func # pyright: ignore[reportMissingImports]
from typing import List
from collections import defaultdict

import models # pyright: ignore[reportMissingImports]
import schemas # pyright: ignore[reportMissingImports]
import ai_service # pyright: ignore[reportMissingImports]
from database import engine, get_db, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI for Digital Public Infrastructure & Governance")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"status": "ok", "message": "DPI Governance API is running"}


@app.post("/api/complaints", response_model=schemas.ComplaintOut)
def create_complaint(complaint: schemas.ComplaintCreate, db: Session = Depends(get_db)):
    ai_result = ai_service.classify_complaint(complaint.raw_text, complaint.language)

    similar_count = db.query(models.Complaint).filter(
        models.Complaint.district == complaint.district,
        models.Complaint.category == ai_result["category"],
    ).count()

    priority = ai_service.compute_priority_score(ai_result["urgency"], similar_count)

    db_complaint = models.Complaint(
        raw_text=complaint.raw_text,
        language=complaint.language,
        state=complaint.state,
        district=complaint.district,
        latitude=complaint.latitude,
        longitude=complaint.longitude,
        category=ai_result["category"],
        urgency=ai_result["urgency"],
        sentiment=ai_result["sentiment"],
        summary=ai_result["summary"],
        priority_score=priority,
    )
    db.add(db_complaint)
    db.commit()
    db.refresh(db_complaint)
    return db_complaint


@app.get("/api/complaints", response_model=List[schemas.ComplaintOut])
def list_complaints(db: Session = Depends(get_db), limit: int = 200):
    return (
        db.query(models.Complaint)
        .order_by(models.Complaint.priority_score.desc())
        .limit(limit)
        .all()
    )


@app.get("/api/dashboard-stats")
def dashboard_stats(db: Session = Depends(get_db)):
    total = db.query(models.Complaint).count()

    category_rows = (
        db.query(models.Complaint.category, func.count(models.Complaint.id))
        .group_by(models.Complaint.category)
        .all()
    )
    category_counts = {c: n for c, n in category_rows}

    state_rows = (
        db.query(models.Complaint.state, func.count(models.Complaint.id))
        .group_by(models.Complaint.state)
        .all()
    )
    state_counts = {s: n for s, n in state_rows}

    avg_urgency = db.query(func.avg(models.Complaint.urgency)).scalar() or 0

    return {
        "total_complaints": total,
        "category_breakdown": category_counts,
        "state_breakdown": state_counts,
        "average_urgency": round(avg_urgency, 2),
    }


@app.get("/api/hotspots")
def hotspots(db: Session = Depends(get_db)):
    """
    Groups complaints by district, computes an aggregate priority score,
    and generates an AI recommendation per hotspot for policymakers.
    """
    rows = db.query(models.Complaint).all()
    grouped = defaultdict(list)
    for r in rows:
        grouped[(r.state, r.district)].append(r)

    results = []
    for (state, district), complaints in grouped.items():
        category_counts = defaultdict(int)
        total_priority = 0.0
        total_urgency = 0
        lat_sum, lng_sum, geo_count = 0.0, 0.0, 0

        for c in complaints:
            category_counts[c.category] += 1
            total_priority += c.priority_score
            total_urgency += c.urgency
            if c.latitude and c.longitude:
                lat_sum += c.latitude
                lng_sum += c.longitude
                geo_count += 1

        avg_urgency = total_urgency / len(complaints)
        recommendation = ai_service.generate_area_recommendation(
            state, district, dict(category_counts), avg_urgency
        )

        results.append({
            "state": state,
            "district": district,
            "complaint_count": len(complaints),
            "total_priority_score": round(total_priority, 2),
            "average_urgency": round(avg_urgency, 2),
            "category_breakdown": dict(category_counts),
            "latitude": lat_sum / geo_count if geo_count else None,
            "longitude": lng_sum / geo_count if geo_count else None,
            "recommendation": recommendation,
        })

    results.sort(key=lambda x: x["total_priority_score"], reverse=True)
    return results