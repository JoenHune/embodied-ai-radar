import tempfile
import unittest
from pathlib import Path
from scripts.model_runtime import ModelConfigurationError, read_model_configuration, load_model_configuration


class ModelRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.root = self.base / "repository"
        self.root.mkdir()
        self.env = self.base / "runtime.env"

    def tearDown(self):
        self.temp.cleanup()

    def test_loggerbot_imports_only_model_fields_and_never_executes_values(self):
        marker = self.base / "executed"
        self.env.write_text('CODEX_PROXY_BASE_URL="http://127.0.0.1:10531/v1"\n'
                            'CODEX_PROXY_API_KEY="fixture-key"\nCODEX_PROXY_MODEL=gpt-5.6-sol\n'
                            f'FEISHU_APP_SECRET="unterminated\nPRIVATE_TOKEN=$(touch {marker})\n')
        target = {"UNRELATED": "keep"}
        metadata = load_model_configuration(loggerbot_env_file=self.env, environ=target, root=self.root)
        self.assertEqual(target, {"UNRELATED": "keep", "LLM_BASE_URL": "http://127.0.0.1:10531/v1", "LLM_API_KEY": "fixture-key", "LLM_MODEL": "gpt-5.6-sol"})
        self.assertEqual(metadata, {"source": "loggerbot_model_fields", "configured": True})
        self.assertNotIn("fixture-key", str(metadata))
        self.assertFalse(marker.exists())

    def test_explicit_process_endpoint_does_not_take_file_credential(self):
        self.env.write_text('CODEX_PROXY_BASE_URL=http://127.0.0.1:10531/v1\nCODEX_PROXY_API_KEY=file-secret\n')
        target = {"LLM_BASE_URL": "http://127.0.0.1:9999/v1", "LLM_MODEL": "explicit-model"}
        load_model_configuration(loggerbot_env_file=self.env, environ=target, root=self.root)
        self.assertNotIn("LLM_API_KEY", target)
        self.assertEqual(target["LLM_MODEL"], "explicit-model")

    def test_file_endpoint_does_not_take_unpaired_environment_secret(self):
        self.env.write_text('LLM_BASE_URL=http://127.0.0.1:9999/v1\n')
        target = {"LLM_API_KEY": "unrelated-secret"}
        load_model_configuration(env_file=self.env, environ=target, root=self.root)
        self.assertNotIn("LLM_API_KEY", target)

    def test_runtime_supports_quotes_comments_exports_and_literal_dollars(self):
        self.env.write_text('export LLM_BASE_URL="http://127.0.0.1:9999/v1" # note\nLLM_API_KEY=\'$(not-executed) # literal\'\n')
        value = read_model_configuration(self.env, root=self.root)
        self.assertEqual(value["LLM_API_KEY"], "$(not-executed) # literal")

    def test_runtime_unknown_duplicate_and_malformed_fields_fail_safely(self):
        for content in ['FEISHU_APP_SECRET=super-secret\n', 'LLM_MODEL=a\nLLM_MODEL=b\n', 'LLM_API_KEY="super-secret\n']:
            self.env.write_text(content)
            with self.assertRaises(ModelConfigurationError) as result:
                read_model_configuration(self.env, root=self.root)
            self.assertNotIn("super-secret", str(result.exception))

    def test_inside_repo_and_symlinks_into_repo_are_rejected(self):
        inside = self.root / "secret.env"
        inside.write_text("LLM_API_KEY=fixture")
        self.env.symlink_to(inside)
        for path in [inside, self.env]:
            with self.assertRaises(ModelConfigurationError):
                read_model_configuration(path, root=self.root)

    def test_missing_file_missing_proxy_and_conflicting_sources(self):
        with self.assertRaises(ModelConfigurationError):
            read_model_configuration(self.env, root=self.root)
        self.env.write_text("OPENAI_API_KEY=not-the-selected-profile")
        with self.assertRaises(ModelConfigurationError):
            read_model_configuration(self.env, loggerbot=True, root=self.root)
        with self.assertRaises(ModelConfigurationError):
            load_model_configuration(env_file=self.env, loggerbot_env_file=self.env, root=self.root)

    def test_default_reads_no_external_file(self):
        target = {"UNRELATED": "keep"}
        self.assertEqual(load_model_configuration(environ=target), {"source": "environment", "configured": False})
        self.assertEqual(target, {"UNRELATED": "keep"})

    def test_launchd_references_only_the_configuration_path(self):
        from scripts.install_weekly_launchd import build_plist
        result = build_plist(self.root, "/bin/python", "/bin/node", "/bin/npm", self.env, loggerbot=True)
        self.assertEqual(result["ProgramArguments"][-2:], ["--loggerbot-env-file", str(self.env)])
        self.assertFalse(set(result["EnvironmentVariables"]) & {"LLM_API_KEY", "CODEX_PROXY_API_KEY", "FEISHU_APP_SECRET"})

    def test_failed_parse_does_not_partially_mutate_environment(self):
        self.env.write_text("LLM_BASE_URL=http://127.0.0.1:9999/v1\nLLM_API_KEY=\"unterminated")
        target = {"KEEP": "value"}
        with self.assertRaises(ModelConfigurationError):
            load_model_configuration(env_file=self.env, environ=target, root=self.root)
        self.assertEqual(target, {"KEEP": "value"})
