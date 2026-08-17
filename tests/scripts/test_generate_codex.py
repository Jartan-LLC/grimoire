"""Tests for the Codex generator's parsing, rendering and drift finders.

Everything here is a function that takes its input as an argument and whose wrong
answer would be silent: a frontmatter field dropped, a TOML string corrupted by
an unescaped backslash, a stale role file left installed in every Codex user's
config. The thin filesystem walk in main() is not covered -- see CONTRIBUTING.md.

Fixtures are temporary directories with `ROOT` patched to point at them, never
this checkout: the drift finders glob the whole tree, so running them here would
assert against whatever the repository happens to hold today.
"""

import importlib.util
import json
import pathlib
import tempfile
import unittest
from unittest import mock

# The hyphen in the filename is not valid in a module name, so the module cannot
# be imported by name.
SOURCE = pathlib.Path(__file__).resolve().parents[2] / "scripts" / "generate-codex.py"
_spec = importlib.util.spec_from_file_location("generate_codex", SOURCE)
gc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gc)


class DisplayNameTests(unittest.TestCase):
    def test_capitalises_the_first_character_only(self):
        self.assertEqual(gc.display_name("praxis"), "Praxis")
        self.assertEqual(gc.display_name("mcpTools"), "McpTools")

    def test_leaves_an_already_capitalised_name_alone(self):
        self.assertEqual(gc.display_name("Grimoire"), "Grimoire")


class ShortDescriptionTests(unittest.TestCase):
    def test_takes_the_lead_clause(self):
        self.assertEqual(
            gc.short_description("Development workflow -- issue planning, review"),
            "Development workflow",
        )

    def test_passes_a_description_with_no_separator_through(self):
        self.assertEqual(gc.short_description("  Development workflow  "), "Development workflow")

    def test_splits_on_the_first_separator_only(self):
        self.assertEqual(gc.short_description("A -- B -- C"), "A")


class QualifyTests(unittest.TestCase):
    def test_namespaces_a_bare_skill_to_its_own_plugin(self):
        self.assertEqual(gc.qualify("readable-code", "praxis"), "praxis:readable-code")

    def test_leaves_an_already_qualified_skill_alone(self):
        self.assertEqual(gc.qualify("gitwise:github-conventions", "praxis"), "gitwise:github-conventions")


class ParseFrontmatterTests(unittest.TestCase):
    def test_reads_scalars_a_list_and_the_body(self):
        text = (
            "---\n"
            "name: general-reviewer\n"
            "description: Reviews code\n"
            "skills:\n"
            "  - readable-code\n"
            "  - review-severity\n"
            "---\n"
            "\n"
            "Body text.\n"
        )
        fields, body = gc.parse_frontmatter(text, "general-reviewer.md")
        self.assertEqual(
            fields,
            {
                "name": "general-reviewer",
                "description": "Reviews code",
                "skills": ["readable-code", "review-severity"],
            },
        )
        self.assertEqual(body, "Body text.")

    def test_keeps_a_colon_inside_a_scalar_value(self):
        fields, _ = gc.parse_frontmatter("---\ndescription: Reviews code: carefully\n---\nx\n", "a.md")
        self.assertEqual(fields["description"], "Reviews code: carefully")

    def test_a_valueless_key_becomes_an_empty_list(self):
        fields, _ = gc.parse_frontmatter("---\nskills:\n---\nx\n", "a.md")
        self.assertEqual(fields["skills"], [])

    def test_ignores_a_list_item_with_no_key_above_it(self):
        fields, body = gc.parse_frontmatter("---\n  - stray\nname: x\n---\nbody\n", "a.md")
        self.assertEqual(fields, {"name": "x"})
        self.assertEqual(body, "body")

    def test_names_the_file_when_the_frontmatter_does_not_open(self):
        with self.assertRaises(ValueError) as caught:
            gc.parse_frontmatter("name: x\n---\nbody\n", "broken.md")
        self.assertIn("broken.md", str(caught.exception))
        self.assertIn("open with ---", str(caught.exception))

    def test_names_the_file_when_the_frontmatter_does_not_close(self):
        with self.assertRaises(ValueError) as caught:
            gc.parse_frontmatter("---\nname: x\nbody\n", "broken.md")
        self.assertIn("broken.md", str(caught.exception))
        self.assertIn("no closing ---", str(caught.exception))


class BasicStringTests(unittest.TestCase):
    def test_quotes_a_plain_value(self):
        self.assertEqual(gc.basic_string("Reviews code"), '"Reviews code"')

    def test_escapes_a_backslash(self):
        # Basic strings process escapes, so an unescaped backslash silently
        # corrupts the value rather than failing to parse.
        self.assertEqual(gc.basic_string("a\\b"), '"a\\\\b"')

    def test_escapes_a_quote(self):
        self.assertEqual(gc.basic_string('say "hi"'), '"say \\"hi\\""')

    def test_escapes_the_control_characters_with_a_shorthand(self):
        self.assertEqual(gc.basic_string("a\nb"), '"a\\nb"')
        self.assertEqual(gc.basic_string("a\rb"), '"a\\rb"')
        self.assertEqual(gc.basic_string("a\tb"), '"a\\tb"')
        self.assertEqual(gc.basic_string("a\x7fb"), '"a\\u007Fb"')

    def test_escapes_a_control_character_with_no_shorthand_as_a_codepoint(self):
        self.assertEqual(gc.basic_string("a\x01b"), '"a\\u0001b"')
        self.assertEqual(gc.basic_string("a\x1fb"), '"a\\u001Fb"')

    def test_escapes_backslashes_before_control_characters(self):
        # A literal backslash followed by `n` must not come out as a newline
        # escape, which is what escaping in the other order would produce.
        self.assertEqual(gc.basic_string("\\n"), '"\\\\n"')
        self.assertEqual(gc.basic_string("\\"), '"\\\\"')
        # And a real newline next to a literal backslash keeps both.
        self.assertEqual(gc.basic_string("\\\n"), '"\\\\\\n"')


class RenderAgentTomlTests(unittest.TestCase):
    def render(self, fields, body="Do the review.", plugin="praxis"):
        return gc.render_agent_toml(fields, body, plugin)

    def test_renders_name_description_and_body(self):
        out = self.render({"name": "test-reviewer", "description": "Reviews tests"})
        self.assertEqual(
            out,
            'name = "test-reviewer"\n'
            'description = "Reviews tests"\n'
            "developer_instructions = '''\n"
            "Do the review.\n"
            "'''\n",
        )

    def test_names_the_preloaded_skills_in_the_instructions(self):
        out = self.render(
            {
                "name": "test-reviewer",
                "description": "Reviews tests",
                "skills": ["testing-patterns", "gitwise:github-conventions"],
            }
        )
        self.assertIn(
            "## Skills\n\nLoad these skills before starting: "
            "`praxis:testing-patterns`, `gitwise:github-conventions`.",
            out,
        )

    def test_omits_the_skills_section_when_there_are_none(self):
        self.assertNotIn("## Skills", self.render({"name": "a", "description": "b"}))
        self.assertNotIn("## Skills", self.render({"name": "a", "description": "b", "skills": []}))

    def test_maps_a_permission_mode_to_a_sandbox(self):
        for mode, sandbox in (
            ("plan", "read-only"),
            ("readOnly", "read-only"),
            ("acceptEdits", "workspace-write"),
        ):
            with self.subTest(mode=mode):
                out = self.render({"name": "a", "description": "b", "permissionMode": mode})
                self.assertIn(f'sandbox_mode = "{sandbox}"\n', out)

    def test_omits_the_sandbox_for_an_absent_or_unmapped_mode(self):
        self.assertNotIn("sandbox_mode", self.render({"name": "a", "description": "b"}))
        self.assertNotIn(
            "sandbox_mode",
            self.render({"name": "a", "description": "b", "permissionMode": "bypassPermissions"}),
        )

    def test_escapes_the_name_and_description_but_not_the_body(self):
        out = self.render(
            {"name": 'a"b', "description": "c\\d"},
            body="A path like C:\\Users stays verbatim.",
        )
        self.assertIn('name = "a\\"b"\n', out)
        self.assertIn('description = "c\\\\d"\n', out)
        self.assertIn("A path like C:\\Users stays verbatim.", out)

    def test_rejects_a_body_that_would_end_the_literal_string(self):
        with self.assertRaises(ValueError) as caught:
            self.render({"name": "test-reviewer", "description": "b"}, body="A fence: '''")
        self.assertIn("test-reviewer", str(caught.exception))
        self.assertIn("cannot be a TOML literal", str(caught.exception))

    def test_rejects_a_triple_quote_introduced_by_the_skills_section(self):
        # The check runs after the section is appended, so a `'''` arriving with
        # the skill names is caught too.
        with self.assertRaises(ValueError):
            self.render({"name": "a", "description": "b", "skills": ["x'''y"]})


class PluginManifestTests(unittest.TestCase):
    def make_plugin(self, root, name, manifest):
        source = root / "plugins" / name
        (source / ".claude-plugin").mkdir(parents=True)
        (source / ".claude-plugin" / "plugin.json").write_text(json.dumps(manifest))
        return source

    def test_builds_the_manifest_with_the_interface_block(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            self.make_plugin(
                root,
                "praxis",
                {"name": "praxis", "version": "1.4.0", "description": "Workflow -- planning and review"},
            )
            entry = {"name": "praxis", "source": "./plugins/praxis", "category": "development", "keywords": ["review"]}

            with mock.patch.object(gc, "ROOT", root):
                path, manifest = gc.plugin_manifest(entry)

            self.assertEqual(path, root / "plugins" / "praxis" / ".codex-plugin" / "plugin.json")
            self.assertEqual(
                manifest,
                {
                    "name": "praxis",
                    "version": "1.4.0",
                    "description": "Workflow -- planning and review",
                    "keywords": ["review"],
                    "interface": {
                        "displayName": "Praxis",
                        "shortDescription": "Workflow",
                        "category": "Development",
                    },
                },
            )

    def test_omits_keywords_when_the_entry_carries_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            self.make_plugin(root, "praxis", {"name": "praxis", "version": "1.0.0", "description": "d"})
            entry = {"name": "praxis", "source": "./plugins/praxis", "category": "development"}

            with mock.patch.object(gc, "ROOT", root):
                _, manifest = gc.plugin_manifest(entry)

            self.assertNotIn("keywords", manifest)

    def test_raises_when_the_manifest_and_the_catalog_name_the_plugin_differently(self):
        # A one-sided rename would otherwise leave the generated pair quietly
        # disagreeing, which nothing downstream would notice.
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            self.make_plugin(root, "praxis", {"name": "praxis-renamed", "version": "1.0.0", "description": "d"})
            entry = {"name": "praxis", "source": "./plugins/praxis", "category": "development"}

            with mock.patch.object(gc, "ROOT", root):
                with self.assertRaises(ValueError) as caught:
                    gc.plugin_manifest(entry)

            message = str(caught.exception)
            self.assertIn("praxis-renamed", message)
            self.assertIn("praxis", message)

    def test_raises_on_a_category_less_entry(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            self.make_plugin(root, "praxis", {"name": "praxis", "version": "1.0.0", "description": "d"})
            entry = {"name": "praxis", "source": "./plugins/praxis"}

            with mock.patch.object(gc, "ROOT", root):
                with self.assertRaises(KeyError):
                    gc.plugin_manifest(entry)


class FindOrphansTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name)
        self.codex_marketplace = self.root / ".agents" / "plugins" / "marketplace.json"
        self.codex_marketplace.parent.mkdir(parents=True)
        self.codex_marketplace.write_text("{}\n")

    def write(self, relative, contents="x\n"):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents)
        return path

    def find(self, targets):
        with mock.patch.object(gc, "ROOT", self.root), mock.patch.object(
            gc, "CODEX_MARKETPLACE", self.codex_marketplace
        ):
            return gc.find_orphans(targets)

    def test_reports_nothing_when_every_file_is_a_target(self):
        kept = self.write("plugins/praxis/codex/agents/kept.toml")
        manifest = self.write("plugins/praxis/.codex-plugin/plugin.json", "{}\n")
        targets = [(self.codex_marketplace, "{}\n"), (kept, "x\n"), (manifest, "{}\n")]
        self.assertEqual(self.find(targets), [])

    def test_reports_a_role_left_behind_by_a_deleted_agent(self):
        kept = self.write("plugins/praxis/codex/agents/kept.toml")
        self.write("plugins/praxis/codex/agents/deleted.toml")
        self.assertEqual(
            self.find([(self.codex_marketplace, "{}\n"), (kept, "x\n")]),
            [pathlib.Path("plugins/praxis/codex/agents/deleted.toml")],
        )

    def test_reports_a_stale_manifest_alongside_a_stale_role(self):
        self.write("plugins/praxis/codex/agents/deleted.toml")
        self.write("plugins/praxis/.codex-plugin/plugin.json", "{}\n")
        self.assertEqual(
            self.find([(self.codex_marketplace, "{}\n")]),
            [
                pathlib.Path("plugins/praxis/.codex-plugin/plugin.json"),
                pathlib.Path("plugins/praxis/codex/agents/deleted.toml"),
            ],
        )

    def test_reports_files_of_a_plugin_that_contributes_no_targets_at_all(self):
        # The reason the directories to scan come from disk and not from the
        # targets: a plugin that dropped to zero agents, or left the marketplace,
        # would otherwise take its whole directory out of the scan along with the
        # files left in it.
        self.write("plugins/gone/codex/agents/old.toml")
        self.assertEqual(
            self.find([(self.codex_marketplace, "{}\n")]),
            [pathlib.Path("plugins/gone/codex/agents/old.toml")],
        )

    def test_ignores_a_subdirectory_inside_a_scanned_directory(self):
        (self.root / "plugins" / "praxis" / "codex" / "agents" / "nested").mkdir(parents=True)
        self.assertEqual(self.find([(self.codex_marketplace, "{}\n")]), [])


class FindDivergentCopiesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name)

    def write_copy(self, plugin, contents):
        path = self.root / "plugins" / plugin / gc.DUPLICATED_HOOK_SCRIPTS[0]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents)

    def find(self):
        with mock.patch.object(gc, "ROOT", self.root):
            return gc.find_divergent_copies()

    def test_reports_nothing_when_the_copies_are_byte_identical(self):
        self.write_copy("praxis", "console.error('sync');\n")
        self.write_copy("recursio", "console.error('sync');\n")
        self.assertEqual(self.find(), [])

    def test_reports_every_copy_once_they_differ(self):
        # Plugins install independently, so they cannot share a module at hook
        # runtime and nothing else stops a one-sided edit drifting.
        self.write_copy("praxis", "console.error('sync');\n")
        self.write_copy("recursio", "console.error('sync');  // edited here only\n")
        self.assertEqual(
            self.find(),
            [
                pathlib.Path("plugins/praxis") / gc.DUPLICATED_HOOK_SCRIPTS[0],
                pathlib.Path("plugins/recursio") / gc.DUPLICATED_HOOK_SCRIPTS[0],
            ],
        )

    def test_reports_nothing_when_only_one_plugin_ships_the_script(self):
        self.write_copy("praxis", "console.error('sync');\n")
        self.assertEqual(self.find(), [])

    def test_reports_nothing_when_no_plugin_ships_it(self):
        self.assertEqual(self.find(), [])


if __name__ == "__main__":
    unittest.main()
