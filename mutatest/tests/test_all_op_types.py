from pathlib import Path
import subprocess
import shutil
import mutatest

HERE = Path(mutatest.__file__).parent / "tests"


def test_all_op_types(monkeypatch, tmp_path):
    """Test all operation types.

    This test ensures KeyError does not occur when accessing mutations by type.
    The test command is fake, so all mutations will survive, but this is designed to
    ensure the cached mutations happen as intended, not for pytest assessment.
    """
    shutil.copy(HERE / "all_op_types.py", tmp_path)
    monkeypatch.chdir(tmp_path)

    cmds = ["mutatest", "-s", "all_op_types.py", "-t", "echo 'fake'", "-n", "500", "-m", "f"]
    subprocess.run(cmds, capture_output=False)
