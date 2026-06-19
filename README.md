# The Final Study AI

**Topic-first PDF study pipeline** — از PDF تا پارت‌های مطالعاتی، ایندکس دوزبانه، و مایندمپ XMind.

```
PDF
  → Markdown (high-fidelity)
  → study parts by TOPIC + bilingual STUDY_INDEX (md + pdf)
  → [user review]
  → OPML → XMind (ChatGPT automation)
```

**نسخه:** v0.1.0 · **تست‌شده:** [`docs/TEST_v0.1.0.md`](docs/TEST_v0.1.0.md)

---

## چرا این پروژه؟

بیشتر ابزارها یا PDF را بدون ساختار موضوعی خرد می‌کنند، یا ایندکس و محدودهٔ صفحات را رها می‌کنند. این پایپ‌لاین:

1. **بر اساس موضوع** تقسیم می‌کند — نه تعداد صفحه
2. برای هر موضوع **محدودهٔ PDF** را در ایندکس ثبت می‌کند (pp. X–Y)
3. ایندکس **دوزبانه** (فارسی + انگلیسی) + خروجی PDF
4. قبل از مایندمپ، **تأیید کاربر** می‌گیرد
5. به پروژهٔ تست‌شدهٔ [`chatgpt-mindmap-to-xmind`](https://github.com/alifazelidehkordi/chatgpt-mindmap-to-xmind) وصل می‌شود

> راهنمای «۵–۱۰ صفحه در هر جلسه» فقط **دید کلی** است — قاعدهٔ تقسیم نیست.

---

## معماری

```
the-final-study-ai/
├── scripts/
│   ├── run_pipeline.sh              # orchestrator (3 steps)
│   ├── segment_markdown_study_parts.py  # topic split + index
│   ├── export_study_index_pdf.py    # STUDY_INDEX.md → PDF
│   └── combine_parts_to_sections.py # optional utility
├── docs/
│   └── TEST_v0.1.0.md               # test report
└── logs/                            # local debug logs (gitignored)
```

### وابستگی‌های خارجی

| Component | Path / repo | نقش |
|-----------|-------------|-----|
| pdf-to-markdown | `~/.grok/skills/pdf-to-markdown` | PDF → Markdown (PyMuPDF4LLM) |
| chatgpt-mindmap-to-xmind | `~/projects/chatgpt-mindmap-to-xmind` | OPML + XMind via ChatGPT |
| PyMuPDF venv | داخل pdf-to-markdown | export ایندکس PDF |

---

## نصب

### ۱. Clone

```bash
git clone https://github.com/alifazelidehkordi/the-final-study-ai.git
cd the-final-study-ai
chmod +x scripts/*.sh scripts/*.py
```

### ۲. pdf-to-markdown

```bash
# اگر از skill استفاده می‌کنید:
ls ~/.grok/skills/pdf-to-markdown/.venv/bin/python

# یا مسیر را override کنید:
export PDF_TO_MD_PY="/path/to/venv/bin/python"
export PDF_TO_MD_SCRIPT="/path/to/convert_pdf.py"
```

### ۳. chatgpt-mindmap-to-xmind

```bash
git clone https://github.com/alifazelidehkordi/chatgpt-mindmap-to-xmind.git ~/projects/chatgpt-mindmap-to-xmind
cd ~/projects/chatgpt-mindmap-to-xmind && ./setup.sh
# یک بار در chrome_profile لاگین ChatGPT کنید
```

---

## استفاده سریع

```bash
./scripts/run_pipeline.sh "/absolute/path/to/book.pdf" --overwrite
```

پایپ‌لاین بعد از تقسیم‌بندی **متوقف می‌شود** تا نتیجه را ببینید.

### بعد از بررسی — ادامه مایندمپ

```bash
./scripts/run_pipeline.sh "/path/to/book.pdf" \
  --skip-convert --approve-segment --overwrite
```

### فقط تقسیم + ایندکس (بدون مرورگر)

```bash
./scripts/run_pipeline.sh "/path/to/book.pdf" \
  --skip-convert --skip-mindmap --overwrite
```

---

## خروجی‌ها

برای `book.pdf` در `/data/books/`:

```text
/data/books/book.md
/data/books/book_images/
/data/books/book_work/
├── STUDY_INDEX.md           # ایندکس دوزبانه FA + EN
├── STUDY_INDEX.pdf          # نسخهٔ چاپی ایندکس
├── SEGMENTATION_PREVIEW.md  # خلاصه برای تأیید
├── parts/                   # یک فایل = یک موضوع
│   ├── 01_Topic_A.md
│   └── ...
├── opml/
└── xmind/                   # خروجی نهایی
```

### نمونه ایندکس (مثل sanei)

| # | پارت | صفحات PDF | توضیح مطالعه |
|---|------|-----------|-------------|
| 1 | Blood cells and haematopoiesis | **pp. 4–9** (6 ص) | مطالعه: Blood cells… |
| 2 | PATOPHYSIOLOGY OF ERYTHROCYTES | **pp. 10–16** (7 ص) | مطالعه: PATOPHYSIOLOGY… |

+ بلوک انگلیسی مشابه + جدول **راهنمای سریع / Quick Reference**

---

## اصل تقسیم‌بندی

| اصل | توضیح |
|-----|--------|
| **موضوع** | هر فایل = یک موضوع (سرتیتر اصلی یا زیرموضوع واضح) |
| **محدوده** | pp. X–Y در ایندکس = جایی که آن موضوع در PDF پوشش داده شده |
| **تغییر موضوع** | مرز طبیعی تقسیم — حتی اگر ۲ صفحه باشد |
| **دانه‌بندی** | فقط عمق زیرموضوع را تنظیم می‌کند، نه تعداد صفحه |

### `--granularity`

| مقدار | رفتار |
|-------|--------|
| `normal` | موضوعات اصلی + زیرموضوع‌های ⮚/❖ (پیش‌فرض) |
| `fine` | زیرموضوع‌های بیشتر |
| `coarse` | فقط موضوعات اصلی |

```bash
# درشت‌تر
./scripts/run_pipeline.sh book.pdf --skip-convert --granularity coarse --overwrite

# ریزتر
./scripts/run_pipeline.sh book.pdf --skip-convert --granularity fine --overwrite
```

---

## مراحل پایپ‌لاین

### Step 1 — PDF → Markdown

PyMuPDF4LLM، بدون OCR پیش‌فرض (`--no-ocr` برای PDFهای با متن embedded).

### Step 2 — Topic split + index

```bash
python3 scripts/segment_markdown_study_parts.py \
  --input book.md \
  --output-dir book_work \
  --source-pdf book.pdf \
  --granularity normal
```

### Step 3 — Mind map → XMind

```bash
cd ~/projects/chatgpt-mindmap-to-xmind
INPUT_DIR=book_work/parts OPML_DIR=book_work/opml XMIND_DIR=book_work/xmind \
  ./run_pdf_to_xmind.sh --overwrite
```

---

## فلگ‌های `run_pipeline.sh`

| Flag | کار |
|------|-----|
| `--skip-convert` | استفاده از `.md` موجود |
| `--skip-segment` | استفاده از `parts/` موجود |
| `--skip-mindmap` | توقف بعد از ایندکس |
| `--approve-segment` | رد شدن از مرحلهٔ تأیید → مایندمپ |
| `--granularity LEVEL` | fine \| normal \| coarse |
| `--limit N` | فقط N پارت اول در مایندمپ |
| `--overwrite` | بازنویسی خروجی |
| `--log-file PATH` | ذخیرهٔ لاگ کامل |

### متغیرهای محیطی

```bash
export PDF_TO_MD_PY=...
export PDF_TO_MD_SCRIPT=...
export MINDMAP_PROJECT=~/projects/chatgpt-mindmap-to-xmind
export PROMPT_FILE=~/projects/chatgpt-mindmap-to-xmind/prompts/prompt-mind-map.md
```

---

## گردش تأیید (Segmentation review)

1. پایپ‌لاین step 2 را اجرا می‌کند
2. `SEGMENTATION_PREVIEW.md` + `STUDY_INDEX.md/pdf` را بخوانید
3. انتخاب کنید:
   - **تایید** → `--approve-segment`
   - **درشت‌تر** → `--granularity coarse`
   - **ریزتر** → `--granularity fine`

> با `--skip-mindmap` مرحلهٔ تأیید رد نمی‌شود — فقط وقتی قرار است مایندمپ اجرا شود.

---

## عیب‌یابی

| مشکل | راه‌حل |
|------|--------|
| Markdown خالی | PDF اسکن‌شده — OCR را در convert_pdf امتحان کنید |
| خطای ChatGPT / login | یک بار در `chrome_profile` لاگین کنید |
| پارت‌های زیاد | `--granularity coarse` |
| پارت‌های کم/بزرگ | `--granularity fine` |
| ایندکس PDF ساخته نشد | `PDF_TO_MD_PY` باید PyMuPDF داشته باشد |
| فاصله در نام PDF | خودکار handle می‌شود (`lulu_fisio_images`) |

---

## تست

گزارش کامل: [`docs/TEST_v0.1.0.md`](docs/TEST_v0.1.0.md)

```bash
# تست سریع تقسیم + ایندکس
./scripts/run_pipeline.sh "lulu fisio.pdf" --skip-convert --skip-mindmap --overwrite

# تست مایندمپ (۱ پارت)
./scripts/run_pipeline.sh "lulu fisio.pdf" --skip-convert --approve-segment --limit 1 --overwrite
```

---

## نقشهٔ راه

- [ ] ترجمهٔ خودکار `توضیح مطالعه` به فارسی
- [ ] پشتیبانی از کتاب‌های فصل‌دار (الگوی sanei کامل)
- [ ] ادغام pdf-to-markdown به‌عنوان submodule
- [ ] رابط وب یا Obsidian plugin

---

## مجوز و نویسنده

MIT (پیشنهادی) — **Ali Fazeli Dehkordi** ([@alifazelidehkordi](https://github.com/alifazelidehkordi))

### پروژه‌های مرتبط

- [chatgpt-mindmap-to-xmind](https://github.com/alifazelidehkordi/chatgpt-mindmap-to-xmind)
- [chatgpt-mindmap-pipeline](https://github.com/alifazelidehkordi/chatgpt-mindmap-pipeline)
