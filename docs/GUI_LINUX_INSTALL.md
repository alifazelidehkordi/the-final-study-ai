# راهنمای نصب و اجرا — Linux

**نسخه:** GUI v0.2.0-gui (beta)  
**ریپوی انتشار:** [the-final-study-ai-gui](https://github.com/alifazelidehkordi/the-final-study-ai-gui)  
**ریلیز:** [v0.2.0-gui](https://github.com/alifazelidehkordi/the-final-study-ai-gui/releases/tag/v0.2.0-gui)

این سند **Ubuntu/Debian و توزیع‌های مشابه (x86_64)** را پوشش می‌دهد.  
برای مایندمپ، **نشست X11** لازم است — Wayland خالص پشتیبانی نمی‌شود.

---

## X11 یا Wayland؟

| نشست | GUI باز می‌شود؟ | Markdown & Index | Complete / Mind Maps |
|------|----------------|------------------|----------------------|
| **X11** | ✅ | ✅ | ✅ (با Setup کامل) |
| **Wayland** | ✅ | ✅ | ❌ مسدود |
| **بدون DISPLAY** (سرور headless) | محدود | ممکن | ❌ |

بررسی سریع:

```bash
echo "DISPLAY=$DISPLAY"
echo "XDG_SESSION_TYPE=$XDG_SESSION_TYPE"
```

اگر `XDG_SESSION_TYPE=wayland` است و می‌خواهی مایندمپ بزنی، در صفحهٔ ورود Ubuntu گزینه **Ubuntu on Xorg** را انتخاب کن.

---

## پیش‌نیاز

| مورد | توضیح |
|------|--------|
| توزیع | Ubuntu 22.04+ / Debian 12+ (x86_64) پیشنهاد می‌شود |
| Python (سورس) | 3.10 تا 3.13 |
| مرورگر | Google Chrome یا Chromium |
| فضای دیسک | حداقل ~2 GB آزاد |

### کتابخانه‌های سیستمی (برای سورس و گاهی بستهٔ آماده)

```bash
sudo apt update
sudo apt install -y \
  libegl1 libgl1 libglib2.0-0 libxkbcommon0 \
  libxcb-cursor0 libxcb-xinerama0 libdbus-1-3
```

### برای presetهای مایندمپ (X11)

```bash
sudo apt install -y python3-tk scrot
```

---

## روش ۱ — بستهٔ آماده (پیشنهادی)

### ۱. دانلود

**`the-final-study-ai-gui-v0.2.0-linux-x86_64.zip`**

```
https://github.com/alifazelidehkordi/the-final-study-ai-gui/releases/download/v0.2.0-gui/the-final-study-ai-gui-v0.2.0-linux-x86_64.zip
```

### ۲. Extract و اجرا

```bash
mkdir -p ~/Apps/the-final-study-ai-gui
cd ~/Apps/the-final-study-ai-gui
unzip ~/Downloads/the-final-study-ai-gui-v0.2.0-linux-x86_64.zip
chmod +x gui/deployment/__main__.dist/__main__.bin
./gui/deployment/__main__.dist/__main__.bin
```

> کل پوشهٔ `__main__.dist` را نگه دار — فقط فایل باینری را جدا کپی نکن.

اگر خطای `libEGL` یا `libGL` دیدی، بسته‌های apt بالا را نصب کن.

---

## روش ۲ — نصب از سورس

### ۱. Clone

```bash
git clone https://github.com/alifazelidehkordi/the-final-study-ai-gui.git
cd the-final-study-ai-gui
git checkout feature/cross-platform-gui
```

### ۲. محیط مجازی

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements/dev-lock.txt
python -m pip install -e .
```

### ۳. اجرا

```bash
source .venv/bin/activate
python -m gui
```

تست smoke بدون پنجره (اختیاری):

```bash
QT_QPA_PLATFORM=offscreen python -m gui &
```

---

## وابستگی‌های پایپ‌لاین

### pdf-to-markdown

```bash
export PDF_TO_MD_PY="$HOME/.grok/skills/pdf-to-markdown/.venv/bin/python"
export PDF_TO_MD_SCRIPT="$HOME/.grok/skills/pdf-to-markdown/convert_pdf.py"
```

یا مسیر خودت را در **Setup** تنظیم کن.

### chatgpt-mindmap-to-xmind

```bash
git clone https://github.com/alifazelidehkordi/chatgpt-mindmap-to-xmind.git ~/projects/chatgpt-mindmap-to-xmind
cd ~/projects/chatgpt-mindmap-to-xmind
git checkout feature/pipeline-events
./setup.sh
export MINDMAP_PROJECT="$HOME/projects/chatgpt-mindmap-to-xmind"
```

یک بار در **Setup → Run login probe** وارد ChatGPT شو.

---

## اولین اجرا — چک‌لیست

1. GUI را در نشست دسکتاپ باز کن (`DISPLAY` باید set باشد)
2. **Setup** → **Refresh**
3. این موارد برای مایندمپ باید **Ready** باشند:
   - Python / PySide6
   - PDF conversion
   - Mind-map project (`feature/pipeline-events`)
   - Chrome
   - Linux desktop (X11 + Tkinter + scrot)
   - Profile / login probe
4. **New Run** → اول **Markdown & Index** را تست کن
5. بعد **Complete Study Pack** → Review → تأیید → مایندمپ

---

## مسیر دادهٔ برنامه

```
~/.local/share/TheFinalStudyAI/The Final Study AI/
├── browser_profile/
├── runs/          # events.jsonl، run.json، run.log
└── tools/
```

باز کردن در فایل‌منیجر:

```bash
xdg-open ~/.local/share/TheFinalStudyAI/The\ Final\ Study\ AI/
```

---

## عیب‌یابی لینوکس

| مشکل | راه‌حل |
|------|--------|
| `ImportError: libEGL.so.1` | `sudo apt install libegl1 libgl1` |
| preset مایندمپ غیرفعال روی Wayland | به نشست **X11** برو یا فقط Markdown & Index |
| Linux desktop = Repairable | `sudo apt install python3-tk scrot` |
| `DISPLAY` خالی | از دسکتاپ اجرا کن، نه SSH بدون X forwarding |
| Login probe شکست خورد | Chrome را ببند، دوباره probe، دستی لاگین |
| Profile locked | همهٔ GUI/CLI را ببند |
| باینری اجرا نمی‌شود | `chmod +x` و کل `__main__.dist` را نگه دار |

جزئیات: [`GUI_TROUBLESHOOTING.md`](GUI_TROUBLESHOOTING.md)

---

## ساخت بسته روی لینوکس (اختیاری)

```bash
sudo apt install patchelf   # اگر pyside6-deploy بخواهد
source .venv/bin/activate
pyside6-deploy gui/__main__.py \
  -c packaging/pysidedeploy.spec \
  --keep-deployment-files \
  -f
```

خروجی:

```
gui/deployment/__main__.dist/__main__.bin
```

---

## English summary

| Step | Action |
|------|--------|
| Session | Use **X11** for mind-map presets; Wayland blocks Complete / Mind Maps Only |
| Download | `the-final-study-ai-gui-v0.2.0-linux-x86_64.zip` |
| Run | `chmod +x gui/deployment/__main__.dist/__main__.bin && ./gui/deployment/__main__.dist/__main__.bin` |
| System deps | `libegl1 libgl1 …` + `python3-tk scrot` for automation |
| Source | `python3 -m venv .venv` → `pip install -r requirements/dev-lock.txt` → `python -m gui` |
| Data dir | `~/.local/share/TheFinalStudyAI/The Final Study AI/` |

Related: [`GUI_SOURCE_INSTALL.md`](GUI_SOURCE_INSTALL.md) · [`SUPPORT_MATRIX.md`](SUPPORT_MATRIX.md)