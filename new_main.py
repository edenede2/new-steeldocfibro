import streamlit as st
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.pagesizes import letter
from io import BytesIO
import datetime
from pathlib import Path
from streamlit_drawable_canvas import st_canvas
from streamlit_pdf_viewer import pdf_viewer
import re
from PIL import Image
import os
import uuid
import smtplib
from email.message import EmailMessage

# --------------------------
# Paths (updated)
# --------------------------
OLD_PDF_PATH = '/mnt/data/doc.pdf'
NEW_PDF_PATH = 'טופס מתכות מחקר 250825.pdf'
FONT_PATH = "OpenSans-VariableFont_wdth,wght.ttf"  # עדכן אם צריך

# רישום פונט (פעם אחת)
try:
    pdfmetrics.registerFont(TTFont('OpenSans', FONT_PATH))
    DEFAULT_FONT = 'OpenSans'
except Exception:
    DEFAULT_FONT = 'Helvetica'  # fallback

# --------------------------
# RTL helper
# --------------------------
def reversing_chars(s: str) -> str:
    parts = re.split(r'([0-9]+|[\u0590-\u05FF]+)', str(s))
    reversed_parts = [part[::-1] if re.match(r'^[\u0590-\u05FF]+$', part or '') else part for part in parts]
    return ''.join(reversed_parts)

# --------------------------
# Template descriptors
# --------------------------
# כל תבנית מגדירה:
# - pdf_path
# - fields: מילוי פרטים בראש הדף (page, x, y)
# - layout: עבור כל עמוד, מיקומי X לתיבות כן/לא/לא יודע, ומיקומי Y לשורות
# - rows_page1 / rows_page2: אינדקסים של השאלות שמופיעות בכל עמוד
# - signature: מיקום חתימה/תאריך בעמוד 2
# ניתן לכייל פיקסלים בודדים בקלות.
TEMPLATES = {
    "old (doc.pdf)": {
        "pdf_path": OLD_PDF_PATH,
        "fields": {
            "full_name": (0, 325, 568),
            "dob":       (0,  95, 568),
            "weight":    (0, 325, 540),
            "height":    (0,  95, 540),
            # בישן אין שורה ברורה לת"ז, נשאיר ריק
            "id":        (0, 9999, 9999),
            "address":   (0, 9999, 9999),  # אין שורה ייעודית בטמפ' הישן
        },
        "layout": {
            # עמוד 1
            0: {
                "x_yes": 235, "x_no": 255, "x_nd": 315,
                "x_details":  75,
                "y_start": 383,
                "y_list": [0, 20, 20, 25, 20, 20, 30, 20, 20, 42, 42, 20, 20],  # 13 שורות ראשונות (כולל חריגים)
            },
            # עמוד 2
            1: {
                "x_yes": 335, "x_no": 355, "x_nd": 315,
                "x_details":  75,
                "y_start": 900 - 185,  # שמרנו על לוגיקה דומה לקוד הישן
                "y_list": [25, 29, 29, 29, 29, 29, 29, 29, 29, 29, 37, 27, 29, 48, 29],
            }
        },
        "rows_page1": list(range(0, 13)),     # 0..12
        "rows_page2": list(range(13, 28)),    # 13..27 (התאם אם צריך)
        "signature": {
            "sig_xy": (350, 135),
            "date_xy": (180, 150),
        },
        "has_id_topline": False,
    },

    "new (250825)": {
        "pdf_path": NEW_PDF_PATH,
        # נקודות פתיחה מכוילות ל־PDF החדש; אם צריך להזיז 2–5 פיקסלים, ערוך כאן:
        "fields": {
            "full_name": (0, 430, 705),   # שם מלא
            "id":        (0, 430, 680),   # ת"ז
            "weight":    (0, 430, 655),   # משקל
            "height":    (0, 150, 655),   # גובה
            "dob":       (0, 150, 680),   # תאריך לידה
            "address":   (0, 9999, 9999), # אין שורה ייעודית בטמפ' החדש
        },
        "layout": {
            # עמוד 1: 12 שורות ראשונות, מרווח קבוע + חריגים קלים
            0: {
                "x_yes": 445, "x_no": 470, "x_nd": 420,
                "x_details": 105,
                "y_start": 520,  # שורה ראשונה ("קוצב לב")
                "y_list": [0, 22, 22, 28, 22, 22, 28, 22, 22, 30, 28, 24],  # 12 פריטים
            },
            # עמוד 2: יתר הפריטים (כולל "אלקטרודות" בתחילת העמוד)
            1: {
                "x_yes": 445, "x_no": 470, "x_nd": 420,
                "x_details": 105,
                "y_start": 720,  # "אלקטרודות" בראש עמ' 2
                "y_list": [26, 28, 34, 26, 26, 26, 26, 26, 28, 26, 28, 28, 28, 28, 28, 34, 28],  # התואם לסדר למטה
            }
        },
        "rows_page1": list(range(0, 12)),     # 0..11
        "rows_page2": list(range(12, 29)),    # 12..28
        "signature": {
            # אזור החתימה בתחתית עמ' 2
            "sig_xy": (390, 115),
            "date_xy": (235, 115),
        },
        "has_id_topline": True,
    }
}

# --------------------------
# Questions (aligned to NEW form)
# --------------------------
# סדר השאלות כפי שמופיע בטופס החדש (עמ'1 ואז עמ'2). זה הסדר שיירשם/יצטייר.
QUESTIONS_NEW = [
    # Page 1 (12)
    'קוצב לב',
    'מסתם לב מלאכותי',
    'שנט במערכת העצבים/אחר',
    'סיכות מתכתיות לאחר ניתוח מפרצת ראש',
    'שתל כוכליארי באוזן',
    'מכשיר שמיעה',
    '(neurostimulator) מגרי עצבים',
    'כתר/גשר/שתל מתכת בשיניים',
    'רסיס מתכת (לאחר פציעה)',
    'סיכות/מהדקים/פילטרים/סלילים לאחר ניתוח וטיפולים בכלי דם',
    'מוט/פלטת ברגים/מסמרים לאחר ניתוחים אורתופדיים',
    'מפרק מלאכותי',

    # Page 2 (rest; includes moved "אלקטרודות" first)
    'אלקטרודות',
    'שתל של רשת מתכתית בדופן הבטן',
    'האם עברת/ה ניתוחים קודמים',
    'שתלים מכל סוג שהוא',
    'קעקועים (ציין גודל, מיקום וצבע/צרף צילום)',
    'פירסינג, עגילים שאי אפשר להסיר',
    'permanent makeup איפור קבוע',
    'האם היית/ה מעורב/ת בתאונת דרכים?',
    'האם עבדת עם מתכת ללא הגנה על העיניים',
    'האם מתכת אי פעם נכנסה לך לעין',
    'האם יש לך בגדים מבדים אנטי-בקטריאליים',
    'האם עברת/ה סריקת MRI בעבר (ציין תאריך, מטרה, מכון)',
    'האם יש עליך/בתוכך אביזר/אובייקט/קוסמטי/רפואי',
    'האם את/ה סובל/ת מקלסטרופוביה',
    'האם יש לך משקפיים',
    'האם יש בגופך התקן תוך-רחמי',
    'האם את בהריון',
]

# לגרסה הישנה—נשמור את הרשימה הקודמת לצורך תאימות לאחור:
QUESTIONS_OLD = [
    'קוצב לב',
    'מסתם לב מלאכותי',
    'שנט במערכת העצבים/אחר',
    'סיכות מתכתיות לאחר ניתוח מפרצת ראש',
    'שתל כוכליארי באוזן',
    'מכשירי שמיעה',
    '(neurostimulator) מגרי עצבים',
    'כתר מתכת/גשר/קיבוע',
    'רסיס מתכת (לאחר פציעה)',
    'סיכות, מהדקים מתכתיים, פילטרים, סלילים לאחר ניתוח וטיפולים בכלי דם ',
    'מוט מתכת, פלטת ברגים, מסמרים לאחר ניתוחים אורתופדים',
    'מפרק מלאכותי',
    'אלקטרודות',
    'שתל של רשת מתכתית',
    'מותחן הזרקה לשד',
    'שתלים מכל סוג שהוא',
    'קעקועים (ציין גודל, מיקום וצבע)',
    'פירסינג, עגילים שאי אפשר להסיר',
    'permanent makeup איפור קבוע',
    'האם עברת ארטרוסקופיה ובאיזו ברך',
    'האם עברת/ה ניתוחים קודמים',
    'האם היית/ה מעורב בתאונת דרכים?',
    'האם עבדת עם מתכת ללא הגנה על העיניים',
    'האם מתכת אי פעם נכנסה לך לעין',
    'האם יש לך בגדים מבדים אנטי בקטריאליים',
    "האם עברת/ה סריקת אמ.אר.איי. בעבר (ציין תאריך, מטרה, מכון)",
    'האם יש עליך או בתוכך אביזר ממתכת',
    'האם את/ה סובל מקלסטרופוביה',
    'האם יש לך משקפיים',
    'האם יש בגופך התקן תוך רחמי',
    'האם את בהריון'
]

# --------------------------
# PDF draw helpers
# --------------------------
def _get_page_size(pdf_path: str, page_index: int = 0):
    reader = PdfReader(pdf_path)
    page = reader.pages[page_index]
    w = float(page.mediabox.width)
    h = float(page.mediabox.height)
    return w, h

def _new_canvas_like(pdf_path: str):
    w, h = _get_page_size(pdf_path, 0)
    pkt = BytesIO()
    can = canvas.Canvas(pkt, pagesize=(w, h))
    can.setFont(DEFAULT_FONT, 10)
    return can, pkt, (w, h)

def _draw_mark(can, x, y, text=None, size=5):
    can.rect(x-1, y-1, 2, 2, stroke=1, fill=0)
    if text:
        can.drawString(x + 3, y + 3, str(text))

def _draw_answer(can, x_yes, x_no, x_nd, y, answer):
    if answer == 'כן':
        can.drawString(x_yes, y, 'X')
    elif answer == 'לא':
        can.drawString(x_no, y, 'X')
    else:  # 'לא יודע/ת'
        can.drawString(x_nd, y, 'X')

def _merge_overlay_on_pdf(overlay_packet: BytesIO, template_pdf_path: str):
    overlay_packet.seek(0)
    overlay_pdf = PdfReader(overlay_packet)
    base_pdf = PdfReader(template_pdf_path)
    writer = PdfWriter()

    # עבור שני עמודים (או יותר)
    num_pages = max(len(base_pdf.pages), len(overlay_pdf.pages))
    for i in range(num_pages):
        base_page = base_pdf.pages[i] if i < len(base_pdf.pages) else base_pdf.pages[-1]
        ovl_page = overlay_pdf.pages[i] if i < len(overlay_pdf.pages) else overlay_pdf.pages[-1]
        base_page.merge_page(ovl_page)
        writer.add_page(base_page)

    out = BytesIO()
    writer.write(out)
    out.seek(0)
    return out

# --------------------------
# PDF creation (template-aware)
# --------------------------
def create_pdf(fields, table_data, template_key: str, signature_img=None, debug=False):
    tpl = TEMPLATES[template_key]
    pdf_path = tpl["pdf_path"]

    # עמוד 1
    can, packet, (w, h) = _new_canvas_like(pdf_path)

    # 1) שדות עליונים
    fcoords = tpl["fields"]
    def draw_field(key, val):
        page, x, y = fcoords[key]
        if x == 9999:  # לא קיים בשבלונה
            return
        if page != 0:
            return
        text = reversing_chars(val) if key in ("full_name", "address") else str(val)
        can.setFont(DEFAULT_FONT, 10)
        can.drawString(x, y, text)

    draw_field("full_name", fields.get("full_name", ""))
    draw_field("dob", fields.get("dob", ""))
    draw_field("height", fields.get("height", ""))
    draw_field("weight", fields.get("weight", ""))
    if tpl["has_id_topline"]:
        draw_field("id", fields.get("Id_num", ""))

    # 2) טבלת שאלות – עמוד 1
    p1 = tpl["layout"][0]
    y = p1["y_start"]
    can.setFont(DEFAULT_FONT, 10)

    # נבנה את הרשימה לפי התבנית הנבחרת
    q_list = QUESTIONS_NEW if "new" in template_key else QUESTIONS_OLD

    for idx in tpl["rows_page1"]:
        row = table_data[idx]
        _draw_answer(can, p1["x_yes"], p1["x_no"], p1["x_nd"], y, row['answer'])
        if row['details'].strip():
            can.drawString(p1["x_details"], y, reversing_chars(row['details'].strip()))
        if debug:
            _draw_mark(can, p1["x_yes"], y, text=idx)
        # עדכון y לפי רשימת דלתאות שנקבעה
        step = p1["y_list"][idx - tpl["rows_page1"][0]] if (idx - tpl["rows_page1"][0]) < len(p1["y_list"]) else 22
        y -= step

    can.showPage()

    # 3) עמוד 2 – המשך השאלות + חתימה/תאריך
    can.setFont(DEFAULT_FONT, 10)
    p2 = tpl["layout"][1]
    y2 = p2["y_start"]

    for j, idx in enumerate(tpl["rows_page2"]):
        row = table_data[idx]
        _draw_answer(can, p2["x_yes"], p2["x_no"], p2["x_nd"], y2, row['answer'])
        if row['details'].strip():
            can.drawString(p2["x_details"], y2, reversing_chars(row['details'].strip()))
        if debug:
            _draw_mark(can, p2["x_yes"], y2, text=idx)
        step = p2["y_list"][j] if j < len(p2["y_list"]) else 26
        y2 -= step

    # 4) חתימה + תאריך נבדק/ת
    now_date = datetime.datetime.now().strftime("%d/%m/%Y")
    if signature_img:
        try:
            sx, sy = tpl["signature"]["sig_xy"]
            dx, dy = tpl["signature"]["date_xy"]
            can.drawImage(signature_img, sx, sy, width=70, height=40, mask=[0,255,255,255,255,255])
            can.drawString(dx, dy, now_date)
        except Exception as e:
            st.write(f"Error drawing image: {e}")

    can.save()
    merged = _merge_overlay_on_pdf(packet, pdf_path)
    return merged

# --------------------------
# Signature helper (unchanged)
# --------------------------
def signature(canvas_result):
    if canvas_result.image_data is not None:
        img_data = canvas_result.image_data
        im = Image.fromarray(img_data.astype("uint8"), mode="RGBA")
        im = im.convert("RGB")
        tmp_dir = "tmp"
        os.makedirs(tmp_dir, exist_ok=True)
        file_path = f"{tmp_dir}/signature_{uuid.uuid4().hex}.png"
        im.save(file_path, "PNG")
        return file_path

# --------------------------
# Email sender (same logic)
# --------------------------
def send_email(pdf_data, full_name, id, address, dob):
    sender_email = st.secrets.get("SENDER_EMAIL_ADDRESS", "")
    sender_password = st.secrets.get("SENDER_EMAIL_PASSWORD", "")

    msg_cont =f"""
טופס מתכות למחקר פיברומיאלגיה
    
טופס מתכות של {full_name}

תאריך לידה {dob}

תעודת זהות {id}

כתובת מגורים {address}
    """
    msg = EmailMessage()
    msg['Subject'] = f'טופס מתכות של {full_name}'
    msg['From'] = sender_email
    msg['To'] = 'admon_fibro@labs.hevra.haifa.ac.il'
    msg.set_content(msg_cont)

    file_name = f'טופס מתכות של {full_name}.pdf'
    msg.add_attachment(pdf_data, maintype='application', subtype='pdf', filename=file_name)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(sender_email, sender_password)
        server.send_message(msg)

# --------------------------
# UI
# --------------------------
st.title("טופס בטיחות - MRI")
st.subheader("סודי רפואי")

st.write("""
המידע הכלול במסמך זה מוגן על פי חוק זכויות החולה, התשנ’’ו –1966 וחוק הגנת הפרטיות, תשמ’’א –1981. אין  
למסור את המידע ו/או תוכן המידע ו/או פרט שהו מהמידע לכל אדם ואו גוף אלא בהתאם להוראות החוק. מסירת המידע  
בניגוד לקבוע בחוקים אלה, מהווה עבירה.  
""")

# Template selector
template_key = st.selectbox(
    "בחר/י תבנית טופס",
    options=list(TEMPLATES.keys()),
    index=1  # ברירת מחדל – החדש
)

is_new = "new" in template_key

min_date = datetime.date(1930, 1, 1)

fields = {
    'full_name': st.text_input("שם מלא:"),
    'dob': st.date_input("תאריך לידה:", value=None, min_value=min_date),
    'height': st.text_input("גובה (מטר):"),
    'weight': st.text_input("משקל (ק״ג):"),
    'Id_num': st.text_input("מספר תעודת זהות:" if is_new else "מספר תעודת זהות (אם מופיע בטופס):"),
    'address': st.text_input("כתובת מגורים מלאה (לצירוף במייל בלבד):"),
}

st.divider()
st.write("בבקשה לקרוא את הטופס בעיון ולענות על כל הסעיפים")

questions_list = QUESTIONS_NEW if is_new else QUESTIONS_OLD

if 'signed' not in st.session_state:
    st.session_state.signed = False
if 'signature_img' not in st.session_state:
    st.session_state.signature_img = None
if 'table_data' not in st.session_state:
    st.session_state.table_data = []

with st.form(key='table_form', clear_on_submit=False):
    table_data = []
    st.write("ציין/ני האם יש בתוך/על גופך את הפריטים הבאים:")
    for i, q in enumerate(questions_list):
        st.write(q)
        row = {
            'answer': st.radio("סמן/ני את המתאים:", options=['כן', 'לא', 'לא יודע/ת'], key=f"answer_{i}", horizontal=True),
            'details': st.text_input("אם כן / לא יודע/ת – הוסיפו פרטים + תאריך של האירוע (עד 60 תווים)", max_chars=60, key=f"details_lab_{i}"),
        }
        st.divider()
        table_data.append(row)

    submit_button = st.form_submit_button("שמור")
    if submit_button:
        st.session_state.signed = False
        st.session_state.signature_img = None
        st.session_state.table_data = []

        # אזור חתימה
        st.write("חתימה (שרטט/י חתימה בתוך המסגרת):")
        canvas_result = st_canvas(
            stroke_width=2,
            stroke_color="black",
            background_color="white",
            height=120,
            width=350,
            drawing_mode="freedraw",
            key="canvas_signature",
            update_streamlit=True
        )
        signature_img = signature(canvas_result)

        check = st.checkbox("אני מאשר/ת שהמידע נכון ומדויק")
        st.write("לאחר האישור—לחץ/י שוב על 'שמור'")
        if check:
            st.session_state.signed = True
            st.session_state.signature_img = signature_img
            st.session_state.table_data = table_data

debug = st.checkbox("מצב כיול (DEBUG): הצגת סמנים ליד כל שורה", value=False)

if st.session_state.signed:
    pdf_stream = create_pdf(fields, st.session_state.table_data, template_key=template_key,
                            signature_img=st.session_state.signature_img, debug=debug)
    binarystream = pdf_stream.getvalue()
    pdf_viewer(input=binarystream, height=800)

    accept = st.checkbox("אני החתום/ה מטה מצהיר/ה שהמידע בטופס נכון ומדויק.")
    if accept:
        if st.button("שלח טופס"):
            send_email(binarystream, fields['full_name'], fields["Id_num"], fields["address"], fields["dob"])
            st.success("הטופס נשלח בהצלחה")
else:
    st.write("אנא מלא/י את הטופס ואשר/י את ההצהרה.")
