"""
พื้นหลัง 3D (Three.js) สำหรับ GraphCar

- ฉากอยู่ใน bg3d/showroom_scene.html  (โรงจอด/โชว์รูมแบบ procedural)
- ถ้ามีไฟล์ static/showroom.glb จะโหลดโมเดลนั้นแทน (ต้องเปิด enableStaticServing ใน .streamlit/config.toml)
- iframe ถูกตรึงเต็มจอไว้หลังเนื้อหาด้วย CSS (.st-key-gc_bg3d)
- หน้าเมนูปัจจุบันส่งให้ฉากผ่าน <div id="gc-page" data-page="..."> ฉากจะหมุนกล้องไปมุมของหน้านั้น
"""
from __future__ import annotations

from pathlib import Path

import streamlit as st

APP_DIR = Path(__file__).resolve().parent
SCENE_FILE = APP_DIR / "bg3d" / "showroom_scene.html"
SHOWROOM_GLB = APP_DIR / "static" / "showroom.glb"
THREE_CDN = "https://cdn.jsdelivr.net/npm/three@0.186.1"

BG_CSS = """
<style>
  /* ตรึงฉาก 3D เต็มจอไว้ด้านหลัง และไม่ให้รับคลิก */
  .st-key-gc_bg3d {
    position: fixed !important; inset: 0 !important; z-index: 0 !important;
    pointer-events: none !important; margin: 0 !important;
  }
  .st-key-gc_bg3d iframe {
    position: fixed !important; inset: 0 !important;
    width: 100vw !important; height: 100vh !important; border: 0 !important;
  }
  .st-key-gc_bg3d + div, .st-key-gc_bg3d ~ div { position: relative; z-index: 1; }
</style>
"""


@st.cache_data(show_spinner=False)
def _scene_html(mtime: float, showroom_url: str, three_base: str) -> str:
    return (
        SCENE_FILE.read_text(encoding="utf-8")
        .replace("__THREE__", three_base)
        .replace("__SHOWROOM_URL__", showroom_url)
    )


def render_background(page_index: int, enabled: bool = True, three_base: str = THREE_CDN) -> None:
    """เรียกครั้งเดียวต่อรอบ ก่อนเนื้อหาหลักของหน้า (ตำแหน่งต้องเหมือนเดิมทุกหน้า iframe จะได้ไม่โหลดใหม่)"""
    if enabled and SCENE_FILE.is_file():
        showroom_url = "app/static/showroom.glb" if SHOWROOM_GLB.is_file() else ""
        html = _scene_html(SCENE_FILE.stat().st_mtime, showroom_url, three_base)
        st.html(BG_CSS)
        with st.container(key="gc_bg3d"):
            st.iframe(html, height=10)
    # ตัวบอกหน้าปัจจุบัน ให้ฉาก 3D อ่านไปหมุนกล้อง
    st.html(f'<div id="gc-page" data-page="{int(page_index)}" style="display:none"></div>')
