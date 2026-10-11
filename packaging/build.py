"""Build on the target OS, verify GUI startup, and archive for distribution."""

import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    system = platform.system()
    if system not in ("Windows", "Darwin"):
        raise SystemExit("Build on Windows or macOS; cross compilation is not supported.")
    args = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--windowed", "--name", "retrokey", "--paths", str(ROOT / "src"), "--distpath", str(ROOT / "dist"), "--workpath", str(ROOT / "build"), "--specpath", str(ROOT / "build")]
    if system == "Windows":
        args.append("--onefile")
    else:
        args.extend(["--onedir", "--osx-bundle-identifier", "lab.redcoast.retrokey"])
    args.append(str(ROOT / "packaging/gui_entry.py"))
    subprocess.run(args, cwd=ROOT, check=True)
    dist = ROOT / "dist"
    executable = dist / "retrokey.exe" if system == "Windows" else dist / "retrokey.app/Contents/MacOS/retrokey"
    report = ROOT / "build/gui-smoke.json"
    report.unlink(missing_ok=True)
    subprocess.run([str(executable), "--smoke-test", str(report)], check=True, timeout=90)
    if not report.exists() or not json.loads(report.read_text(encoding="utf-8")).get("ok"):
        raise SystemExit("Bundled GUI/clipboard smoke test failed; inspect build/gui-smoke.json.")
    arch = {"AMD64": "x64", "x86_64": "x64", "arm64": "arm64", "aarch64": "arm64"}.get(platform.machine(), platform.machine().lower())
    name = f"retrokey-{'windows' if system == 'Windows' else 'macos'}-{arch}"
    archive = dist / f"{name}.zip"
    if system == "Windows":
        import zipfile
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as output:
            output.write(executable, "retrokey.exe")
            output.write(ROOT / "packaging/USER_GUIDE.txt", "はじめに.txt")
    else:
        # ditto preserves .app permissions and symlinks, unlike a plain ZIP walk.
        stage = ROOT / "build" / name
        stage.mkdir(parents=True, exist_ok=True)
        shutil.copytree(dist / "retrokey.app", stage / "retrokey.app", symlinks=True, dirs_exist_ok=True)
        shutil.copy2(ROOT / "packaging/USER_GUIDE.txt", stage / "はじめに.txt")
        subprocess.run(["ditto", "-c", "-k", "--sequesterRsrc", "--keepParent", str(stage), str(archive)], check=True)
    print(archive)


if __name__ == "__main__":
    main()
