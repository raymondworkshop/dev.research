import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from scripts.tagger import route_message

__all__ = ["route_message"]
