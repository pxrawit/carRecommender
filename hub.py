"""
Homework Hub: หน้าแรกของเว็บ รวมการบ้านทั้ง 4 งาน

ไฟล์การบ้านอยู่ในโฟลเดอร์ homework/ ของ repo นี้
ถ้าเปลี่ยนชื่อไฟล์ หรืออยากแก้ชื่อ/คำอธิบายงาน ให้แก้ที่ HOMEWORK ด้านล่างที่เดียว
"""
from __future__ import annotations

from pathlib import Path

import streamlit as st

APP_DIR = Path(__file__).resolve().parent
HW_DIR = APP_DIR / "homework"

GITHUB_REPO = "https://github.com/pxrawit/carRecommender"
GITHUB_BRANCH = "main"
APP_URL = "https://carrecommender-dv7rqrvlfumdkqnrrkmecn.streamlit.app/"

MIME = {
    ".pdf": "application/pdf",
    ".ipynb": "application/x-ipynb+json",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}
KIND = {".pdf": "PDF", ".ipynb": "Jupyter Notebook", ".pptx": "PowerPoint"}

HOMEWORK = [
    {
        "title": "Club Recommendation Graph ด้วย Neo4j",
        "desc": "รายงานแนะนำชมรมจากเครือข่ายเพื่อนและความสนใจของนักเรียน "
                "(Student, Club, Interest · FRIEND_OF, MEMBER_OF)",
        "file": "hw1_Neo4jGraphDB.pdf",
        "colab": None,
    },
    {
        "title": "Car Recommender System ด้วย Graph (Colab)",
        "desc": "จำลองผู้ใช้ 10 คน รถ 10 รุ่น สร้างกราฟความชอบด้วย NetworkX แล้วแนะนำรถจากคนที่ชอบคล้ายกัน",
        "file": "hw2_Car_Recommender_System.ipynb",
        "colab": "https://colab.research.google.com/drive/13stLswwxWIXYDtpie11vY-qSljzDWfnu?usp=sharing",
    },
    {
        "title": "Car Recommender ด้วย Neo4j Aura (Colab)",
        "desc": "ย้ายกราฟไป Neo4j Aura: สร้าง User · Car · LIKES · TEST_DROVE ด้วย Python driver "
                "และเขียน Cypher แนะนำรถให้ Alice",
        "file": "hw3_CarRecommender_Neo4j.ipynb",
        "colab": "https://colab.research.google.com/drive/1BcClBwQDS0jVlHTcX0fpEBPwHrB4fw8I?usp=sharing",
    },
    {
        "title": "Car Recommended — เว็บแอป + Presentation",
        "desc": "ระบบแนะนำรถยนต์บนเว็บ (Streamlit + Neo4j Aura) พร้อมรูปรถ โมเดล 3D "
                "เพิ่ม/แก้ไข/ลบข้อมูล และสไลด์นำเสนอ",
        "file": "hw4_Car_Recommended_Presentation.pptx",
        "colab": None,
        "app": True,
    },
]

HUB_CSS = """
<style>
  [class*="st-key-hw_card_"] {
    border: 1px solid #e5e7eb !important; border-radius: 4px !important;
    padding: 1.4rem 1.5rem 1.3rem !important; background: #fff; height: 100%;
  }
  [class*="st-key-hw_card_"]:hover { border-color: #111 !important; }
  .hw-num { font-size: .74rem; letter-spacing: .2em; color: #8a8f98; text-transform: uppercase; }
  .hw-big { font-size: 2.6rem; font-weight: 600; line-height: 1; color: #111; margin: .35rem 0 .7rem; letter-spacing: -.02em; }
  .hw-title { font-size: 1.2rem; font-weight: 600; color: #111; margin-bottom: .35rem; }
  .hw-desc { color: #4b5563; font-size: .93rem; min-height: 3em; }
  .hw-meta { margin-top: .75rem; color: #8a8f98; font-size: .8rem; }
  .hw-meta b { color: #4b5563; font-weight: 500; }
</style>
"""


def _size(n: int) -> str:
    return f"{n / 1024 / 1024:.1f} MB" if n >= 1024 * 1024 else f"{n / 1024:.0f} KB"


@st.cache_data(show_spinner=False)
def _read(path: str, mtime: float) -> bytes:
    return Path(path).read_bytes()


def _github_url(name: str) -> str:
    return f"{GITHUB_REPO}/blob/{GITHUB_BRANCH}/homework/{name}"


def _card(i: int, hw: dict, open_app) -> None:
    file = HW_DIR / hw["file"]
    ext = file.suffix.lower()
    with st.container(key=f"hw_card_{i}"):
        st.html(
            f'<div class="hw-num">Homework</div><div class="hw-big">{i:02d}</div>'
            f'<div class="hw-title">{hw["title"]}</div><div class="hw-desc">{hw["desc"]}</div>'
        )
        if file.is_file():
            st.html(f'<div class="hw-meta"><b>{KIND.get(ext, ext)}</b> · {hw["file"]} · {_size(file.stat().st_size)}</div>')
        else:
            st.html(f'<div class="hw-meta">ยังไม่มีไฟล์ homework/{hw["file"]} ใน repo</div>')

        with st.container(horizontal=True, gap="small"):
            if file.is_file():
                st.download_button(
                    f"ดาวน์โหลด {KIND.get(ext, '')}".strip(),
                    data=_read(str(file), file.stat().st_mtime),
                    file_name=hw["file"], mime=MIME.get(ext, "application/octet-stream"),
                    type="primary", key=f"hw_dl_{i}",
                )
            if hw.get("app"):
                st.button("เปิดเว็บแอป", key=f"hw_open_{i}", on_click=open_app,
                          type="secondary" if file.is_file() else "primary")
            if hw.get("colab"):
                st.link_button("เปิดใน Colab", hw["colab"])
            st.link_button("GitHub", GITHUB_REPO if hw.get("app") or not file.is_file() else _github_url(hw["file"]))


def render_hub(open_app) -> None:
    """open_app = callback ที่สลับไปหน้าแรกของระบบ Car Recommended"""
    st.html(HUB_CSS)
    for start in (0, 2):
        cols = st.columns(2, gap="medium")
        for col, (i, hw) in zip(cols, list(enumerate(HOMEWORK, start=1))[start:start + 2]):
            with col:
                _card(i, hw, open_app)
    st.caption(f"Source code ทั้งหมด: {GITHUB_REPO}")
