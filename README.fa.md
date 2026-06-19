# The Final Study AI

**پایپ‌لاین مطالعاتی موضوع‌محور** — از PDF تا پارت‌های مطالعاتی، ایندکس دوزبانه با محدودهٔ صفحات، و مایندمپ XMind.

> **زبان‌ها:** [English — README.md](README.md) · فارسی (این صفحه)

**نسخه:** CLI v0.1.0 · GUI بتا v0.2.0 · **گزارش‌ها:** [`docs/TEST_v0.1.0.md`](docs/TEST_v0.1.0.md)، [`docs/RELEASE_QUALIFICATION_v0.2.0-gui.md`](docs/RELEASE_QUALIFICATION_v0.2.0-gui.md)

```
PDF
  → Markdown (با وفاداری بالا)
  → پارت مطالعاتی بر اساس موضوع + ایندکس دوزبانه STUDY_INDEX (md + pdf)
  → [بررسی و تأیید کاربر]
  → OPML → XMind (اتوماسیون ChatGPT)
```

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

## شروع سریع

```bash
git clone https://github.com/alifazelidehkordi/the-final-study-ai.git
cd the-final-study-ai
chmod +x scripts/*.sh scripts/*.py

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

## معماری

```
the-final-study-ai/
├── scripts/
│   ├── run_pipeline.sh              # orchestrator (3 مرحله)
│   ├── run_pipeline.py              # orchestrator اصلی و چندسکویی
│   ├── segment_markdown_study_parts.py  # تقسیم موضوعی + ایندکس
│   ├── export_study_index_pdf.py    # STUDY_INDEX.md → PDF
│   └── combine_parts_to_sections.py # ابزار کمکی
├── docs/
│   └── TEST_v0.1.0.md               # گزارش تست
└── logs/                            # لاگ دیباگ محلی (gitignored)
```

### وابستگی‌های خارجی

| Component | Path / repo | نقش |
|-----------|-------------|-----|
| pdf-to-markdown | `~/.grok/skills/pdf-to-markdown` | PDF → Markdown (PyMuPDF4LLM) |
| chatgpt-mindmap-to-xmind | `~/projects/chatgpt-mindmap-to-xmind` | OPML + XMind via ChatGPT |
| PyMuPDF venv | داخل pdf-to-markdown | export ایندکس PDF |

---

## نصب

### رابط گرافیکی (بتا)

برنامهٔ دسکتاپ PySide6 با صفحات Setup، اجرای جدید، پیشرفت، بررسی، نتایج و تاریخچه.

| سند | موضوع |
|---|---|
| [`docs/GUI_WINDOWS_INSTALL.md`](docs/GUI_WINDOWS_INSTALL.md) | **راهنمای نصب و اجرا — Windows** |
| [`docs/GUI_LINUX_INSTALL.md`](docs/GUI_LINUX_INSTALL.md) | **راهنمای نصب و اجرا — Linux** |
| [`docs/GUI_SOURCE_INSTALL.md`](docs/GUI_SOURCE_INSTALL.md) | نصب قفل‌شده و بسته‌بندی |
| [`docs/SUPPORT_MATRIX.md`](docs/SUPPORT_MATRIX.md) | پشتیبانی سیستم‌عامل و presetها |
| [`docs/GUI_TROUBLESHOOTING.md`](docs/GUI_TROUBLESHOOTING.md) | عیب‌یابی GUI |
| [`docs/RELEASE_NOTES_v0.2.0-gui.md`](docs/RELEASE_NOTES_v0.2.0-gui.md) | یادداشت انتشار GUI |

```bash
python3 -m venv .venv && source .venv/bin/activate
python -m pip install -r requirements/dev-lock.txt
python -m gui
```

presetهای مایندمپ روی Wayland و macOS عمداً مسدود هستند تا پذیرش تعاملی کامل شود.

### ۱. Clone

```bash
git clone https://github.com/alifazelidehkordi/the-final-study-ai.git
cd the-final-study-ai
chmod +x scripts/*.sh scripts/*.py
```

### ۲. pdf-to-markdown

```bash
ls ~/.grok/skills/pdf-to-markdown/.venv/bin/python

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

## خروجی‌ها

برای `book.pdf` در `/data/books/`:

```text
/data/books/book.md
/data/books/book_images/
/data/books/book_work/
├── STUDY_INDEX.md           # ایندکس دوزبانه FA + EN
├── STUDY_INDEX.pdf          # نسخهٔ چاپی ایندکس
├── SEGMENTATION_PREVIEW.md  # خلاصه برای تأیید
├── parts-manifest.json      # ترتیب و hash پارت‌ها برای resume امن
├── parts/                   # یک فایل = یک موضوع
│   ├── 01_Topic_A.md
│   └── ...
├── opml/
└── xmind/                   # خروجی نهایی
```

### نمونه ایندکس

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
./scripts/run_pipeline.sh book.pdf --skip-convert --granularity coarse --overwrite
./scripts/run_pipeline.sh book.pdf --skip-convert --granularity fine --overwrite
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
>
> توقف برای بازبینی با کد خروج `20` مشخص می‌شود. این وضعیت برای GUI و ابزارهای
> اتوماسیون به معنی «در انتظار تأیید» است، نه خطای پایپ‌لاین.

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

`run_pipeline.sh` اکنون wrapper سازگار با نسخه‌های قبلی است و اجرای اصلی را به
`scripts/run_pipeline.py` می‌سپارد. entry point پایتونی علاوه بر فلگ‌های قبلی،
گزینه‌های `--event-file`، `--manifest-file`، `--start-at` و `--stop-after` را
برای GUI فراهم می‌کند. JSON Schemaهای نسخه‌بندی‌شده در `schemas/` قرار دارند.

---

## عیب‌یابی

CLI:

| مشکل | راه‌حل |
|------|--------|
| Markdown خالی | PDF اسکن‌شده — OCR را در convert_pdf امتحان کنید |
| خطای ChatGPT / login | یک بار در `chrome_profile` لاگین کنید |
| پارت‌های زیاد | `--granularity coarse` |
| پارت‌های کم/بزرگ | `--granularity fine` |
| ایندکس PDF ساخته نشد | `PDF_TO_MD_PY` باید PyMuPDF داشته باشد |
| فاصله در نام PDF | خودکار handle می‌شود (`lulu_fisio_images`) |

GUI: [`docs/GUI_TROUBLESHOOTING.md`](docs/GUI_TROUBLESHOOTING.md)

---

## تست

| گزارش | محدوده |
|---|---|
| [`docs/TEST_v0.1.0.md`](docs/TEST_v0.1.0.md) | CLI روی `lulu fisio.pdf` |
| [`docs/RELEASE_QUALIFICATION_v0.2.0-gui.md`](docs/RELEASE_QUALIFICATION_v0.2.0-gui.md) | دروازه‌های خودکار GUI + CLI |

```bash
bash scripts/ci/run_release_qualification.sh
./scripts/run_pipeline.sh "lulu fisio.pdf" --skip-convert --skip-mindmap --overwrite
./scripts/run_pipeline.sh "lulu fisio.pdf" --skip-convert --approve-segment --limit 1 --overwrite
```

چک‌لیست پذیرش تعاملی مایندمپ:
[`docs/INTERACTIVE_ACCEPTANCE_CHECKLIST.md`](docs/INTERACTIVE_ACCEPTANCE_CHECKLIST.md)

---

## نقشهٔ راه

- [x] رابط گرافیکی چندسکویی (بتا روی `feature/cross-platform-gui`)
- [ ] پذیرش تعاملی مایندمپ روی ویندوز + لینوکس X11
- [ ] `--resume` در orchestrator برای اجراهای متوقف‌شده
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
