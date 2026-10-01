from __future__ import annotations

import base64
import json
import html
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

from background3d import render_background
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
    MODEL_DIR,
    default_image_path,
    default_model_path,
    image_slug,
    set_car_image,
    set_car_model,
    change_like,
    rename_user,
    update_car,
    update_test_drive,
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
    initial_sidebar_state="collapsed",
)

st.html(
    """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Thai:wght@400;500;600&family=Prompt:wght@500;600;700&display=swap');
      :root {
        --glass: rgba(9, 13, 21, .66);
        --glass-2: rgba(255, 255, 255, .045);
        --line: rgba(148, 163, 184, .18);
        --accent: #38bdf8;
        --accent-2: #fbbf24;
        --muted: #94a3b8;
      }
      html, body, .stApp, .stMarkdown, p, li, label, input, textarea, button, [data-testid="stWidgetLabel"] {
        font-family: 'IBM Plex Sans Thai', system-ui, sans-serif;
      }
      h1, h2, h3, h4, .hero-title { font-family: 'Prompt', 'IBM Plex Sans Thai', sans-serif !important; letter-spacing: .2px; }

      /* ให้ฉาก 3D ด้านหลังมองเห็นได้ */
      .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], [data-testid="stBottom"] { background: transparent !important; }
      [data-testid="stHeader"] { background: transparent !important; }
      .block-container { max-width: 1200px; padding-top: 2.2rem; padding-bottom: 4rem; }

      /* ซ่อน sidebar และ header เดิม ใช้แถบเมนูด้านบนแทน */
      [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], [data-testid="collapsedControl"],
      [data-testid="stHeader"] { display: none !important; }
      .block-container { padding-top: 6.2rem !important; }

      /* ---------- แถบเมนูด้านบน ---------- */
      .st-key-gc_nav {
        position: fixed !important; top: 14px; left: 50%; transform: translateX(-50%);
        width: min(1240px, calc(100vw - 28px)) !important; z-index: 1000;
        padding: .5rem .6rem .5rem 1.1rem !important; flex-wrap: nowrap !important;
        background: rgba(8, 11, 18, .72); backdrop-filter: blur(18px) saturate(1.35);
        border: 1px solid var(--line); border-radius: 20px;
        box-shadow: 0 14px 44px rgba(0, 0, 0, .45), inset 0 1px 0 rgba(255,255,255,.05);
        overflow-x: auto; scrollbar-width: none;
      }
      .st-key-gc_nav::-webkit-scrollbar { display: none; }
      .st-key-gc_nav > div { flex: 0 0 auto; width: auto !important; }
      .st-key-gc_nav > div:has(.stButtonGroup), .st-key-gc_nav > div:has([data-testid="stButtonGroup"]) { flex: 1 1 auto; display: flex; justify-content: center; }
      .gc-brand {
        font-family: 'Prompt', sans-serif; font-weight: 700; font-size: 1.2rem; color: #f8fafc;
        white-space: nowrap; letter-spacing: .3px; padding-right: .4rem;
      }
      .gc-brand span { background: linear-gradient(90deg, #7dd3fc, #fbbf24); -webkit-background-clip: text; background-clip: text; color: transparent; }
      .st-key-gc_nav [data-testid="stButtonGroup"] { gap: .25rem !important; flex-wrap: nowrap !important; }
      .st-key-gc_nav [data-testid="stButtonGroup"] button {
        background: transparent !important; border: 1px solid transparent !important;
        border-radius: 999px !important; padding: .38rem .95rem !important; min-height: 0 !important;
        color: #cbd5e1 !important; white-space: nowrap; transition: background .2s, color .2s, border-color .2s;
      }
      .st-key-gc_nav [data-testid="stButtonGroup"] button:hover {
        background: rgba(56, 189, 248, .10) !important; color: #f8fafc !important;
      }
      .st-key-gc_nav [data-testid="stButtonGroup"] button[aria-checked="true"],
      .st-key-gc_nav [data-testid="stButtonGroup"] button[data-selected="true"] {
        background: linear-gradient(135deg, rgba(56,189,248,.28), rgba(56,189,248,.10)) !important;
        border-color: rgba(56, 189, 248, .45) !important; color: #f0f9ff !important;
        box-shadow: 0 0 18px rgba(56, 189, 248, .25);
      }
      .st-key-gc_nav > div:has([data-testid="stButtonGroup"]) { min-width: 0; }
      .st-key-gc_nav [data-testid="stButtonGroup"] { width: max-content; }

      /* มือถือ/จอแคบ: โลโก้ + สวิตช์อยู่แถวบน เมนูเลื่อนซ้าย-ขวาแถวล่าง */
      @media (max-width: 900px) {
        .st-key-gc_nav { flex-wrap: wrap !important; row-gap: .35rem !important; overflow: visible; padding: .55rem .7rem !important; }
        .st-key-gc_nav > div:has(.gc-brand) { order: 1; flex: 1 1 auto; }
        .st-key-gc_nav > div:has([data-testid="stCheckbox"]), .st-key-gc_nav > div:has([data-testid="stToggle"]) { order: 2; }
        .st-key-gc_nav > div:has([data-testid="stButtonGroup"]) {
          order: 3; flex: 1 1 100% !important; width: 100% !important; justify-content: flex-start !important;
          overflow-x: auto; scrollbar-width: none; -webkit-overflow-scrolling: touch;
        }
        .st-key-gc_nav > div:has([data-testid="stButtonGroup"])::-webkit-scrollbar { display: none; }
        .block-container { padding-top: 8.4rem !important; }
        .st-key-gc_panel { padding: 1.1rem 1rem 1.4rem; border-radius: 20px; }
      }
      .st-key-gc_nav [data-testid="stCheckbox"] label p, .st-key-gc_nav [data-testid="stToggle"] label p { color: #94a3b8; font-size: .85rem; }

      /* sidebar แบบกระจกฝ้า (ไม่ได้ใช้แล้ว เก็บไว้เผื่อเปิดกลับ) */
      [data-testid="stSidebar"] {
        background: rgba(7, 10, 16, .74) !important; backdrop-filter: blur(16px);
        border-right: 1px solid var(--line);
      }
      [data-testid="stSidebar"] [role="radiogroup"] label {
        padding: .45rem .7rem; border-radius: 12px; margin-bottom: .15rem; transition: background .2s;
      }
      [data-testid="stSidebar"] [role="radiogroup"] label:hover { background: rgba(56, 189, 248, .10); }
      [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
        background: linear-gradient(90deg, rgba(56,189,248,.22), rgba(56,189,248,.04));
        box-shadow: inset 3px 0 0 var(--accent);
      }

      /* hero โปร่ง ให้เห็นฉากด้านหลัง */
      .hero { padding: 3.2rem .4rem 2.2rem; color: #f8fafc; text-shadow: 0 2px 18px rgba(0,0,0,.65); }
      .hero .eyebrow { color: var(--accent); font-weight: 600; letter-spacing: .18em; font-size: .78rem; text-transform: uppercase; }
      .hero-title { font-size: clamp(2rem, 4.2vw, 3.3rem); font-weight: 700; margin: .35rem 0 .5rem; line-height: 1.1; }
      .hero-title span {
        background: linear-gradient(90deg, #7dd3fc, #fbbf24); -webkit-background-clip: text; background-clip: text; color: transparent;
      }
      .hero p { color: #cbd5e1; max-width: 640px; margin: 0; }
      .chips { display: flex; flex-wrap: wrap; gap: .45rem; margin-top: 1rem; }
      .chip {
        font-family: ui-monospace, monospace; font-size: .78rem; color: #e2e8f0;
        padding: .28rem .65rem; border-radius: 999px; background: rgba(15, 23, 42, .6);
        border: 1px solid var(--line); backdrop-filter: blur(6px);
      }

      /* แผงเนื้อหาหลัก */
      .st-key-gc_panel {
        background: var(--glass); backdrop-filter: blur(14px) saturate(1.2);
        border: 1px solid var(--line); border-radius: 26px;
        padding: 1.6rem 1.8rem 2rem; box-shadow: 0 30px 80px rgba(0,0,0,.45);
      }
      [data-testid="stMetric"] {
        background: var(--glass-2); border: 1px solid var(--line); border-radius: 18px; padding: .9rem 1.1rem;
      }
      [data-testid="stMetricValue"] { font-family: 'Prompt', sans-serif; }
      [data-testid="stExpander"], [data-testid="stForm"] { background: var(--glass-2); border-radius: 16px; }
      /* กรอบรูปรถขนาดเท่ากันทุกใบ (16:10) รูปไม่ถูกครอบตัด ส่วนที่เหลือเติมพื้นขาว */
      [data-testid="stImage"], [data-testid="stImageContainer"] { width: 100% !important; }
      [data-testid="stImage"] img, [data-testid="stImageContainer"] img {
        width: 100% !important; height: auto !important; max-height: none !important;
        aspect-ratio: 16 / 10; object-fit: contain; object-position: center;
        background: #ffffff; padding: 6px; box-sizing: border-box;
        border-radius: 14px; box-shadow: 0 6px 18px rgba(0,0,0,.25);
      }
      .stTabs [data-baseweb="tab-list"] { gap: .3rem; }
      .stTabs [data-baseweb="tab"] { border-radius: 10px 10px 0 0; padding: .4rem .9rem; }

      .car-card {
        padding: 1rem 1.2rem; border: 1px solid var(--line); border-radius: 18px;
        margin-bottom: .75rem; background: var(--glass-2);
      }
      .car-card h3 { margin: .55rem 0 .2rem 0; }
      .score-pill {
        display: inline-block; padding: .22rem .65rem; border-radius: 999px;
        background: linear-gradient(90deg, #0284c7, #38bdf8); color: white; font-size: .8rem; font-weight: 700;
      }
      .muted { color: var(--muted); font-size: .9rem; }
      .no-img {
        aspect-ratio: 16/10; display: flex; align-items: center; justify-content: center;
        border: 1px dashed var(--line); border-radius: 14px; color: var(--muted);
      }
    </style>
    """
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


RESULT_TEXT = {
    "exists": "ชื่อ/ข้อมูลนี้มีอยู่แล้ว",
    "notfound": "ไม่พบข้อมูล (อาจถูกลบไปแล้ว)",
    "empty": "ชื่อต้องไม่ว่าง",
}


def editor_key(name: str) -> str:
    """key ของตาราง data_editor  เปลี่ยนทุกครั้งที่บันทึก เพื่อล้างค่าที่แก้ค้างไว้"""
    return f"{name}_{st.session_state.get('editor_ver', 0)}"


def done(message: str, kind: str = "success") -> None:
    """แสดงข้อความหลัง rerun และรีเซ็ตตารางแก้ไขทั้งหมด"""
    st.session_state["editor_ver"] = st.session_state.get("editor_ver", 0) + 1
    flash(message, kind)


def report(results: list[tuple[str, str]]) -> None:
    """สรุปผลการแก้ไขหลายรายการ แล้ว rerun"""
    ok = [label for label, r in results if r == "ok"]
    failed = [f"{label} ({RESULT_TEXT.get(r, r)})" for label, r in results if r not in ("ok", "same")]
    if failed:
        done(f"บันทึกสำเร็จ {len(ok)} รายการ · ไม่สำเร็จ: " + " · ".join(failed), "warning")
    elif ok:
        done(f"บันทึกการแก้ไขแล้ว {len(ok)} รายการ: " + " · ".join(ok))
    else:
        done("ไม่มีอะไรเปลี่ยน", "info")


def save_button(n_changes: int, key: str, apply) -> None:
    """ปุ่มบันทึกใต้ตาราง data_editor  โชว์เมื่อมีการแก้ไข"""
    if not n_changes:
        return
    b1, b2 = st.columns([1, 1])
    if b1.button(f"💾 บันทึกการแก้ไข ({n_changes} รายการ)", type="primary", width="stretch", key=key):
        report(apply())
    if b2.button("↩️ ยกเลิกการแก้ไข", width="stretch", key=f"{key}_cancel"):
        done("ยกเลิกการแก้ไขแล้ว", "info")


def clean(value) -> str:
    return "" if value is None or (isinstance(value, float) and pd.isna(value)) else str(value).strip()


def to_date(value) -> date | None:
    if value is None or (not isinstance(value, (str, date)) and pd.isna(value)):
        return None
    if isinstance(value, str):
        return date.fromisoformat(value[:10]) if value else None
    if hasattr(value, "date") and not type(value) is date:
        return value.date()
    return value


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
MODEL_TYPES = ["glb"]
MODEL_VIEWER_JS = "https://cdn.jsdelivr.net/npm/@google/model-viewer@4.3.1/dist/model-viewer.min.js"
MAX_MODEL_MB = 25  # ไฟล์ในเครื่องจะถูกฝังเป็น base64 ไฟล์ใหญ่กว่านี้ให้ใช้ URL แทน


def is_url(path: str) -> bool:
    return path.startswith(("http://", "https://"))


def resolve_local(path: str | None) -> Path | None:
    """แปลง path ที่เก็บใน Neo4j เป็นไฟล์จริงในโฟลเดอร์แอป  ถ้าไม่มีหรืออยู่นอกโฟลเดอร์คืน None"""
    if not path or is_url(path):
        return None
    file = (APP_DIR / path).resolve()
    if APP_DIR not in file.parents or not file.is_file():  # กันไม่ให้อ่านไฟล์นอกโฟลเดอร์แอป
        return None
    return file


def resolve_image(path: str | None) -> str | None:
    """คืน URL หรือ path ไฟล์รูปที่ใช้ได้จริง  ถ้าหาไม่เจอคืน None"""
    if path and is_url(path):
        return path
    file = resolve_local(path)
    return str(file) if file else None


@st.cache_data(show_spinner=False)
def _glb_data_uri(file: str, mtime: float) -> str:
    return "data:model/gltf-binary;base64," + base64.b64encode(Path(file).read_bytes()).decode()


def model_src(path: str | None) -> str | None:
    """คืน src สำหรับ <model-viewer>: URL ตรง ๆ หรือไฟล์ใน repo ที่แปลงเป็น data URI"""
    if path and is_url(path):
        return path
    file = resolve_local(path)
    if not file:
        return None
    if file.stat().st_size > MAX_MODEL_MB * 1024 * 1024:
        st.warning(f"{path} ใหญ่เกิน {MAX_MODEL_MB} MB ให้ใช้ URL (เช่น raw.githubusercontent.com) แทน")
        return None
    return _glb_data_uri(str(file), file.stat().st_mtime)


def show_3d(model_path: str | None, image_path: str | None = None, height: int = 420, alt: str = "car") -> None:
    """แสดงโมเดล 3D หมุน/ซูมได้  ถ้ายังไม่มีโมเดลจะแสดงรูปแทน"""
    src = model_src(model_path)
    if not src:
        show_car_image(image_path)
        st.caption("ยังไม่มีโมเดล 3D ของรถคันนี้")
        return
    viewer = f"""
        <script type="module" src="{MODEL_VIEWER_JS}"></script>
        <style>
          html, body {{ margin: 0; background: transparent; font-family: sans-serif; }}
          model-viewer {{
            width: 100%; height: {height}px; border-radius: 18px;
            background: radial-gradient(circle at 50% 30%, #1e293b 0%, #0b1220 65%, #05070c 100%);
            --progress-bar-color: #0369a1;
          }}
          .hint {{
            position: absolute; bottom: 10px; left: 50%; transform: translateX(-50%);
            font-size: 12px; color: #cbd5e1; background: rgba(15,23,42,.7);
            padding: 4px 10px; border-radius: 999px;
          }}
        </style>
        <model-viewer src="{html.escape(src, quote=True)}" alt="{html.escape(alt, quote=True)}"
            camera-controls auto-rotate rotation-per-second="18deg"
            camera-orbit="35deg 72deg auto" shadow-intensity="1" shadow-softness="0.8"
            exposure="1.05" environment-image="neutral"
            interaction-prompt="none" touch-action="pan-y">
          <div class="hint">🖱️ ลากเพื่อหมุน · scroll เพื่อซูม · คลิกขวาลากเพื่อเลื่อน</div>
        </model-viewer>
        """
    if hasattr(st, "iframe"):  # Streamlit รุ่นใหม่
        st.iframe(viewer, height=height + 8)
    else:  # Streamlit รุ่นเก่า
        import streamlit.components.v1 as components
        components.html(viewer, height=height + 8)


def show_car_image(path: str | None, caption: str | None = None) -> None:
    src = resolve_image(path)
    if src:
        st.image(src, caption=caption, width="stretch")
    else:
        st.markdown('<div class="no-img">🚗 ไม่มีรูป</div>', unsafe_allow_html=True)
        if caption:
            st.caption(caption)


def save_upload(car_name: str, uploaded, folder: str, default_ext: str) -> str:
    """บันทึกไฟล์ที่อัปโหลดลง <folder>/<ชื่อรถ>.<นามสกุล> แล้วคืน path แบบ relative"""
    ext = Path(uploaded.name).suffix.lower() or default_ext
    rel = f"{folder}/{image_slug(car_name)}{ext}"
    (APP_DIR / folder).mkdir(exist_ok=True)
    (APP_DIR / rel).write_bytes(uploaded.getvalue())
    return rel


def save_uploaded_image(car_name: str, uploaded) -> str:
    return save_upload(car_name, uploaded, IMAGE_DIR, ".png")


def save_uploaded_model(car_name: str, uploaded) -> str:
    return save_upload(car_name, uploaded, MODEL_DIR, ".glb")


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


VIS_NETWORK_JS = "https://cdn.jsdelivr.net/npm/vis-network@9.1.9/standalone/umd/vis-network.min.js"


def draw_graph(rows: list[dict], focus: str | None = None, height: int = 620) -> None:
    """กราฟแบบโต้ตอบในกรอบสี่เหลี่ยม: scroll = ซูม, ลาก = เลื่อน, คลิก node = ไฮไลต์เพื่อนบ้าน"""
    degree: dict[str, int] = {}
    for r in rows:
        for k in (f"U:{r['user']}", f"C:{r['car']}"):
            degree[k] = degree.get(k, 0) + 1

    nodes: dict[str, dict] = {}
    edges: list[dict] = []
    for r in rows:
        u, c = f"U:{r['user']}", f"C:{r['car']}"
        nodes.setdefault(u, {
            "id": u, "label": r["user"], "group": "focus" if r["user"] == focus else "user",
            "value": degree[u], "title": f"User: {r['user']} · {degree[u]} เส้น",
        })
        nodes.setdefault(c, {
            "id": c, "label": r["car"], "group": "car", "title": f"Car: {r['car']} · {degree[c]} เส้น",
        })
        if r["rel"] == "TEST_DROVE":
            d = r.get("test_date") or ""
            edges.append({
                "from": u, "to": c, "label": d, "dashes": True, "rel": "TEST_DROVE",
                "title": f"{r['user']} ลองขับ {r['car']} {d}",
                "color": {"color": "#f87171", "highlight": "#fecaca", "hover": "#fca5a5"},
            })
        else:
            edges.append({
                "from": u, "to": c, "rel": "LIKES", "title": f"{r['user']} ชอบ {r['car']}",
                "color": {"color": "rgba(148,163,184,.55)", "highlight": "#7dd3fc", "hover": "#bae6fd"},
            })

    # ป้องกัน "</script>" ในชื่อจาก database หลุดออกจากแท็ก script
    data = json.dumps({"nodes": list(nodes.values()), "edges": edges}, ensure_ascii=False).replace("</", "<\\/")

    st.iframe(
        f"""
        <script src="{VIS_NETWORK_JS}"></script>
        <style>
          html, body {{ margin: 0; background: transparent; font-family: 'IBM Plex Sans Thai', system-ui, sans-serif; }}
          #wrap {{
            position: relative; height: {height}px; border-radius: 18px; overflow: hidden;
            background: radial-gradient(circle at 50% 40%, #142036 0%, #0a1020 60%, #060910 100%);
            border: 1px solid rgba(148,163,184,.18);
          }}
          #net {{ position: absolute; inset: 0; }}
          .bar {{ position: absolute; top: 12px; right: 12px; display: flex; gap: 6px; z-index: 5; }}
          .bar button {{
            background: rgba(15,23,42,.82); color: #e2e8f0; border: 1px solid rgba(148,163,184,.28);
            border-radius: 10px; padding: 6px 11px; font-size: 13px; cursor: pointer; font-family: inherit;
          }}
          .bar button:hover {{ border-color: #38bdf8; color: #fff; }}
          .hint, .legend {{
            position: absolute; left: 12px; z-index: 5; font-size: 12px; color: #94a3b8;
            background: rgba(15,23,42,.72); border: 1px solid rgba(148,163,184,.18);
            border-radius: 10px; padding: 6px 10px; pointer-events: none;
          }}
          .hint {{ top: 12px; }}
          .legend {{ bottom: 12px; display: flex; gap: 14px; align-items: center; }}
          .dot {{ display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 5px; vertical-align: -1px; }}
          .box {{ display: inline-block; width: 14px; height: 10px; border-radius: 3px; margin-right: 5px; background: #fb923c; vertical-align: -1px; }}
          .ln {{ display: inline-block; width: 22px; border-top: 2px solid #94a3b8; margin-right: 5px; vertical-align: 3px; }}
          .ln.dash {{ border-top: 2px dashed #f87171; }}
          div.vis-tooltip {{
            background: #0f172a !important; color: #e2e8f0 !important; border: 1px solid #334155 !important;
            border-radius: 8px !important; font-family: inherit !important; font-size: 12px !important; padding: 6px 9px !important;
          }}
        </style>
        <div id="wrap">
          <div id="net"></div>
          <div class="hint">🖱️ scroll = ซูม · ลาก = เลื่อน · คลิก node = ไฮไลต์</div>
          <div class="bar">
            <button id="zin" title="ซูมเข้า">＋</button>
            <button id="zout" title="ซูมออก">－</button>
            <button id="fit" title="แสดงทั้งหมด">⤢ พอดีกรอบ</button>
            <button id="phys" title="จัดวางใหม่">✨ จัดวางใหม่</button>
          </div>
          <div class="legend">
            <span><span class="dot" style="background:#38bdf8"></span>User</span>
            <span><span class="dot" style="background:#fbbf24"></span>User ที่เลือก</span>
            <span><span class="box"></span>Car</span>
            <span><span class="ln"></span>LIKES</span>
            <span><span class="ln dash"></span>TEST_DROVE</span>
          </div>
        </div>
        <script>
          const data = {data};
          const nodes = new vis.DataSet(data.nodes), edges = new vis.DataSet(data.edges);
          const network = new vis.Network(document.getElementById("net"), {{ nodes, edges }}, {{
            autoResize: true,
            nodes: {{
              font: {{ color: "#e2e8f0", size: 14, strokeWidth: 4, strokeColor: "#0a1020" }},
              borderWidth: 2, scaling: {{ min: 10, max: 26 }},
            }},
            groups: {{
              user:  {{ shape: "dot", color: {{ background: "#38bdf8", border: "#bae6fd", highlight: {{ background: "#7dd3fc", border: "#fff" }}, hover: {{ background: "#7dd3fc", border: "#fff" }} }} }},
              focus: {{ shape: "dot", color: {{ background: "#fbbf24", border: "#fde68a", highlight: {{ background: "#fcd34d", border: "#fff" }}, hover: {{ background: "#fcd34d", border: "#fff" }} }} }},
              car:   {{ shape: "box", margin: 9, shapeProperties: {{ borderRadius: 8 }},
                       font: {{ color: "#1c1003", strokeWidth: 0, size: 13 }},
                       color: {{ background: "#fb923c", border: "#fdba74", highlight: {{ background: "#fdba74", border: "#fff" }}, hover: {{ background: "#fdba74", border: "#fff" }} }} }},
            }},
            edges: {{
              arrows: {{ to: {{ enabled: true, scaleFactor: 0.55 }} }},
              width: 1.6, selectionWidth: 1.5, hoverWidth: 0.8,
              smooth: {{ type: "dynamic" }},
              font: {{ size: 10, color: "#fca5a5", strokeWidth: 0, align: "middle" }},
            }},
            physics: {{
              solver: "forceAtlas2Based",
              forceAtlas2Based: {{ gravitationalConstant: -70, springLength: 130, springConstant: 0.05, avoidOverlap: 0.4 }},
              stabilization: {{ iterations: 300 }},
            }},
            interaction: {{ hover: true, tooltipDelay: 120, zoomSpeed: 0.7, keyboard: true }},
          }});

          const freeze = () => network.setOptions({{ physics: false }});
          network.once("stabilizationIterationsDone", () => {{ freeze(); network.fit({{ animation: {{ duration: 500 }} }}); }});

          const zoom = (f) => network.moveTo({{ scale: network.getScale() * f, animation: {{ duration: 250 }} }});
          document.getElementById("zin").onclick = () => zoom(1.3);
          document.getElementById("zout").onclick = () => zoom(1 / 1.3);
          document.getElementById("fit").onclick = () => network.fit({{ animation: {{ duration: 400 }} }});
          document.getElementById("phys").onclick = () => {{
            network.setOptions({{ physics: true }}); network.stabilize(200);
            network.once("stabilized", () => {{ freeze(); network.fit({{ animation: {{ duration: 400 }} }}); }});
          }};

          // คลิก node: ไฮไลต์ node ที่เชื่อมกัน ที่เหลือจางลง
          const reset = () => {{
            nodes.update(nodes.getIds().map(id => ({{ id, opacity: 1 }})));
            edges.update(edges.get().map(e => ({{ id: e.id, hidden: false }})));
          }};
          network.on("selectNode", (p) => {{
            const id = p.nodes[0], keep = new Set([id, ...network.getConnectedNodes(id)]);
            const keepEdges = new Set(network.getConnectedEdges(id));
            nodes.update(nodes.getIds().map(n => ({{ id: n, opacity: keep.has(n) ? 1 : 0.15 }})));
            edges.update(edges.get().map(e => ({{ id: e.id, hidden: !keepEdges.has(e.id) }})));
          }});
          network.on("deselectNode", reset);
        </script>
        """,
        height=height + 4,
    )


# ---------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------
require_connection()

# key = ชื่อหน้า (ใช้ใน if/elif ด้านล่าง), value = ป้ายที่โชว์บนแถบเมนู
PAGES = {
    "Dashboard": "📊 ภาพรวม",
    "Recommendations": "✨ แนะนำรถ",
    "Car Search": "🔎 ค้นหา",
    "3D Showroom": "🧊 3D Showroom",
    "จัดการข้อมูล": "🛠️ จัดการข้อมูล",
    "Graph Explorer": "🕸️ กราฟ",
    "Admin / Setup": "⚙️ ตั้งค่า",
}

# ---------------- แถบเมนูด้านบน ----------------
with st.container(key="gc_nav", horizontal=True, vertical_alignment="center", gap="medium"):
    st.html('<div class="gc-brand">🚗 Graph<span>Car</span></div>')
    page = st.segmented_control(
        "เมนู",
        list(PAGES),
        format_func=lambda p: PAGES[p],
        default="Dashboard",
        required=True,
        key="nav",
        label_visibility="collapsed",
    ) or "Dashboard"
    bg_on = st.toggle("3D", value=True, key="bg_on", help="เปิด/ปิดพื้นหลัง 3D (ปิดได้ถ้าเครื่องช้าหรือใช้มือถือ)")

render_background(list(PAGES).index(page), enabled=bg_on)

st.html(
    """
    <div class="hero">
      <div class="eyebrow">Graph-powered car recommender</div>
      <div class="hero-title">GraphCar <span>Showroom</span></div>
      <p>ระบบแนะนำรถยนต์ด้วย Graph Database — ดูว่าคนที่ชอบรถแบบเดียวกับคุณ ชอบและลองขับรุ่นไหน</p>
      <div class="chips">
        <span class="chip">(User)-[:LIKES]-&gt;(Car)</span>
        <span class="chip">(User)-[:TEST_DROVE]-&gt;(Car)</span>
        <span class="chip">Neo4j Aura</span>
      </div>
    </div>
    """
)

with st.container(key="gc_panel"):  # แผงกระจกครอบเนื้อหาทุกหน้า
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

        if rows:
            st.divider()
            pick = st.selectbox("🧊 ดูรถที่แนะนำแบบ 3D", [r["car"] for r in rows], key="rec_3d")
            chosen = next(r for r in rows if r["car"] == pick)
            show_3d(chosen.get("model"), chosen.get("image"), height=380, alt=pick)

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
    # 3D Showroom
    # =====================================================================
    elif page == "3D Showroom":
        st.subheader("🧊 3D Showroom")
        cars = get_cars()
        if not cars:
            st.info("ยังไม่มีรถ กรุณาไปหน้า จัดการข้อมูล หรือ Admin / Setup ก่อน")
            st.stop()

        target = st.selectbox("เลือกรถ", [c["name"] for c in cars], key="showroom_car")
        car = next(c for c in cars if c["name"] == target)

        left, right = st.columns([3, 1.3])
        with left:
            show_3d(car.get("model"), car.get("image"), height=480, alt=target)
        with right:
            st.markdown(f"## {target}")
            st.caption(car.get("brand") or "ไม่ระบุยี่ห้อ")
            m1, m2 = st.columns(2)
            m1.metric("❤️ ชอบ", car["likes"])
            m2.metric("🔑 ลองขับ", car["test_drives"])
            detail = next((r for r in search_cars(target) if r["car"] == target), None)
            liked_by = (detail or {}).get("liked_by") or []
            st.markdown("**คนที่ชอบ:** " + (", ".join(sorted(liked_by)) or "ยังไม่มี"))

            st.divider()
            names = user_names()
            if names:
                who = st.selectbox("ในนามของ User", names, key="showroom_user")
                if st.button("❤️ ชอบรถคันนี้", width="stretch"):
                    if add_like(who, target):
                        flash(f"{who} -[:LIKES]-> {target}")
                    else:
                        st.info(f"{who} ชอบ {target} อยู่แล้ว")
                if st.button("🔑 บันทึกทดลองขับวันนี้", type="primary", width="stretch"):
                    add_test_drive(who, target, date.today().isoformat())
                    flash(f"{who} -[:TEST_DROVE {{{date.today().isoformat()}}}]-> {target}")
            st.caption(f"model: {car.get('model') or '-'}")

    # =====================================================================
    # จัดการข้อมูล (เพิ่ม / ลบ)
    # =====================================================================
    elif page == "จัดการข้อมูล":
        st.subheader("🛠️ จัดการข้อมูล")
        st.caption("✏️ ดับเบิลคลิกช่องในตารางเพื่อแก้ไขได้ทันที แล้วกดปุ่ม 💾 บันทึก  ·  หรือใช้ฟอร์ม เพิ่ม / แก้ไข / ลบ ด้านล่างตาราง")
        tab_user, tab_car, tab_like, tab_td = st.tabs(["👤 User", "🚗 Car", "❤️ LIKES", "🔑 TEST_DROVE"])

        # ---------------- User ----------------
        with tab_user:
            users = get_users()
            edited = st.data_editor(
                df(users, ["name", "likes", "test_drives"]),
                key=editor_key("ed_users"), hide_index=True, width="stretch", num_rows="fixed",
                disabled=["likes", "test_drives"],
                column_config={
                    "name": st.column_config.TextColumn("ชื่อ ✏️", required=True),
                    "likes": st.column_config.NumberColumn("❤️ ชอบ"),
                    "test_drives": st.column_config.NumberColumn("🔑 ลองขับ"),
                },
            )
            changes = [
                (u["name"], clean(n)) for u, n in zip(users, edited["name"]) if clean(n) != u["name"]
            ]
            save_button(len(changes), "save_users", lambda: [
                (f"{o} → {n}", rename_user(o, n)) for o, n in changes
            ])

            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown("#### ➕ เพิ่ม User")
                with st.form("add_user_form", clear_on_submit=True):
                    new_name = st.text_input("ชื่อ")
                    if st.form_submit_button("เพิ่ม", type="primary", width="stretch"):
                        if not new_name.strip():
                            st.error("กรุณาใส่ชื่อ")
                        elif add_user(new_name):
                            done(f"เพิ่ม User '{new_name.strip()}' แล้ว")
                        else:
                            st.warning(f"มี User '{new_name.strip()}' อยู่แล้ว")
            with c2:
                st.markdown("#### ✏️ แก้ไข User")
                if users:
                    target = st.selectbox("เลือก User", [u["name"] for u in users], key="edit_user")
                    renamed = st.text_input("ชื่อใหม่", value=target, key=f"edit_user_name_{target}")
                    if st.button("บันทึกชื่อ", type="primary", width="stretch", key="edit_user_btn"):
                        report([(f"{target} → {renamed.strip()}", rename_user(target, renamed))])
                    st.caption("ความสัมพันธ์ LIKES / TEST_DROVE ของคนนี้ยังอยู่ครบ")
                else:
                    st.info("ยังไม่มี User")
            with c3:
                st.markdown("#### 🗑️ ลบ User")
                if users:
                    target = st.selectbox("เลือก User", [u["name"] for u in users], key="del_user")
                    info = next(u for u in users if u["name"] == target)
                    st.caption(f"จะลบ LIKES {info['likes']} เส้น และ TEST_DROVE {info['test_drives']} เส้นของ {target} ไปด้วย")
                    confirm = st.checkbox("ยืนยันการลบ", key="confirm_del_user")
                    if st.button("ลบ User", disabled=not confirm, width="stretch"):
                        delete_user(target)
                        done(f"ลบ User '{target}' แล้ว", "warning")
                else:
                    st.info("ยังไม่มี User")

        # ---------------- Car ----------------
        with tab_car:
            cars = get_cars()
            edited = st.data_editor(
                df(cars, ["name", "brand", "image", "model", "likes", "test_drives"]),
                key=editor_key("ed_cars"), hide_index=True, width="stretch", num_rows="fixed",
                disabled=["image", "model", "likes", "test_drives"],
                column_config={
                    "name": st.column_config.TextColumn("ชื่อรุ่น ✏️", required=True),
                    "brand": st.column_config.TextColumn("ยี่ห้อ ✏️"),
                    "image": st.column_config.TextColumn("รูป"),
                    "model": st.column_config.TextColumn("โมเดล 3D"),
                    "likes": st.column_config.NumberColumn("❤️ ชอบ"),
                    "test_drives": st.column_config.NumberColumn("🔑 ลองขับ"),
                },
            )
            changes = [
                (c["name"], clean(n), clean(b))
                for c, n, b in zip(cars, edited["name"], edited["brand"])
                if clean(n) != c["name"] or clean(b) != (c.get("brand") or "")
            ]
            save_button(len(changes), "save_cars", lambda: [
                (f"{o} → {n} ({b})", update_car(o, n, b)) for o, n, b in changes
            ])

            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown("#### ➕ เพิ่ม Car")
                with st.form("add_car_form", clear_on_submit=True):
                    car_name = st.text_input("ชื่อรุ่น", placeholder="เช่น Toyota Fortuner")
                    car_brand = st.text_input("ยี่ห้อ", placeholder="เว้นว่างได้ จะใช้คำแรกของชื่อรุ่น")
                    car_upload = st.file_uploader("รูปรถ (ไม่บังคับ)", type=IMAGE_TYPES)
                    car_path = st.text_input("หรือใส่ path/URL ของรูป",
                                             placeholder="เช่น images/toyota_fortuner.jpg")
                    model_upload = st.file_uploader("โมเดล 3D .glb (ไม่บังคับ)", type=MODEL_TYPES)
                    model_path = st.text_input("หรือใส่ path/URL ของโมเดล",
                                               placeholder="เช่น models/toyota_fortuner.glb")
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
                            if model_upload is not None:
                                model_value = save_uploaded_model(car_name, model_upload)
                            elif model_path.strip():
                                model_value = model_path.strip()
                            elif resolve_local(default_model_path(car_name)):
                                model_value = default_model_path(car_name)  # มีไฟล์ชื่อตรงกันใน repo อยู่แล้ว
                            else:
                                model_value = ""
                            if add_car(car_name, brand_value, image_value, model_value):
                                done(f"เพิ่ม Car '{car_name.strip()}' ({brand_value}) แล้ว")
                            else:
                                done(f"มี '{car_name.strip()}' อยู่แล้ว อัปเดตยี่ห้อเป็น {brand_value}", "info")
            with c2:
                st.markdown("#### ✏️ แก้ไข Car")
                if cars:
                    target = st.selectbox("เลือกรถ", [c["name"] for c in cars], key="edit_car")
                    car = next(c for c in cars if c["name"] == target)
                    new_car_name = st.text_input("ชื่อรุ่นใหม่", value=target, key=f"edit_car_name_{target}")
                    new_brand = st.text_input("ยี่ห้อ", value=car.get("brand") or "", key=f"edit_car_brand_{target}")
                    if st.button("บันทึกรถ", type="primary", width="stretch", key="edit_car_btn"):
                        report([(f"{target} → {new_car_name.strip()} ({new_brand.strip()})",
                                 update_car(target, new_car_name, new_brand))])
                    st.caption("รูป/โมเดล แก้ได้ที่ส่วน 🖼️ ด้านล่าง")
                else:
                    st.info("ยังไม่มีรถ")
            with c3:
                st.markdown("#### 🗑️ ลบ Car")
                if cars:
                    target = st.selectbox("เลือกรถ", [c["name"] for c in cars], key="del_car")
                    info = next(c for c in cars if c["name"] == target)
                    st.caption(f"จะลบ LIKES {info['likes']} เส้น และ TEST_DROVE {info['test_drives']} เส้นที่ชี้มาที่ {target} ไปด้วย")
                    confirm = st.checkbox("ยืนยันการลบ", key="confirm_del_car")
                    if st.button("ลบ Car", disabled=not confirm, width="stretch"):
                        delete_car(target)
                        done(f"ลบ Car '{target}' แล้ว", "warning")
                else:
                    st.info("ยังไม่มีรถ")

            st.divider()
            st.markdown("#### 🖼️ เปลี่ยนรูป / โมเดล 3D")
            if cars:
                target = st.selectbox("เลือกรถ", [c["name"] for c in cars], key="img_car")
                car = next(c for c in cars if c["name"] == target)
                img_col, model_col = st.columns(2)

                with img_col:
                    st.markdown("**รูป**")
                    current = car.get("image")
                    show_car_image(current, caption=current or "ยังไม่มี path รูป")
                    new_upload = st.file_uploader("อัปโหลดรูปใหม่", type=IMAGE_TYPES, key=f"img_up_{target}")
                    new_path = st.text_input("หรือใส่ path/URL", value=current or "", key=f"img_path_{target}")
                    b1, b2 = st.columns(2)
                    if b1.button("บันทึกรูป", type="primary", width="stretch"):
                        value = save_uploaded_image(target, new_upload) if new_upload is not None else new_path.strip()
                        set_car_image(target, value)
                        done(f"อัปเดตรูปของ {target} เป็น {value or '(ไม่มีรูป)'}")
                    if b2.button("ลบรูปออกจากรถ", width="stretch"):
                        set_car_image(target, None)
                        done(f"ลบ path รูปของ {target} แล้ว (ไฟล์ใน {IMAGE_DIR}/ ยังอยู่)", "warning")

                with model_col:
                    st.markdown("**โมเดล 3D**")
                    current_model = car.get("model")
                    show_3d(current_model, None, height=260, alt=target)
                    st.caption(current_model or "ยังไม่มี path โมเดล")
                    new_model = st.file_uploader("อัปโหลดโมเดล .glb", type=MODEL_TYPES, key=f"model_up_{target}")
                    new_model_path = st.text_input("หรือใส่ path/URL", value=current_model or "",
                                                   key=f"model_path_{target}")
                    b1, b2 = st.columns(2)
                    if b1.button("บันทึกโมเดล", type="primary", width="stretch"):
                        value = (save_uploaded_model(target, new_model) if new_model is not None
                                 else new_model_path.strip())
                        set_car_model(target, value)
                        done(f"อัปเดตโมเดลของ {target} เป็น {value or '(ไม่มีโมเดล)'}")
                    if b2.button("ลบโมเดลออกจากรถ", width="stretch"):
                        set_car_model(target, None)
                        done(f"ลบ path โมเดลของ {target} แล้ว (ไฟล์ใน {MODEL_DIR}/ ยังอยู่)", "warning")

                st.caption(
                    f"ไฟล์ที่อัปโหลดจะถูกบันทึกเป็น {IMAGE_DIR}/<ชื่อรถ>.<นามสกุล> และ {MODEL_DIR}/<ชื่อรถ>.glb "
                    "ถ้ารันในเครื่องต้อง commit + push ไฟล์นั้นขึ้น GitHub ด้วย "
                    "บน Streamlit Cloud ไฟล์ที่อัปโหลดจะหายเมื่อแอปรีสตาร์ต ให้ใส่ไฟล์ใน repo แล้วกรอก path แทน"
                )

        # ---------------- LIKES ----------------
        with tab_like:
            users, cars = user_names(), car_names()
            likes = get_likes()
            edited = st.data_editor(
                df(likes, ["user", "car"]),
                key=editor_key("ed_likes"), hide_index=True, width="stretch", num_rows="fixed",
                disabled=["user"],
                column_config={
                    "user": st.column_config.TextColumn("User"),
                    "car": st.column_config.SelectboxColumn("รถที่ชอบ ✏️", options=cars, required=True),
                },
            )
            changes = [
                (x["user"], x["car"], clean(c)) for x, c in zip(likes, edited["car"]) if clean(c) != x["car"]
            ]
            save_button(len(changes), "save_likes", lambda: [
                (f"{u}: {o} → {n}", change_like(u, o, n)) for u, o, n in changes
            ])

            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown("#### ➕ เพิ่ม LIKES")
                if users and cars:
                    u = st.selectbox("User", users, key="like_user")
                    c = st.selectbox("Car", cars, key="like_car")
                    if st.button("เพิ่ม LIKES", type="primary", width="stretch"):
                        if add_like(u, c):
                            done(f"{u} -[:LIKES]-> {c}")
                        else:
                            st.warning(f"{u} ชอบ {c} อยู่แล้ว")
                else:
                    st.info("ต้องมีทั้ง User และ Car ก่อน")
            with c2:
                st.markdown("#### ✏️ เปลี่ยนรถที่ชอบ")
                if likes:
                    labels = {f"{x['user']} → {x['car']}": x for x in likes}
                    chosen = st.selectbox("เลือกเส้น", list(labels), key="edit_like")
                    x = labels[chosen]
                    new_c = st.selectbox("เปลี่ยนเป็นรถ", cars, index=cars.index(x["car"]) if x["car"] in cars else 0,
                                         key=f"edit_like_car_{chosen}")
                    if st.button("บันทึก LIKES", type="primary", width="stretch", key="edit_like_btn"):
                        report([(f"{x['user']}: {x['car']} → {new_c}", change_like(x["user"], x["car"], new_c))])
                else:
                    st.info("ยังไม่มี LIKES")
            with c3:
                st.markdown("#### 🗑️ ลบ LIKES")
                if likes:
                    labels = {f"{x['user']} → {x['car']}": x for x in likes}
                    chosen = st.selectbox("เลือกเส้นที่จะลบ", list(labels), key="del_like")
                    if st.button("ลบ LIKES", width="stretch"):
                        x = labels[chosen]
                        remove_like(x["user"], x["car"])
                        done(f"ลบ {x['user']} -[:LIKES]-> {x['car']} แล้ว", "warning")
                else:
                    st.info("ยังไม่มี LIKES")

        # ---------------- TEST_DROVE ----------------
        with tab_td:
            users, cars = user_names(), car_names()
            tds = get_test_drives()
            td_df = df(tds, ["user", "car", "test_date"])
            td_df["test_date"] = pd.to_datetime(td_df["test_date"], errors="coerce")  # ต้องเป็นชนิดวันที่ แม้ตารางว่าง
            edited = st.data_editor(
                td_df,
                key=editor_key("ed_td"), hide_index=True, width="stretch", num_rows="fixed",
                disabled=["user"],
                column_config={
                    "user": st.column_config.TextColumn("User"),
                    "car": st.column_config.SelectboxColumn("รถ ✏️", options=cars, required=True),
                    "test_date": st.column_config.DateColumn("วันที่ลองขับ ✏️", format="YYYY-MM-DD", required=True),
                },
            )
            changes = [
                (x["user"], x["car"], clean(c), to_date(d))
                for x, c, d in zip(tds, edited["car"], edited["test_date"])
                if clean(c) != x["car"] or to_date(d) != to_date(x["test_date"])
            ]
            save_button(len(changes), "save_td", lambda: [
                (f"{u}: {o} → {n} ({d})", update_test_drive(u, o, d.isoformat(), n)) for u, o, n, d in changes
            ])

            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown("#### ➕ เพิ่ม TEST_DROVE")
                if users and cars:
                    u = st.selectbox("User", users, key="td_user")
                    c = st.selectbox("Car", cars, key="td_car")
                    d = st.date_input("วันที่ทดลองขับ", value=date.today(), key="td_date")
                    if st.button("บันทึก TEST_DROVE", type="primary", width="stretch"):
                        created = add_test_drive(u, c, d.isoformat())
                        msg = "บันทึก" if created else "อัปเดตวันที่"
                        done(f"{msg} {u} -[:TEST_DROVE {{{d.isoformat()}}}]-> {c}")
                else:
                    st.info("ต้องมีทั้ง User และ Car ก่อน")
            with c2:
                st.markdown("#### ✏️ แก้ไข TEST_DROVE")
                if tds:
                    labels = {f"{x['user']} → {x['car']} ({x['test_date']})": x for x in tds}
                    chosen = st.selectbox("เลือกเส้น", list(labels), key="edit_td")
                    x = labels[chosen]
                    new_c = st.selectbox("รถ", cars, index=cars.index(x["car"]) if x["car"] in cars else 0,
                                         key=f"edit_td_car_{chosen}")
                    new_d = st.date_input("วันที่", value=to_date(x["test_date"]) or date.today(),
                                          key=f"edit_td_date_{chosen}")
                    if st.button("บันทึก TEST_DROVE", type="primary", width="stretch", key="edit_td_btn"):
                        report([(f"{x['user']}: {x['car']} → {new_c} ({new_d})",
                                 update_test_drive(x["user"], x["car"], new_d.isoformat(), new_c))])
                else:
                    st.info("ยังไม่มี TEST_DROVE")
            with c3:
                st.markdown("#### 🗑️ ลบ TEST_DROVE")
                if tds:
                    labels = {f"{x['user']} → {x['car']} ({x['test_date']})": x for x in tds}
                    chosen = st.selectbox("เลือกเส้นที่จะลบ", list(labels), key="del_td")
                    if st.button("ลบ TEST_DROVE", width="stretch"):
                        x = labels[chosen]
                        remove_test_drive(x["user"], x["car"])
                        done(f"ลบ {x['user']} -[:TEST_DROVE]-> {x['car']} แล้ว", "warning")
                else:
                    st.info("ยังไม่มี TEST_DROVE")

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
            - `(:Car {name, brand, image, model})`
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
