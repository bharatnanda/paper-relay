import pdfplumber
from typing import List, Dict, Any
import re
from io import BytesIO


class PDFParser:
    MIN_TEXT_LENGTH = 500  # Minimum characters for valid paper
    GARBLED_THRESHOLD = 0.15  # Max 15% non-printable/replacement characters
    SECTION_HEADING_RE = re.compile(
        r'^((\d+(\.\d+)*)\s+)?'
        r'(abstract|introduction|background|related work|preliminaries|problem setup|method|methods|approach|'
        r'model|architecture|training|experimental setup|experiments|evaluation|results|analysis|ablation|'
        r'discussion|limitations|conclusion|conclusions|appendix)\s*:?\s*$',
        re.I,
    )
    EQUATION_LINE_RE = re.compile(
        r'(\b(argmax|argmin|softmax|loss|objective|reward|score|probability)\b|[=≈≤≥∈∑∏λμσθαβγΔ])',
        re.I,
    )

    def __init__(self):
        self.latex_pattern = re.compile(r'\$(.+?)\$|\\\[(.+?)\\\]')

    def parse_pdf(self, pdf_bytes: bytes) -> Dict[str, Any]:
        result = {"text": "", "sections": [], "formulas": [], "references": [], "figure_captions": [], "tables": []}

        try:
            with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
                current_section_title = "Paper overview"
                for page_num, page in enumerate(pdf.pages):
                    text = page.extract_text() or ""
                    result["text"] += f"\n\n{text}"
                    lines = text.split('\n')
                    page_sections = self._detect_page_sections(lines)
                    if page_sections:
                        current_section_title = page_sections[-1]

                    formulas = self._extract_formulas(text)
                    result["formulas"].extend(formulas)
                    result["figure_captions"].extend(
                        self._extract_figure_captions(lines, page_num, current_section_title)
                    )
                    result["tables"].extend(
                        self._extract_tables(page, lines, page_num, current_section_title)
                    )

                result["references"] = self._extract_references(result["text"])
                result["sections"] = self._extract_sections(result["text"])

            # VALIDATION: Check text quality AFTER extraction
            validation = self._validate_extracted_text(result["text"])
            if not validation["valid"]:
                result["error"] = validation["reason"]
                result["text"] = ""  # Clear invalid text
                result["sections"] = []  # Clear sections too

        except Exception as e:
            result["error"] = str(e)

        return result

    def _validate_extracted_text(self, text: str) -> Dict[str, Any]:
        """Validate extracted text quality.
        
        Checks:
        1. Minimum text length (500 chars) - filters empty/near-empty PDFs
        2. Garbled text ratio (max 30% non-alphanumeric) - filters corrupted PDFs
        
        Returns:
            Dict with 'valid' boolean and 'reason' string (if invalid)
        """
        if len(text) < self.MIN_TEXT_LENGTH:
            return {
                "valid": False,
                "reason": f"Extracted text too short ({len(text)} chars, minimum {self.MIN_TEXT_LENGTH})"
            }

        # Check for garbled text using non-printable/replacement characters instead of punishing
        # normal academic punctuation, citations, and math-heavy text.
        suspicious_count = sum(
            1
            for c in text
            if (not c.isprintable() and not c.isspace()) or c == "\ufffd"
        )
        garbled_ratio = (suspicious_count / len(text)) if text else 0

        if garbled_ratio > self.GARBLED_THRESHOLD:
            return {
                "valid": False,
                "reason": f"Text appears garbled ({garbled_ratio:.1%} non-printable characters)"
            }

        return {"valid": True, "reason": None}

    def _extract_formulas(self, text: str) -> List[Dict[str, Any]]:
        formulas = []
        for match in re.finditer(r'\$([^\$]+)\$', text):
            formulas.append({"type": "inline", "latex": match.group(1),
                           "context": text[max(0,match.start()-180):min(len(text),match.end()+180)]})
        for match in re.finditer(r'\\\[(.+?)\\\]', text, re.DOTALL):
            formulas.append({"type": "display", "latex": match.group(1).strip(),
                           "context": text[max(0,match.start()-220):min(len(text),match.end()+220)]})
        formulas.extend(self._extract_equation_like_lines(text))
        deduped = []
        seen = set()
        for formula in formulas:
            key = formula.get("latex", "").strip()
            if not key or key in seen:
                continue
            seen.add(key)
            deduped.append(formula)
        return deduped

    def _extract_equation_like_lines(self, text: str) -> List[Dict[str, Any]]:
        formulas = []
        lines = text.splitlines()
        for index, line in enumerate(lines):
            candidate = " ".join(line.strip().split())
            if len(candidate) < 10 or len(candidate) > 180:
                continue
            if candidate.endswith(".") and "=" not in candidate:
                continue
            if not self.EQUATION_LINE_RE.search(candidate):
                continue
            alpha_numeric = sum(char.isalnum() for char in candidate)
            if alpha_numeric < 6:
                continue
            if candidate.count(" ") > 24:
                continue
            context_window = [
                " ".join(raw.strip().split())
                for raw in lines[max(0, index - 2):min(len(lines), index + 3)]
                if raw.strip()
            ]
            formulas.append(
                {
                    "type": "equation_line",
                    "latex": candidate,
                    "context": " ".join(context_window).strip() or candidate,
                }
            )
        return formulas

    def _extract_sections(self, text: str) -> List[Dict[str, Any]]:
        sections: List[Dict[str, Any]] = []
        current_title = "Paper overview"
        current_lines: List[str] = []

        def flush_section():
            content = "\n".join(current_lines).strip()
            if not content:
                return
            sections.append({"title": current_title, "page": None, "content": content})

        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                if current_lines and current_lines[-1] != "":
                    current_lines.append("")
                continue

            if self.SECTION_HEADING_RE.match(line) and len(line) <= 80:
                if current_lines:
                    flush_section()
                    current_lines = []
                current_title = line
                continue

            current_lines.append(line)

        if current_lines:
            flush_section()

        if sections:
            return sections[:12]

        normalized = " ".join(text.split())
        chunks = []
        chunk_size = 4500
        for index in range(0, len(normalized), chunk_size):
            chunk = normalized[index:index + chunk_size].strip()
            if chunk:
                chunks.append(
                    {
                        "title": f"Chunk {len(chunks) + 1}",
                        "page": None,
                        "content": chunk,
                    }
                )
        return chunks[:8]

    def _detect_page_sections(self, lines: List[str]) -> List[str]:
        return [
            line.strip()
            for line in lines
            if self.SECTION_HEADING_RE.match(line.strip()) and len(line.strip()) <= 80
        ]

    def _extract_references(self, text: str) -> List[Dict[str, Any]]:
        return [{"citation": m.group(1), "position": m.start()}
                for m in re.finditer(r'\[([^\]]+)\]', text)]

    def _extract_figure_captions(self, lines: List[str], page_num: int, section_title: str) -> List[Dict[str, Any]]:
        captions = []
        caption_pattern = re.compile(r'^(Figure|Fig\.)\s*(\d+)\s*[:.\s-]+(.+)', re.I)

        for index, raw_line in enumerate(lines):
            line = raw_line.strip()
            match = caption_pattern.match(line)
            if not match:
                continue

            caption = line
            continuation = []
            for next_line in lines[index + 1:index + 4]:
                candidate = next_line.strip()
                if not candidate:
                    break
                if re.match(r'^(Figure|Fig\.|Table)\s*\d+', candidate, re.I):
                    break
                if len(candidate) < 6:
                    break
                continuation.append(candidate)
            if continuation:
                caption = " ".join([caption, *continuation])

            context = self._build_artifact_context(lines, index, index + len(continuation), caption)

            captions.append(
                {
                    "label": f"{match.group(1)} {match.group(2)}",
                    "caption": caption,
                    "page": page_num,
                    "section_title": section_title,
                    "context_before": context["before"],
                    "context_after": context["after"],
                    "context": context["combined"],
                }
            )

        return captions

    def _extract_tables(
        self,
        page: pdfplumber.page.Page,
        lines: List[str],
        page_num: int,
        section_title: str,
    ) -> List[Dict[str, Any]]:
        tables = []
        table_titles = [
            {"title": line.strip(), "index": index}
            for index, line in enumerate(lines)
            if re.match(r'^Table\s*\d+[:.\s-]+', line.strip(), re.I)
        ]

        try:
            extracted_tables = page.extract_tables() or []
        except Exception:
            extracted_tables = []

        for index, rows in enumerate(extracted_tables):
            normalized_rows = []
            for row in rows or []:
                cells = [cell.strip() if isinstance(cell, str) else "" for cell in (row or [])]
                if any(cells):
                    normalized_rows.append(cells)

            if not normalized_rows:
                continue

            title_entry = table_titles[index] if index < len(table_titles) else None
            title = title_entry["title"] if title_entry else f"Table on page {page_num + 1}"
            title_index = title_entry["index"] if title_entry else self._find_table_anchor_index(lines, normalized_rows)
            context = self._build_artifact_context(lines, title_index, title_index, title)
            header = normalized_rows[0] if normalized_rows else []

            tables.append(
                {
                    "title": title,
                    "page": page_num,
                    "section_title": section_title,
                    "header": header,
                    "rows": normalized_rows[:12],
                    "row_count": len(normalized_rows),
                    "column_count": max((len(row) for row in normalized_rows), default=0),
                    "context_before": context["before"],
                    "context_after": context["after"],
                    "context": context["combined"],
                }
            )

        return tables

    def _build_artifact_context(
        self,
        lines: List[str],
        start_index: int,
        end_index: int,
        anchor_text: str,
        window: int = 4,
    ) -> Dict[str, str]:
        safe_start = max(start_index, 0)
        safe_end = max(end_index, safe_start)
        before = self._collapse_context_lines(lines[max(0, safe_start - window):safe_start])
        after = self._collapse_context_lines(lines[safe_end + 1:safe_end + 1 + window])
        combined_parts = [part for part in (before, anchor_text.strip(), after) if part]
        return {
            "before": before,
            "after": after,
            "combined": " ".join(combined_parts).strip(),
        }

    def _collapse_context_lines(self, lines: List[str]) -> str:
        cleaned = []
        for raw_line in lines:
            line = " ".join(raw_line.strip().split())
            if not line:
                continue
            if self.SECTION_HEADING_RE.match(line):
                continue
            cleaned.append(line)
        return " ".join(cleaned).strip()

    def _find_table_anchor_index(self, lines: List[str], rows: List[List[str]]) -> int:
        if not rows:
            return 0
        candidates = [cell.strip() for cell in rows[0] if isinstance(cell, str) and cell.strip()]
        for index, raw_line in enumerate(lines):
            line = raw_line.strip()
            if not line:
                continue
            if any(candidate and candidate in line for candidate in candidates[:2]):
                return index
        return 0
