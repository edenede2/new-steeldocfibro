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
import base64
import os
import uuid
import smtplib
from email.message import EmailMessage

# Load the PDF
pdf_path = 'doc.pdf'
font_path = "OpenSans-VariableFont_wdth,wght.ttf"  # Adjust this to the path of your font file

pdfmetrics.registerFont(TTFont('OpenSans', font_path))

def reversing_chars(s):
    # Split text by Hebrew characters and numbers separately
    parts = re.split(r'([0-9]+|[\u0590-\u05FF]+)', s)
    
    # Reverse Hebrew parts, keep numbers as they are
    reversed_parts = [
        part[::-1] if re.match(r'[\u0590-\u05FF]', part) else part
        for part in parts
    ]
    
    # Join all parts back into a single string
    return ''.join(reversed_parts)


def create_pdf(fields, table_data, signature_img=None):
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    
    # Register and set the font
    #pdfmetrics.registerFont(TTFont('OpenSans', font_path))
    can.setFont('OpenSans', 10)


    # Adjusted coordinates (from pdfplumber output, converting from points to position in the document)
    # Example coordinates, you might need to adjust based on exact needs
    x_name = 325  # Adjust this value as needed
    y_name = 568  # Adjust this value as needed

    # Fill text fields (adjust coordinates as needed)
    can.drawString(x_name, y_name, f"{reversing_chars(fields['full_name'])}")
    can.drawString(x_name-230, y_name, f"{fields['dob']}")
    can.drawString(x_name, y_name - 28, f"{fields['height']}")
    can.drawString(x_name-230, y_name - 28, f"{fields['weight']}")
    

    ros_counter = 0

    # Fill table (adjust coordinates as needed)
    for row in table_data:
        if ros_counter < 13:
            if ros_counter == 3:
                if row['answer'] == 'כן':
                    can.drawString(x_name + 10, y_name - 185, 'X')
                elif row['answer'] == 'לא':
                    can.drawString(x_name + 30, y_name - 185, 'X')
                elif row['answer'] == 'לא יודע/ת':
                    can.drawString(x_name - 10, y_name - 185, 'X')

                if row['details'] != '':
                    can.drawString(x_name - 250, y_name - 185, f"{reversing_chars(row['details'])}")

                y_name -= 25
            elif ros_counter == 6:
                if row['answer'] == 'כן':
                    can.drawString(x_name + 10, y_name - 185, 'X')
                elif row['answer'] == 'לא':
                    can.drawString(x_name + 30, y_name - 185, 'X')
                elif row['answer'] == 'לא יודע/ת':
                    can.drawString(x_name - 10, y_name - 185, 'X')

                if row['details'] != '':
                    can.drawString(x_name - 250, y_name - 185, f"{reversing_chars(row['details'])}")

                y_name -= 30
            elif ros_counter == 9:
                if row['answer'] == 'כן':
                    can.drawString(x_name + 10, y_name - 185, 'X')
                elif row['answer'] == 'לא':
                    can.drawString(x_name + 30, y_name - 185, 'X')
                elif row['answer'] == 'לא יודע/ת':
                    can.drawString(x_name - 10, y_name - 185, 'X')

                if row['details'] != '':
                    can.drawString(x_name - 250, y_name - 185, f"{reversing_chars(row['details'])}")

                y_name -= 42

            elif ros_counter == 10:
                if row['answer'] == 'כן':
                    can.drawString(x_name + 10, y_name - 185, 'X')
                elif row['answer'] == 'לא':
                    can.drawString(x_name + 30, y_name - 185, 'X')
                elif row['answer'] == 'לא יודע/ת':
                    can.drawString(x_name - 10, y_name - 185, 'X')

                if row['details'] != '':
                    can.drawString(x_name - 250, y_name - 185, f"{reversing_chars(row['details'])}")

                y_name -= 42
            else:
                if row['answer'] == 'כן':
                    can.drawString(x_name + 10, y_name - 185, 'X')
                elif row['answer'] == 'לא':
                    can.drawString(x_name + 30, y_name - 185, 'X')
                elif row['answer'] == 'לא יודע/ת':
                    can.drawString(x_name - 10, y_name - 185, 'X')

                if row['details'] != '':
                    can.drawString(x_name - 250, y_name - 185, f"{reversing_chars(row['details'])}")
                    
                y_name -= 20
            ros_counter += 1

    can.showPage()
    
    #pdfmetrics.registerFont(TTFont('OpenSans', font_path))
    can.setFont('OpenSans', 10)
    
    x_name = 325
    y_name = 900

    table_data = table_data[13:]

    for row in table_data:
        if ros_counter >= 13:
            if row['answer'] == 'כן':
                can.drawString(x_name + 10, y_name - 185, 'X')
            elif row['answer'] == 'לא':
                can.drawString(x_name + 30, y_name - 185, 'X')
            elif row['answer'] == 'לא יודע/ת':
                can.drawString(x_name - 10, y_name - 185, 'X')

            if row['details'] != '':
                can.drawString(x_name - 250, y_name - 185, f"{reversing_chars(row['details'])}")

            if ros_counter == 13:
                y_name -= 25
            elif ros_counter == 16:
                y_name -= 29
            elif ros_counter == 17:
                y_name -= 29
            elif ros_counter == 18:
                y_name -= 29
            elif ros_counter == 19:
                y_name -= 29
            elif ros_counter == 20:
                y_name -= 29
            elif ros_counter == 21:
                y_name -= 29
            elif ros_counter == 22:
                y_name -= 29
            elif ros_counter == 23:
                y_name -= 29
            elif ros_counter == 24:
                y_name -= 29
            elif ros_counter == 25:
                y_name -= 37
            elif ros_counter == 26:
                y_name -= 27
            elif ros_counter == 27:
                y_name -= 29
            elif ros_counter == 28:
                y_name -= 48
            elif ros_counter == 29:
                y_name -= 29
            else:
                y_name -= 20
            ros_counter += 1

    
    now_date = datetime.datetime.now().strftime("%d/%m/%Y")

    if signature_img:
        try:
            can.drawImage(signature_img, 350, 135, width=70, height=40, mask=[0,255,255,255,255,255])
            can.drawString(180, 150, now_date)
        except Exception as e:
            st.write(f"Error drawing image: {e}")


    can.save()
    
    # Move to the beginning of the StringIO buffer
    packet.seek(0)
    
    # Read the existing PDF
    existing_pdf = PdfReader(pdf_path)
    output = PdfWriter()
    
    # Add the "watermark" (which is the new pdf) on the existing page
    new_pdf = PdfReader(packet)
    page = existing_pdf.pages[0]
    page.merge_page(new_pdf.pages[0])
    output.add_page(page)

    if len(existing_pdf.pages) > 1:
        second_page = existing_pdf.pages[1]
        second_page.merge_page(new_pdf.pages[1])
        output.add_page(second_page)
    else:
        output.add_page(new_pdf.pages[1])


    
    # Finally, write "output" to a real file
    output_stream = BytesIO()
    output.write(output_stream)
    output_stream.seek(0)
    
    return output_stream


def signature(canvas_result):
    if canvas_result.image_data is not None:
        img_data = canvas_result.image_data
        im = Image.fromarray(img_data.astype("uint8"), mode="RGBA")
        # Convert to RGB to avoid issues with transparency
        im = im.convert("RGB")
        
        # Ensure the tmp directory exists
        tmp_dir = "tmp"
        if not os.path.exists(tmp_dir):
            os.makedirs(tmp_dir)
        
        file_path = f"{tmp_dir}/signature_{uuid.uuid4().hex}.png"
        im.save(file_path, "PNG")
        return file_path


def send_email(pdf_data, full_name, id, address, dob):
    sender_email = 'edenstream988@gmail.com'  # Replace with your sender email
    sender_password = 'aiyh ffqj hgps rwan'  # Replace with your email password or app-specific password

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

    file_name = f'טופס מתכות של {full_name}'
    file_name = file_name + '.pdf'

    msg.add_attachment(pdf_data, maintype='application', subtype='pdf', filename=file_name)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(sender_email, sender_password)
        server.send_message(msg)


st.title("טופס בטיחות - MRI")

st.subheader("סודי רפואי")

st.write("""
המידע הכלול במסמך זה מוגן על פי חוק זכויות החולה, התשנ’’ו –1966 וחוק הגנת הפרטיות, תשמ’’א –1981. אין  
למסור את המידע ו/או תוכן המידע ו/או פרט שהו מהמידע לכל אדם ואו גוף אלא בהתאם להוראות החוק. מסירת המידע  
בניגוד לקבוע בחוקים אלה, מהווה עבורה.  
         """)

# Min value for the date input field in datetime date format
min_date = datetime.date(1930, 1, 1)

# Text fields
fields = {
    'full_name': st.text_input("שם מלא:"),
    'dob': st.date_input("תאריך לידה:", value=None, min_value=min_date),
    'height': st.text_input("גובה (מטר):"),
    'weight': st.text_input("משקל (קג):"),
    'Id_num': st.text_input("מספר תעודת זהות:"),
    'address': st.text_input("כתובת מגורים מלאה:"),
}

st.divider()

# Label of instructions before the table
st.write("בבקשה לקרוא את הטופס בעיון ולענות על כל הסעיפים")
st.write("""
.(פי שניים ממגנט טיפוסי במגרש גרוטאות) T3 פועל שדה מגנטי חזק MRI באזור מכשיר 

השדה המגנטי אינו משפיע על רקמות ביולוגיות, אבל מאוד משפיע על מתכות.

מטרת השאלות היא לוודא 
שאין בתוך גופך או על גופך כל מתכת – בכדי שהימצאותך בשדה המגנטי לא תסכן את בריאותך.
"""
)

st.divider()

questions_list= [
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
    'קעקועים (ציין גודל, מיקום וצבע, אפשר גם לשלוח תצלום לצוות המחקר)',
    'פירסינג, עגילים שאי אפשר להסיר',
    'permanent makeup איפור קבוע',
    'האם עברת ארטרוסקופיה ובאיזו ברך',
    'האם עברת/ה ניתוחים קודמים',
    'האם היית/ה מעורב בתאונת דרכים?',
    'האם עבדת עם מתכת ללא הגנה על העיניים',
    'האם מתכת אי פעם נכנסה לך לעין',
    'האם יש לך בגדים מבדים אנטי בקטריאליים',
    " (MRI) האם עברת/ה סריקת אמ.אר.איי. בעבר (ציין תאריך, מטרה, מכון)",
    'האם יש עליך או בתוכך אביזר ממתכת',
    'האם את/ה סובל מקלסטרופוביה',
    'האם יש לך משקפיים',
    'האם יש בגופך התקן תוך רחמי',
    'האם את בהריון'
]


if 'signed' not in st.session_state:
    st.session_state.signed = False

if 'signature_img' not in st.session_state:
    st.session_state.signature_img = None

if 'table_data' not in st.session_state:
    st.session_state.table_data = []


with st.form(key='table_form', clear_on_submit=False):
    table_data = []
    st.write("""ציין האם יש בתוך/על גופך את הפרטים הבאים:""", key='table_label')
    for i in range(len(questions_list)):
        row = {
            'question_obj': st.write(questions_list[i]),
            'question': st.write(f"סמנו את המתאים", key=f"question_labels_{i}"), 
            'answer': st.radio("", options=['כן', 'לא', 'לא יודע/ת'], key=f"answer_{i}"),
            'details': st.text_input("אם כן / לא יודע/ת הוסיפו פרטים + תאריך של האירוע",max_chars= 48,key=f"details_lab_{i}"),
        }
        st.divider()

        table_data.append(row)
    
    submit_button = st.form_submit_button("שמור")
    # Create PDF
    if submit_button:
        
        if 'signed' in st.session_state:
            st.session_state.signed = False
        
        if 'signature_img' in st.session_state:
            st.session_state.signature_img = None

        if 'table_data' in st.session_state:
            st.session_state.table_data = []
            
        signature_img = signature(st_canvas(update_streamlit=True, stroke_color= "black", background_color='white', key="canvas"))
        
        # Save the signature image
        check = st.checkbox("אני מאשר/ת שהמידע נכון ומדוייק")
        st.write("לאחר אישור לחץ שוב על הכפתור שמור")

        if check:
            st.session_state.signed = True
            st.session_state.signature_img = signature_img
            st.session_state.table_data = table_data
    else:
        check = False
        
if st.session_state.signed:
    pdf_stream = create_pdf(fields,(st.session_state.table_data), signature_img=(st.session_state.signature_img))
    binarystream = pdf_stream.getvalue()
    pdf_viewer(input=binarystream, height=800)

    accept = st.checkbox("אני החתום מטה מצהיר שהמידע בטופס נכון ומדוייק.")

    if accept:
        if st.button("שלח טופס"):
            send_email(binarystream, fields['full_name'], fields["Id_num"], fields["address"], fields["dob"])
            st.success("הטופס נשלח בהצלחה")
    else:
        st.write("אנא אשר את ההצהרה")


else:
    st.write("אנא אשר את ההצהרה")
        









        
