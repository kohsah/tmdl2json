import os
import tempfile
import unittest
from unittest import mock

from erd_generator import generate_png_from_mermaid_local, generate_png_from_mermaid_python


class TestErdGeneratorLocalPng(unittest.TestCase):
    def test_local_mode_missing_mmdc(self):
        with mock.patch("shutil.which", return_value=None):
            with self.assertRaises(FileNotFoundError):
                generate_png_from_mermaid_local("erDiagram\n", "out.png")

    def test_local_mode_invokes_mmdc(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, "out.png")
            with mock.patch("shutil.which", return_value="mmdc"):
                with mock.patch("subprocess.run") as run_mock:
                    run_mock.return_value = mock.Mock(returncode=0, stdout="", stderr="")
                    generate_png_from_mermaid_local("erDiagram\n", out_path)
                    args, kwargs = run_mock.call_args
                    self.assertEqual(args[0][0], "mmdc")
                    self.assertIn("-i", args[0])
                    self.assertIn("-o", args[0])
                    self.assertIn(out_path, args[0])
                    self.assertTrue(kwargs.get("capture_output"))
                    self.assertTrue(kwargs.get("text"))

    def test_local_mode_uses_env_var_mmdc_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, "out.png")
            with mock.patch.dict(os.environ, {"MMDC_PATH": "C:\\mmdc\\mmdc.cmd"}, clear=True):
                with mock.patch("shutil.which", return_value=None):
                    with mock.patch("subprocess.run") as run_mock:
                        run_mock.return_value = mock.Mock(returncode=0, stdout="", stderr="")
                        generate_png_from_mermaid_local("erDiagram\n", out_path)
                        args, _kwargs = run_mock.call_args
                        self.assertEqual(args[0][0], "C:\\mmdc\\mmdc.cmd")

    def test_local_mode_precedence_cli_over_env_and_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, "out.png")
            with mock.patch.dict(os.environ, {"MMDC_PATH": "C:\\mmdc\\env.cmd"}, clear=True):
                with mock.patch("shutil.which", return_value="C:\\mmdc\\path.cmd"):
                    with mock.patch("subprocess.run") as run_mock:
                        run_mock.return_value = mock.Mock(returncode=0, stdout="", stderr="")
                        generate_png_from_mermaid_local("erDiagram\n", out_path, mmdc_path="C:\\mmdc\\cli.cmd")
                        args, _kwargs = run_mock.call_args
                        self.assertEqual(args[0][0], "C:\\mmdc\\cli.cmd")

    def test_local_mode_precedence_env_over_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, "out.png")
            with mock.patch.dict(os.environ, {"MMDC_PATH": "C:\\mmdc\\env.cmd"}, clear=True):
                with mock.patch("shutil.which", return_value="C:\\mmdc\\path.cmd"):
                    with mock.patch("subprocess.run") as run_mock:
                        run_mock.return_value = mock.Mock(returncode=0, stdout="", stderr="")
                        generate_png_from_mermaid_local("erDiagram\n", out_path)
                        args, _kwargs = run_mock.call_args
                        self.assertEqual(args[0][0], "C:\\mmdc\\env.cmd")

class TestErdGeneratorPythonPng(unittest.TestCase):
    def test_python_mode_missing_mermaid_cli(self):
        with mock.patch("importlib.import_module", side_effect=ModuleNotFoundError("mermaid_cli")):
            with self.assertRaises(ImportError):
                generate_png_from_mermaid_python("erDiagram\n", "out.png")

    def test_python_mode_invokes_mermaid_cli_sync_render(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, "out.png")
            fake_module = mock.Mock()
            fake_module.render_mermaid_file_sync = mock.Mock()
            with mock.patch("importlib.import_module", return_value=fake_module):
                with mock.patch("urllib.request.urlopen") as urlopen_mock:
                    generate_png_from_mermaid_python("erDiagram\n", out_path)
                    urlopen_mock.assert_not_called()
            fake_module.render_mermaid_file_sync.assert_called_once()
            _args, kwargs = fake_module.render_mermaid_file_sync.call_args
            self.assertEqual(kwargs["output_file"], out_path)
            self.assertEqual(kwargs["output_format"], "png")
            self.assertTrue(kwargs["input_file"].endswith(".mmd"))


if __name__ == "__main__":
    unittest.main()
