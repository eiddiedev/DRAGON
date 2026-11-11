# Single final-body installer; never reconstruct current UI from older snapshots.
import runpy
from pathlib import Path
runpy.run_path(str(Path(__file__).with_name("install_final.py")),run_name="__main__")
