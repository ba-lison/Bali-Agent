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

    def test_execute_tool_search_memory(self):
        mock_memory_content = (
            "## 2026-06-18T08:00:00 - task - setup validado\n"
            "- **Summary:** time base e adapters verificados\n\n"
            "## 2026-06-18T08:10:00 - commit - autenticacao\n"
            "- **Summary:** corrigido o fluxo de login\n"
        )
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", unittest.mock.mock_open(read_data=mock_memory_content)):
                result = run.execute_tool("search_memory", {"query": "login"})
                self.assertIn("autenticacao", result)
                self.assertIn("corrigido o fluxo de login", result)
                self.assertNotIn("setup validado", result)

    def test_checkpoint_persistence(self):
        import tempfile
        original_join = os.path.join
        with tempfile.TemporaryDirectory() as tmpdir:
            session_id = "test_session_123"
            def mock_join(*args):
                if len(args) >= 2 and args[0] == ".agent" and args[1] == "sessions":
                    return os.path.join(tmpdir, *args[1:])
                return original_join(*args)

            with patch("os.path.join", side_effect=mock_join):
                with patch.dict(os.environ, {"BALI_SESSION_ID": session_id}):
                    mock_response = {
                        "choices": [{
                            "message": {
                                "role": "assistant",
                                "content": "Done"
                            }
                        }]
                    }
                    with patch("run.call_llm_api", return_value=mock_response):
                        with patch("run.load_agent_prompt", return_value="System Prompt"):
                            res = run.run_agent_loop("test_agent", "start task", max_loops=1)
                            self.assertEqual(res, "Done")
                            
                            checkpoint_path = os.path.join(tmpdir, "sessions", f"{session_id}.json")
                            self.assertTrue(os.path.exists(checkpoint_path))
                            
                            with open(checkpoint_path, "r", encoding="utf-8") as f:
                                saved_messages = json.load(f)
                                
                            self.assertEqual(saved_messages[0]["role"], "system")
                            self.assertEqual(saved_messages[1]["role"], "user")
                            self.assertEqual(saved_messages[2]["role"], "assistant")
                            
                            mock_response_2 = {
                                "choices": [{
                                    "message": {
                                        "role": "assistant",
                                        "content": "Resume Done"
                                    }
                                }]
                            }
                            with patch("run.call_llm_api", return_value=mock_response_2):
                                res2 = run.run_agent_loop("test_agent", "start task", max_loops=1)
                                self.assertEqual(res2, "Resume Done")
                                
                                with open(checkpoint_path, "r", encoding="utf-8") as f:
                                    resaved_messages = json.load(f)
                                self.assertTrue(len(resaved_messages) > 3)
                                self.assertEqual(resaved_messages[3]["role"], "assistant")
                                self.assertEqual(resaved_messages[3]["content"], "Resume Done")

    def test_fuzzy_search_memory(self):
        mock_memory_content = (
            "## 2026-06-18T08:00:00 - task - setup validado\n"
            "- **Summary:** time base e adapters verificados\n\n"
            "## 2026-06-18T08:10:00 - commit - autenticacao\n"
            "- **Summary:** corrected login error\n"
        )
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", unittest.mock.mock_open(read_data=mock_memory_content)):
                result = run.execute_tool("search_memory", {"query": "erro"})
                self.assertIn("autenticacao", result)
                self.assertIn("corrected login error", result)
                self.assertNotIn("setup validado", result)

    def test_auto_save_validation(self):
        valid_context = (
            "# Working Context\n"
            "## Status Atual\n"
            "Tudo verde.\n"
            "## Progresso Recente\n"
            "- Setup concluído\n"
        )
        invalid_context_1 = "No title here"
        invalid_context_2 = (
            "# Working Context\n"
            "No status and no progress headers"
        )
        
        self.assertTrue(run.validate_working_context(valid_context))
        self.assertFalse(run.validate_working_context(invalid_context_1))
        self.assertFalse(run.validate_working_context(invalid_context_2))
        
        with patch("run.load_working_context", return_value="some context"):
            with patch("run.call_llm_api", return_value={"choices": [{"message": {"content": invalid_context_2}}]}):
                with patch("builtins.open", unittest.mock.mock_open()) as mock_file:
                    run.save_context_auto("instruction", [])
                    mock_file.assert_called()
                    written_data = "".join(call[0][0] for call in mock_file().write.call_args_list if call[0])
                    self.assertIn("Auto-Save Fallback", written_data)
                    
        with patch("run.load_working_context", return_value="some context"):
            with patch("run.call_llm_api", return_value={"choices": [{"message": {"content": valid_context}}]}):
                with patch("builtins.open", unittest.mock.mock_open()) as mock_file:
                    run.save_context_auto("instruction", [])
                    mock_file.assert_called_once()
                    args, kwargs = mock_file.call_args
                    self.assertIn("working-context.md", args[0])

    def test_claude_hook_dynamic_extraction(self):
        import claude_hook
        mock_context = (
            "# Working Context\n"
            "Some general description.\n"
            "\n"
            "## Status Atual\n"
            "Atualmente implementando testes.\n"
            "\n"
            "## Stack Tecnológica\n"
            "- Python\n"
            "\n"
            "## Progresso Recente\n"
            "- Código modificado\n"
            "\n"
            "## Bugs Conhecidos\n"
            "- Nenhum no momento\n"
            "\n"
            "## Seção Extra Não Crítica\n"
            "Esta seção não deve ser incluída no extrato.\n"
        )
        
        extracted = claude_hook.extract_critical_sections(mock_context)
        
        self.assertIn("Working Context", extracted)
        self.assertIn("Status Atual", extracted)
        self.assertIn("Stack Tecnológica", extracted)
        self.assertIn("Progresso Recente", extracted)
        self.assertIn("Bugs Conhecidos", extracted)
        self.assertNotIn("Seção Extra Não Crítica", extracted)

    @patch("builtins.input", return_value="n")
    def test_agent_shield_command_chaining(self, mock_input):
        result = run.execute_tool("run_command", {"command": "pytest && rm -rf ."})
        self.assertIn("rejeitada pelo usuário", result)
        
    @patch("builtins.input", return_value="n")
    def test_agent_shield_unauthorized_git(self, mock_input):
        result = run.execute_tool("run_command", {"command": "git push"})
        self.assertIn("rejeitada pelo usuário", result)
        
    @patch("subprocess.run")
    def test_agent_shield_authorized_git(self, mock_run):
        mock_proc = MagicMock()
        mock_proc.stdout = "On branch main"
        mock_proc.stderr = ""
        mock_run.return_value = mock_proc
        
        result = run.execute_tool("run_command", {"command": "git status"})
        self.assertIn("On branch main", result)
        mock_run.assert_called_once_with("git status", shell=True, capture_output=True, text=True, timeout=60)

    @patch("time.sleep")
    @patch("urllib.request.urlopen")
    def test_call_llm_api_retry_backoff(self, mock_urlopen, mock_sleep):
        import urllib.error
        response_success = MagicMock()
        response_success.__enter__.return_value = response_success
        response_success.read.return_value = json.dumps({
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "sucesso após retry"
                }
            }]
        }).encode("utf-8")
        
        err_429 = urllib.error.HTTPError("url", 429, "Too Many Requests", {}, None)
        err_503 = urllib.error.HTTPError("url", 503, "Service Unavailable", {}, None)
        
        mock_urlopen.side_effect = [err_429, err_503, response_success]
        
        os.environ["BALI_LLM_PROVIDER"] = "openai"
        os.environ["BALI_LLM_MODEL"] = "gpt-4o"
        os.environ["BALI_API_KEY"] = "fake-key"
        
        messages = [{"role": "user", "content": "olá"}]
        res = run.call_llm_api(messages)
        
        self.assertIsNotNone(res)
        self.assertEqual(res["choices"][0]["message"]["content"], "sucesso após retry")
        self.assertEqual(mock_urlopen.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)
        mock_sleep.assert_any_call(1)
        mock_sleep.assert_any_call(2)

    @patch("run.run_agent_loop")
    def test_subagent_recursion_limit(self, mock_loop):
        # Configura a profundidade no ambiente
        os.environ["BALI_SUBAGENT_DEPTH"] = "2"
        mock_loop.return_value = "should_not_be_called"
        
        result = run.execute_tool("invoke_subagent", {"agent_name": "database", "prompt": "query"})
        self.assertIn("Limite de profundidade de subagentes atingido", result)
        mock_loop.assert_not_called()
        
        # Teste de profundidade permitida (depth=1)
        os.environ["BALI_SUBAGENT_DEPTH"] = "1"
        mock_loop.return_value = "Sub-done"
        result2 = run.execute_tool("invoke_subagent", {"agent_name": "database", "prompt": "query"})
        self.assertEqual(result2, "Sub-done")
        mock_loop.assert_called_once()

    def test_auto_save_deterministic_fallback(self):
        import tempfile
        original_exists = os.path.exists
        
        with tempfile.TemporaryDirectory() as tmpdir:
            context_file = os.path.join(tmpdir, "working-context.md")
            # Conteúdo inicial
            initial_content = "# Working Context\n## Status Atual\nGreen\n## Progresso Recente\nDone\n"
            with open(context_file, "w", encoding="utf-8") as f:
                f.write(initial_content)
                
            # Mock de os.path.join e de open
            with patch("os.path.join", side_effect=lambda *args: context_file if (len(args) >= 2 and args[0] == ".agent" and args[1] == "working-context.md") else os.path.join(*args)):
                # Mock de call_llm_api para falhar
                with patch("run.call_llm_api", return_value=None):
                    # Roda o auto save
                    run.save_context_auto("Instrução nova", [{"role": "user", "content": "Olá"}])
                    
                    # Verifica se o arquivo contém o fallback
                    with open(context_file, "r", encoding="utf-8") as f:
                        new_content = f.read()
                        
                    self.assertIn("Auto-Save Fallback", new_content)
                    self.assertIn("Instrução nova", new_content)

    @patch("os.replace")
    @patch("builtins.open", new_callable=unittest.mock.mock_open)
    @patch("json.dump")
    def test_atomic_checkpoint_save(self, mock_dump, mock_open, mock_replace):
        import tempfile
        original_join = os.path.join
        with tempfile.TemporaryDirectory() as tmpdir:
            session_id = "test_atomic_123"
            def mock_join(*args):
                if len(args) >= 2 and args[0] == ".agent" and args[1] == "sessions":
                    return os.path.join(tmpdir, *args[1:])
                return original_join(*args)
                
            with patch("os.path.join", side_effect=mock_join):
                with patch.dict(os.environ, {"BALI_SESSION_ID": session_id}):
                    with patch("run.load_agent_prompt", return_value="System"):
                        with patch("run.call_llm_api", return_value={"choices": [{"message": {"content": "Ok"}}]}):
                            run.run_agent_loop("test", "run", max_loops=1)
                            mock_replace.assert_called()

    @patch("subprocess.run")
    def test_cli_runtime_auto_save_and_fallback(self, mock_run):
        import sys
        if str(REPO / "templates" / "runtime") not in sys.path:
            sys.path.append(str(REPO / "templates" / "runtime"))
        import bali_runtime
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            context_file = tmp_path / ".agent" / "working-context.md"
            context_file.parent.mkdir(parents=True, exist_ok=True)
            initial_content = "# Working Context\n## Status Atual\nGreen\n## Progresso Recente\nDone\n"
            context_file.write_text(initial_content, encoding="utf-8")
            
            # Mock de BALI_LLM_COMMAND
            os.environ["BALI_LLM_COMMAND"] = "mock_command {prompt_file} {output_file} {agent}"
            
            # Mock de subprocess.run para retornar erro
            mock_proc = MagicMock()
            mock_proc.returncode = 1
            mock_run.return_value = mock_proc
            
            # Roda
            bali_runtime.save_context_auto_cli(tmp_path, "tarefa_cli", ["orchestrator", "planner"], tmp_path)
            
            # Como a resposta do LLM foi inválida (retornou erro), deve ter aplicado fallback
            new_content = context_file.read_text(encoding="utf-8")
            self.assertIn("Auto-Save Fallback", new_content)
            self.assertIn("orchestrator -> planner", new_content)

if __name__ == "__main__":
    unittest.main()
