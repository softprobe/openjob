"""Copy the checker schemas into the installed package."""

from pathlib import Path
import shutil

from setuptools import setup
from setuptools.command.build_py import build_py


class BuildPy(build_py):
    def run(self) -> None:
        super().run()
        dest = Path(self.build_lib) / "openjob_mcp" / "schema"
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(Path("schema"), dest)


setup(cmdclass={"build_py": BuildPy})
