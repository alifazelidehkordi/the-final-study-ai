#!/usr/bin/env python3
"""Split extracted PDF markdown into study-session parts with a page-aware index."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass, field
from pathlib import Path

PAGE_MARKER_RE = re.compile(r"^<!-- Page (\d+) -->\s*$")
HEADING_RE = re.compile(r"^##\s+(.+?)\s*$")
NUMBERED_HEADING_RE = re.compile(
    r"^##\s+(?:\*\*|_)?(\d+(?:\.\d+)*)(?:\s+|\*\*|_)(.+?)(?:\*\*|_)?\s*$"
)
CHAPTER_NUMBER_RE = re.compile(r"^##\s+\*\*(\d+)\*\*\s+(.+?)\s*$")
BOOK_PAGE_RE = re.compile(r"^\*\*(\d{1,4}|[ivxlcdm]+)\*\*\s*$", re.IGNORECASE)
ROMAN_ONLY_RE = re.compile(r"^[ivxlcdm]+$", re.IGNORECASE)

@dataclass
class GranularityConfig:
    """Topic-first split depth. Page ranges are recorded in the index, not used to cut parts."""

    split_subtopics: bool = True
    split_minor_sections: bool = True
    split_deep_sections: bool = False
    max_part_lines: int = 450
    merge_fragment_lines: int = 12
    label: str = "normal"


GRANULARITY_PRESETS: dict[str, GranularityConfig] = {
    "fine": GranularityConfig(True, True, True, 220, 8, "fine"),
    "normal": GranularityConfig(True, True, False, 450, 12, "normal"),
    "coarse": GranularityConfig(False, False, False, 800, 20, "coarse"),
}

GUIDE_PAGES_MIN = 5
GUIDE_PAGES_MAX = 10

ACTIVE_GRANULARITY = GRANULARITY_PRESETS["normal"]


def apply_granularity(name: str) -> GranularityConfig:
    global ACTIVE_GRANULARITY
    key = name.lower().strip()
    if key not in GRANULARITY_PRESETS:
        valid = ", ".join(GRANULARITY_PRESETS)
        raise ValueError(f"Unknown granularity '{name}'. Choose: {valid}")
    ACTIVE_GRANULARITY = GRANULARITY_PRESETS[key]
    return ACTIVE_GRANULARITY


def split_subtopics() -> bool:
    return ACTIVE_GRANULARITY.split_subtopics


def split_minor_sections() -> bool:
    return ACTIVE_GRANULARITY.split_minor_sections


def split_deep_sections() -> bool:
    return ACTIVE_GRANULARITY.split_deep_sections


def max_part_lines() -> int:
    return ACTIVE_GRANULARITY.max_part_lines


def merge_fragment_lines() -> int:
    return ACTIVE_GRANULARITY.merge_fragment_lines


def part_page_count(part: StudyPart) -> int:
    start, end = part.start_page, part.end_page
    if start is None or end is None:
        return 0
    return end - start + 1


def root_topic(title: str) -> str:
    cleaned = clean_heading_text(title)
    if " + " in cleaned:
        return cleaned.split(" + ", 1)[0].strip()
    if " — " in cleaned:
        return cleaned.split(" — ", 1)[0].strip()
    return cleaned


def same_topic(left: StudyPart, right: StudyPart) -> bool:
    return study_focus(left) == study_focus(right)


def topics_compatible(left: StudyPart, right: StudyPart) -> bool:
    left_kind = left.sections[0].kind
    right_kind = right.sections[0].kind
    if left_kind != right_kind:
        return False
    if left_kind in {"references", "preface", "abbreviations", "symbols", "chapter", "chapter_intro"}:
        return False
    if left.chapter is not None and right.chapter is not None and left.chapter != right.chapter:
        return False
    return are_adjacent_siblings(left.sections[0], right.sections[0])


def topic_suffix(full_title: str, root: str) -> str:
    focus = clean_heading_text(full_title)
    root_clean = clean_heading_text(root)
    if focus == root_clean:
        return ""
    if focus.startswith(root_clean):
        return focus[len(root_clean) :].strip(" —+")
    if " — " in focus:
        return focus.split(" — ", 1)[1].strip()
    return focus


def combine_parts(left: StudyPart, right: StudyPart) -> StudyPart:
    left_root = root_topic(left.title)
    right_root = root_topic(right.title)

    if left_root == right_root:
        left_suffix = topic_suffix(left.title, left_root)
        right_suffix = topic_suffix(right.title, right_root)
        if left_suffix and right_suffix and left_suffix != right_suffix:
            title = f"{left_root} — {left_suffix} + {right_suffix}"
        elif right_suffix and not left_suffix:
            title = f"{left_root} — {right_suffix}"
        elif left_suffix and not right_suffix:
            title = f"{left_root} — {left_suffix}"
        else:
            title = left_root
    else:
        left_focus = study_focus(left)
        right_focus = study_focus(right)
        if right_focus.startswith(left_focus):
            title = right_focus
        elif left_focus == right_focus:
            title = left_focus
        else:
            title = f"{left_focus} + {right_focus}"
    return StudyPart(title=title, sections=[*left.sections, *right.sections])


def is_oversized_part(part: StudyPart) -> bool:
    return part.line_count > max_part_lines()

SKIP_HEADING_PATTERNS = (
    "contents",
    "other wiley",
    "library of congress",
    "british library",
    "eeg signal processing",
    "saeid sanei",
)

LECTURE_INTRO_SKIP = (
    "hey you",
    "covid has done",
    "want to know something great",
    "no need to thank me",
    "buono studio",
    "lucrezia vivona",
)

LECTURE_STRONG_KEYWORDS = (
    "PATHOPHYSIOLOGY OF",
    "PATOPHYSIOLOGY OF",
    "DISORDERS OF IRON METABOLISM",
    "BLOOD-RELATED DISORDERS",
    "INBORN ERRORS OF METABOLISM",
    "HAEMATOPOIETIC MALIGNANCIES",
    "MYELOID MALIGNANCIES",
    "LYMPHOID MALIGNANCIES",
    "THYROID DISEASES",
    "CONGENITAL ADRENAL",
    "PARATHYROID",
    "POLYCYSTIC",
    "DIABETES",
    "KIDNEY",
)

LECTURE_DIAMOND_KEYWORDS = (
    "ANAEMIA FOR",
    "ANAEMIAS FOR",
    "HAEMOSTASIS",
    "CML",
    "MPN",
    "HYPERTHYROID",
    "HYPOTHYROID",
    "SPHINGOLIPIDOSIS",
    "GLYCOGENOSIS",
    "MUCOPOLYSACCHAROIDOSIS",
)

LECTURE_FIRST_TOPICS = {
    "blood cells and haematopoiesis",
}


@dataclass
class RawSection:
    title: str
    lines: list[str]
    start_line: int
    end_line: int
    start_page: int | None
    end_page: int | None
    section_number: str | None = None
    chapter: int | None = None
    kind: str = "section"
    depth: int = 0

    @property
    def line_count(self) -> int:
        return len(self.lines)

    @property
    def text(self) -> str:
        return "\n".join(self.lines).rstrip() + "\n"


@dataclass
class StudyPart:
    title: str
    sections: list[RawSection] = field(default_factory=list)
    filename: str = ""

    @property
    def lines(self) -> list[str]:
        merged: list[str] = []
        for section in self.sections:
            merged.extend(section.lines)
        return merged

    @property
    def line_count(self) -> int:
        return len(self.lines)

    @property
    def start_page(self) -> int | None:
        pages = [s.start_page for s in self.sections if s.start_page is not None]
        return min(pages) if pages else None

    @property
    def end_page(self) -> int | None:
        pages = [s.end_page for s in self.sections if s.end_page is not None]
        return max(pages) if pages else None

    @property
    def chapter(self) -> int | None:
        for section in self.sections:
            if section.chapter is not None:
                return section.chapter
        return None

    @property
    def book_pages(self) -> str:
        for line in self.lines[:12]:
            match = BOOK_PAGE_RE.match(line.strip())
            if match and not ROMAN_ONLY_RE.fullmatch(match.group(1)):
                first = match.group(1)
                for candidate in reversed(self.lines[:20]):
                    later = BOOK_PAGE_RE.match(candidate.strip())
                    if later and not ROMAN_ONLY_RE.fullmatch(later.group(1)):
                        last = later.group(1)
                        return first if first == last else f"{first}–{last}"
                return first
        return "—"

    @property
    def text(self) -> str:
        return "\n".join(self.lines).rstrip() + "\n"


def clean_heading_text(raw: str) -> str:
    text = raw.strip()
    text = re.sub(r"\*\*|__", "", text)
    text = re.sub(r"(?<!\w)_([^_]+)_(?!\w)", r"\1", text)
    text = re.sub(r"^[*_❖⮚•`🡺]+|[*_❖⮚•`🡺]+$", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def heading_should_skip(title: str) -> bool:
    lowered = title.lower()
    if ROMAN_ONLY_RE.fullmatch(title):
        return True
    if title.isdigit():
        return True
    return any(pattern in lowered for pattern in SKIP_HEADING_PATTERNS)


def parse_heading(line: str) -> tuple[str, str | None, int, str] | None:
    match = HEADING_RE.match(line)
    if not match:
        return None

    raw = match.group(1)
    title = clean_heading_text(raw)

    chapter_match = CHAPTER_NUMBER_RE.match(line)
    if chapter_match:
        chapter = int(chapter_match.group(1))
        chapter_title = clean_heading_text(chapter_match.group(2))
        return chapter_title, str(chapter), 0, "chapter"

    numbered = NUMBERED_HEADING_RE.match(line)
    if numbered:
        number = numbered.group(1)
        section_title = clean_heading_text(numbered.group(2))
        depth = number.count(".") + 1
        chapter = int(number.split(".")[0])
        kind = "major" if depth == 2 else "minor"
        return f"{number} {section_title}".strip(), number, depth, kind

    lowered = title.lower()
    if lowered == "preface":
        return title, None, 0, "preface"
    if lowered.startswith("list of abbreviations"):
        return title, None, 0, "abbreviations"
    if lowered.startswith("list of symbols"):
        return title, None, 0, "symbols"
    if lowered == "references":
        return title, None, 0, "references"
    if lowered.startswith("introduction to"):
        return title, None, 0, "chapter_intro"

    if heading_should_skip(title):
        return None

    return title, None, 1, "section"


def heading_upper_ratio(title: str) -> float:
    letters = [char for char in title if char.isalpha()]
    if not letters:
        return 0.0
    return sum(1 for char in letters if char.isupper()) / len(letters)


def is_major_lecture_heading(line: str, title: str) -> bool:
    lowered = title.lower()
    if any(pattern in lowered for pattern in LECTURE_INTRO_SKIP):
        return False
    if line.startswith("## ⮚") or line.startswith("## •") or line.startswith("## -"):
        return False
    if re.match(r"^##\s+\d+[-.)]", line):
        return False
    if re.match(r"^\d+[-.)]\s", title):
        return False

    upper = title.upper()
    ratio = heading_upper_ratio(title)

    if lowered in LECTURE_FIRST_TOPICS:
        return True
    if ratio >= 0.78 and len(title) >= 12:
        return True
    if "❖" in line and any(keyword in upper for keyword in LECTURE_DIAMOND_KEYWORDS):
        return True
    if any(keyword in upper for keyword in LECTURE_STRONG_KEYWORDS) and ratio >= 0.45:
        return True
    if upper.strip() in {"ANAEMIA", "HAEMOSTASIS"}:
        return True
    return False


def lecture_subtopic_points(
    section: RawSection, source_lines: list[str]
) -> list[tuple[int, str]]:
    children: list[tuple[int, str]] = []
    for index in range(section.start_line, section.end_line + 1):
        line = source_lines[index]
        if line.startswith("## ⮚") or line.startswith("## ❖"):
            match = HEADING_RE.match(line)
            if match:
                children.append((index, clean_heading_text(match.group(1))))
    return children


def should_split_lecture_section(section: RawSection, subtopics: list[tuple[int, str]]) -> bool:
    if section.kind != "lecture_topic" or len(subtopics) < 2:
        return False
    if split_subtopics():
        return True
    return section.line_count > max_part_lines()


def split_large_lecture_sections(sections: list[RawSection], source_lines: list[str]) -> list[RawSection]:
    expanded: list[RawSection] = []
    for section in sections:
        if section.kind != "lecture_topic":
            expanded.append(section)
            continue

        children: list[tuple[int, str]] = lecture_subtopic_points(section, source_lines)
        if not should_split_lecture_section(section, children):
            expanded.append(section)
            continue

        if len(children) < 2:
            expanded.append(section)
            continue

        preamble_end = children[0][0]
        if preamble_end > section.start_line:
            preamble = source_lines[section.start_line:preamble_end]
            expanded.append(
                RawSection(
                    title=section.title,
                    lines=preamble,
                    start_line=section.start_line,
                    end_line=preamble_end - 1,
                    start_page=page_span(preamble)[0],
                    end_page=page_span(preamble)[1],
                    kind="lecture_topic",
                )
            )

        for idx, (line_index, title) in enumerate(children):
            next_index = children[idx + 1][0] if idx + 1 < len(children) else section.end_line + 1
            chunk = source_lines[line_index:next_index]
            expanded.append(
                RawSection(
                    title=f"{section.title} — {title}",
                    lines=chunk,
                    start_line=line_index,
                    end_line=next_index - 1,
                    start_page=page_span(chunk)[0],
                    end_page=page_span(chunk)[1],
                    kind="lecture_topic",
                )
            )
    return expanded


def split_lecture_sections(lines: list[str]) -> list[RawSection]:
    split_points: list[tuple[int, str]] = []
    for index, line in enumerate(lines):
        match = HEADING_RE.match(line)
        if not match:
            continue
        title = clean_heading_text(match.group(1))
        if is_major_lecture_heading(line, title):
            split_points.append((index, title))

    if not split_points:
        start_page, end_page = page_span(lines)
        return [
            RawSection(
                title="Document",
                lines=lines,
                start_line=0,
                end_line=len(lines) - 1,
                start_page=start_page,
                end_page=end_page,
                kind="lecture_topic",
            )
        ]

    sections: list[RawSection] = []
    for idx, (line_index, title) in enumerate(split_points):
        end_index = split_points[idx + 1][0] if idx + 1 < len(split_points) else len(lines)
        chunk = lines[line_index:end_index]
        start_page, end_page = page_span(chunk)
        sections.append(
            RawSection(
                title=title,
                lines=chunk,
                start_line=line_index,
                end_line=end_index - 1,
                start_page=start_page,
                end_page=end_page,
                kind="lecture_topic",
            )
        )
    return sections


def should_use_lecture_split(sections: list[RawSection], line_count: int) -> bool:
    if line_count < 500:
        return False
    major_like = [
        section
        for section in sections
        if section.kind in {"major", "chapter", "chapter_intro", "preface"}
        or section.section_number is not None
    ]
    return len(major_like) <= 2


def annotate_pages(lines: list[str]) -> tuple[list[str], list[int | None]]:
    pages: list[int | None] = []
    current_page: int | None = None
    for line in lines:
        marker = PAGE_MARKER_RE.match(line)
        if marker:
            current_page = int(marker.group(1))
        pages.append(current_page)
    return lines, pages


def page_span(section_lines: list[str]) -> tuple[int | None, int | None]:
    pages: list[int] = []
    for line in section_lines:
        marker = PAGE_MARKER_RE.match(line)
        if marker:
            pages.append(int(marker.group(1)))
    if not pages:
        return None, None
    return min(pages), max(pages)


def split_raw_sections(lines: list[str]) -> list[RawSection]:
    _, page_by_line = annotate_pages(lines)
    boundaries: list[tuple[int, str, str | None, int, str]] = []

    for index, line in enumerate(lines):
        parsed = parse_heading(line)
        if parsed is None:
            continue
        title, number, depth, kind = parsed
        boundaries.append((index, title, number, depth, kind))

    if not boundaries:
        start_page, end_page = page_span(lines)
        return [
            RawSection(
                title="Document",
                lines=lines,
                start_line=0,
                end_line=len(lines) - 1,
                start_page=start_page,
                end_page=end_page,
            )
        ]

    start_index = 0
    for index, title, number, depth, kind in boundaries:
        if kind in {"preface", "abbreviations", "symbols", "chapter_intro", "chapter", "major", "references"}:
            start_index = index
            break

    split_points = [
        (index, title, number, depth, kind)
        for index, title, number, depth, kind in boundaries
        if index >= start_index
        and kind
        in {
            "preface",
            "abbreviations",
            "symbols",
            "chapter_intro",
            "chapter",
            "major",
            "references",
        }
    ]

    if not split_points:
        split_points = boundaries[start_index : start_index + 1]

    sections: list[RawSection] = []
    for idx, (line_index, title, number, depth, kind) in enumerate(split_points):
        end_index = (
            split_points[idx + 1][0]
            if idx + 1 < len(split_points)
            else len(lines)
        )
        chunk = lines[line_index:end_index]
        start_page, end_page = page_span(chunk)
        chapter = None
        if number and number.isdigit():
            chapter = int(number)
        elif number and "." in number:
            chapter = int(number.split(".")[0])

        sections.append(
            RawSection(
                title=title,
                lines=chunk,
                start_line=line_index,
                end_line=end_index - 1,
                start_page=start_page,
                end_page=end_page,
                section_number=number,
                chapter=chapter,
                kind=kind,
                depth=depth,
            )
        )

    return sections


def number_segments(number: str | None) -> int:
    if not number:
        return 0
    return len(number.split("."))


def collect_child_sections(
    lines: list[str],
    start: int,
    end: int,
    parent: RawSection,
    *,
    extra_depth: int = 1,
) -> list[RawSection]:
    parent_segments = number_segments(parent.section_number)
    target_segments = parent_segments + extra_depth if parent_segments else 0

    children: list[tuple[int, str, str | None, int, str]] = []
    for index in range(start, end):
        parsed = parse_heading(lines[index])
        if parsed is None:
            continue
        title, number, depth, kind = parsed
        if not number:
            continue
        if parent_segments:
            if number_segments(number) != target_segments:
                continue
        elif number_segments(number) < 2:
            continue
        children.append((index, title, number, depth, kind))

    if not children:
        return [parent]

    results: list[RawSection] = []
    preamble_end = children[0][0]
    if preamble_end > start:
        preamble = lines[start:preamble_end]
        start_page, end_page = page_span(preamble)
        results.append(
            RawSection(
                title=parent.title,
                lines=preamble,
                start_line=start,
                end_line=preamble_end - 1,
                start_page=start_page,
                end_page=end_page,
                section_number=parent.section_number,
                chapter=parent.chapter,
                kind=parent.kind,
                depth=parent.depth,
            )
        )

    for idx, (line_index, title, number, depth, kind) in enumerate(children):
        next_index = children[idx + 1][0] if idx + 1 < len(children) else end
        chunk = lines[line_index:next_index]
        start_page, end_page = page_span(chunk)
        chapter = parent.chapter
        if number and "." in number:
            chapter = int(number.split(".")[0])
        results.append(
            RawSection(
                title=title,
                lines=chunk,
                start_line=line_index,
                end_line=next_index - 1,
                start_page=start_page,
                end_page=end_page,
                section_number=number,
                chapter=chapter,
                kind=kind,
                depth=depth,
            )
        )
    return results


def explode_nested_sections(sections: list[RawSection], source_lines: list[str]) -> list[RawSection]:
    if not split_minor_sections():
        return sections

    expanded: list[RawSection] = []
    for section in sections:
        if section.kind != "major" or section.line_count < 80:
            expanded.append(section)
            continue
        children = collect_child_sections(
            source_lines,
            section.start_line,
            section.end_line + 1,
            section,
            extra_depth=1,
        )
        if len(children) > 1:
            expanded.extend(children)
        else:
            expanded.append(section)
    return expanded


def subdivide_large_sections(sections: list[RawSection], source_lines: list[str]) -> list[RawSection]:
    if not split_minor_sections():
        return sections

    expanded: list[RawSection] = []
    for section in sections:
        if section.line_count <= max_part_lines():
            expanded.append(section)
            continue
        children = collect_child_sections(
            source_lines,
            section.start_line,
            section.end_line + 1,
            section,
            extra_depth=1,
        )
        if len(children) > 1:
            expanded.extend(children)
            continue
        if split_deep_sections():
            deep_children = collect_child_sections(
                source_lines,
                section.start_line,
                section.end_line + 1,
                section,
                extra_depth=2,
            )
            if len(deep_children) > 1:
                expanded.extend(deep_children)
                continue
        expanded.append(section)
    return expanded


def are_adjacent_siblings(left: RawSection, right: RawSection) -> bool:
    if not left.section_number or not right.section_number:
        return False
    left_parts = left.section_number.split(".")
    right_parts = right.section_number.split(".")
    if len(left_parts) != len(right_parts):
        return False
    if left_parts[:-1] != right_parts[:-1]:
        return False
    return int(right_parts[-1]) == int(left_parts[-1]) + 1


def sections_to_parts(sections: list[RawSection]) -> list[StudyPart]:
    return [StudyPart(title=section.title, sections=[section]) for section in sections]


def merge_textbook_siblings(parts: list[StudyPart]) -> list[StudyPart]:
    if not parts:
        return []

    merged: list[StudyPart] = []
    index = 0
    while index < len(parts):
        current = parts[index]
        next_part = parts[index + 1] if index + 1 < len(parts) else None
        current_kind = current.sections[0].kind
        next_kind = next_part.sections[0].kind if next_part else None
        can_merge = (
            next_part is not None
            and topics_compatible(current, next_part)
            and current.line_count + next_part.line_count <= max_part_lines()
            and max(current.line_count, next_part.line_count) < 90
            and current_kind == "major"
            and next_kind == "major"
        )
        if can_merge:
            merged.append(combine_parts(current, next_part))
            index += 2
            continue
        merged.append(current)
        index += 1
    return merged


def merge_heading_fragments(parts: list[StudyPart]) -> list[StudyPart]:
    """Attach tiny heading-only stubs to the previous part when they share a topic."""
    if not parts:
        return []

    merged: list[StudyPart] = [parts[0]]
    for part in parts[1:]:
        prev = merged[-1]
        if (
            part.line_count <= merge_fragment_lines()
            and part_page_count(part) == 0
            and root_topic(part.title) == root_topic(prev.title)
            and not same_topic(prev, part)
        ):
            merged[-1] = combine_parts(prev, part)
            continue
        merged.append(part)
    return merged


def merge_small_sections(sections: list[RawSection]) -> list[StudyPart]:
    parts = sections_to_parts(sections)
    parts = merge_textbook_siblings(parts)
    return merge_heading_fragments(parts)


def display_title(title: str) -> str:
    cleaned = clean_heading_text(title)
    if " — " in cleaned:
        parent, child = cleaned.rsplit(" — ", 1)
        return f"{parent} — {clean_heading_text(child)}"
    return cleaned


def is_subsplit_heading(line: str, index: int) -> bool:
    if index == 0 or not HEADING_RE.match(line):
        return False
    if line.startswith("## ⮚") or line.startswith("## ❖"):
        return split_subtopics()
    if split_deep_sections() and (line.startswith("## _**") or line.startswith("## **")):
        title = clean_heading_text(HEADING_RE.match(line).group(1))
        if heading_upper_ratio(title) >= 0.45 and len(title) >= 10:
            return True
    return False


def split_one_study_part(part: StudyPart) -> list[StudyPart]:
    lines = part.lines
    if not is_oversized_part(part):
        return [part]

    split_points: list[tuple[int, str]] = []
    for index, line in enumerate(lines):
        if not is_subsplit_heading(line, index):
            continue
        title = clean_heading_text(HEADING_RE.match(line).group(1))
        split_points.append((index, title))

    if not split_points:
        return [part]
    else:
        chunks = []
        if split_points[0][0] > 0:
            chunks.append((part.title, lines[: split_points[0][0]]))
        for idx, (line_index, title) in enumerate(split_points):
            end_index = split_points[idx + 1][0] if idx + 1 < len(split_points) else len(lines)
            sub_title = f"{part.title} — {title}" if title else part.title
            chunks.append((sub_title, lines[line_index:end_index]))

    results: list[StudyPart] = []
    for title, chunk_lines in chunks:
        if not chunk_lines:
            continue
        results.append(
            StudyPart(
                title=title,
                sections=[
                    RawSection(
                        title=title,
                        lines=chunk_lines,
                        start_line=part.sections[0].start_line,
                        end_line=part.sections[-1].end_line,
                        start_page=page_span(chunk_lines)[0],
                        end_page=page_span(chunk_lines)[1],
                        kind=part.sections[0].kind,
                        chapter=part.sections[0].chapter,
                    )
                ],
            )
        )
    return results or [part]


def split_oversized_study_parts(parts: list[StudyPart]) -> list[StudyPart]:
    for _ in range(6):
        expanded: list[StudyPart] = []
        changed = False
        for part in parts:
            split_parts = split_one_study_part(part)
            if len(split_parts) > 1:
                changed = True
            expanded.extend(split_parts)
        parts = expanded
        if not changed or all(not is_oversized_part(part) for part in parts):
            break
    return parts


def split_large_parts(parts: list[StudyPart], source_lines: list[str]) -> list[StudyPart]:
    final: list[StudyPart] = []
    for part in parts:
        if not is_oversized_part(part):
            final.append(part)
            continue

        start = part.sections[0].start_line
        end = part.sections[-1].end_line + 1
        minors = collect_child_sections(source_lines, start, end, part.sections[0], extra_depth=1)
        if len(minors) <= 1:
            final.append(part)
            continue

        for minor in minors:
            final.append(StudyPart(title=minor.title, sections=[minor]))
    return final


def split_long_front_matter(parts: list[StudyPart]) -> list[StudyPart]:
    adjusted: list[StudyPart] = []
    split_counters: dict[str, int] = {}

    for part in parts:
        kind = part.sections[0].kind
        if kind not in {"abbreviations", "symbols"} or part.line_count <= 180:
            adjusted.append(part)
            continue

        midpoint = len(part.lines) // 2
        first_lines = part.lines[:midpoint]
        second_lines = part.lines[midpoint:]
        split_counters[kind] = split_counters.get(kind, 0)

        for suffix, chunk_lines in (("A", first_lines), ("B", second_lines)):
            adjusted.append(
                StudyPart(
                    title=f"{part.title} ({suffix})",
                    sections=[
                        RawSection(
                            title=f"{part.title} ({suffix})",
                            lines=chunk_lines,
                            start_line=part.sections[0].start_line,
                            end_line=part.sections[0].start_line + len(chunk_lines) - 1,
                            start_page=page_span(chunk_lines)[0],
                            end_page=page_span(chunk_lines)[1],
                            kind=kind,
                        )
                    ],
                )
            )
    return adjusted


def split_references(parts: list[StudyPart]) -> list[StudyPart]:
    adjusted: list[StudyPart] = []
    for part in parts:
        if part.sections[0].kind != "references" or part.line_count <= 180:
            adjusted.append(part)
            continue

        midpoint = len(part.lines) // 2
        first_lines = part.lines[:midpoint]
        second_lines = part.lines[midpoint:]
        first = StudyPart(
            title=f"{part.title} (Part A)",
            sections=[
                RawSection(
                    title=f"{part.title} (Part A)",
                    lines=first_lines,
                    start_line=part.sections[0].start_line,
                    end_line=part.sections[0].start_line + len(first_lines) - 1,
                    start_page=page_span(first_lines)[0],
                    end_page=page_span(first_lines)[1],
                    kind="references",
                )
            ],
        )
        second = StudyPart(
            title=f"{part.title} (Part B)",
            sections=[
                RawSection(
                    title=f"{part.title} (Part B)",
                    lines=second_lines,
                    start_line=part.sections[0].start_line + midpoint,
                    end_line=part.sections[-1].end_line,
                    start_page=page_span(second_lines)[0],
                    end_page=page_span(second_lines)[1],
                    kind="references",
                )
            ],
        )
        adjusted.extend([first, second])
    return adjusted


def safe_slug(title: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "_", title)
    slug = slug.strip("_")
    return slug[:80] or "Section"


def infer_chapters(parts: list[StudyPart]) -> None:
    current_chapter = 1
    for part in parts:
        kind = part.sections[0].kind
        if kind in {"chapter_intro", "chapter"}:
            current_chapter = part.chapter or current_chapter
            for section in part.sections:
                section.chapter = current_chapter
            continue
        if part.chapter is not None:
            current_chapter = part.chapter
        elif kind == "references":
            part.sections[0].chapter = current_chapter
        else:
            for section in part.sections:
                section.chapter = current_chapter


def assign_filenames(parts: list[StudyPart]) -> None:
    counters: dict[str, int] = {}

    for part in parts:
        kind = part.sections[0].kind
        number = part.sections[0].section_number
        title = part.title

        if kind == "preface":
            stem = "00_Preface"
        elif kind == "abbreviations":
            key = "abbrev"
            counters[key] = counters.get(key, 0) + 1
            suffix = "_A" if counters[key] == 1 else "_B"
            stem = f"00_Abbreviations{suffix}"
        elif kind == "symbols":
            key = "symbols"
            counters[key] = counters.get(key, 0) + 1
            suffix = "_A" if counters[key] == 1 else "_B"
            stem = f"00_Symbols{suffix}"
        elif kind == "lecture_topic":
            counters["lecture"] = counters.get("lecture", 0) + 1
            stem = f"{counters['lecture']:02d}_{safe_slug(display_title(title))}"
        elif kind in {"chapter_intro", "chapter"}:
            chapter = part.chapter or 1
            stem = f"{chapter:02d}_00_Chapter_Intro"
        elif kind == "references":
            chapter = part.chapter or part.sections[0].chapter or 1
            key = f"refs_{chapter}"
            counters[key] = counters.get(key, 0) + 1
            if "Part B" in title:
                suffix = "_B"
            elif counters[key] > 1:
                suffix = "_B"
            else:
                suffix = "_A"
            stem = f"{chapter:02d}_{12 if chapter == 1 else 24}_References{suffix}"
        elif number:
            chapter = int(number.split(".")[0])
            pieces = number.split(".")
            if len(pieces) == 2:
                stem = f"{chapter:02d}_{int(pieces[1]):02d}_{safe_slug(title.split(' ', 1)[-1])}"
            else:
                joined = "_".join(f"{int(piece):02d}" for piece in pieces[1:])
                stem = f"{chapter:02d}_{joined}_{safe_slug(title.split(' ', 1)[-1])}"
        else:
            stem = f"00_{safe_slug(title)}"

        part.filename = f"{stem}.md"


def sanitized_stem(path: Path) -> str:
    slug = re.sub(r"[^\w.-]+", "_", path.stem).strip("_")
    return slug or "document"


def rewrite_image_paths(text: str, source_md: Path, output_dir: Path) -> str:
    images_dir_name = f"{sanitized_stem(source_md)}_images"
    sibling_images = source_md.parent / images_dir_name
    if not sibling_images.exists():
        legacy_images = source_md.parent / f"{source_md.stem}_images"
        if legacy_images.exists():
            sibling_images = legacy_images
            images_dir_name = legacy_images.name
    if not sibling_images.exists():
        return text

    relative_prefix = Path("..") / images_dir_name
    text = text.replace(f"({images_dir_name}/", f"({relative_prefix.as_posix()}/")
    text = text.replace(f"({images_dir_name}\\", f"({relative_prefix.as_posix()}\\")
    return text


def format_pdf_pages(start: int | None, end: int | None, *, persian: bool = True) -> str:
    if start is None or end is None:
        return "—"
    if start == end:
        return f"**pp. {start}** (1 ص)" if persian else f"pp. {start} (1 pg)"
    count = end - start + 1
    if persian:
        return f"**pp. {start}–{end}** ({count} ص)"
    return f"pp. {start}–{end} ({count} pg)"


def format_pdf_pages_plain(start: int | None, end: int | None) -> str:
    if start is None or end is None:
        return "—"
    if start == end:
        return f"pp. {start}"
    return f"pp. {start}–{end}"


def study_focus(part: StudyPart) -> str:
    return display_title(part.title)


def study_focus_fa(part: StudyPart) -> str:
    topic = study_focus(part)
    kind = part.sections[0].kind
    if kind in {"preface", "abbreviations", "symbols"}:
        return f"بخش مرجع: {topic}"
    if kind in {"chapter_intro", "chapter"}:
        return f"مقدمه فصل: {topic}"
    if kind == "references":
        return f"مراجع: {topic}"
    return f"مطالعه: {topic}"


def document_title(source_md: Path, source_pdf: Path | None) -> str:
    if source_pdf:
        return source_pdf.stem
    return source_md.stem


def group_parts_for_index(parts: list[StudyPart]) -> list[tuple[str, str, list[StudyPart]]]:
    groups: list[tuple[str, str, list[StudyPart]]] = []
    reference_parts: list[StudyPart] = []
    current_group_fa = ""
    current_group_en = ""
    current_parts: list[StudyPart] = []

    def flush_group() -> None:
        nonlocal current_parts, current_group_fa, current_group_en
        if current_parts:
            groups.append((current_group_fa, current_group_en, current_parts))
            current_parts = []

    for part in parts:
        kind = part.sections[0].kind
        if kind in {"preface", "abbreviations", "symbols"}:
            reference_parts.append(part)
            continue

        if kind == "lecture_topic":
            if current_group_fa != "موضوعات درسی":
                flush_group()
                current_group_fa = "موضوعات درسی"
                current_group_en = "Lecture topics"
            current_parts.append(part)
            continue

        if kind in {"chapter_intro", "chapter"}:
            flush_group()
            chapter = part.chapter or 1
            title = part.sections[0].title
            current_group_fa = f"فصل {chapter} — {title}"
            current_group_en = f"Chapter {chapter} — {title}"
            current_parts = [part]
            continue

        if part.chapter and not current_parts:
            current_group_fa = f"فصل {part.chapter}"
            current_group_en = f"Chapter {part.chapter}"

        current_parts.append(part)

    flush_group()
    if reference_parts:
        groups.insert(0, ("مرجع (اختیاری)", "Reference (optional)", reference_parts))
    return groups


def build_persian_index_section(
    parts: list[StudyPart],
    groups: list[tuple[str, str, list[StudyPart]]],
    pdf_name: str,
    source_md: Path,
    source_pdf: Path | None,
) -> list[str]:
    doc_title = document_title(source_md, source_pdf)
    lines = [
        f"# فهرست پارت‌های مطالعاتی — {doc_title}",
        "",
        f"منبع PDF: [`{pdf_name}`]({Path('..') / pdf_name})",
        f"منبع متن: [`{source_md.name}`]({Path('..') / source_md.name})",
        "",
        "هر فایل = **یک موضوع**. محدودهٔ صفحات نشان می‌دهد آن موضوع در PDF از کجا تا کجا آمده است.",
        "",
        f"- **صفحات PDF** → محدودهٔ پوشش موضوع در `{pdf_name}` (pp. X–Y)",
        "- **صفحات کتاب** → شماره چاپی کتاب (در صورت وجود در متن استخراج‌شده)",
        f"- *راهنمای کلی:* معمولاً هر جلسه ≈ {GUIDE_PAGES_MIN}–{GUIDE_PAGES_MAX} صفحه — فقط دید کلی، نه قاعدهٔ تقسیم",
        "",
    ]
    session_number = 0
    for group_fa, _group_en, group_parts in groups:
        lines.extend([f"## {group_fa}", ""])
        lines.append(
            f"| # | پارت | صفحات PDF (`{pdf_name}`) | صفحات کتاب | خطوط | توضیح مطالعه |"
        )
        lines.append("|---|------|-------------------------|------------|------|-------------|")
        for part in group_parts:
            session_number += 1
            focus = study_focus(part)
            focus_fa = study_focus_fa(part)
            link = f"[{focus}](parts/{part.filename})"
            lines.append(
                "| {num} | {link} | {pdf} | {book} | {lines} | {focus_fa} |".format(
                    num=session_number,
                    link=link,
                    pdf=format_pdf_pages(part.start_page, part.end_page),
                    book=part.book_pages,
                    lines=part.line_count,
                    focus_fa=focus_fa,
                )
            )
        lines.append("")
    return lines


def build_english_index_section(
    parts: list[StudyPart],
    groups: list[tuple[str, str, list[StudyPart]]],
    pdf_name: str,
    source_md: Path,
    source_pdf: Path | None,
) -> list[str]:
    doc_title = document_title(source_md, source_pdf)
    lines = [
        f"# Study Index — {doc_title}",
        "",
        f"Source PDF: [`{pdf_name}`]({Path('..') / pdf_name})",
        f"Source Markdown: [`{source_md.name}`]({Path('..') / source_md.name})",
        "",
        "Each file = **one topic**. Page ranges show where that topic is covered in the PDF.",
        "",
        f"- **PDF pages** → topic coverage in `{pdf_name}` (pp. X–Y)",
        "- **Book pages** → printed page numbers when detected in extracted text",
        f"- *Rule of thumb:* ~{GUIDE_PAGES_MIN}–{GUIDE_PAGES_MAX} pages per session — orientation only, not a split rule",
        "",
    ]
    session_number = 0
    for _group_fa, group_en, group_parts in groups:
        lines.extend([f"## {group_en}", ""])
        lines.append(
            f"| # | Part | PDF pages (`{pdf_name}`) | Book pages | Lines | Study focus |"
        )
        lines.append("|---|------|------------------------|------------|-------|-------------|")
        for part in group_parts:
            session_number += 1
            focus = study_focus(part)
            link = f"[{focus}](parts/{part.filename})"
            lines.append(
                "| {num} | {link} | {pdf} | {book} | {lines} | {focus} |".format(
                    num=session_number,
                    link=link,
                    pdf=format_pdf_pages(part.start_page, part.end_page, persian=False),
                    book=part.book_pages,
                    lines=part.line_count,
                    focus=focus,
                )
            )
        lines.append("")
    return lines


def build_index(
    parts: list[StudyPart],
    source_md: Path,
    source_pdf: Path | None,
    output_dir: Path,
    language: str,
) -> str:
    pdf_name = source_pdf.name if source_pdf else source_md.with_suffix(".pdf").name
    groups = group_parts_for_index(parts)
    lines = build_persian_index_section(parts, groups, pdf_name, source_md, source_pdf)
    lines.extend(["---", ""])
    lines.extend(build_english_index_section(parts, groups, pdf_name, source_md, source_pdf))
    lines.extend(["---", "", f"## راهنمای سریع / Quick Reference — {len(parts)} sessions", ""])
    lines.append("| جلسه | Session | موضوع (FA) | Topic (EN) | PDF | کتاب / Book | فایل / File |")
    lines.append("|---:|---:|---|---|---|---|---|")
    for index, part in enumerate(parts, start=1):
        lines.append(
            f"| {index} | {index} | {study_focus_fa(part)} | {study_focus(part)} | "
            f"{format_pdf_pages_plain(part.start_page, part.end_page)} | "
            f"{part.book_pages} | `{part.filename}` |"
        )
    lines.append("")
    return "\n".join(lines)


def build_segmentation_preview(
    parts: list[StudyPart],
    *,
    granularity: str,
    source_md: Path,
    source_pdf: Path | None,
) -> str:
    line_counts = [part.line_count for part in parts]
    pdf_starts = [part.start_page for part in parts if part.start_page is not None]
    pdf_ends = [part.end_page for part in parts if part.end_page is not None]
    groups = group_parts_for_index(parts)
    page_counts = [part_page_count(part) for part in parts if part_page_count(part) > 0]

    lines = [
        "# پیش‌نمایش تقسیم‌بندی / Segmentation Preview",
        "",
        f"- سند / Document: `{source_md.name}`",
        f"- PDF: `{source_pdf.name if source_pdf else source_md.with_suffix('.pdf').name}`",
        f"- دانه‌بندی / Granularity: **{granularity}** (عمق تقسیم موضوعی: "
        f"{'ریز' if granularity == 'fine' else 'درشت' if granularity == 'coarse' else 'معمولی'})",
        "- اصل تقسیم: **موضوع** + محدودهٔ صفحات (pp. X–Y)",
        f"- راهنمای کلی صفحات: ~{GUIDE_PAGES_MIN}–{GUIDE_PAGES_MAX} (فقط دید کلی)",
        f"- تعداد پارت‌ها / Parts: **{len(parts)}**",
        f"- خطوط هر پارت / Lines: min {min(line_counts)} / avg {sum(line_counts) // len(line_counts)} / "
        f"max {max(line_counts)}",
    ]
    if page_counts:
        lines.append(
            f"- صفحات هر پارت / Pages: min {min(page_counts)} / "
            f"avg {sum(page_counts) // len(page_counts)} / max {max(page_counts)}"
        )
    if pdf_starts and pdf_ends:
        lines.append(
            f"- پوشش PDF: pp. {min(pdf_starts)}–{max(pdf_ends)} "
            f"({max(pdf_ends) - min(pdf_starts) + 1} pages)"
        )
    lines.extend(["", "## گروه‌ها / Groups", ""])
    for group_fa, group_en, group_parts in groups:
        lines.append(f"- **{group_fa} / {group_en}**: {len(group_parts)} parts")
    lines.extend(["", "## نمونه پارت‌ها / Sample parts (first 10)", ""])
    lines.append("| # | فایل | PDF pages | Lines | Topic (EN) |")
    lines.append("|---|------|-----------|-------|------------|")
    for index, part in enumerate(parts[:10], start=1):
        pages = part_page_count(part)
        page_label = format_pdf_pages_plain(part.start_page, part.end_page)
        if pages:
            page_label = f"{page_label} ({pages} pg)"
        lines.append(
            f"| {index} | `{part.filename}` | {page_label} | "
            f"{part.line_count} | {study_focus(part)} |"
        )
    if len(parts) > 10:
        lines.extend(["", "## انتهای فهرست / Last 5 parts", ""])
        lines.append("| # | فایل | PDF pages | Lines | Topic (EN) |")
        lines.append("|---|------|-----------|-------|------------|")
        for index, part in enumerate(parts[-5:], start=len(parts) - 4):
            pages = part_page_count(part)
            page_label = format_pdf_pages_plain(part.start_page, part.end_page)
            if pages:
                page_label = f"{page_label} ({pages} pg)"
            lines.append(
                f"| {index} | `{part.filename}` | {page_label} | "
                f"{part.line_count} | {study_focus(part)} |"
            )
    lines.extend(
        [
            "",
            "---",
            "",
            "**تایید می‌کنید؟**",
            "- `تایید` / `approve` → ادامه به مایندمپ",
            "- `درشت‌تر` / `coarse` → پارت‌های بزرگ‌تر و کمتر",
            "- `ریزتر` / `fine` → پارت‌های کوچک‌تر و بیشتر",
            "",
            f"ایندکس کامل: `STUDY_INDEX.md` و `STUDY_INDEX.pdf`",
        ]
    )
    return "\n".join(lines)


def export_index_pdf(index_md: Path, output_pdf: Path) -> None:
    script_dir = Path(__file__).resolve().parent
    export_script = script_dir / "export_study_index_pdf.py"
    if not export_script.exists():
        return

    import subprocess
    import sys

    venv_python = Path.home() / ".grok/skills/pdf-to-markdown/.venv/bin/python"
    python_bin = str(venv_python) if venv_python.exists() else sys.executable
    subprocess.run(
        [python_bin, str(export_script), "--index-md", str(index_md), "--output", str(output_pdf)],
        check=True,
    )


def segment_markdown(
    source_md: Path,
    output_dir: Path,
    source_pdf: Path | None = None,
    language: str = "Persian",
    *,
    granularity: str = "normal",
    export_pdf: bool = True,
) -> list[StudyPart]:
    cfg = apply_granularity(granularity)
    text = source_md.read_text(encoding="utf-8")
    source_lines = text.splitlines()
    raw_sections = split_raw_sections(source_lines)
    if should_use_lecture_split(raw_sections, len(source_lines)):
        raw_sections = split_lecture_sections(source_lines)
    for section in raw_sections:
        if section.kind == "chapter_intro" and section.chapter is None:
            section.chapter = 1
    if raw_sections and raw_sections[0].kind != "lecture_topic":
        raw_sections = explode_nested_sections(raw_sections, source_lines)
    if raw_sections and raw_sections[0].kind == "lecture_topic":
        raw_sections = split_large_lecture_sections(raw_sections, source_lines)
    else:
        raw_sections = subdivide_large_sections(raw_sections, source_lines)
    parts = merge_small_sections(raw_sections)
    parts = split_large_parts(parts, source_lines)
    parts = split_oversized_study_parts(parts)
    parts = split_long_front_matter(parts)
    parts = split_references(parts)
    infer_chapters(parts)
    assign_filenames(parts)

    parts_dir = output_dir / "parts"
    if parts_dir.exists():
        for old_file in parts_dir.glob("*.md"):
            old_file.unlink()
    parts_dir.mkdir(parents=True, exist_ok=True)

    for part in parts:
        body = rewrite_image_paths(part.text, source_md, parts_dir)
        if not body.lstrip().startswith("#"):
            body = f"# {part.title}\n\n{body}"
        (parts_dir / part.filename).write_text(body, encoding="utf-8")

    index_text = build_index(parts, source_md, source_pdf, output_dir, language)
    index_md = output_dir / "STUDY_INDEX.md"
    index_md.write_text(index_text, encoding="utf-8")

    preview_text = build_segmentation_preview(
        parts,
        granularity=cfg.label,
        source_md=source_md,
        source_pdf=source_pdf,
    )
    (output_dir / "SEGMENTATION_PREVIEW.md").write_text(preview_text, encoding="utf-8")

    if export_pdf:
        try:
            export_index_pdf(index_md, output_dir / "STUDY_INDEX.pdf")
        except Exception as exc:
            print(f"WARNING: Could not export STUDY_INDEX.pdf: {exc}", flush=True)

    return parts


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Split extracted PDF markdown into study parts with page-aware STUDY_INDEX.md"
    )
    parser.add_argument("--input", type=Path, required=True, help="Source markdown file")
    parser.add_argument("--output-dir", type=Path, required=True, help="Output directory")
    parser.add_argument("--source-pdf", type=Path, help="Original PDF path for index links")
    parser.add_argument("--language", default="Persian", help="Language note for index descriptions")
    parser.add_argument(
        "--granularity",
        choices=sorted(GRANULARITY_PRESETS),
        default="normal",
        help="Topic split depth: fine (more subtopics), normal, coarse (major topics only)",
    )
    parser.add_argument(
        "--no-pdf",
        action="store_true",
        help="Skip STUDY_INDEX.pdf export",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if not args.input.exists():
        raise SystemExit(f"Input not found: {args.input}")

    parts = segment_markdown(
        source_md=args.input.resolve(),
        output_dir=args.output_dir.resolve(),
        source_pdf=args.source_pdf.resolve() if args.source_pdf else None,
        language=args.language,
        granularity=args.granularity,
        export_pdf=not args.no_pdf,
    )

    output_dir = args.output_dir.resolve()
    print(f"Created {len(parts)} study parts in {output_dir / 'parts'}")
    print(f"Index (md) : {output_dir / 'STUDY_INDEX.md'}")
    print(f"Index (pdf): {output_dir / 'STUDY_INDEX.pdf'}")
    print(f"Preview    : {output_dir / 'SEGMENTATION_PREVIEW.md'}")
    print(f"Granularity: {args.granularity}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())