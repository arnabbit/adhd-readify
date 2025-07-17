from fastapi import FastAPI, UploadFile
from fastapi.responses import FileResponse
import tempfile
import fitz  # PyMuPDF

def adhd_bold_clean_pdf(input_path, output_path):
    src_doc = fitz.open(input_path)
    new_doc = fitz.open()  # brand new blank PDF

    for src_page in src_doc:
        rect = src_page.rect

        # ✅ Create a completely blank page
        new_page = new_doc.new_page(width=rect.width, height=rect.height)

        # ✅ Extract text words
        words = src_page.get_text("words")  # [(x0, y0, x1, y1, "word", block, line, word_no)]

        for w in words:
            x0, y0, x1, y1, word, *_ = w
            if not word.strip():
                continue

            # how many letters to bold
            n = 1 if len(word) <= 3 else 2 if len(word) <= 5 else 3
            bold_part = word[:n]
            rest_part = word[n:]

            # ✅ draw bold part in blue
            new_page.insert_text(
                (x0, y1),
                bold_part,
                fontname="helv",   # built-in Helvetica
                fontsize=10,
                color=(0, 0, 1)
            )

            # ✅ measure width of bold part
            width = fitz.get_text_length(bold_part, fontname="helv", fontsize=10)

            # ✅ draw remaining letters in black right after bold
            new_page.insert_text(
                (x0 + width, y1),
                rest_part,
                fontname="helv",
                fontsize=10,
                color=(0, 0, 0)
            )

    new_doc.save(output_path)
    src_doc.close()
    new_doc.close()
    print(f"✅ Clean ADHD-friendly PDF created: {output_path}")


app = FastAPI()

@app.post("/adhd-clean")
async def adhd_clean_endpoint(file: UploadFile):
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_in:
        tmp_in.write(await file.read())
        input_path = tmp_in.name

    output_path = input_path.replace(".pdf", "-adhd.pdf")

    # Run the ADHD text-only conversion
    adhd_bold_clean_pdf(input_path, output_path)

    return FileResponse(output_path, filename="adhd-friendly.pdf")