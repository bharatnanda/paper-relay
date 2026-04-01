import pytest
from app.services.pdf_parser import PDFParser


class TestPDFParser:

    @pytest.fixture
    def parser(self):
        return PDFParser()

    def test_extract_inline_formula(self, parser):
        formulas = parser._extract_formulas("The equation $E = mc^2$ is famous.")
        assert len(formulas) == 1
        assert formulas[0]["latex"] == "E = mc^2"

    def test_extract_display_formula(self, parser):
        formulas = parser._extract_formulas("Consider:\\[E = mc^2\\]")
        assert len(formulas) == 1
        assert formulas[0]["type"] == "display"

    def test_extract_equation_like_line(self, parser):
        formulas = parser._extract_formulas(
            "We score each candidate.\n"
            "score = lambda * reward + (1 - lambda) * relevance\n"
            "Higher values are better."
        )
        assert len(formulas) == 1
        assert formulas[0]["type"] == "equation_line"
        assert "We score each candidate." in formulas[0]["context"]
        assert "Higher values are better." in formulas[0]["context"]

    def test_extract_sections(self, parser):
        text = "Abstract\nThis is the abstract.\nIntroduction\nThis is the intro.\nMethod\nThis is the method."
        sections = parser._extract_sections(text)
        assert len(sections) >= 3
        assert sections[0]["title"] == "Abstract"
        assert "This is the method." in sections[2]["content"]

    def test_extract_figure_caption_with_context(self, parser):
        lines = [
            "We evaluate the system against prior work.",
            "Figure 2: Accuracy versus retrieval depth",
            "The proposed method outperforms the baseline in all settings.",
            "This gap is largest at depth 10.",
        ]
        figures = parser._extract_figure_captions(lines, 3, "Results")
        assert len(figures) == 1
        assert figures[0]["label"] == "Figure 2"
        assert figures[0]["section_title"] == "Results"
        assert "We evaluate the system" in figures[0]["context_before"]
        assert "outperforms the baseline" in figures[0]["context_after"]
        assert "Accuracy versus retrieval depth" in figures[0]["context"]

    def test_extract_tables_with_context_and_header(self, parser):
        class FakePage:
            def extract_tables(self):
                return [
                    [
                        ["Model", "Accuracy"],
                        ["Baseline", "73.1"],
                        ["Ours", "81.4"],
                    ]
                ]

        lines = [
            "We compare against strong baselines.",
            "Table 1: Main results on the benchmark.",
            "Model Accuracy",
            "Baseline 73.1",
            "Ours 81.4",
            "Higher is better.",
        ]

        tables = parser._extract_tables(FakePage(), lines, 1, "Experiments")
        assert len(tables) == 1
        assert tables[0]["title"] == "Table 1: Main results on the benchmark."
        assert tables[0]["section_title"] == "Experiments"
        assert tables[0]["header"] == ["Model", "Accuracy"]
        assert tables[0]["row_count"] == 3
        assert tables[0]["column_count"] == 2
        assert "We compare against strong baselines." in tables[0]["context_before"]
        assert "Higher is better." in tables[0]["context_after"]
        assert "Main results on the benchmark" in tables[0]["context"]

    def test_extract_references(self, parser):
        refs = parser._extract_references("As shown in [1] and [2, 3]")
        assert len(refs) == 2
        assert refs[0]["citation"] == "1"
