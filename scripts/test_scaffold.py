#!/usr/bin/env python3
"""
Unit tests for scaffold-plugin.py

Run with: python -m pytest scripts/test_scaffold.py -v
Or:       python scripts/test_scaffold.py
"""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

# Import from scaffold
sys.path.insert(0, str(Path(__file__).parent))
from importlib import import_module

scaffold = import_module("scaffold-plugin")
validator = import_module("validate-plugins")

scaffold_plugin = scaffold.scaffold_plugin
create_manifest = scaffold.create_manifest
create_example_command = scaffold.create_example_command
create_readme = scaffold.create_readme
create_license = scaffold.create_license


class TestScaffoldBasic(unittest.TestCase):
    """Test basic scaffold functionality."""

    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_creates_directory_structure(self):
        """Basic scaffold creates expected directories."""
        scaffold_plugin(
            name="test-plugin",
            tier="curated",
            author="Test Author",
            with_hooks=False,
            with_agents=False,
            output_dir=self.tmp_dir
        )

        plugin_dir = self.tmp_dir / "test-plugin"
        self.assertTrue(plugin_dir.exists())
        self.assertTrue((plugin_dir / ".claude-plugin").is_dir())
        self.assertTrue((plugin_dir / "commands").is_dir())
        self.assertTrue((plugin_dir / "skills").is_dir())
        self.assertTrue((plugin_dir / ".github" / "workflows").is_dir())

    def test_creates_required_files(self):
        """Scaffold creates all required files."""
        scaffold_plugin(
            name="test-plugin",
            tier="curated",
            author="Test Author",
            with_hooks=False,
            with_agents=False,
            output_dir=self.tmp_dir
        )

        plugin_dir = self.tmp_dir / "test-plugin"
        self.assertTrue((plugin_dir / ".claude-plugin" / "plugin.json").is_file())
        self.assertTrue((plugin_dir / "commands" / "example.md").is_file())
        self.assertTrue((plugin_dir / "skills" / "example" / "skill.md").is_file())
        self.assertTrue((plugin_dir / "README.md").is_file())
        self.assertTrue((plugin_dir / "LICENSE").is_file())
        self.assertTrue((plugin_dir / ".github" / "workflows" / "validate.yml").is_file())

    def test_no_hooks_by_default(self):
        """Hooks directory not created by default."""
        scaffold_plugin(
            name="test-plugin",
            tier="curated",
            author="Test Author",
            with_hooks=False,
            with_agents=False,
            output_dir=self.tmp_dir
        )

        plugin_dir = self.tmp_dir / "test-plugin"
        self.assertFalse((plugin_dir / "hooks").exists())

    def test_no_agents_by_default(self):
        """Agents directory not created by default."""
        scaffold_plugin(
            name="test-plugin",
            tier="curated",
            author="Test Author",
            with_hooks=False,
            with_agents=False,
            output_dir=self.tmp_dir
        )

        plugin_dir = self.tmp_dir / "test-plugin"
        self.assertFalse((plugin_dir / "agents").exists())


class TestScaffoldWithOptions(unittest.TestCase):
    """Test scaffold with hooks and agents options."""

    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_with_hooks_creates_hooks_dir(self):
        """--with-hooks creates hooks directory."""
        scaffold_plugin(
            name="test-plugin",
            tier="curated",
            author="Test Author",
            with_hooks=True,
            with_agents=False,
            output_dir=self.tmp_dir
        )

        plugin_dir = self.tmp_dir / "test-plugin"
        self.assertTrue((plugin_dir / "hooks").is_dir())
        self.assertTrue((plugin_dir / "hooks" / "post-tool-use.md").is_file())

    def test_with_agents_creates_agents_dir(self):
        """--with-agents creates agents directory."""
        scaffold_plugin(
            name="test-plugin",
            tier="curated",
            author="Test Author",
            with_hooks=False,
            with_agents=True,
            output_dir=self.tmp_dir
        )

        plugin_dir = self.tmp_dir / "test-plugin"
        self.assertTrue((plugin_dir / "agents").is_dir())
        self.assertTrue((plugin_dir / "agents" / "specialist.md").is_file())

    def test_with_both_hooks_and_agents(self):
        """Both hooks and agents can be created."""
        scaffold_plugin(
            name="test-plugin",
            tier="curated",
            author="Test Author",
            with_hooks=True,
            with_agents=True,
            output_dir=self.tmp_dir
        )

        plugin_dir = self.tmp_dir / "test-plugin"
        self.assertTrue((plugin_dir / "hooks").is_dir())
        self.assertTrue((plugin_dir / "agents").is_dir())


class TestCuratedManifest(unittest.TestCase):
    """Test curated tier manifest generation."""

    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_curated_manifest_structure(self):
        """Curated manifest has correct structure."""
        scaffold_plugin(
            name="curated-plugin",
            tier="curated",
            author="Test Author",
            with_hooks=False,
            with_agents=False,
            output_dir=self.tmp_dir
        )

        manifest_path = self.tmp_dir / "curated-plugin" / ".claude-plugin" / "plugin.json"
        manifest = json.loads(manifest_path.read_text())

        self.assertEqual(manifest["name"], "curated-plugin")
        self.assertEqual(manifest["policyTier"], "curated")
        self.assertEqual(manifest["capabilities"]["network"]["mode"], "none")
        self.assertNotIn("risk", manifest)

    def test_curated_manifest_has_no_domains(self):
        """Curated manifest has no network domains."""
        scaffold_plugin(
            name="curated-plugin",
            tier="curated",
            author="Test Author",
            with_hooks=False,
            with_agents=False,
            output_dir=self.tmp_dir
        )

        manifest_path = self.tmp_dir / "curated-plugin" / ".claude-plugin" / "plugin.json"
        manifest = json.loads(manifest_path.read_text())

        self.assertNotIn("domains", manifest["capabilities"]["network"])


class TestCommunityManifest(unittest.TestCase):
    """Test community tier manifest generation."""

    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_community_manifest_structure(self):
        """Community manifest has correct structure."""
        scaffold_plugin(
            name="community-plugin",
            tier="community",
            author="Test Author",
            with_hooks=False,
            with_agents=False,
            output_dir=self.tmp_dir
        )

        manifest_path = self.tmp_dir / "community-plugin" / ".claude-plugin" / "plugin.json"
        manifest = json.loads(manifest_path.read_text())

        self.assertEqual(manifest["name"], "community-plugin")
        self.assertEqual(manifest["policyTier"], "community")
        self.assertEqual(manifest["capabilities"]["network"]["mode"], "allowlist")
        self.assertIn("domains", manifest["capabilities"]["network"])

    def test_community_manifest_has_risk(self):
        """Community manifest includes risk field."""
        scaffold_plugin(
            name="community-plugin",
            tier="community",
            author="Test Author",
            with_hooks=False,
            with_agents=False,
            output_dir=self.tmp_dir
        )

        manifest_path = self.tmp_dir / "community-plugin" / ".claude-plugin" / "plugin.json"
        manifest = json.loads(manifest_path.read_text())

        self.assertIn("risk", manifest)
        self.assertIn("dataEgress", manifest["risk"])
        self.assertIn("notes", manifest["risk"])


class TestManifestContent(unittest.TestCase):
    """Test manifest content generation function."""

    def test_curated_manifest_content(self):
        """create_manifest generates valid curated JSON."""
        content = create_manifest("test", "curated", "Author", False, False)
        manifest = json.loads(content)

        self.assertEqual(manifest["name"], "test")
        self.assertEqual(manifest["policyTier"], "curated")
        self.assertEqual(manifest["capabilities"]["network"]["mode"], "none")

    def test_community_manifest_content(self):
        """create_manifest generates valid community JSON."""
        content = create_manifest("test", "community", "Author", False, False)
        manifest = json.loads(content)

        self.assertEqual(manifest["name"], "test")
        self.assertEqual(manifest["policyTier"], "community")
        self.assertEqual(manifest["capabilities"]["network"]["mode"], "allowlist")
        self.assertIn("risk", manifest)


class TestReadmeGeneration(unittest.TestCase):
    """Test README generation."""

    def test_readme_contains_plugin_name(self):
        """README includes plugin name."""
        readme = create_readme("my-plugin", "curated", "Test Author")
        self.assertIn("my-plugin", readme)
        self.assertIn("# my-plugin", readme)

    def test_readme_curated_badge(self):
        """Curated README has curated badge."""
        readme = create_readme("my-plugin", "curated", "Test Author")
        self.assertIn("tier-curated", readme)

    def test_readme_community_badge(self):
        """Community README has community badge."""
        readme = create_readme("my-plugin", "community", "Test Author")
        self.assertIn("tier-community", readme)

    def test_community_readme_has_network_section(self):
        """Community README includes network access section."""
        readme = create_readme("my-plugin", "community", "Test Author")
        self.assertIn("Network Access", readme)

    def test_curated_readme_no_network_section(self):
        """Curated README has no network section."""
        readme = create_readme("my-plugin", "curated", "Test Author")
        self.assertNotIn("Network Access", readme)


class TestLicenseGeneration(unittest.TestCase):
    """Test LICENSE file generation."""

    def test_license_contains_author(self):
        """LICENSE includes author name."""
        license_text = create_license("John Doe")
        self.assertIn("John Doe", license_text)

    def test_license_is_mit(self):
        """LICENSE is MIT license."""
        license_text = create_license("John Doe")
        self.assertIn("MIT License", license_text)

    def test_license_has_current_year(self):
        """LICENSE has current year."""
        from datetime import datetime
        license_text = create_license("John Doe")
        self.assertIn(str(datetime.now().year), license_text)


class TestCommandGeneration(unittest.TestCase):
    """Test command file generation."""

    def test_command_contains_plugin_name(self):
        """Command file references plugin name."""
        command = create_example_command("my-plugin")
        self.assertIn("my-plugin", command)

    def test_command_has_frontmatter(self):
        """Command file has YAML frontmatter."""
        command = create_example_command("my-plugin")
        self.assertTrue(command.startswith("---"))
        self.assertIn("description:", command)


class TestDirectoryAlreadyExists(unittest.TestCase):
    """Test error handling for existing directories."""

    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_exits_if_directory_exists(self):
        """Scaffold exits if plugin directory already exists."""
        (self.tmp_dir / "existing-plugin").mkdir()

        with self.assertRaises(SystemExit):
            scaffold_plugin(
                name="existing-plugin",
                tier="curated",
                author="Test Author",
                with_hooks=False,
                with_agents=False,
                output_dir=self.tmp_dir
            )


class TestReturnedFileList(unittest.TestCase):
    """Test that scaffold returns correct file list."""

    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_returns_created_files(self):
        """Scaffold returns list of created files."""
        created = scaffold_plugin(
            name="test-plugin",
            tier="curated",
            author="Test Author",
            with_hooks=False,
            with_agents=False,
            output_dir=self.tmp_dir
        )

        self.assertIsInstance(created, list)
        self.assertTrue(len(created) > 0)
        self.assertTrue(any("plugin.json" in f for f in created))
        self.assertTrue(any("README.md" in f for f in created))
        self.assertTrue(any("LICENSE" in f for f in created))

    def test_hooks_in_file_list_when_enabled(self):
        """File list includes hooks when --with-hooks."""
        created = scaffold_plugin(
            name="test-plugin",
            tier="curated",
            author="Test Author",
            with_hooks=True,
            with_agents=False,
            output_dir=self.tmp_dir
        )

        self.assertTrue(any("hooks" in f for f in created))

    def test_agents_in_file_list_when_enabled(self):
        """File list includes agents when --with-agents."""
        created = scaffold_plugin(
            name="test-plugin",
            tier="curated",
            author="Test Author",
            with_hooks=False,
            with_agents=True,
            output_dir=self.tmp_dir
        )

        self.assertTrue(any("agents" in f for f in created))


class TestCLIIntegration(unittest.TestCase):
    """Integration tests: run actual CLI and validate output."""

    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.script_path = Path(__file__).parent / "scaffold-plugin.py"

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def run_scaffold_cli(self, *args):
        """Run scaffold-plugin.py with given arguments."""
        import subprocess
        cmd = [sys.executable, str(self.script_path)] + list(args)
        result = subprocess.run(
            cmd,
            cwd=self.tmp_dir,
            capture_output=True,
            text=True
        )
        return result

    def test_cli_basic_curated(self):
        """CLI: python scaffold-plugin.py --name test-plugin"""
        result = self.run_scaffold_cli("--name", "test-plugin", "--output", str(self.tmp_dir))

        self.assertEqual(result.returncode, 0, f"CLI failed: {result.stderr}")
        self.assertIn("Scaffolding plugin", result.stdout)
        self.assertIn("test-plugin", result.stdout)

        # Verify files exist
        plugin_dir = self.tmp_dir / "test-plugin"
        self.assertTrue(plugin_dir.exists())
        self.assertTrue((plugin_dir / ".claude-plugin" / "plugin.json").exists())

    def test_cli_community_tier(self):
        """CLI: python scaffold-plugin.py --name api-plugin --tier community"""
        result = self.run_scaffold_cli(
            "--name", "api-plugin",
            "--tier", "community",
            "--output", str(self.tmp_dir)
        )

        self.assertEqual(result.returncode, 0, f"CLI failed: {result.stderr}")
        self.assertIn("community", result.stdout.lower())

        # Verify manifest has community settings
        manifest_path = self.tmp_dir / "api-plugin" / ".claude-plugin" / "plugin.json"
        manifest = json.loads(manifest_path.read_text())
        self.assertEqual(manifest["policyTier"], "community")
        self.assertIn("risk", manifest)

    def test_cli_with_hooks_flag(self):
        """CLI: python scaffold-plugin.py --name hook-plugin --with-hooks"""
        result = self.run_scaffold_cli(
            "--name", "hook-plugin",
            "--with-hooks",
            "--output", str(self.tmp_dir)
        )

        self.assertEqual(result.returncode, 0, f"CLI failed: {result.stderr}")

        # Verify hooks directory created
        hooks_dir = self.tmp_dir / "hook-plugin" / "hooks"
        self.assertTrue(hooks_dir.exists())
        self.assertTrue((hooks_dir / "post-tool-use.md").exists())

    def test_cli_with_agents_flag(self):
        """CLI: python scaffold-plugin.py --name agent-plugin --with-agents"""
        result = self.run_scaffold_cli(
            "--name", "agent-plugin",
            "--with-agents",
            "--output", str(self.tmp_dir)
        )

        self.assertEqual(result.returncode, 0, f"CLI failed: {result.stderr}")

        # Verify agents directory created
        agents_dir = self.tmp_dir / "agent-plugin" / "agents"
        self.assertTrue(agents_dir.exists())
        self.assertTrue((agents_dir / "specialist.md").exists())

    def test_cli_all_flags_combined(self):
        """CLI: python scaffold-plugin.py --name full-plugin --tier community --with-hooks --with-agents"""
        result = self.run_scaffold_cli(
            "--name", "full-plugin",
            "--tier", "community",
            "--with-hooks",
            "--with-agents",
            "--output", str(self.tmp_dir)
        )

        self.assertEqual(result.returncode, 0, f"CLI failed: {result.stderr}")

        plugin_dir = self.tmp_dir / "full-plugin"

        # All directories exist
        self.assertTrue((plugin_dir / ".claude-plugin").exists())
        self.assertTrue((plugin_dir / "commands").exists())
        self.assertTrue((plugin_dir / "skills").exists())
        self.assertTrue((plugin_dir / "hooks").exists())
        self.assertTrue((plugin_dir / "agents").exists())

        # Manifest is community tier
        manifest = json.loads((plugin_dir / ".claude-plugin" / "plugin.json").read_text())
        self.assertEqual(manifest["policyTier"], "community")

    def test_cli_invalid_name_rejected(self):
        """CLI rejects invalid plugin names."""
        result = self.run_scaffold_cli(
            "--name", "Invalid_Plugin",
            "--output", str(self.tmp_dir)
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("lowercase", result.stdout.lower() + result.stderr.lower())

    def test_cli_custom_author(self):
        """CLI: --author flag sets author in manifest."""
        result = self.run_scaffold_cli(
            "--name", "author-test",
            "--author", "Custom Author",
            "--output", str(self.tmp_dir)
        )

        self.assertEqual(result.returncode, 0)

        manifest = json.loads(
            (self.tmp_dir / "author-test" / ".claude-plugin" / "plugin.json").read_text()
        )
        self.assertEqual(manifest["author"], "Custom Author")


class TestValidatorIntegration(unittest.TestCase):
    """Integration tests: validate generated plugins with actual validator."""

    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.script_path = Path(__file__).parent / "scaffold-plugin.py"

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_generated_curated_passes_manifest_validation(self):
        """Generated curated plugin passes manifest schema validation."""
        # Import validator functions
        validate_manifest = validator.validate_plugin_manifest_schema
        validate_policy = validator.validate_tier_policy

        # Generate plugin
        scaffold_plugin(
            name="valid-curated",
            tier="curated",
            author="Test",
            with_hooks=False,
            with_agents=False,
            output_dir=self.tmp_dir
        )

        # Load and validate manifest
        manifest_path = self.tmp_dir / "valid-curated" / ".claude-plugin" / "plugin.json"
        manifest = json.loads(manifest_path.read_text())

        schema_errors, schema_warnings = validate_manifest(manifest, "curated")
        policy_errors = validate_policy(manifest, "curated")

        self.assertEqual(len(schema_errors), 0, f"Schema errors: {schema_errors}")
        self.assertEqual(len(policy_errors), 0, f"Policy errors: {policy_errors}")

    def test_generated_community_passes_manifest_validation(self):
        """Generated community plugin passes manifest schema validation."""
        validate_manifest = validator.validate_plugin_manifest_schema
        validate_policy = validator.validate_tier_policy

        # Generate plugin
        scaffold_plugin(
            name="valid-community",
            tier="community",
            author="Test",
            with_hooks=False,
            with_agents=False,
            output_dir=self.tmp_dir
        )

        # Load and validate manifest
        manifest_path = self.tmp_dir / "valid-community" / ".claude-plugin" / "plugin.json"
        manifest = json.loads(manifest_path.read_text())

        schema_errors, schema_warnings = validate_manifest(manifest, "community")
        policy_errors = validate_policy(manifest, "community")

        self.assertEqual(len(schema_errors), 0, f"Schema errors: {schema_errors}")
        self.assertEqual(len(policy_errors), 0, f"Policy errors: {policy_errors}")

    def test_generated_plugin_has_required_files(self):
        """Generated plugin has all files required by validator."""
        # Generate plugin
        scaffold_plugin(
            name="complete-plugin",
            tier="curated",
            author="Test",
            with_hooks=False,
            with_agents=False,
            output_dir=self.tmp_dir
        )

        plugin_dir = self.tmp_dir / "complete-plugin"

        # Check validator's REQUIRED_FILES
        for required in validator.REQUIRED_FILES:
            self.assertTrue(
                (plugin_dir / required).exists(),
                f"Missing required file: {required}"
            )

        # Check for content directory (validator's POSSIBLE_CONTENT_DIRS)
        has_content = any(
            (plugin_dir / d).exists()
            for d in validator.POSSIBLE_CONTENT_DIRS
        )
        self.assertTrue(has_content, "No content directory found")

        # Check for manifest (validator's POSSIBLE_PLUGIN_MANIFESTS)
        has_manifest = any(
            (plugin_dir / m).exists()
            for m in validator.POSSIBLE_PLUGIN_MANIFESTS
        )
        self.assertTrue(has_manifest, "No plugin manifest found")

    def test_generated_plugin_no_security_issues(self):
        """Generated plugin has no secrets or network code."""
        # Generate plugin with all options
        scaffold_plugin(
            name="secure-plugin",
            tier="curated",
            author="Test",
            with_hooks=True,
            with_agents=True,
            output_dir=self.tmp_dir
        )

        plugin_dir = self.tmp_dir / "secure-plugin"

        # Scan all generated files
        for content_dir in ["commands", "hooks", "agents", "skills"]:
            dir_path = plugin_dir / content_dir
            if not dir_path.exists():
                continue

            for f in dir_path.rglob("*"):
                if not f.is_file():
                    continue
                if f.suffix not in validator.SCANNABLE_EXTENSIONS | {".md"}:
                    continue

                content = f.read_text()

                # No secrets
                secret_findings = validator.scan_file_for_secrets(f, content)
                self.assertEqual(
                    len(secret_findings), 0,
                    f"Secrets found in {f}: {secret_findings}"
                )

                # No telemetry
                telemetry_findings = validator.scan_file_for_telemetry(f, content)
                self.assertEqual(
                    len(telemetry_findings), 0,
                    f"Telemetry found in {f}: {telemetry_findings}"
                )

    def test_generated_manifest_json_is_valid(self):
        """Generated manifest is valid parseable JSON."""
        for tier in ["curated", "community"]:
            scaffold_plugin(
                name=f"json-test-{tier}",
                tier=tier,
                author="Test",
                with_hooks=False,
                with_agents=False,
                output_dir=self.tmp_dir
            )

            manifest_path = self.tmp_dir / f"json-test-{tier}" / ".claude-plugin" / "plugin.json"

            # Should not raise
            try:
                manifest = json.loads(manifest_path.read_text())
                self.assertIsInstance(manifest, dict)
                self.assertIn("name", manifest)
                self.assertIn("policyTier", manifest)
                self.assertIn("capabilities", manifest)
            except json.JSONDecodeError as e:
                self.fail(f"Invalid JSON in {tier} manifest: {e}")


def run_tests():
    """Run all tests and print summary."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestScaffoldBasic))
    suite.addTests(loader.loadTestsFromTestCase(TestScaffoldWithOptions))
    suite.addTests(loader.loadTestsFromTestCase(TestCuratedManifest))
    suite.addTests(loader.loadTestsFromTestCase(TestCommunityManifest))
    suite.addTests(loader.loadTestsFromTestCase(TestManifestContent))
    suite.addTests(loader.loadTestsFromTestCase(TestReadmeGeneration))
    suite.addTests(loader.loadTestsFromTestCase(TestLicenseGeneration))
    suite.addTests(loader.loadTestsFromTestCase(TestCommandGeneration))
    suite.addTests(loader.loadTestsFromTestCase(TestDirectoryAlreadyExists))
    suite.addTests(loader.loadTestsFromTestCase(TestReturnedFileList))
    suite.addTests(loader.loadTestsFromTestCase(TestCLIIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestValidatorIntegration))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 50)
    total = result.testsRun
    if result.wasSuccessful():
        print(f"✅ All {total} tests passed!")
        return 0
    else:
        print(f"❌ {len(result.failures)} failures, {len(result.errors)} errors out of {total} tests")
        return 1


if __name__ == "__main__":
    sys.exit(run_tests())
