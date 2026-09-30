# GraphCar Recommender (Neo4j Aura + Streamlit)

## โครงสร้าง
```
car_app/
├── app.py
├── neo4j_service.py
├── background3d.py             ← ฝังฉาก 3D เป็นพื้นหลัง
├── bg3d/showroom_scene.html    ← ฉากโรงจอด Three.js (แก้แสง/สี/มุมกล้องได้ที่นี่)
├── static/showroom.glb         ← (ไม่บังคับ) โมเดลโชว์รูมของตัวเอง
├── requirements.txt
├── images/                     ← รูปรถ (commit ขึ้น GitHub)
│   ├── toyota_yaris.png
│   └── ...
├── models/                     ← โมเดล 3D .glb (commit ขึ้น GitHub)
│   ├── toyota_yaris.glb
│   └── ...
└── .streamlit/
    ├── config.toml             ← ธีมมืด + เปิด static file serving
    └── secrets.toml            ← ห้าม commit (อยู่ใน .gitignore)
```

## รูปรถ
- Neo4j เก็บแค่ **path** ของรูปใน property `Car.image` เช่น `images/toyota_yaris.png`
- ตัวไฟล์รูปอยู่ในโฟลเดอร์ `images/` ของ repo
- ตั้งชื่อไฟล์ = ชื่อรุ่นตัวเล็ก เว้นวรรคเป็น `_` เช่น `Mazda CX-5` → `images/mazda_cx-5.png`
- รูปใน `images/` ตอนนี้เป็น placeholder ให้แทนที่ด้วยรูปจริงโดยใช้ชื่อไฟล์เดิม
- ถ้าใช้ .jpg ให้แก้ path ในหน้า จัดการข้อมูล → เปลี่ยนรูปรถ

## โมเดล 3D
- Neo4j เก็บ **path** ของโมเดลใน `Car.model` เช่น `models/toyota_yaris.glb` (หรือ URL)
- ใช้ไฟล์ **.glb** เท่านั้น (ถ้าได้ .gltf + textures มา ให้แปลงเป็น .glb ก่อน เช่นด้วย Blender หรือ gltf.report)
- ตั้งชื่อไฟล์แบบเดียวกับรูป เช่น `Mazda CX-5` → `models/mazda_cx-5.glb`
- โมเดลใน `models/` ตอนนี้เป็นรถ low-poly แบบง่าย (placeholder) ให้แทนที่ด้วยโมเดลจริงโดยใช้ชื่อไฟล์เดิม
- แหล่งโมเดลฟรี: Sketchfab (เลือก Downloadable), Poly Pizza — **ต้องเช็ก license และใส่เครดิตผู้สร้างตามที่กำหนด**
- ไฟล์ในเครื่องใหญ่ได้ไม่เกิน 25 MB (ถูกฝังเข้าเพจ) ถ้าใหญ่กว่านั้นให้ใส่ URL แทน เช่น
  `https://raw.githubusercontent.com/<user>/<repo>/main/models/xxx.glb`
- ตัวแสดงผลใช้ `<model-viewer>` ของ Google โหลดจาก cdn.jsdelivr.net เครื่องที่เปิดเว็บต้องต่ออินเทอร์เน็ต

## พื้นหลัง 3D
- เป็นฉากโรงจอดที่สร้างด้วยโค้ด (Three.js) ไม่ต้องมีไฟล์โมเดล
- กล้องหมุนตามเมาส์ และตามการ scroll หน้า เมื่อเปลี่ยนเมนู กล้องจะหมุนไปมุมใหม่ (`PAGE_YAW` ใน showroom_scene.html)
- อยากใช้โมเดลโชว์รูมของตัวเอง: วางไฟล์เป็น `static/showroom.glb` แล้ว Reboot แอป
- ปิดได้จาก toggle "พื้นหลัง 3D" ใน sidebar (เผื่อเครื่องช้า/มือถือ)

## รัน
```
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # แล้วใส่ค่าจาก Aura
streamlit run app.py
```
