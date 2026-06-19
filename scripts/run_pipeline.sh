#!/usr/bin/env bash
# Full pipeline: PDF -> Markdown -> study parts + index -> OPML -> XMind
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PDF_TO_MD_PY="${PDF_TO_MD_PY:-${HOME}/.grok/skills/pdf-to-markdown/.venv/bin/python}"
PDF_TO_MD_SCRIPT="${PDF_TO_MD_SCRIPT:-${HOME}/.grok/skills/pdf-to-markdown/scripts/convert_pdf.py}"
SEGMENT_SCRIPT="${SCRIPT_DIR}/segment_markdown_study_parts.py"
MINDMAP_PROJECT="${MINDMAP_PROJECT:-${HOME}/projects/chatgpt-mindmap-to-xmind}"

usage() {
  cat <<'EOF'
Usage: run_pipeline.sh [options] /absolute/path/to/document.pdf

Runs the full fidelity pipeline automatically:
  1) PDF -> Markdown (PyMuPDF4LLM)
  2) Markdown -> study parts + STUDY_INDEX.md (with PDF page ranges)
  3) Study parts -> OPML -> XMind (ChatGPT automation)

Options:
  --work-dir PATH       Output workspace (default: <pdf_dir>/<stem>_work)
  --skip-convert        Reuse existing <stem>.md beside the PDF
  --skip-segment        Reuse existing study parts in WORK_DIR
  --skip-mindmap        Stop after segmentation
  --mindmap-only        Skip convert + segment; only run mind map step
  --limit N             Process only first N study parts in mind map step
  --overwrite           Overwrite generated outputs
  --language LANG       Index language note (default: Persian)
  --granularity LEVEL   Split size: fine | normal | coarse (default: normal)
  --approve-segment     Skip segmentation review and continue to mind map
  --log-file PATH       Append full stdout/stderr to this log file
  -h, --help            Show this help

Environment overrides:
  PDF_TO_MD_PY          Python for pdf-to-markdown venv
  PDF_TO_MD_SCRIPT      Path to convert_pdf.py
  MINDMAP_PROJECT       Local chatgpt-mindmap-to-xmind project
  PROMPT_FILE           Mind map prompt (default: prompts/prompt-mind-map.md)
EOF
}

PDF_PATH=""
WORK_DIR=""
SKIP_CONVERT=0
SKIP_SEGMENT=0
SKIP_MINDMAP=0
MINDMAP_ONLY=0
LIMIT_ARGS=()
OVERWRITE_ARGS=()
LANGUAGE="Persian"
GRANULARITY="normal"
APPROVE_SEGMENT=0
LOG_FILE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --work-dir)
      WORK_DIR="$2"
      shift 2
      ;;
    --skip-convert)
      SKIP_CONVERT=1
      shift
      ;;
    --skip-segment)
      SKIP_SEGMENT=1
      shift
      ;;
    --skip-mindmap)
      SKIP_MINDMAP=1
      shift
      ;;
    --mindmap-only)
      MINDMAP_ONLY=1
      SKIP_CONVERT=1
      SKIP_SEGMENT=1
      shift
      ;;
    --limit)
      LIMIT_ARGS=(--limit "$2")
      shift 2
      ;;
    --overwrite)
      OVERWRITE_ARGS=(--overwrite)
      shift
      ;;
    --language)
      LANGUAGE="$2"
      shift 2
      ;;
    --granularity)
      GRANULARITY="$2"
      shift 2
      ;;
    --approve-segment)
      APPROVE_SEGMENT=1
      shift
      ;;
    --log-file)
      LOG_FILE="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      if [[ -z "${PDF_PATH}" ]]; then
        PDF_PATH="$1"
      else
        echo "ERROR: unexpected argument: $1" >&2
        usage >&2
        exit 1
      fi
      shift
      ;;
  esac
done

if [[ -z "${PDF_PATH}" ]]; then
  echo "ERROR: PDF path is required." >&2
  usage >&2
  exit 1
fi

if [[ ! -f "${PDF_PATH}" ]]; then
  echo "ERROR: PDF not found: ${PDF_PATH}" >&2
  exit 1
fi

PDF_PATH="$(readlink -f "${PDF_PATH}")"
PDF_DIR="$(dirname "${PDF_PATH}")"
PDF_STEM="$(basename "${PDF_PATH}" .pdf)"
if [[ -z "${WORK_DIR}" ]]; then
  WORK_DIR="${PDF_DIR}/${PDF_STEM}_work"
fi
WORK_DIR="$(readlink -f -m "${WORK_DIR}")"
mkdir -p "${WORK_DIR}"

if [[ -n "${LOG_FILE}" && "${PIPELINE_TEED:-}" != "1" ]]; then
  export PIPELINE_TEED=1
  mkdir -p "$(dirname "${LOG_FILE}")"
  {
    echo "=== LOG START $(date -Iseconds) ==="
    echo "PDF: ${PDF_PATH}"
    echo "WORK: ${WORK_DIR}"
    echo ""
  } >> "${LOG_FILE}"
  exec > >(tee -a "${LOG_FILE}") 2>&1
fi

MARKDOWN_FILE="${PDF_DIR}/${PDF_STEM}.md"
PARTS_DIR="${WORK_DIR}/parts"
OPML_DIR="${WORK_DIR}/opml"
XMIND_DIR="${WORK_DIR}/xmind"
PROMPT_FILE="${PROMPT_FILE:-${MINDMAP_PROJECT}/prompts/prompt-mind-map.md}"

echo "=== PDF Fidelity Mind Map Pipeline ==="
echo "PDF       : ${PDF_PATH}"
echo "Work dir  : ${WORK_DIR}"
echo ""

if [[ ${MINDMAP_ONLY} -eq 0 && ${SKIP_CONVERT} -eq 0 ]]; then
  echo "=== Step 1/3: PDF -> Markdown ==="
  CONVERT_ARGS=()
  if [[ ${#OVERWRITE_ARGS[@]} -gt 0 ]]; then
    CONVERT_ARGS+=(--overwrite)
  fi
  "${PDF_TO_MD_PY}" "${PDF_TO_MD_SCRIPT}" "${PDF_PATH}" \
    --output "${MARKDOWN_FILE}" \
    --no-ocr \
    "${CONVERT_ARGS[@]}"
  echo "Markdown  : ${MARKDOWN_FILE}"
  echo ""
elif [[ ! -f "${MARKDOWN_FILE}" ]]; then
  echo "ERROR: Markdown not found: ${MARKDOWN_FILE}" >&2
  echo "Run without --skip-convert first." >&2
  exit 1
else
  echo "=== Step 1/3: skipped (using ${MARKDOWN_FILE}) ==="
  echo ""
fi

if [[ ${MINDMAP_ONLY} -eq 0 && ${SKIP_SEGMENT} -eq 0 ]]; then
  echo "=== Step 2/3: Markdown -> study parts + STUDY_INDEX.md + STUDY_INDEX.pdf ==="
  python3 "${SEGMENT_SCRIPT}" \
    --input "${MARKDOWN_FILE}" \
    --output-dir "${WORK_DIR}" \
    --source-pdf "${PDF_PATH}" \
    --language "${LANGUAGE}" \
    --granularity "${GRANULARITY}"
  echo "Parts dir : ${PARTS_DIR}"
  echo "Index     : ${WORK_DIR}/STUDY_INDEX.md"
  echo "Index PDF : ${WORK_DIR}/STUDY_INDEX.pdf"
  echo "Preview   : ${WORK_DIR}/SEGMENTATION_PREVIEW.md"
  echo "Granularity: ${GRANULARITY}"
  echo ""

  if [[ ${APPROVE_SEGMENT} -eq 0 && ${SKIP_MINDMAP} -eq 0 ]]; then
    echo "=== Segmentation review required ==="
    echo "Read ${WORK_DIR}/SEGMENTATION_PREVIEW.md and STUDY_INDEX.md"
    echo "Then choose one:"
    echo "  - approve and continue mind map:"
    echo "      $(basename "$0") \"${PDF_PATH}\" --skip-convert --approve-segment ${OVERWRITE_ARGS[*]:-}"
    echo "  - coarser (fewer, larger parts):"
    echo "      $(basename "$0") \"${PDF_PATH}\" --skip-convert --granularity coarse ${OVERWRITE_ARGS[*]:-}"
    echo "  - finer (more, smaller parts):"
    echo "      $(basename "$0") \"${PDF_PATH}\" --skip-convert --granularity fine ${OVERWRITE_ARGS[*]:-}"
    echo ""
    echo "Stopping before mind map step. Re-run with --approve-segment to continue."
    exit 0
  fi
elif [[ ! -d "${PARTS_DIR}" ]]; then
  echo "ERROR: Study parts not found: ${PARTS_DIR}" >&2
  echo "Run without --skip-segment first." >&2
  exit 1
else
  echo "=== Step 2/3: skipped (using ${PARTS_DIR}) ==="
  echo ""
fi

if [[ ${SKIP_MINDMAP} -eq 1 ]]; then
  echo "Mind map step skipped."
  echo "Done."
  exit 0
fi

if [[ ! -d "${MINDMAP_PROJECT}" ]]; then
  echo "ERROR: Mind map project not found: ${MINDMAP_PROJECT}" >&2
  exit 1
fi

echo "=== Step 3/3: Study parts -> OPML -> XMind (chatgpt-mindmap-to-xmind) ==="
echo "Mind map project: ${MINDMAP_PROJECT}"
cd "${MINDMAP_PROJECT}"
if [[ ! -x ".venv-linux/bin/python" ]]; then
  ./setup.sh
fi

INPUT_DIR="${PARTS_DIR}" \
OPML_DIR="${OPML_DIR}" \
XMIND_DIR="${XMIND_DIR}" \
PROMPT_FILE="${PROMPT_FILE}" \
./run_pdf_to_xmind.sh "${OVERWRITE_ARGS[@]}" "${LIMIT_ARGS[@]}"

echo ""
echo "Done."
echo "Study index : ${WORK_DIR}/STUDY_INDEX.md"
echo "Index PDF   : ${WORK_DIR}/STUDY_INDEX.pdf"
echo "Study parts : ${PARTS_DIR}/"
echo "XMind files : ${XMIND_DIR}/"
