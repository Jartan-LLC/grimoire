"""Unit tests for generate-codex.py's pure functions.

Loaded via importlib rather than `import generate_codex` -- the source file's
name has a hyphen, which a plain import statement cannot spell. Covers the
parsing and rendering functions that carry real logic (Codex's
deny_unknown_fields makes a malformed render take down the whole role file);
the filesystem-walking functions (collect_targets, find_orphans,
find_divergent_copies, main) run end to end against the real repo every time
`make verify` invokes --check, which is its own regression coverage.
"""

import importlib.util
import pathlib
import unittest

MODULE_PATH = pathlib.Path(__file__).resolve().parent / "generate-codex.py"
_spec = importlib.util.spec_from_file_location("generate_codex", MODULE_PATH)
generate_codex = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(generate_codex)


class ParseFrontmatterTest(unittest.TestCase):
    def test_splits_scalar_fields_and_body(self):
        text = (
            "---\n"
            "name: foo\n"
            "description: bar baz\n"
            "---\n"
            "\n"
            "Body text here.\n"
        )
        fields, body = generate_codex.parse_frontmatter(text, "x.md")
        self.assertEqual(fields, {"name": "foo", "description": "bar baz"})
        self.assertEqual(body, "Body text here.")

    def test_parses_a_list_field(self):
        text = (
            "---\n"
            "name: foo\n"
            "skills:\n"
            "  - a\n"
            "  - b:c\n"
            "---\n"
            "Body.\n"
        )
        fields, _ = generate_codex.parse_frontmatter(text, "x.md")
        self.assertEqual(fields["skills"], ["a", "b:c"])

    def test_missing_opening_delimiter_names_the_path(self):
        with self.assertRaises(ValueError) as ctx:
            generate_codex.parse_frontmatter("name: foo\n---\n", "x.md")
        self.assertIn("x.md", str(ctx.exception))
        self.assertIn("open", str(ctx.exception))

    def test_missing_closing_delimiter_names_the_path(self):
        with self.assertRaises(ValueError) as ctx:
            generate_codex.parse_frontmatter("---\nname: foo\n", "x.md")
        self.assertIn("x.md", str(ctx.exception))
        self.assertIn("closing", str(ctx.exception))


class QualifyTest(unittest.TestCase):
    def test_prefixes_a_bare_skill_name(self):
        self.assertEqual(generate_codex.qualify("code-hygiene", "praxis"), "praxis:code-hygiene")

    def test_leaves_an_already_qualified_name_alone(self):
        self.assertEqual(
            generate_codex.qualify("gitwise:github-conventions", "praxis"),
            "gitwise:github-conventions",
        )


class DisplayNameTest(unittest.TestCase):
    def test_capitalizes_only_the_first_letter(self):
        self.assertEqual(generate_codex.display_name("praxis"), "Praxis")
        self.assertEqual(generate_codex.display_name("gitWise"), "GitWise")


class ShortDescriptionTest(unittest.TestCase):
    def test_takes_the_lead_clause(self):
        self.assertEqual(
            generate_codex.short_description("Summary -- detail that follows"),
            "Summary",
        )

    def test_returns_the_whole_string_when_no_separator(self):
        self.assertEqual(generate_codex.short_description("Just a summary  "), "Just a summary")


class BasicStringTest(unittest.TestCase):
    def test_escapes_backslash_before_quotes(self):
        # Order matters: escaping the quote first would double-escape the
        # backslash the quote's own escape just introduced.
        self.assertEqual(generate_codex.basic_string('a\\b'), '"a\\\\b"')

    def test_escapes_double_quotes(self):
        self.assertEqual(generate_codex.basic_string('a"b'), '"a\\"b"')

    def test_escaping_a_backslash_and_a_quote_together_stays_parseable(self):
        # Order-dependent: escaping the quote first, then the backslash,
        # would re-escape the backslash the quote's own escape just
        # introduced and leave a bare quote in the output -- which a TOML
        # parser reads as the string ending early, not as a literal quote.
        escaped = generate_codex.basic_string('a\\"b')
        self.assertEqual(escaped, '"a\\\\\\"b"')
        decoded = escaped[1:-1].replace('\\\\', '\x00').replace('\\"', '"').replace('\x00', '\\')
        self.assertEqual(decoded, 'a\\"b')

    def test_escapes_newline_tab_and_cr_with_shorthand(self):
        self.assertEqual(generate_codex.basic_string("a\nb\tc\rd"), '"a\\nb\\tc\\rd"')

    def test_escapes_other_control_characters_as_unicode(self):
        self.assertEqual(generate_codex.basic_string("a\x01b"), '"a\\u0001b"')

    def test_escapes_del_with_named_shorthand(self):
        self.assertEqual(generate_codex.basic_string("a\x7fb"), '"a\\u007Fb"')

    def test_plain_string_is_only_quoted(self):
        self.assertEqual(generate_codex.basic_string("plain"), '"plain"')


class RenderAgentTomlTest(unittest.TestCase):
    def test_appends_a_skills_section_when_skills_present(self):
        fields = {"name": "reviewer", "description": "desc", "skills": ["code-hygiene"]}
        out = generate_codex.render_agent_toml(fields, "Body.", "praxis")
        self.assertIn("## Skills", out)
        self.assertIn("`praxis:code-hygiene`", out)

    def test_omits_skills_section_when_absent(self):
        fields = {"name": "reviewer", "description": "desc"}
        out = generate_codex.render_agent_toml(fields, "Body.", "praxis")
        self.assertNotIn("## Skills", out)

    def test_maps_a_known_permission_mode_to_sandbox(self):
        fields = {"name": "r", "description": "d", "permissionMode": "plan"}
        out = generate_codex.render_agent_toml(fields, "Body.", "praxis")
        self.assertIn('sandbox_mode = "read-only"', out)

    def test_omits_sandbox_mode_for_an_unmapped_permission_mode(self):
        fields = {"name": "r", "description": "d", "permissionMode": "bypassPermissions"}
        out = generate_codex.render_agent_toml(fields, "Body.", "praxis")
        self.assertNotIn("sandbox_mode", out)

    def test_rejects_a_body_containing_a_toml_literal_delimiter(self):
        # A body containing ''' would end the TOML literal string early and
        # corrupt every field after it -- Codex's deny_unknown_fields then
        # takes down the whole role rather than just this one.
        fields = {"name": "reviewer", "description": "d"}
        with self.assertRaises(ValueError) as ctx:
            generate_codex.render_agent_toml(fields, "before '''  after", "praxis")
        self.assertIn("reviewer", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
