"""
Contains hard-coded paths to relevant files and directories.
"""
from pathlib import Path

root = Path(__file__).parents[2]
package = root / "seacharts"

config = package / "config.yaml"
config_schema = package / "config_schema.yaml"

cwd = Path.cwd()
data = cwd / "data"
db = data / "db"

default_resources = cwd, data, db

shapefiles = data / "shapefiles"

vessels = data / "vessels.csv"

output = root / "output"


def _guess_data_directory_from_resources(resources: list[str]) -> Path | None:
	"""
	Tries to infer the data directory from configured ENC resources.

	Expected common layouts are:
	- <project>/data/db
	- <project>/data/db/<chart_or_fgdb>
	"""
	for resource in resources:
		path = Path(resource).expanduser().resolve()
		if path.name == "db":
			return path.parent
		if path.parent.name == "db":
			return path.parent.parent
	return None


def configure_runtime_paths(config_path: Path | str, resources: list[str]) -> None:
	"""
	Reconfigures runtime paths so file outputs are anchored to user config/resources,
	not to the process working directory.
	"""
	global cwd, data, db, shapefiles, vessels, default_resources, output

	config_dir = Path(config_path).expanduser().resolve().parent
	data_dir = _guess_data_directory_from_resources(resources)

	cwd = config_dir
	if data_dir is None:
		data = cwd / "data"
		db = data / "db"
	else:
		data = data_dir
		db = data / "db"

	default_resources = cwd, data, db
	shapefiles = data / "shapefiles"
	vessels = data / "vessels.csv"
	output = cwd / "output"
