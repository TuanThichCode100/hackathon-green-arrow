import random
import csv
import io
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.modules.communes.models import Commune, Hamlet
from app.modules.residents.models import Resident
from app.modules.predictions.models import Prediction
from app.modules.notifications.models import Notification
from app.modules.documents.models import Document
from app.modules.agent.models import AgentDecision
from app.core.database import engine, Base

COMMUNES_CSV = """location_id,commune_name,latitude,longitude,elevation,utc_offset_seconds,timezone,timezone_abbreviation
0,Mường Nhé,22.2642077,102.3731569,500.0,0,GMT,GMT
1,Sín Thầu,22.3757559,102.2540299,500.0,0,GMT,GMT
2,Mường Toong,22.1574708,102.5724901,500.0,0,GMT,GMT
3,Nậm Kè,22.0619829,102.5143555,500.0,0,GMT,GMT
4,Quảng Lâm,21.9859511,102.6031629,500.0,0,GMT,GMT
5,Nà Hỳ,21.8333380,102.7325616,500.0,0,GMT,GMT
6,Mường Chà,21.8272713,103.1428346,500.0,0,GMT,GMT
7,Nà Bủng,21.7258132,102.7160411,500.0,0,GMT,GMT
8,Chà Tở,21.9896598,102.9376092,500.0,0,GMT,GMT
9,Si Pa Phìn,21.8098376,102.9201731,500.0,0,GMT,GMT
10,Na Sang,21.7586618,103.0904718,500.0,0,GMT,GMT
11,Mường Tùng,21.9519678,103.0926433,500.0,0,GMT,GMT
12,Pa Ham,21.9312434,103.2376065,500.0,0,GMT,GMT
13,Nậm Nèn,21.8044040,103.2258203,500.0,0,GMT,GMT
14,Mường Pồn,21.5869655,103.0296833,500.0,0,GMT,GMT
15,Tủa Chùa,21.9709478,103.3774060,500.0,0,GMT,GMT
16,Sín Chải,22.0538305,103.3480596,500.0,0,GMT,GMT
17,Sính Phình,21.9436694,103.3270886,500.0,0,GMT,GMT
18,Tủa Thàng,22.0324290,103.4386917,500.0,0,GMT,GMT
19,Sáng Nhè,21.8465622,103.4586649,500.0,0,GMT,GMT
20,Tuần Giáo,21.6456592,103.3711885,500.0,0,GMT,GMT
21,Quài Tở,21.5417485,103.4569434,500.0,0,GMT,GMT
22,Mường Mùn,21.7248422,103.3184198,500.0,0,GMT,GMT
23,Pú Nhung,21.7226384,103.4901395,500.0,0,GMT,GMT
24,Chiềng Sinh,21.6100291,103.3363912,500.0,0,GMT,GMT
25,Mường Ảng,21.5267978,103.2594999,500.0,0,GMT,GMT
26,Nà Tấu,21.5624221,103.1443005,500.0,0,GMT,GMT
27,Búng Lao,21.5463226,103.2891237,500.0,0,GMT,GMT
28,Mường Lạn,21.4514940,103.3176827,500.0,0,GMT,GMT
29,Mường Phăng,21.4487193,103.1349607,500.0,0,GMT,GMT
30,Thanh Nưa,21.4215085,102.9733819,500.0,0,GMT,GMT
31,Thanh An,21.3018221,103.0464810,500.0,0,GMT,GMT
32,Thanh Yên,21.3060702,102.9473232,500.0,0,GMT,GMT
33,Sam Mứn,21.2072347,102.9486785,500.0,0,GMT,GMT
34,Núa Ngam,21.1792549,103.0525592,500.0,0,GMT,GMT
35,Mường Nhà,21.1269462,103.1004962,500.0,0,GMT,GMT
36,Na Son,21.2967320,103.2200930,500.0,0,GMT,GMT
37,Xa Dung,21.3182894,103.2995758,500.0,0,GMT,GMT
38,Pu Nhi,21.3456912,103.1344866,500.0,0,GMT,GMT
39,Mường Luân,21.2469241,103.3801762,500.0,0,GMT,GMT
40,Tìa Dình,21.1414586,103.3380428,500.0,0,GMT,GMT
41,Phình Giàng,21.1251928,103.2244561,500.0,0,GMT,GMT
42,Mường Lay,22.0311514,103.1274828,500.0,0,GMT,GMT
43,Điện Biên Phủ,21.4904376,103.1046352,500.0,0,GMT,GMT
44,Mường Thanh,21.3872796,103.0168652,500.0,0,GMT,GMT"""

def generate_vietnamese_name(ethnic):
    ho_kinh = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Vũ", "Võ", "Đặng", "Bùi", "Đỗ", "Hồ", "Ngô", "Dương", "Lý"]
    ho_mong = ["Vàng", "Giàng", "Thào", "Hờ", "Lý", "Sùng", "Mùa", "Hạng", "Phàng", "Tráng"]
    ho_thai = ["Lò", "Cầm", "Quàng", "Bạc", "Hà", "Lương", "Tòng", "Vi", "Đèo"]
    ho_khomu = ["Quàng", "Lò", "Lữ", "Cụt", "Moong"]
    ho_dao = ["Bàn", "Triệu", "Chảo", "Đặng", "Phùng"]
    
    dem_nam = ["Văn", "Đình", "Hữu", "Thái", "A", "Mí"]
    dem_nu = ["Thị", "Thu", "Mai", "Ngọc", "Y"]
    
    ten = ["Sáng", "Páo", "Chứ", "Chúa", "Lềnh", "Dũng", "Tâm", "Hải", "Tuấn", "Nhi", "Hương", "Anh", "Minh", "Kỳ", "Lan", "Hoa", "Bình", "Đức"]
    
    if ethnic == "Mông": ho = random.choice(ho_mong)
    elif ethnic == "Thái": ho = random.choice(ho_thai)
    elif ethnic == "Khơ Mú": ho = random.choice(ho_khomu)
    elif ethnic == "Dao": ho = random.choice(ho_dao)
    else: ho = random.choice(ho_kinh)

    dem = random.choice(dem_nam + dem_nu)
    t = random.choice(ten)
    return f"{ho} {dem} {t}"

def seed_database(db: Session):
    if db.query(Commune).count() > 0:
        print("Database already seeded. Skipping.")
        return

    print("Starting database seeding...")

    # 1. Seed Communes & Hamlets
    reader = csv.DictReader(io.StringIO(COMMUNES_CSV.strip()))
    communes_list = []
    
    alert_commune_ids = [0, 1, 15, 20, 30] 

    for row in reader:
        pop = random.randint(2000, 15000)
        c_id = int(row['location_id']) + 1
        
        status = "not_sent"
        if int(row['location_id']) in alert_commune_ids:
            status = random.choice(["sent", "delivered"])

        commune = Commune(
            id=c_id,
            name=row['commune_name'],
            lat=float(row['latitude']),
            lng=float(row['longitude']),
            population=pop,
            notification_status=status
        )
        db.add(commune)
        communes_list.append(commune)

    db.commit()

    hamlets_list = []
    for c in communes_list:
        num_hamlets = random.randint(2, 5)
        for i in range(num_hamlets):
            ethnic = random.choice(["Thái", "Mông", "Kinh", "Khơ Mú", "Dao"])
            hamlet = Hamlet(
                commune_id=c.id,
                name=f"Bản {c.name.split()[-1]} {i+1}",
                headman_name=generate_vietnamese_name(ethnic),
                headman_phone=f"0{random.randint(300000000, 999999999)}",
                population=random.randint(200, 1000)
            )
            db.add(hamlet)
            hamlets_list.append(hamlet)
    db.commit()

    # 2. Seed Residents (~200 records total)
    ethnics_dist = ["Thái"]*33 + ["Mông"]*27 + ["Kinh"]*22 + ["Khơ Mú"]*8 + ["Dao"]*5 + ["Khác"]*5
    residents_list = []
    
    selected_hamlets = random.sample(hamlets_list, k=min(50, len(hamlets_list)))
    
    for i in range(200):
        h = random.choice(selected_hamlets)
        eth = random.choice(ethnics_dist)
        lit = random.choice([True, False]) if eth != "Kinh" else True
        
        res = Resident(
            commune_id=h.commune_id,
            hamlet_id=h.id,
            name=generate_vietnamese_name(eth),
            phone=f"0{random.randint(300000000, 999999999)}",
            ethnic=eth,
            literate=lit,
            created_at=datetime.utcnow() - timedelta(days=random.randint(1, 100))
        )
        db.add(res)
        residents_list.append(res)
    db.commit()

    # 3. Seed Documents (5 mock docs)
    docs = [
        {"code": "CĐ 04/CĐ-UBND", "title": "Sơ tán khẩn cấp dân cư sát bờ sông Nậm Rốm khi mưa lũ", "doc_type": "Công điện", "issued_by": "UBND Tỉnh"},
        {"code": "QĐ 118/QĐ-PCTT", "title": "Phương án ứng phó sạt lở đất khu vực Mường Nhé", "doc_type": "Quyết định", "issued_by": "Ban CH PCTT"},
        {"code": "TB 45/TB-BCH", "title": "Thông báo xả lũ hồ thủy điện Điện Biên", "doc_type": "Thông báo", "issued_by": "Ban CH PCTT"},
        {"code": "HD 12/HD-SNN", "title": "Hướng dẫn chằng chống nhà cửa mùa mưa bão", "doc_type": "Hướng dẫn", "issued_by": "Sở NN&PTNT"},
        {"code": "CV 89/CV-UBND", "title": "Công điện khẩn về việc trực ban 24/24", "doc_type": "Công văn", "issued_by": "UBND Tỉnh"}
    ]
    for d in docs:
        doc = Document(
            code=d["code"],
            title=d["title"],
            doc_type=d["doc_type"],
            issued_by=d["issued_by"],
            file_path=f"/uploads/{d['code'].replace('/', '_')}.pdf",
            llm_summary=f"Bản tóm tắt tự động cho {d['title']}. Yêu cầu các cấp chủ động phòng chống thiên tai.",
            start_date=datetime.utcnow().date() - timedelta(days=random.randint(1, 30)),
            end_date=datetime.utcnow().date() + timedelta(days=random.randint(30, 365)),
            status="active",
            created_at=datetime.utcnow() - timedelta(days=random.randint(1, 30))
        )
        db.add(doc)
    db.commit()

    # 4. Seed Predictions
    disasters = ["Lũ quét", "Sạt lở đất", "Mưa đá", "Ngập lụt"]
    for cid in alert_commune_ids:
        pred = Prediction(
            commune_id=cid + 1,
            disaster_type=random.choice(disasters),
            probability=random.uniform(0.75, 0.99),
            severity=random.choice(["HIGH", "CRITICAL"]),
            predicted_at=datetime.utcnow() - timedelta(minutes=random.randint(5, 60))
        )
        db.add(pred)
    db.commit()

    # 5. Seed Agent Decisions
    dec1 = AgentDecision(
        trigger_type="auto",
        reasoning="Phát hiện lượng mưa tích lũy 120mm/2h tại Mường Nhé, nguy cơ sạt lở 85%. Tự động kích hoạt cảnh báo sơ tán theo QĐ 118.",
        actions_json='[{"action": "send_sms", "count": 1200}, {"action": "auto_call", "count": 300}]',
        communes_affected="1,2",
        notifications_sent=1500,
        status="completed",
        created_at=datetime.utcnow() - timedelta(hours=2)
    )
    dec2 = AgentDecision(
        trigger_type="manual",
        reasoning="Cán bộ tỉnh kích hoạt khẩn cấp do nước lũ dâng cao tại sông Nậm Rốm.",
        actions_json='[{"action": "send_zalo", "count": 5000}]',
        communes_affected="30,31",
        notifications_sent=5000,
        status="completed",
        created_at=datetime.utcnow() - timedelta(minutes=30)
    )
    db.add_all([dec1, dec2])
    db.commit()

    # 6. Seed Notifications (20+ logs)
    channels = ["zalo", "sms", "call"]
    languages = ["Tiếng Kinh", "Tiếng Mông", "Tiếng Thái", "Tiếng Khơ Mú"]
    statuses = ["delivered", "delivered", "delivered", "failed", "pending"]
    
    for _ in range(25):
        notif = Notification(
            commune_id=random.choice(communes_list).id,
            channel=random.choice(channels),
            ethnic_language=random.choice(languages),
            content="Cảnh báo khẩn cấp thiên tai. Đề nghị bà con chú ý an toàn.",
            recipient_count=random.randint(100, 5000),
            status=random.choice(statuses),
            sent_at=datetime.utcnow() - timedelta(minutes=random.randint(1, 1440))
        )
        db.add(notif)
    db.commit()

    print("Database seeding completed successfully.")
