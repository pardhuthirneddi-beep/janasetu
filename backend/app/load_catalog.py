import argparse
from pathlib import Path
from app.main import load_catalog

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load authoritative JanSetu service catalog entries")
    parser.add_argument("--file", type=Path, default=Path(__file__).parent / "data" / "service_catalog.json")
    args = parser.parse_args()
    print(load_catalog(args.file))
