import tarfile
from pathlib import Path

from function import copyfolder
from tps2toj import make_tar_xz_with_progress


def test_copyfolder_allows_existing_destination(tmp_path):
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    (src / "nested").mkdir(parents=True)
    (src / "nested" / "file.txt").write_text("hello")

    dst.mkdir()

    copyfolder((src,), (dst,))

    copied = dst / "nested" / "file.txt"
    assert copied.exists()
    assert copied.read_text() == "hello"


def test_make_tar_xz_with_progress_includes_files(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.txt").write_text("content")

    dest = tmp_path / "out.tar.xz"
    make_tar_xz_with_progress(str(src), str(dest))

    assert dest.exists()
    with tarfile.open(dest, "r:xz") as tar:
        names = tar.getnames()
        assert "a.txt" in names
        extracted = tar.extractfile("a.txt")
        assert extracted is not None
        assert extracted.read().decode() == "content"
