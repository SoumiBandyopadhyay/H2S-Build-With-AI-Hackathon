"""
Seeds the database with realistic sample citizen complaints across
multiple Indian states, districts, categories and languages.

Run once after setting up the backend:
    python sample_data.py
"""
import random
from datetime import datetime, timedelta

from database import SessionLocal, engine, Base
import models # pyright: ignore[reportMissingImports]
import ai_service # pyright: ignore[reportMissingImports]

Base.metadata.create_all(bind=engine)

# (text, language, state, district, lat, lng)
SAMPLE_COMPLAINTS = [
    ("The main road near the market has huge potholes, two accidents happened last week.", "en", "Bihar", "Patna", 25.5941, 85.1376),
    ("রাস্তায় অনেকদিন ধরে জল জমে আছে, গাড়ি চলতে পারছে না।", "bn", "West Bengal", "Kolkata", 22.5726, 88.3639),
    ("पिछले 3 दिन से बिजली नहीं आ रही है, ट्रांसफार्मर खराब है।", "hi", "Uttar Pradesh", "Lucknow", 26.8467, 80.9462),
    ("Our village hand pump has been broken for two months, we walk 3km for water.", "en", "Rajasthan", "Jodhpur", 26.2389, 73.0243),
    ("সরকারি হাসপাতালে সন্ধ্যার পর কোনো ডাক্তার থাকেন না।", "bn", "West Bengal", "Howrah", 22.5958, 88.2636),
    ("The government school building roof is leaking, children get wet during monsoon.", "en", "Odisha", "Bhubaneswar", 20.2961, 85.8245),
    ("गटर का पानी सड़क पर बह रहा है, बीमारी फैलने का डर है।", "hi", "Madhya Pradesh", "Bhopal", 23.2599, 77.4126),
    ("Mobile network and internet connectivity is very poor in our panchayat.", "en", "Jharkhand", "Ranchi", 23.3441, 85.3096),
    ("বাস স্টপে কোনো শেড নেই, রোদে-বৃষ্টিতে দাঁড়াতে কষ্ট হয়।", "bn", "West Bengal", "Siliguri", 26.7271, 88.3953),
    ("Street lights on our lane have not worked for six months, unsafe at night.", "en", "Maharashtra", "Nagpur", 21.1458, 79.0882),
    ("सड़क पर बड़ा गड्ढा है, कल एक बुजुर्ग गिर गए थे।", "hi", "Uttar Pradesh", "Kanpur", 26.4499, 80.3319),
    ("Water supply comes only for 1 hour every alternate day in our locality.", "en", "Tamil Nadu", "Chennai", 13.0827, 80.2707),
    ("প্রাথমিক স্বাস্থ্যকেন্দ্রে ওষুধের সরবরাহ নেই এক মাস ধরে।", "bn", "West Bengal", "Durgapur", 23.5204, 87.3119),
    ("There is no proper drainage system, our street floods every monsoon.", "en", "Karnataka", "Bengaluru", 12.9716, 77.5946),
    ("गांव की सड़क कच्ची है, बरसात में स्कूल जाना मुश्किल हो जाता है।", "hi", "Bihar", "Gaya", 24.7955, 85.0002),
    ("Government hospital lacks an ambulance, patients struggle during emergencies.", "en", "Odisha", "Cuttack", 20.4625, 85.8828),
    ("বিদ্যুতের খুঁটি হেলে পড়েছে, বিপদজনক অবস্থা।", "bn", "West Bengal", "Asansol", 23.6739, 86.9524),
    ("Public toilets in our area are unusable, no water or cleaning for weeks.", "en", "Delhi", "New Delhi", 28.6139, 77.2090),
    ("नाली जाम होने से पूरा मोहल्ला गंदे पानी से भरा हुआ है।", "hi", "Rajasthan", "Jaipur", 26.9124, 75.7873),
    ("Our area has no digital literacy center, youth cannot access online government services.", "en", "Assam", "Guwahati", 26.1445, 91.7362),
    ("এলাকায় কোনো নিকাশি ব্যবস্থা নেই, বৃষ্টি হলেই জলমগ্ন হয়ে যায়।", "bn", "West Bengal", "Kolkata", 22.5820, 88.3640),
    ("Highway repair work has been stalled for a year, traffic jams daily.", "en", "Punjab", "Ludhiana", 30.9010, 75.8573),
    ("स्कूल में शौचालय की सफाई नहीं होती, बच्चों को परेशानी होती है।", "hi", "Madhya Pradesh", "Indore", 22.7196, 75.8577),
    ("Frequent power cuts are damaging our small business equipment.", "en", "Telangana", "Hyderabad", 17.3850, 78.4867),
    ("গ্রামের রাস্তা কাঁচা, বর্ষায় স্কুলে যাওয়া কঠিন হয়ে পড়ে।", "bn", "West Bengal", "Malda", 25.0119, 88.1414),
]


def seed():
    db = SessionLocal()
    existing = db.query(models.Complaint).count()
    if existing > 0:
        print(f"Database already has {existing} complaints. Skipping seed.")
        db.close()
        return

    print(f"Seeding {len(SAMPLE_COMPLAINTS)} sample complaints (calls the AI classifier for each)...\n")
    for i, (text, lang, state, district, lat, lng) in enumerate(SAMPLE_COMPLAINTS):
        ai_result = ai_service.classify_complaint(text, lang)

        similar_count = db.query(models.Complaint).filter(
            models.Complaint.district == district,
            models.Complaint.category == ai_result["category"],
        ).count()
        priority = ai_service.compute_priority_score(ai_result["urgency"], similar_count)

        jitter_lat = lat + random.uniform(-0.02, 0.02)
        jitter_lng = lng + random.uniform(-0.02, 0.02)

        db_complaint = models.Complaint(
            raw_text=text,
            language=lang,
            state=state,
            district=district,
            latitude=jitter_lat,
            longitude=jitter_lng,
            category=ai_result["category"],
            urgency=ai_result["urgency"],
            sentiment=ai_result["sentiment"],
            summary=ai_result["summary"],
            priority_score=priority,
            created_at=datetime.utcnow() - timedelta(days=random.randint(0, 30)),
        )
        db.add(db_complaint)
        print(f"  [{i + 1}/{len(SAMPLE_COMPLAINTS)}] {district}, {state}: {ai_result['category']} (urgency {ai_result['urgency']})")

    db.commit()
    db.close()
    print("\nDone seeding. Start the server and open the frontend to explore.")


if __name__ == "__main__":
    seed()