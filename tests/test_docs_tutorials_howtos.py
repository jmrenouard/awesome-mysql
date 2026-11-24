"""Executable tests validating awesome-mysql Jekyll config, entries, SQL/bash fences, Diataxis, STE, and Mermaid."""

from __future__ import annotations

import os
import pathlib
import re
import shutil
import subprocess
import unittest
from urllib.parse import unquote

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / "docs"
REQUIRED_QUADRANTS = ("01-tutorials", "02-how-to-guides", "03-reference", "04-explanation")

FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")
LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)\n]+)\)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
ASCII_BOX_RE = re.compile(r"[┌┐└┘├┤┬┴┼═║╔╗╚╝]|^\s*\+[-+]+\+\s*$", re.M)
MERMAID_TYPES = ("graph ", "flowchart ", "sequenceDiagram", "classDiagram", "stateDiagram", "erDiagram")
AWESOME_ENTRY_RE = re.compile(r"^-\s+\[([^\]]+)\]\((https?://[^)\s]+)\)\s+-\s+.+$")


def _strip_inline_code(line: str) -> str:
    """Mask CommonMark inline code spans so doc examples like `[item](link)` do not trigger link checks."""
    return re.sub(r"`[^`]*`", " ", line)


def _github_anchor_slug(heading_text: str) -> str:
    cleaned = re.sub(r"`([^`]+)`", r"\1", heading_text.strip().lower())
    out: list[str] = []
    for ch in cleaned:
        if ch.isalnum() or ch == "_":
            out.append(ch)
        elif ch in (" ", "-"):
            out.append("-")
    return "".join(out)


def _split_fenced_blocks(text: str) -> tuple[list[tuple[int, str]], list[tuple[int, str, str]], bool]:
    non_code: list[tuple[int, str]] = []
    blocks: list[tuple[int, str, str]] = []
    in_fence = False
    fence_char = ""
    fence_len = 0
    fence_lang = ""
    fence_start = 0
    buf: list[str] = []

    for lineno, line in enumerate(text.splitlines(), 1):
        stripped = line.lstrip()
        m = FENCE_RE.match(line)
        if not in_fence:
            if m:
                marker = m.group(1)
                in_fence = True
                fence_char = marker[0]
                fence_len = len(marker)
                fence_lang = stripped[fence_len:].strip().split()[0].lower() if stripped[fence_len:].strip() else ""
                fence_start = lineno
                buf = []
                continue
            non_code.append((lineno, line))
        else:
            if stripped.startswith(fence_char * fence_len) and stripped[fence_len:].strip() == "":
                blocks.append((fence_start, fence_lang, "\n".join(buf)))
                in_fence = False
                buf = []
            else:
                buf.append(line)

    return non_code, blocks, in_fence


class TestJekyllEntriesAndSnippets(unittest.TestCase):
    """Validate Jekyll config/layout safety, awesome-list formatting, SQL/bash fences, and git history."""

    def test_jekyll_config_and_static_assets(self) -> None:
        if yaml is None:
            self.skipTest("PyYAML not installed in current Python runtime.")

        cfg = yaml.safe_load((REPO_ROOT / "_config.yml").read_text(encoding="utf-8"))
        self.assertEqual(cfg["title"], "Awesome MySQL")
        self.assertEqual(cfg["markdown"], "kramdown")
        self.assertIn("README.md", cfg["exclude"])
        self.assertIn("tests/", cfg["exclude"])

        layout = (REPO_ROOT / "_layouts" / "default.html").read_text(encoding="utf-8")
        for asset in ("css/normalize.css", "css/syntax.css", "css/solo.css", "_includes/head.html", "_includes/scripts.html"):
            self.assertTrue((REPO_ROOT / asset).is_file(), f"Missing Jekyll asset: {asset}")
        self.assertIn("css/solo.css", layout)

        # Nested docs/ files must omit layout: default so relative CSS paths in default.html never break
        for md in sorted(DOCS_DIR.rglob("*.md")):
            txt = md.read_text(encoding="utf-8")
            self.assertFalse(txt.lstrip().startswith("---\nlayout: default"), f"{md.relative_to(REPO_ROOT)} uses relative layout")

    def test_awesome_list_entries_and_archived_history(self) -> None:
        readme_lines = (REPO_ROOT / "README.md").read_text(encoding="utf-8").splitlines()
        entries = [ln.strip() for ln in readme_lines if re.match(r"^-\s+\[[^\]]+\]\(https?://", ln.strip())]
        self.assertGreaterEqual(len(entries), 10)
        for entry in entries:
            self.assertRegex(entry, AWESOME_ENTRY_RE, f"Invalid awesome-list entry syntax: {entry}")
            self.assertTrue(entry.endswith("."), f"Awesome entry must end with period: {entry}")

        git_bin = shutil.which("git")
        if git_bin and (REPO_ROOT / ".git").exists():
            hist = subprocess.run(
                [git_bin, "cat-file", "-e", "ae5cf0a:index.md"],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            if hist.returncode == 0:
                show = subprocess.run(
                    [git_bin, "show", "ae5cf0a:index.md"],
                    cwd=REPO_ROOT,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    check=True,
                )
                self.assertIn("## Analysis", show.stdout)
                self.assertIn("## Toolkits", show.stdout)
                self.assertEqual(len(re.findall(r"^## ", show.stdout, re.M)), 21)

    def test_documented_sql_and_bash_fences(self) -> None:
        bash_bin = shutil.which("bash") if os.name == "posix" else None
        sql_checked = 0
        bash_checked = 0

        for md in (REPO_ROOT / "README.md", *sorted(DOCS_DIR.rglob("*.md"))):
            _, blocks, _ = _split_fenced_blocks(md.read_text(encoding="utf-8"))
            for start_line, lang, code in blocks:
                if lang == "sql":
                    stmts = [s.strip() for s in code.splitlines() if s.strip() and not s.strip().startswith("--")]
                    self.assertTrue(stmts, f"{md.name}:{start_line}: empty SQL block")
                    for stmt in stmts:
                        self.assertTrue(stmt.endswith(";"), f"{md.name}:{start_line}: SQL statement missing ';': {stmt}")
                        self.assertEqual(stmt.count("("), stmt.count(")"), f"{md.name}:{start_line}: unbalanced parens")
                        self.assertRegex(stmt.upper(), r"^(EXPLAIN|SELECT|SHOW|USE|DESCRIBE)\b")
                        sql_checked += 1
                elif lang in ("bash", "sh") and bash_bin:
                    # Validate syntax of runnable shell blocks cleanly with bash -n
                    chk = subprocess.run(
                        [bash_bin, "-n"],
                        input=code,
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    self.assertEqual(chk.returncode, 0, f"{md.name}:{start_line}: bash -n error: {chk.stderr}")
                    bash_checked += 1

        self.assertGreaterEqual(sql_checked, 2)
        if bash_bin:
            self.assertGreaterEqual(bash_checked, 4)


class TestDocsDiataxisSTEAndDiagrams(unittest.TestCase):
    """Validate Diataxis layout, ASD-STE100 rules, links, Mermaid, and English isolation."""

    def test_diataxis_structure_ste_and_english_isolation(self) -> None:
        self.assertTrue((DOCS_DIR / "index.md").is_file())
        for q in REQUIRED_QUADRANTS:
            qdir = DOCS_DIR / q
            self.assertTrue(qdir.is_dir())
            self.assertTrue((qdir / "index.md").is_file())
            self.assertTrue([p for p in qdir.glob("*.md") if p.name != "index.md"])

        howtos = [p for p in (DOCS_DIR / "02-how-to-guides").glob("*.md") if p.name != "index.md"]
        for md in howtos:
            non_code, _, _ = _split_fenced_blocks(md.read_text(encoding="utf-8"))
            body = "\n".join(ln for _, ln in non_code)
            self.assertRegex(body, r"(?im)^##\s+Validation")
            self.assertRegex(body, r"(?im)^##\s+Rollback")
            for lineno, line in non_code:
                s = line.strip()
                if not s or s.startswith(("#", "|", "NOTE:", ">")):
                    continue
                self.assertNotIn(";", s, f"{md.name}:{lineno}: semicolon violates STE")
                self.assertNotRegex(s, r"\b(should|would|may|might|shall)\b")
                clean = re.sub(r"`[^`]+`|\[([^\]]+)\]\([^)]+\)", r"\1", re.sub(r"^\d+\.\s+|^-\s+", "", s))
                for sent in [p.strip() for p in re.split(r"(?<=[.!?])\s+", clean) if p.strip()]:
                    words = [w for w in sent.split() if re.search(r"[A-Za-z0-9]", w)]
                    self.assertLessEqual(len(words), 20, f"{md.name}:{lineno} > 20 words: {sent}")

        for md in sorted(REPO_ROOT.rglob("*.md")):
            non_code, _, _ = _split_fenced_blocks(md.read_text(encoding="utf-8"))
            prose = "\n".join(_strip_inline_code(ln) for _, ln in non_code)
            self.assertNotRegex(prose, r"\b(Voici|Étape|Procédure|Vérification|dépôt)\b")

    def test_links_fences_zero_ascii_and_mermaid(self) -> None:
        errors: list[str] = []
        mermaid_count = 0
        for md in sorted(REPO_ROOT.rglob("*.md")):
            rel = md.relative_to(REPO_ROOT).as_posix()
            txt = md.read_text(encoding="utf-8")
            non_code, blocks, unclosed = _split_fenced_blocks(txt)
            if unclosed:
                errors.append(f"{rel}: unclosed fenced block")
            if ASCII_BOX_RE.search(txt):
                errors.append(f"{rel}: ASCII/Unicode box diagram found")

            slugs = {_github_anchor_slug(m.group(2)) for _, ln in non_code if (m := HEADING_RE.match(ln))}
            for lineno, raw_line in non_code:
                for m in LINK_RE.finditer(_strip_inline_code(raw_line)):
                    tgt = m.group(1).strip().split()[0]
                    if tgt.startswith(("http://", "https://", "mailto:")):
                        continue
                    if tgt.startswith("#"):
                        if tgt[1:] not in slugs:
                            errors.append(f"{rel}:{lineno}: broken anchor {tgt}")
                        continue
                    fpart, _, frag = tgt.partition("#")
                    resolved = (md.parent / unquote(fpart)).resolve()
                    if not (resolved.is_file() or resolved.is_dir()):
                        errors.append(f"{rel}:{lineno}: missing link target {tgt}")
                    elif frag and resolved.is_file():
                        t_nc, _, _ = _split_fenced_blocks(resolved.read_text(encoding="utf-8"))
                        t_slugs = {_github_anchor_slug(hm.group(2)) for _, ln in t_nc if (hm := HEADING_RE.match(ln))}
                        if frag not in t_slugs:
                            errors.append(f"{rel}:{lineno}: broken target anchor #{frag}")

            for start_line, lang, code in blocks:
                first_tok = code.strip().splitlines()[0].strip() if code.strip() else ""
                if lang == "mermaid":
                    mermaid_count += 1
                    if not any(first_tok.startswith(pfx) for pfx in MERMAID_TYPES):
                        errors.append(f"{rel}:{start_line}: invalid Mermaid header '{first_tok}'")
                    if code.count("[") != code.count("]") or code.count("{") != code.count("}"):
                        errors.append(f"{rel}:{start_line}: unbalanced Mermaid brackets")
                elif any(first_tok.startswith(pfx) for pfx in MERMAID_TYPES):
                    errors.append(f"{rel}:{start_line}: untagged Mermaid block")

            for lineno, line in enumerate(txt.splitlines(), 1):
                if line.lstrip().startswith("```mermaid") and not line.startswith("```mermaid"):
                    errors.append(f"{rel}:{lineno}: indented ```mermaid fence")

        self.assertGreaterEqual(mermaid_count, 4)
        self.assertEqual(errors, [], "\n".join(errors))


if __name__ == "__main__":
    unittest.main()
