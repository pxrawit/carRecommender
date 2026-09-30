from __future__ import annotations

from typing import Any

import streamlit as st
from neo4j import GraphDatabase, RoutingControl

# =====================================================================
# Graph schema
#   (:User {name})
#   (:Car  {name, brand, image})   image = path ในโฟลเดอร์ images/ ของ repo (หรือ URL)
#   (:User)-[:LIKES]->(:Car)
#   (:User)-[:TEST_DROVE {test_date}]->(:Car)
# =====================================================================


# ---------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------
def _config() -> tuple[str, str, str, str | None]:
    cfg = st.secrets["neo4j"]
    return (
        cfg["uri"],
        cfg["username"],
        cfg["password"],
        cfg.get("database") or None,  # None = ใช้ home database ของ instance
    )


@st.cache_resource(show_spinner=False)
def get_driver():
    """สร้าง Neo4j Driver ครั้งเดียวต่อ Streamlit process"""
    uri, username, password, _ = _config()
    driver = GraphDatabase.driver(uri, auth=(username, password))
    driver.verify_connectivity()
    return driver


def query(cypher: str, parameters: dict[str, Any] | None = None, *, write: bool = False) -> list[dict[str, Any]]:
    """รัน Cypher แบบมี parameter แล้วคืนผลเป็น list ของ dict"""
    _, _, _, database = _config()
    records, _, _ = get_driver().execute_query(
        cypher,
        parameters_=parameters or {},
        database_=database,
        routing_=RoutingControl.WRITE if write else RoutingControl.READ,
    )
    return [record.data() for record in records]


def ping() -> bool:
    rows = query("RETURN 1 AS ok")
    return bool(rows and rows[0]["ok"] == 1)


# ---------------------------------------------------------------------
# Schema + demo data
# ---------------------------------------------------------------------
IMAGE_DIR = "images"


def image_slug(name: str) -> str:
    """'Mazda CX-5' -> 'mazda_cx-5'  ใช้ตั้งชื่อไฟล์รูป"""
    out = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in name.strip().lower())
    return "_".join(filter(None, out.split("_")))


def default_image_path(name: str) -> str:
    return f"{IMAGE_DIR}/{image_slug(name)}.png"


DEMO_USERS = ["Alice", "Bob", "Charlie", "David", "Emma", "Frank", "Grace", "Henry", "Ivy", "Jack"]

DEMO_CARS = [
    {"name": "Toyota Yaris", "brand": "Toyota"},
    {"name": "Honda City", "brand": "Honda"},
    {"name": "Toyota Corolla", "brand": "Toyota"},
    {"name": "Honda Civic", "brand": "Honda"},
    {"name": "Mazda 3", "brand": "Mazda"},
    {"name": "Nissan Almera", "brand": "Nissan"},
    {"name": "Ford Ranger", "brand": "Ford"},
    {"name": "Toyota Camry", "brand": "Toyota"},
    {"name": "Honda Accord", "brand": "Honda"},
    {"name": "Mazda CX-5", "brand": "Mazda"},
]
for _car in DEMO_CARS:
    _car["image"] = default_image_path(_car["name"])

DEMO_LIKES = [
    ("Alice", "Toyota Yaris"), ("Alice", "Honda City"), ("Alice", "Toyota Corolla"),
    ("Bob", "Toyota Yaris"), ("Bob", "Honda City"), ("Bob", "Toyota Corolla"), ("Bob", "Honda Civic"),
    ("Charlie", "Toyota Yaris"), ("Charlie", "Toyota Corolla"), ("Charlie", "Mazda 3"),
    ("David", "Toyota Corolla"), ("David", "Honda Civic"), ("David", "Mazda 3"), ("David", "Nissan Almera"),
    ("Emma", "Honda Civic"), ("Emma", "Mazda 3"), ("Emma", "Nissan Almera"),
    ("Frank", "Nissan Almera"), ("Frank", "Ford Ranger"), ("Frank", "Toyota Camry"),
    ("Grace", "Ford Ranger"), ("Grace", "Toyota Camry"), ("Grace", "Honda Accord"),
    ("Henry", "Toyota Camry"), ("Henry", "Honda Accord"), ("Henry", "Mazda CX-5"),
    ("Ivy", "Honda Accord"), ("Ivy", "Mazda CX-5"), ("Ivy", "Toyota Yaris"),
    ("Jack", "Mazda CX-5"), ("Jack", "Toyota Yaris"), ("Jack", "Honda City"),
]

DEMO_TEST_DRIVES = [
    {"user": "Alice", "car": "Toyota Yaris", "date": "2026-09-01"},
    {"user": "Bob", "car": "Honda Civic", "date": "2026-09-02"},
    {"user": "Charlie", "car": "Mazda 3", "date": "2026-09-03"},
    {"user": "David", "car": "Nissan Almera", "date": "2026-09-04"},
    {"user": "Alice", "car": "Honda Civic", "date": "2026-09-05"},
    {"user": "Emma", "car": "Mazda 3", "date": "2026-09-06"},
    {"user": "Frank", "car": "Ford Ranger", "date": "2026-09-07"},
    {"user": "Grace", "car": "Toyota Camry", "date": "2026-09-08"},
    {"user": "Henry", "car": "Mazda CX-5", "date": "2026-09-09"},
    {"user": "Jack", "car": "Toyota Yaris", "date": "2026-09-10"},
]


def create_schema() -> None:
    for stmt in [
        "CREATE CONSTRAINT user_name_unique IF NOT EXISTS FOR (u:User) REQUIRE u.name IS UNIQUE",
        "CREATE CONSTRAINT car_name_unique IF NOT EXISTS FOR (c:Car) REQUIRE c.name IS UNIQUE",
    ]:
        query(stmt, write=True)


def seed_demo_data() -> None:
    """ข้อมูลตัวอย่าง ใช้ MERGE ทั้งหมด กดซ้ำได้ไม่เกิดข้อมูลซ้ำ"""
    create_schema()
    query("UNWIND $rows AS name MERGE (:User {name: name})", {"rows": DEMO_USERS}, write=True)
    query(
        """
        UNWIND $rows AS row
        MERGE (c:Car {name: row.name})
        SET c.brand = row.brand,
            c.image = coalesce(c.image, row.image)
        """,
        {"rows": DEMO_CARS},
        write=True,
    )
    query(
        """
        UNWIND $rows AS row
        MATCH (u:User {name: row[0]}), (c:Car {name: row[1]})
        MERGE (u)-[:LIKES]->(c)
        """,
        {"rows": [list(x) for x in DEMO_LIKES]},
        write=True,
    )
    query(
        """
        UNWIND $rows AS row
        MATCH (u:User {name: row.user}), (c:Car {name: row.car})
        MERGE (u)-[r:TEST_DROVE]->(c)
        SET r.test_date = date(row.date)
        """,
        {"rows": DEMO_TEST_DRIVES},
        write=True,
    )


def clear_car_data() -> int:
    """ลบเฉพาะ User และ Car (พร้อมเส้นทั้งหมด) ข้อมูลอื่นใน database ไม่ถูกแตะ"""
    rows = query(
        "MATCH (n) WHERE n:User OR n:Car DETACH DELETE n RETURN count(*) AS deleted",
        write=True,
    )
    return rows[0]["deleted"] if rows else 0


# ---------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------
def get_users() -> list[dict[str, Any]]:
    return query(
        """
        MATCH (u:User)
        RETURN u.name AS name,
               COUNT { (u)-[:LIKES]->() } AS likes,
               COUNT { (u)-[:TEST_DROVE]->() } AS test_drives
        ORDER BY name
        """
    )


def get_cars() -> list[dict[str, Any]]:
    return query(
        """
        MATCH (c:Car)
        RETURN c.name AS name, c.brand AS brand, c.image AS image,
               COUNT { ()-[:LIKES]->(c) } AS likes,
               COUNT { ()-[:TEST_DROVE]->(c) } AS test_drives
        ORDER BY name
        """
    )


def list_brands() -> list[str]:
    rows = query("MATCH (c:Car) WHERE c.brand IS NOT NULL RETURN DISTINCT c.brand AS brand ORDER BY brand")
    return [r["brand"] for r in rows]


def get_dashboard_metrics() -> dict[str, int]:
    rows = query(
        """
        RETURN COUNT { (:User) } AS users,
               COUNT { (:Car) } AS cars,
               COUNT { (:User)-[:LIKES]->(:Car) } AS likes,
               COUNT { (:User)-[:TEST_DROVE]->(:Car) } AS test_drives
        """
    )
    return rows[0] if rows else {"users": 0, "cars": 0, "likes": 0, "test_drives": 0}


def popular_cars(limit: int = 10) -> list[dict[str, Any]]:
    return query(
        """
        MATCH (c:Car)
        RETURN c.name AS car, c.brand AS brand, c.image AS image,
               COUNT { ()-[:LIKES]->(c) } AS likes,
               COUNT { ()-[:TEST_DROVE]->(c) } AS test_drives
        ORDER BY likes DESC, test_drives DESC, car
        LIMIT $limit
        """,
        {"limit": int(limit)},
    )


def get_profile(name: str) -> dict[str, Any] | None:
    rows = query(
        """
        MATCH (u:User {name:$name})
        RETURN u.name AS name,
               [(u)-[:LIKES]->(c:Car) | {car: c.name, brand: c.brand, image: c.image}] AS liked,
               [(u)-[r:TEST_DROVE]->(c:Car) |
                    {car: c.name, brand: c.brand, image: c.image, test_date: toString(r.test_date)}] AS test_drives
        """,
        {"name": name},
    )
    if not rows:
        return None
    row = rows[0]
    row["liked"] = sorted(row["liked"], key=lambda x: x["car"])
    row["test_drives"] = sorted(row["test_drives"], key=lambda x: x["test_date"] or "")
    return row


def similar_users(name: str) -> list[dict[str, Any]]:
    return query(
        """
        MATCH (me:User {name:$name})-[:LIKES]->(c:Car)<-[:LIKES]-(other:User)
        WHERE other <> me
        RETURN other.name AS user, count(c) AS same_cars, collect(c.name) AS cars
        ORDER BY same_cars DESC, user
        """,
        {"name": name},
    )


def recommend_cars(name: str, mode: str = "test_drive", exclude_test_driven: bool = True,
                   limit: int = 10) -> list[dict[str, Any]]:
    """
    mode = "test_drive" : รถที่คนซึ่งชอบรถเหมือนเราเคย "ลองขับ" แต่เรายังไม่เคยลองขับ
    mode = "likes"      : รถที่คนซึ่งชอบรถเหมือนเรา "ชอบ" แต่เรายังไม่ได้ชอบ
    score = จำนวนเส้นทางใน graph ที่ไปถึงรถคันนั้น
    """
    if mode == "likes":
        cypher = """
        MATCH (me:User {name:$name})-[:LIKES]->(shared:Car)<-[:LIKES]-(other:User)-[:LIKES]->(car:Car)
        WHERE other <> me
          AND NOT EXISTS { MATCH (me)-[:LIKES]->(car) }
          AND ($exclude_td = false OR NOT EXISTS { MATCH (me)-[:TEST_DROVE]->(car) })
        """
    else:
        cypher = """
        MATCH (me:User {name:$name})-[:LIKES]->(shared:Car)<-[:LIKES]-(other:User)-[:TEST_DROVE]->(car:Car)
        WHERE other <> me
          AND NOT EXISTS { MATCH (me)-[:TEST_DROVE]->(car) }
        """
    cypher += """
        RETURN car.name AS car, car.brand AS brand, car.image AS image,
               count(*) AS score,
               collect(DISTINCT other.name) AS via_users,
               collect(DISTINCT shared.name) AS shared_cars
        ORDER BY score DESC, car
        LIMIT $limit
    """
    return query(cypher, {"name": name, "exclude_td": bool(exclude_test_driven), "limit": int(limit)})


def search_cars(keyword: str = "", brand: str = "") -> list[dict[str, Any]]:
    return query(
        """
        MATCH (c:Car)
        WHERE ($keyword = '' OR toLower(c.name) CONTAINS toLower($keyword))
          AND ($brand = '' OR c.brand = $brand)
        RETURN c.name AS car, c.brand AS brand, c.image AS image,
               COUNT { ()-[:LIKES]->(c) } AS likes,
               COUNT { ()-[:TEST_DROVE]->(c) } AS test_drives,
               [(u:User)-[:LIKES]->(c) | u.name] AS liked_by
        ORDER BY car
        """,
        {"keyword": keyword.strip(), "brand": brand or ""},
    )


def get_likes() -> list[dict[str, Any]]:
    return query(
        "MATCH (u:User)-[:LIKES]->(c:Car) RETURN u.name AS user, c.name AS car ORDER BY user, car"
    )


def get_test_drives() -> list[dict[str, Any]]:
    return query(
        """
        MATCH (u:User)-[r:TEST_DROVE]->(c:Car)
        RETURN u.name AS user, c.name AS car, toString(r.test_date) AS test_date
        ORDER BY r.test_date, user
        """
    )


def graph_edges(name: str | None = None, show_similar: bool = False) -> list[dict[str, Any]]:
    """คืน edge สำหรับวาดกราฟ ถ้า name เป็น None จะคืนทั้งกราฟ"""
    if name is None:
        return query(
            """
            MATCH (u:User)-[r:LIKES|TEST_DROVE]->(c:Car)
            RETURN u.name AS user, c.name AS car, type(r) AS rel, toString(r.test_date) AS test_date
            """
        )
    rows = query(
        """
        MATCH (u:User {name:$name})-[r:LIKES|TEST_DROVE]->(c:Car)
        RETURN u.name AS user, c.name AS car, type(r) AS rel, toString(r.test_date) AS test_date
        """,
        {"name": name},
    )
    if show_similar:
        rows += query(
            """
            MATCH (me:User {name:$name})-[:LIKES]->(c:Car)<-[r:LIKES]-(o:User)
            WHERE o <> me
            RETURN DISTINCT o.name AS user, c.name AS car, type(r) AS rel, null AS test_date
            """,
            {"name": name},
        )
    return rows


# ---------------------------------------------------------------------
# Write: เพิ่ม / ลบ
# ---------------------------------------------------------------------
def add_user(name: str) -> bool:
    """คืน True ถ้าสร้างใหม่, False ถ้ามีอยู่แล้ว"""
    rows = query(
        """
        OPTIONAL MATCH (x:User {name:$name})
        WITH x IS NULL AS created
        MERGE (:User {name:$name})
        RETURN created
        """,
        {"name": name.strip()},
        write=True,
    )
    return bool(rows and rows[0]["created"])


def delete_user(name: str) -> int:
    rows = query(
        "MATCH (u:User {name:$name}) DETACH DELETE u RETURN count(*) AS deleted",
        {"name": name},
        write=True,
    )
    return rows[0]["deleted"] if rows else 0


def add_car(name: str, brand: str, image: str = "") -> bool:
    """
    คืน True ถ้าสร้างใหม่, False ถ้ามีอยู่แล้ว (จะอัปเดตยี่ห้อ และรูปถ้าส่งมา)
    image = path ของรูปใน repo เช่น images/toyota_yaris.png หรือ URL
    """
    rows = query(
        """
        OPTIONAL MATCH (x:Car {name:$name})
        WITH x IS NULL AS created
        MERGE (c:Car {name:$name})
        SET c.brand = $brand,
            c.image = CASE WHEN $image = '' THEN c.image ELSE $image END
        RETURN created
        """,
        {"name": name.strip(), "brand": brand.strip(), "image": (image or "").strip()},
        write=True,
    )
    return bool(rows and rows[0]["created"])


def set_car_image(name: str, image: str | None) -> int:
    """เปลี่ยน path รูปของรถ ส่ง None หรือ '' เพื่อลบรูปออกจาก node"""
    rows = query(
        """
        MATCH (c:Car {name:$name})
        SET c.image = CASE WHEN $image = '' THEN null ELSE $image END
        RETURN count(c) AS updated
        """,
        {"name": name, "image": (image or "").strip()},
        write=True,
    )
    return rows[0]["updated"] if rows else 0


def delete_car(name: str) -> int:
    rows = query(
        "MATCH (c:Car {name:$name}) DETACH DELETE c RETURN count(*) AS deleted",
        {"name": name},
        write=True,
    )
    return rows[0]["deleted"] if rows else 0


def add_like(user: str, car: str) -> bool:
    rows = query(
        """
        MATCH (u:User {name:$user}), (c:Car {name:$car})
        OPTIONAL MATCH (u)-[old:LIKES]->(c)
        WITH u, c, old IS NULL AS created
        MERGE (u)-[:LIKES]->(c)
        RETURN created
        """,
        {"user": user, "car": car},
        write=True,
    )
    return bool(rows and rows[0]["created"])


def remove_like(user: str, car: str) -> int:
    rows = query(
        "MATCH (:User {name:$user})-[r:LIKES]->(:Car {name:$car}) DELETE r RETURN count(*) AS deleted",
        {"user": user, "car": car},
        write=True,
    )
    return rows[0]["deleted"] if rows else 0


def add_test_drive(user: str, car: str, test_date: str) -> bool:
    """1 คู่ User-Car มี TEST_DROVE ได้เส้นเดียว ถ้ามีแล้วจะอัปเดตวันที่"""
    rows = query(
        """
        MATCH (u:User {name:$user}), (c:Car {name:$car})
        OPTIONAL MATCH (u)-[old:TEST_DROVE]->(c)
        WITH u, c, old IS NULL AS created
        MERGE (u)-[r:TEST_DROVE]->(c)
        SET r.test_date = date($test_date)
        RETURN created
        """,
        {"user": user, "car": car, "test_date": test_date},
        write=True,
    )
    return bool(rows and rows[0]["created"])


def remove_test_drive(user: str, car: str) -> int:
    rows = query(
        "MATCH (:User {name:$user})-[r:TEST_DROVE]->(:Car {name:$car}) DELETE r RETURN count(*) AS deleted",
        {"user": user, "car": car},
        write=True,
    )
    return rows[0]["deleted"] if rows else 0
