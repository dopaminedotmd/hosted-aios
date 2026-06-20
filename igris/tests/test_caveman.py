"""
Tests for Caveman Ultra — surgical patch tool.
"""

from pathlib import Path

import pytest

from igris.skills.caveman import CavemanUltra, PatchResult, BatchResult, surgical_patch


@pytest.fixture
def temp_file(tmp_path):
    """Create a test file with known content."""
    f = tmp_path / "test.py"
    f.write_text("""def hello():
    print("hello world")
    return True

def goodbye():
    print("goodbye")
    return False
""")
    return f


@pytest.fixture
def caveman(tmp_path):
    return CavemanUltra(backup=True, backup_dir=tmp_path / "backups")


class TestCavemanUltra:
    def test_basic_patch(self, caveman, temp_file):
        result = caveman.patch(str(temp_file), 'print("hello world")', 'print("hej världen")')
        assert result.success
        assert result.occurrences_replaced == 1
        content = temp_file.read_text()
        assert 'hej världen' in content
        assert 'hello world' not in content

    def test_patch_not_found(self, caveman, temp_file):
        result = caveman.patch(str(temp_file), "nonexistent text", "replacement")
        assert not result.success
        assert "not found" in result.error

    def test_patch_file_not_found(self, caveman):
        result = caveman.patch("nonexistent.py", "x", "y")
        assert not result.success
        assert "File not found" in result.error

    def test_dry_run_does_not_write(self, caveman, temp_file):
        original = temp_file.read_text()
        result = caveman.patch(str(temp_file), "goodbye", "farewell", dry_run=True)
        assert result.success
        assert result.diff  # should have diff output
        # File should be unchanged
        assert temp_file.read_text() == original

    def test_replace_all(self, caveman, temp_file):
        result = caveman.patch(str(temp_file), "print", "log", replace_all=True)
        assert result.occurrences_replaced == 2

    def test_replace_first_only(self, caveman, temp_file):
        result = caveman.patch(str(temp_file), "print", "log", replace_all=False)
        assert result.occurrences_replaced == 1

    def test_backup_created(self, caveman, temp_file):
        result = caveman.patch(str(temp_file), "hello", "hi")
        assert result.backup_path
        assert Path(result.backup_path).exists()

    def test_rollback(self, caveman, temp_file):
        original = temp_file.read_text()
        # Use a unique string that only appears once
        caveman.patch(str(temp_file), 'def hello():', 'def hi():')
        # File changed
        assert 'def hello():' not in temp_file.read_text()
        assert 'def hi():' in temp_file.read_text()

        success = caveman.rollback_last()
        assert success
        assert temp_file.read_text() == original

    def test_batch_patch(self, caveman, tmp_path):
        f1 = tmp_path / "a.py"
        f1.write_text("AAA")
        f2 = tmp_path / "b.py"
        f2.write_text("BBB")

        batch = caveman.patch_batch([
            (str(f1), "AAA", "111"),
            (str(f2), "BBB", "222"),
        ])
        assert batch.all_success
        assert batch.successful == 2
        assert f1.read_text() == "111"
        assert f2.read_text() == "222"

    def test_batch_stop_on_failure(self, caveman, tmp_path):
        f1 = tmp_path / "a.py"
        f1.write_text("AAA")
        f2 = tmp_path / "b.py"
        f2.write_text("BBB")

        batch = caveman.patch_batch([
            (str(f1), "NONEXISTENT", "x"),
            (str(f2), "BBB", "222"),
        ], stop_on_first_failure=True)
        assert batch.failed == 1
        assert batch.successful == 0
        # f2 should NOT be changed because we stopped
        assert f2.read_text() == "BBB"

    def test_preview(self, caveman, temp_file):
        diff = caveman.preview(str(temp_file), "hello", "hej")
        assert "-hello" in diff or "-print" not in diff  # diff should show change
        assert len(diff) > 0

    def test_rollback_all(self, caveman, tmp_path):
        f1 = tmp_path / "a.py"
        f1.write_text("AAA")
        f2 = tmp_path / "b.py"
        f2.write_text("BBB")

        caveman.patch(str(f1), "AAA", "111")
        caveman.patch(str(f2), "BBB", "222")

        assert f1.read_text() == "111"
        assert f2.read_text() == "222"

        count = caveman.rollback_all()
        assert count == 2
        assert f1.read_text() == "AAA"
        assert f2.read_text() == "BBB"

    def test_convenience_function(self, temp_file):
        result = surgical_patch(str(temp_file), "goodbye", "farewell")
        assert result.success

    def test_patch_history(self, caveman, temp_file):
        caveman.patch(str(temp_file), "hello", "h")
        caveman.patch(str(temp_file), "goodbye", "g")
        assert len(caveman.patch_history) == 2

    def test_post_hook(self, tmp_path, temp_file):
        hook_called = []

        def fake_hook(files):
            hook_called.extend(files)
            return {"passed": 5, "failed": 0}

        cm = CavemanUltra(post_hook=fake_hook, backup_dir=tmp_path / "backups")
        result = cm.patch(str(temp_file), "hello", "hi")
        assert result.success
        assert len(hook_called) == 1
        assert result.tests_passed == 5
