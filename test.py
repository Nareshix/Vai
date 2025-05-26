from pathlib import Path

project_root = Path(__file__).resolve().parent
static_dir = project_root / 'static'
wanted_basenames = {'favicon', 'logo'}

found = {}
for file_path in static_dir.rglob('*'):
    if file_path.is_file():
        stem = file_path.stem
        if stem in wanted_basenames:
            found[stem] = file_path.name

print(found['favicon'])

