from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

from neo4j_service import (
    add_car,
    add_like,
    add_test_drive,
    add_user,
    clear_car_data,
    delete_car,
    delete_user,
    get_cars,
    get_dashboard_metrics,
    get_likes,
    get_profile,
    get_test_drives,
    get_users,
    IMAGE_DIR,
    default_image_path,
    image_slug,
    set_car_image,
    graph_edges,
    list_brands,
    ping,
    popular_cars,
    recommend_cars,
    remove_like,
    remove_test_drive,
    search_cars,
    seed_demo_data,
    similar_users,
)

st.set_page_config(
    page_title="GraphCar Recommender",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      .block-container {padding-top: 1.3rem; padding-bottom: 2rem;}
      .hero {
        padding: 1.4rem 1.6rem; border-radius: 22px;
        background: linear-gradient(120deg, #111827 0%, #1e3a8a 55%, #0369a1 100%);
        color: white; margin-bottom: 1rem;
      }
      .hero h1 {margin:0; font-size:2.15rem;}
      .hero p {opacity:.88; margin:.35rem 0 0 0;}
      .car-card {
        padding: 1rem 1.1rem; border: 1px solid rgba(128,128,128,.25);
        border-radius: 16px; margin-bottom: .75rem;
      }
      .score-pill {
        display:inline-block; padding:.2rem .55rem; border-radius:999px;
        background:#0369a1; color:white; font-size:.8rem; font-weight:700;
      }
      .muted {opacity:.72; font-size:.9rem;}
      .no-img {aspect-ratio: 16/10; display:flex; align-items:center; justify-content:center;
               border:1px dashed rgba(128,128,128,.45); border-radius:12px; opacity:.6;}
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def require_connection() -> None:
    try:
        if not ping():
            raise RuntimeError("Neo4j did not return a healthy response")
    except Exception as exc:
        st.error("ยังเชื่อมต่อ Neo4j Aura ไม่สำเร็จ")
        st.code(
            '[neo4j]\nuri = "neo4j+s://YOUR_INSTANCE.databases.neo4j.io"\n'
            'username = "YOUR_USERNAME"\npassword = "YOUR_PASSWORD"',
            language="toml",
        )
        st.caption("ให้นำค่าด้านบนไปใส่ใน .streamlit/secrets.toml หรือ Streamlit Secrets และห้าม commit password ลง GitHub")
        st.exception(exc)
        st.stop()


def flash(message: str, kind: str = "success") -> None:
    """เก็บข้อความไว้แสดงหลัง st.rerun()"""
    st.session_state["flash"] = (kind, message)
    st.rerun()


def show_flash() -> None:
    if "flash" in st.session_state:
        kind, message = st.session_state.pop("flash")
        getattr(st, kind)(message)


def user_names() -> list[str]:
    return [u["name"] for u in get_users()]


def car_names() -> list[str]:
    return [c["name"] for c in get_cars()]


def user_selector(key: str) -> str:
    names = user_names()
    if not names:
        st.info("ยังไม่มี User กรุณาไปหน้า จัดการข้อมูล หรือ Admin / Setup ก่อน")
        st.stop()
    return st.selectbox("เลือก User", names, key=key)


APP_DIR = Path(__file__).resolve().parent
IMAGE_TYPES = ["png", "jpg", "jpeg", "webp"]


def resolve_image(path: str | None) -> str | None:
    """แปลง path ที่เก็บใน Neo4j ให้เป็นไฟล์จริงใน repo หรือ URL  ถ้าหาไม่เจอคืน None"""
    if not path:
        return None
    if path.startswith(("http://", "https://")):
        return path
    file = (APP_DIR / path).resolve()
    if APP_DIR not in file.parents or not file.is_file():  # กันไม่ให้อ่านไฟล์นอกโฟลเดอร์แอป
        return None
    return str(file)


def show_car_image(path: str | None, caption: str | None = None) -> None:
    src = resolve_image(path)
    if src:
        st.image(src, caption=caption, width="stretch")
    else:
        st.markdown('<div class="no-img">🚗 ไม่มีรูป</div>', unsafe_allow_html=True)
        if caption:
            st.caption(caption)


def save_uploaded_image(car_name: str, uploaded) -> str:
    """บันทึกไฟล์ที่อัปโหลดลง images/<ชื่อรถ>.<นามสกุล> แล้วคืน path แบบ relative"""
    ext = Path(uploaded.name).suffix.lower() or ".png"
    rel = f"{IMAGE_DIR}/{image_slug(car_name)}{ext}"
    (APP_DIR / IMAGE_DIR).mkdir(exist_ok=True)
    (APP_DIR / rel).write_bytes(uploaded.getvalue())
    return rel


def car_gallery(rows: list[dict], name_key: str = "car", cols: int = 4, detail=None) -> None:
    """แสดงรถเป็นการ์ดรูป cols ช่องต่อแถว"""
    for start in range(0, len(rows), cols):
        columns = st.columns(cols)
        for col, row in zip(columns, rows[start:start + cols]):
            with col:
                show_car_image(row.get("image"))
                st.markdown(f"**{row[name_key]}**")
                st.caption(detail(row) if detail else (row.get("brand") or ""))


def df(rows: list[dict], columns: list[str] | None = None) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=columns)


def draw_graph(rows: list[dict], focus: str | None = None) -> None:
    dot = [
        "digraph G {",
        'rankdir="LR";',
        'node [style="rounded,filled", fontname="Helvetica"];',
    ]
    seen: set[str] = set()
    for r in rows:
        for node_id, label, is_user in [(f"U:{r['user']}", r["user"], True), (f"C:{r['car']}", r["car"], False)]:
            if node_id in seen:
                continue
            seen.add(node_id)
            safe = str(label).replace('"', "'")
            if is_user:
                color = "#fde68a" if label == focus else "#bae6fd"
                dot.append(f'"{node_id}" [label="{safe}", shape=ellipse, fillcolor="{color}"];')
            else:
                dot.append(f'"{node_id}" [label="{safe}", shape=box, fillcolor="#fed7aa"];')
        if r["rel"] == "TEST_DROVE":
            date_label = r.get("test_date") or ""
            dot.append(
                f'"U:{r["user"]}" -> "C:{r["car"]}" '
                f'[label="TEST_DROVE\\n{date_label}", style=dashed, color="#dc2626", fontcolor="#dc2626"];'
            )
        else:
            dot.append(f'"U:{r["user"]}" -> "C:{r["car"]}" [label="LIKES", color="#475569", fontcolor="#475569"];')
    dot.append("}")
    st.graphviz_chart("\n".join(dot), width="stretch")


# ---------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------
require_connection()

with st.sidebar:
    st.markdown("## 🚗 GraphCar")
    st.caption("Neo4j Aura + Streamlit")
    page = st.radio(
        "เมนู",
        ["Dashboard", "Recommendations", "Car Search", "จัดการข้อมูล", "Graph Explorer", "Admin / Setup"],
    )
    st.divider()
    st.caption("Car Recommender System ด้วย Graph Database")

st.markdown(
    """
    <div class="hero">
      <h1>🚗 GraphCar Recommendation System</h1>
      <p>ระบบแนะนำรถยนต์ด้วย Graph Database — (User)-[:LIKES]->(Car), (User)-[:TEST_DROVE]->(Car)</p>
    </div>
    """,
    unsafe_allow_html=True,
)

show_flash()

# =====================================================================
# Dashboard
# =====================================================================
if page == "Dashboard":
    st.subheader("ภาพรวมระบบ")
    m = get_dashboard_metrics()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Users", m.get("users", 0))
    c2.metric("Cars", m.get("cars", 0))
    c3.metric("LIKES", m.get("likes", 0))
    c4.metric("TEST_DROVE", m.get("test_drives", 0))

    st.markdown("### 🏆 รถยอดนิยม")
    popular = popular_cars(10)
    car_gallery(popular[:4], detail=lambda r: f"{r['brand']} · ❤️ {r['likes']} · 🔑 {r['test_drives']}")
    with st.expander("ดูตารางรถยอดนิยม 10 อันดับ"):
        st.dataframe(df(popular, ["car", "brand", "likes", "test_drives"]), width="stretch", hide_index=True)

    st.divider()
    name = user_selector("dash_user")
    profile = get_profile(name)
    if profile:
        left, mid, right = st.columns(3)
        with left:
            st.markdown(f"### 👤 {profile['name']}")
            st.markdown("**รถที่ชอบ**")
            if profile["liked"]:
                car_gallery(profile["liked"], cols=2)
            else:
                st.info("ยังไม่ได้ชอบรถคันไหน")
        with mid:
            st.markdown("### 🔑 ประวัติการทดลองขับ")
            if profile["test_drives"]:
                car_gallery(profile["test_drives"], cols=2, detail=lambda r: f"ลองขับ {r['test_date']}")
            else:
                st.info("ยังไม่เคยทดลองขับ")
        with right:
            st.markdown("### 👥 คนที่ชอบรถคล้ายกัน")
            sims = similar_users(name)
            if sims:
                st.dataframe(df(sims), width="stretch", hide_index=True)
            else:
                st.info("ยังไม่มีคนที่ชอบรถตรงกัน")

# =====================================================================
# Recommendations
# =====================================================================
elif page == "Recommendations":
    st.subheader("✨ รถที่แนะนำ")
    name = user_selector("rec_user")

    c1, c2, c3 = st.columns([2, 1, 1])
    mode_label = c1.radio(
        "แนะนำจาก",
        ["รถที่คนคล้ายกันเคยลองขับ", "รถที่คนคล้ายกันชอบ"],
        horizontal=True,
    )
    mode = "test_drive" if mode_label.startswith("รถที่คนคล้ายกันเคยลองขับ") else "likes"
    exclude_td = c2.checkbox("ตัดรถที่เคยลองขับแล้ว", value=True, disabled=(mode == "test_drive"),
                             help="โหมดลองขับจะตัดรถที่เคยลองขับให้อัตโนมัติ")
    top_n = c3.slider("จำนวน", 3, 10, 5)

    if mode == "test_drive":
        st.caption("Alice -LIKES-> รถ <-LIKES- คนคล้ายกัน -TEST_DROVE-> รถที่แนะนำ  ·  score = จำนวนเส้นทางที่ไปถึงรถคันนั้น")
    else:
        st.caption("Alice -LIKES-> รถ <-LIKES- คนคล้ายกัน -LIKES-> รถที่แนะนำ  ·  score = จำนวนเส้นทางที่ไปถึงรถคันนั้น")

    rows = recommend_cars(name, mode, exclude_td, top_n)
    if not rows:
        st.info("ยังไม่มีคำแนะนำสำหรับ User นี้ ลองเพิ่มรถที่ชอบหรือประวัติการลองขับในหน้า จัดการข้อมูล")
    action = "ลองขับ" if mode == "test_drive" else "ชอบ"
    for i, row in enumerate(rows, start=1):
        img_col, card_col = st.columns([1, 3])
        with img_col:
            show_car_image(row.get("image"))
        card_col.markdown(
            f"""
            <div class="car-card">
              <span class="score-pill">#{i} · score {row['score']}</span>
              <h3 style="margin:.55rem 0 .2rem 0">{row['car']}</h3>
              <div class="muted">{row.get('brand') or 'ไม่ระบุยี่ห้อ'}</div>
              <p><b>เหตุผล:</b> {", ".join(row['via_users'])} เคย{action}รถคันนี้
                 และชอบรถเหมือน {name} ({", ".join(row['shared_cars'])})</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

# =====================================================================
# Car Search
# =====================================================================
elif page == "Car Search":
    st.subheader("🔎 ค้นหารถ")
    c1, c2 = st.columns([2, 1])
    keyword = c1.text_input("ชื่อรุ่น", placeholder="เช่น Civic, Mazda, Camry")
    brand = c2.selectbox("ยี่ห้อ", [""] + list_brands(), format_func=lambda x: "ทุกยี่ห้อ" if x == "" else x)
    rows = search_cars(keyword, brand)
    st.write(f"พบ {len(rows)} รายการ")
    car_gallery(rows, detail=lambda r: f"{r['brand']} · ❤️ {r['likes']} · 🔑 {r['test_drives']}")
    with st.expander("ดูแบบตาราง"):
        st.dataframe(df(rows, ["car", "brand", "image", "likes", "test_drives", "liked_by"]),
                     width="stretch", hide_index=True)

# =====================================================================
# จัดการข้อมูล (เพิ่ม / ลบ)
# =====================================================================
elif page == "จัดการข้อมูล":
    st.subheader("🛠️ จัดการข้อมูล")
    tab_user, tab_car, tab_like, tab_td = st.tabs(["👤 User", "🚗 Car", "❤️ LIKES", "🔑 TEST_DROVE"])

    # ---------------- User ----------------
    with tab_user:
        users = get_users()
        st.dataframe(df(users, ["name", "likes", "test_drives"]), width="stretch", hide_index=True)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### ➕ เพิ่ม User")
            with st.form("add_user_form", clear_on_submit=True):
                new_name = st.text_input("ชื่อ")
                if st.form_submit_button("เพิ่ม", type="primary", width="stretch"):
                    if not new_name.strip():
                        st.error("กรุณาใส่ชื่อ")
                    elif add_user(new_name):
                        flash(f"เพิ่ม User '{new_name.strip()}' แล้ว")
                    else:
                        st.warning(f"มี User '{new_name.strip()}' อยู่แล้ว")
        with c2:
            st.markdown("#### 🗑️ ลบ User")
            if users:
                target = st.selectbox("เลือก User", [u["name"] for u in users], key="del_user")
                info = next(u for u in users if u["name"] == target)
                st.caption(f"จะลบ LIKES {info['likes']} เส้น และ TEST_DROVE {info['test_drives']} เส้นของ {target} ไปด้วย")
                confirm = st.checkbox("ยืนยันการลบ", key="confirm_del_user")
                if st.button("ลบ User", disabled=not confirm, width="stretch"):
                    delete_user(target)
                    flash(f"ลบ User '{target}' แล้ว", "warning")
            else:
                st.info("ยังไม่มี User")

    # ---------------- Car ----------------
    with tab_car:
        cars = get_cars()
        st.dataframe(df(cars, ["name", "brand", "image", "likes", "test_drives"]), width="stretch", hide_index=True)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### ➕ เพิ่ม Car")
            with st.form("add_car_form", clear_on_submit=True):
                car_name = st.text_input("ชื่อรุ่น", placeholder="เช่น Toyota Fortuner")
                car_brand = st.text_input("ยี่ห้อ", placeholder="เว้นว่างได้ จะใช้คำแรกของชื่อรุ่น")
                car_upload = st.file_uploader("รูปรถ (ไม่บังคับ)", type=IMAGE_TYPES)
                car_path = st.text_input("หรือใส่ path/URL ของรูป",
                                         placeholder="เช่น images/toyota_fortuner.jpg")
                if st.form_submit_button("เพิ่ม", type="primary", width="stretch"):
                    if not car_name.strip():
                        st.error("กรุณาใส่ชื่อรุ่น")
                    else:
                        brand_value = car_brand.strip() or car_name.strip().split()[0]
                        if car_upload is not None:
                            image_value = save_uploaded_image(car_name, car_upload)
                        elif car_path.strip():
                            image_value = car_path.strip()
                        elif resolve_image(default_image_path(car_name)):
                            image_value = default_image_path(car_name)  # มีไฟล์ชื่อตรงกันใน repo อยู่แล้ว
                        else:
                            image_value = ""
                        if add_car(car_name, brand_value, image_value):
                            flash(f"เพิ่ม Car '{car_name.strip()}' ({brand_value}) แล้ว")
                        else:
                            flash(f"มี '{car_name.strip()}' อยู่แล้ว อัปเดตยี่ห้อเป็น {brand_value}", "info")
        with c2:
            st.markdown("#### 🗑️ ลบ Car")
            if cars:
                target = st.selectbox("เลือกรถ", [c["name"] for c in cars], key="del_car")
                info = next(c for c in cars if c["name"] == target)
                st.caption(f"จะลบ LIKES {info['likes']} เส้น และ TEST_DROVE {info['test_drives']} เส้นที่ชี้มาที่ {target} ไปด้วย")
                confirm = st.checkbox("ยืนยันการลบ", key="confirm_del_car")
                if st.button("ลบ Car", disabled=not confirm, width="stretch"):
                    delete_car(target)
                    flash(f"ลบ Car '{target}' แล้ว", "warning")
            else:
                st.info("ยังไม่มีรถ")

        st.divider()
        st.markdown("#### 🖼️ เปลี่ยนรูปรถ")
        if cars:
            c1, c2 = st.columns([1, 2])
            target = c2.selectbox("เลือกรถ", [c["name"] for c in cars], key="img_car")
            current = next(c for c in cars if c["name"] == target).get("image")
            with c1:
                show_car_image(current, caption=current or "ยังไม่มี path รูป")
            with c2:
                new_upload = st.file_uploader("อัปโหลดรูปใหม่", type=IMAGE_TYPES, key=f"img_up_{target}")
                new_path = st.text_input("หรือใส่ path/URL", value=current or "", key=f"img_path_{target}")
                b1, b2 = st.columns(2)
                if b1.button("บันทึกรูป", type="primary", width="stretch"):
                    value = save_uploaded_image(target, new_upload) if new_upload is not None else new_path.strip()
                    set_car_image(target, value)
                    flash(f"อัปเดตรูปของ {target} เป็น {value or '(ไม่มีรูป)'}")
                if b2.button("ลบรูปออกจากรถ", width="stretch"):
                    set_car_image(target, None)
                    flash(f"ลบ path รูปของ {target} แล้ว (ไฟล์ใน images/ ยังอยู่)", "warning")
            st.caption(
                f"รูปที่อัปโหลดจะถูกบันทึกเป็น {IMAGE_DIR}/<ชื่อรถ>.<นามสกุล> ในโฟลเดอร์แอป "
                "ถ้ารันในเครื่องต้อง commit + push ไฟล์นั้นขึ้น GitHub ด้วย "
                "บน Streamlit Cloud ไฟล์ที่อัปโหลดจะหายเมื่อแอปรีสตาร์ต ให้ใส่รูปใน repo แล้วกรอก path แทน"
            )

    # ---------------- LIKES ----------------
    with tab_like:
        users, cars = user_names(), car_names()
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### ➕ เพิ่ม LIKES")
            if users and cars:
                u = st.selectbox("User", users, key="like_user")
                c = st.selectbox("Car", cars, key="like_car")
                if st.button("เพิ่ม LIKES", type="primary", width="stretch"):
                    if add_like(u, c):
                        flash(f"{u} -[:LIKES]-> {c}")
                    else:
                        st.warning(f"{u} ชอบ {c} อยู่แล้ว")
            else:
                st.info("ต้องมีทั้ง User และ Car ก่อน")
        with c2:
            st.markdown("#### 🗑️ ลบ LIKES")
            likes = get_likes()
            if likes:
                labels = {f"{x['user']} → {x['car']}": x for x in likes}
                chosen = st.selectbox("เลือกเส้นที่จะลบ", list(labels), key="del_like")
                if st.button("ลบ LIKES", width="stretch"):
                    x = labels[chosen]
                    remove_like(x["user"], x["car"])
                    flash(f"ลบ {x['user']} -[:LIKES]-> {x['car']} แล้ว", "warning")
            else:
                st.info("ยังไม่มี LIKES")
        st.markdown("#### LIKES ทั้งหมด")
        st.dataframe(df(get_likes(), ["user", "car"]), width="stretch", hide_index=True)

    # ---------------- TEST_DROVE ----------------
    with tab_td:
        users, cars = user_names(), car_names()
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### ➕ เพิ่ม TEST_DROVE")
            if users and cars:
                u = st.selectbox("User", users, key="td_user")
                c = st.selectbox("Car", cars, key="td_car")
                d = st.date_input("วันที่ทดลองขับ", value=date.today(), key="td_date")
                if st.button("บันทึก TEST_DROVE", type="primary", width="stretch"):
                    created = add_test_drive(u, c, d.isoformat())
                    msg = "บันทึก" if created else "อัปเดตวันที่"
                    flash(f"{msg} {u} -[:TEST_DROVE {{{d.isoformat()}}}]-> {c}")
            else:
                st.info("ต้องมีทั้ง User และ Car ก่อน")
        with c2:
            st.markdown("#### 🗑️ ลบ TEST_DROVE")
            tds = get_test_drives()
            if tds:
                labels = {f"{x['user']} → {x['car']} ({x['test_date']})": x for x in tds}
                chosen = st.selectbox("เลือกเส้นที่จะลบ", list(labels), key="del_td")
                if st.button("ลบ TEST_DROVE", width="stretch"):
                    x = labels[chosen]
                    remove_test_drive(x["user"], x["car"])
                    flash(f"ลบ {x['user']} -[:TEST_DROVE]-> {x['car']} แล้ว", "warning")
            else:
                st.info("ยังไม่มี TEST_DROVE")
        st.markdown("#### TEST_DROVE ทั้งหมด")
        st.dataframe(df(get_test_drives(), ["user", "car", "test_date"]), width="stretch", hide_index=True)

# =====================================================================
# Graph Explorer
# =====================================================================
elif page == "Graph Explorer":
    st.subheader("🕸️ Graph Explorer")
    names = user_names()
    c1, c2 = st.columns([2, 1])
    choice = c1.selectbox("แสดงกราฟของ", ["(ทั้งหมด)"] + names)
    show_similar = c2.checkbox("แสดงคนที่ชอบรถเหมือนกัน", value=True, disabled=(choice == "(ทั้งหมด)"))

    focus = None if choice == "(ทั้งหมด)" else choice
    rows = graph_edges(focus, show_similar)
    st.caption("🟦 User  ·  🟧 Car  ·  เส้นทึบ = LIKES  ·  เส้นประสีแดง = TEST_DROVE")
    if not rows:
        st.info("ยังไม่มีข้อมูลความสัมพันธ์")
    else:
        draw_graph(rows, focus)
        with st.expander("ดูข้อมูล edge ที่ใช้วาดกราฟ"):
            st.dataframe(df(rows), width="stretch", hide_index=True)

# =====================================================================
# Admin / Setup
# =====================================================================
elif page == "Admin / Setup":
    st.subheader("⚙️ Setup ข้อมูลตัวอย่าง")
    st.markdown(
        """
        **Graph schema**
        - `(:User {name})`
        - `(:Car {name, brand})`
        - `(:User)-[:LIKES]->(:Car)`
        - `(:User)-[:TEST_DROVE {test_date}]->(:Car)`
        """
    )

    st.info("ปุ่มนี้ใช้ MERGE จึงกดซ้ำได้ ไม่เกิดข้อมูลซ้ำ (User 10, Car 10, LIKES 32, TEST_DROVE 10)")
    if st.button("สร้าง Constraint + Demo Data", type="primary", width="stretch"):
        with st.spinner("กำลังสร้างข้อมูล..."):
            seed_demo_data()
        flash("สร้างข้อมูลตัวอย่างเรียบร้อยแล้ว")

    st.divider()
    st.markdown("#### 🧨 ล้างข้อมูลทั้งหมด")
    st.warning("ลบ User และ Car ทั้งหมดพร้อมทุกความสัมพันธ์ (ข้อมูล label อื่นใน database ไม่ถูกลบ) ย้อนกลับไม่ได้")
    confirm = st.text_input("พิมพ์ DELETE เพื่อยืนยัน")
    if st.button("ล้างข้อมูล", disabled=(confirm != "DELETE"), width="stretch"):
        n = clear_car_data()
        flash(f"ลบ {n} nodes แล้ว", "warning")
