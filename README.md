# GraphCar Recommender (Neo4j Aura + Streamlit)

## โครงสร้าง
```
car_app/
├── app.py
├── neo4j_service.py
├── requirements.txt
├── images/                     ← รูปรถ (commit ขึ้น GitHub)
│   ├── toyota_yaris.png
│   └── ...
└── .streamlit/
    └── secrets.toml            ← ห้าม commit (อยู่ใน .gitignore)
```

## รูปรถ
- Neo4j เก็บแค่ **path** ของรูปใน property `Car.image` เช่น `images/toyota_yaris.png`
- ตัวไฟล์รูปอยู่ในโฟลเดอร์ `images/` ของ repo
- ตั้งชื่อไฟล์ = ชื่อรุ่นตัวเล็ก เว้นวรรคเป็น `_` เช่น `Mazda CX-5` → `images/mazda_cx-5.png`
- รูปใน `images/` ตอนนี้เป็น placeholder ให้แทนที่ด้วยรูปจริงโดยใช้ชื่อไฟล์เดิม
- ถ้าใช้ .jpg ให้แก้ path ในหน้า จัดการข้อมูล → เปลี่ยนรูปรถ

## รัน
```
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # แล้วใส่ค่าจาก Aura
streamlit run app.py
```
