import unittest
from pathlib import Path


class _FakeAnalysis:
    def __init__(self, scripts, **kwargs):
        self.scripts_arg = scripts
        self.kwargs = kwargs
        self.pure = []
        self.scripts = []
        self.binaries = []
        self.datas = []


class WindowsPackagingSpecTests(unittest.TestCase):
    def test_windows_spec_uses_paths_that_exist_from_spec_directory(self):
        root = Path(__file__).resolve().parents[1]
        spec = root / "packaging" / "windows" / "sleep-noise-guard-windows.spec"
        captured = {}

        def analysis(scripts, **kwargs):
            captured["analysis"] = _FakeAnalysis(scripts, **kwargs)
            return captured["analysis"]

        def pyz(_pure):
            return object()

        def exe(*args, **kwargs):
            captured["exe"] = (args, kwargs)
            return object()

        namespace = {
            "Analysis": analysis,
            "PYZ": pyz,
            "EXE": exe,
            "SPECPATH": str(spec.parent),
        }
        exec(compile(spec.read_text(encoding="utf-8"), str(spec), "exec"), namespace)

        analysis_obj = captured["analysis"]
        self.assertEqual(
            [str(root / "sleep_noise_guard" / "windows_desktop.py")],
            analysis_obj.scripts_arg,
        )
        self.assertTrue(Path(analysis_obj.scripts_arg[0]).is_file())
        self.assertEqual([str(root)], analysis_obj.kwargs["pathex"])

        data_sources = [Path(source) for source, _target in analysis_obj.kwargs["datas"]]
        self.assertEqual(
            [
                root / "sounds",
                root / "README.md",
                root / "docs" / "中文说明.md",
            ],
            data_sources,
        )
        for source in data_sources:
            self.assertTrue(source.exists(), source)


if __name__ == "__main__":
    unittest.main()
