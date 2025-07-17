from fastapi import FastAPI, UploadFile
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import fitz  # PyMuPDF

app = FastAPI()

# ✅ Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # you can restrict to your frontend URL later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Core processing: create new PDF with bigger first letters
def adhd_bold_clean_pdf(input_path, output_path):
    src_doc = fitz.open(input_path)
    new_doc = fitz.open()

    NORMAL_SIZE = 10        # Base font size
    SCALE_FACTOR = 1.15      # First letters 30% bigger

    for src_page in src_doc:
        rect = src_page.rect

        # create blank page with same size
        new_page = new_doc.new_page(width=rect.width, height=rect.height)

        # extract words with coordinates
        words = src_page.get_text("words")

        for w in words:
            x0, y0, x1, y1, word, *_ = w
            if not word.strip():
                continue

            # decide how many letters to enlarge
            n = 1 if len(word) <= 3 else 2 if len(word) <= 5 else 3
            big_part = word[:n]
            rest_part = word[n:]

            big_size = NORMAL_SIZE * SCALE_FACTOR

            # Draw first few letters larger + blue
            new_page.insert_text(
                (x0, y1),
                big_part,
                fontname="helv",
                fontsize=big_size,
                color=(0, 0, 1)  # blue
            )

            # Measure width of enlarged letters
            width_big = fitz.get_text_length(big_part, fontname="helv", fontsize=big_size)

            # Draw the rest of the word in normal black
            new_page.insert_text(
                (x0 + width_big, y1),
                rest_part,
                fontname="helv",
                fontsize=NORMAL_SIZE,
                color=(0, 0, 0)  # black
            )

    new_doc.save(output_path)
    src_doc.close()
    new_doc.close()
    print(f"✅ Clean ADHD-friendly PDF created: {output_path}")


@app.post("/adhd-clean")
async def adhd_clean_endpoint(file: UploadFile):
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_in:
        tmp_in.write(await file.read())
        input_path = tmp_in.name

    # Create output temp file
    output_path = input_path.replace(".pdf", "-adhd.pdf")

    # Process the PDF
    adhd_bold_clean_pdf(input_path, output_path)

    # Return the processed file
    return FileResponse(output_path, filename="adhd-friendly.pdf")


@app.get("/")
def root():
    return {"message": "✅ ADHD-friendly PDF API is running!"}
