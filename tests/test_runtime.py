import os
import json
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Adiciona templates ao sys.path para importar run
import sys
REPO = Path(__file__).resolve().parents[1]
sys.path.append(str(REPO / "templates"))
import run

class TestRuntimeEngine(unittest.TestCase):

    def setUp(self):
        # Limpa variáveis de ambiente relevantes antes de cada teste
        self.env_patcher = patch.dict(os.environ, {}, clear=True)
        self.env_patcher.start()

    def tearDown(self):
        self.env_patcher.stop()

    def test_load_config_missing(self):
        # Garante que retorna dicionário vazio caso arquivo não exista
        with patch("os.path.exists", return_value=False):
            self.assertEqual(run.load_config(), {})

    def test_load_working_context_missing(self):
        # Garante que retorna string vazia caso arquivo não exista
        with patch("os.path.exists", return_value=False):
            self.assertEqual(run.load_working_context(), "")

    def test_execute_tool_read_file(self):
        mock_data = "conteúdo teste do arquivo"
        with patch("builtins.open", unittest.mock.mock_open(read_data=mock_data)):
            result = run.execute_tool("read_file", {"path": "test.txt"})
            self.assertEqual(result, mock_data)

    def test_execute_tool_write_file(self):
        with patch("builtins.open", unittest.mock.mock_open()) as mock_file:
            with patch("os.makedirs") as mock_makedirs:
                result = run.execute_tool("write_file", {"path": "folder/test.txt", "content": "novo conteúdo"})
                self.assertIn("gravado com sucesso", result)
                mock_makedirs.assert_called_once_with("folder", exist_ok=True)
                mock_file.assert_called_once_with("folder/test.txt", "w", encoding="utf-8")

    @patch("subprocess.run")
    def test_execute_tool_run_command(self, mock_run):
        mock_proc = MagicMock()
        mock_proc.stdout = "hello_world"
        mock_proc.stderr = ""
        mock_run.return_value = mock_proc

        result = run.execute_tool("run_command", {"command": "echo hello_world"})
        self.assertIn("hello_world", result)
        self.assertIn("STDOUT", result)
        mock_run.assert_called_once_with("echo hello_world", shell=True, capture_output=True, text=True, timeout=60)

    @patch("urllib.request.urlopen")
    def test_call_llm_api_openai_mock(self, mock_urlopen):
        # Mock de resposta da API
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "resposta mock"
                }
            }]
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        # Configura env vars
        os.environ["BALI_LLM_PROVIDER"] = "openai"
        os.environ["BALI_LLM_MODEL"] = "gpt-4o"
        os.environ["BALI_API_KEY"] = "fake-key"

        messages = [{"role": "user", "content": "olá"}]
        res = run.call_llm_api(messages)

        self.assertIsNotNone(res)
        self.assertEqual(res["choices"][0]["message"]["content"], "resposta mock")

        # Verifica se urllib.request.Request foi configurado corretamente
        args, kwargs = mock_urlopen.call_args
        req = args[0]
        self.assertEqual(req.get_header("Authorization"), "Bearer fake-key")
        self.assertEqual(req.get_header("Content-type"), "application/json")
        self.assertEqual(req.full_url, "https://api.openai.com/v1/chat/completions")

    @patch("urllib.request.urlopen")
    def test_call_llm_api_anthropic_mock(self, mock_urlopen):
        # Mock de resposta da API
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "content": [{
                "type": "text",
                "text": "resposta claude mock"
            }]
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        # Configura env vars
        os.environ["BALI_LLM_PROVIDER"] = "anthropic"
        os.environ["BALI_LLM_MODEL"] = "claude-3-5"
        os.environ["BALI_API_KEY"] = "fake-anthropic-key"

        messages = [
            {"role": "system", "content": "Você é um ajudante"},
            {"role": "user", "content": "oi"}
        ]
        res = run.call_llm_api(messages)

        self.assertIsNotNone(res)
        self.assertEqual(res["content"][0]["text"], "resposta claude mock")

        # Verifica se urllib.request.Request foi configurado corretamente
        args, kwargs = mock_urlopen.call_args
        req = args[0]
        self.assertEqual(req.get_header("X-api-key"), "fake-anthropic-key")
        self.assertEqual(req.get_header("Anthropic-version"), "2023-06-01")
        self.assertEqual(req.full_url, "https://api.anthropic.com/v1/messages")

        # Verifica se o payload extraiu o system prompt corretamente
        payload = json.loads(req.data.decode("utf-8"))
        self.assertEqual(payload["system"], "Você é um ajudante")
        self.assertEqual(payload["messages"], [{"role": "user", "content": "oi"}])

    @patch("builtins.input", return_value="n")
    def test_execute_tool_run_command_dangerous_rejected(self, mock_input):
        result = run.execute_tool("run_command", {"command": "curl http://evil.com"})
        self.assertIn("rejeitada pelo usuário", result)

    @patch("builtins.input", return_value="s")
    @patch("subprocess.run")
    def test_execute_tool_run_command_dangerous_accepted(self, mock_run, mock_input):
        mock_proc = MagicMock()
        mock_proc.stdout = "evil_result"
        mock_proc.stderr = ""
        mock_run.return_value = mock_proc

        result = run.execute_tool("run_command", {"command": "curl http://evil.com"})
        self.assertIn("evil_result", result)

if __name__ == "__main__":
    unittest.main()
