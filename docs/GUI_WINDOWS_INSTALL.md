# راهنمای نصب و اجرا — Windows

**نسخه:** GUI v0.2.0-gui (beta)  
**ریپوی انتشار:** [the-final-study-ai-gui](https://github.com/alifazelidehkordi/the-final-study-ai-gui)  
**ریلیز:** [v0.2.0-gui](https://github.com/alifazelidehkordi/the-final-study-ai-gui/releases/tag/v0.2.0-gui)

این سند فقط **ویندوز ۱۰/۱۱ (64-bit)** را پوشش می‌دهد.

---

## پیش‌نیاز

| مورد | توضیح |
|------|--------|
| سیستم‌عامل | Windows 10 یا 11 — معماری x64 |
| مرورگر | Google Chrome (برای login probe و مایندمپ) |
| فضای دیسک | حداقل ~2 GB آزاد (بسته + خروجی‌های PDF) |
| اینترنت | برای نصب از سورس و اجرای ChatGPT |

برای preset **Markdown & Index** فقط خود GUI کافی است.  
برای **Complete Study Pack** و **Mind Maps Only** باید pdf-to-markdown و پروژهٔ mind-map هم در Setup سبز باشند.

---

## روش ۱ — بستهٔ آماده (پیشنهادی)

### ۱. دانلود

از صفحهٔ ریلیز این فایل را بگیر:

**`the-final-study-ai-gui-v0.2.0-windows-x86_64.zip`**

لینک مستقیم:

```
https://github.com/alifazelidehkordi/the-final-study-ai-gui/releases/download/v0.2.0-gui/the-final-study-ai-gui-v0.2.0-windows-x86_64.zip
```

### ۲. Extract

فایل zip را در مسیری **بدون فاصله و حروف فارسی** باز کن، مثلاً:

```
C:\Apps\the-final-study-ai-gui\
```

### ۳. اجرا

داخل پوشهٔ extract‌شده:

```
gui\deployment\__main__.dist\__main__.exe
```

یا در PowerShell:

```powershell
cd C:\Apps\the-final-study-ai-gui
.\gui\deployment\__main__.dist\__main__.exe
```

### ۴. هشدار SmartScreen

بیلد CI **امضا نشده** است. اگر Windows Defender SmartScreen هشدار داد:

1. **More info** / **اطلاعات بیشتر**
2. **Run anyway** / **اجرا در هر صورت**

اگر آنتی‌ویروس فایل را قرنطینه کرد، پوشهٔ `__main__.dist` را به استثنا اضافه کن.

---

## روش ۲ — نصب از سورس

اگر می‌خواهی کد را ویرایش کنی یا بسته zip کار نکرد.

### ۱. Clone

```powershell
git clone https://github.com/alifazelidehkordi/the-final-study-ai-gui.git
cd the-final-study-ai-gui
git checkout feature/cross-platform-gui
```

### ۲. Python 3.12

از [python.org](https://www.python.org/downloads/) نسخه **3.10 تا 3.13** نصب کن و در نصب گزینه **Add Python to PATH** را فعال کن.

بررسی:

```powershell
python --version
```

### ۳. محیط مجازی و وابستگی‌ها

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements\dev-lock.txt
python -m pip install -e .
```

اگر `Activate.ps1` خطای execution policy داد:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### ۴. اجرای GUI

```powershell
.\.venv\Scripts\Activate.ps1
python -m gui
```

---

## وابستگی‌های پایپ‌لاین (برای مایندمپ)

### pdf-to-markdown

مسیر Python و اسکریپت تبدیل را در **Setup** یا با متغیر محیطی تنظیم کن:

```powershell
$env:PDF_TO_MD_PY = "C:\path\to\pdf-to-markdown\.venv\Scripts\python.exe"
$env:PDF_TO_MD_SCRIPT = "C:\path\to\pdf-to-markdown\convert_pdf.py"
```

### chatgpt-mindmap-to-xmind

```powershell
git clone https://github.com/alifazelidehkordi/chatgpt-mindmap-to-xmind.git C:\Users\YOU\projects\chatgpt-mindmap-to-xmind
cd C:\Users\YOU\projects\chatgpt-mindmap-to-xmind
git checkout feature/pipeline-events
```

سپس در Setup مسیر پروژه را انتخاب کن یا:

```powershell
$env:MINDMAP_PROJECT = "C:\Users\YOU\projects\chatgpt-mindmap-to-xmind"
```

یک بار در **Setup → Run login probe** وارد ChatGPT شو.

---

## اولین اجرا — چک‌لیست

1. GUI را باز کن
2. برو **Setup** → **Refresh** — همهٔ موارد لازم باید **Ready** باشند
3. **Run login probe** — لاگین ChatGPT در پنجرهٔ مرورگر
4. **New Run** → برای تست اول **Markdown & Index** (بدون مرورگر)
5. PDF کوچک انتخاب کن → **Start**
6. **Progress** → **Results** → **History**

برای preset کامل (**Complete Study Pack**):

- Review بعد از تقسیم‌بندی ظاهر می‌شود (exit code 20)
- تأیید کن → مرحلهٔ مایندمپ شروع می‌شود

---

## مسیر دادهٔ برنامه روی ویندوز

GUI تنظیمات و اجراها را اینجا نگه می‌دارد:

```
%APPDATA%\TheFinalStudyAI\The Final Study AI\
├── browser_profile\     # پروفایل Chrome مدیریت‌شده
├── runs\                # لاگ، events.jsonl، run.json هر اجرا
└── tools\               # ابزارهای نصب‌شده توسط Setup
```

باز کردن در Explorer:

```powershell
explorer "$env:APPDATA\TheFinalStudyAI\The Final Study AI"
```

---

## عیب‌یابی ویندوز

| مشکل | راه‌حل |
|------|--------|
| SmartScreen / «Windows protected your PC» | More info → Run anyway (بیلد امضا نشده) |
| برنامه باز نمی‌شود | کل پوشهٔ `__main__.dist` را extract کن؛ فقط exe را جدا کپی نکن |
| `No module named 'PySide6'` (سورس) | `pip install -r requirements\dev-lock.txt` داخل venv |
| preset مایندمپ غیرفعال | Setup را Refresh کن؛ Chrome و mind-map project را Ready کن |
| Login probe شکست خورد | Chrome را ببند، دوباره probe بزن، دستی لاگین کن |
| Profile locked | همهٔ پنجره‌های GUI/CLI را ببند و دوباره امتحان کن |
| آنتی‌ویروس exe را حذف کرد | استثنا برای `__main__.dist` |

جزئیات بیشتر: [`GUI_TROUBLESHOOTING.md`](GUI_TROUBLESHOOTING.md)

---

## ساخت بسته روی خود ویندوز (اختیاری)

```powershell
.\.venv\Scripts\Activate.ps1
pyside6-deploy gui\__main__.py -c packaging\pysidedeploy.spec --keep-deployment-files -f
```

خروجی:

```
gui\deployment\__main__.dist\__main__.exe
```

---

## English summary

| Step | Action |
|------|--------|
| Download | `the-final-study-ai-gui-v0.2.0-windows-x86_64.zip` from the v0.2.0-gui release |
| Run | `gui\deployment\__main__.dist\__main__.exe` |
| Source | `python -m venv .venv` → `.\.venv\Scripts\Activate.ps1` → `pip install -r requirements\dev-lock.txt` → `python -m gui` |
| Data dir | `%APPDATA%\TheFinalStudyAI\The Final Study AI\` |

Related: [`GUI_SOURCE_INSTALL.md`](GUI_SOURCE_INSTALL.md) · [`SUPPORT_MATRIX.md`](SUPPORT_MATRIX.md)