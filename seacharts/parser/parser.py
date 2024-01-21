import warnings
from pathlib import Path
from typing import Generator

import fiona

from seacharts.utils import paths


class DataParser:
    def __init__(self, bounding_box: tuple, path_strings: list[str]):
        self.bounding_box = bounding_box
        self.paths = set([p.resolve() for p in (map(Path, path_strings))])
        self.paths.update(paths.default_resources)

    @property
    def gdb_paths(self) -> Generator[Path, None, None]:
        for path in self.paths:
            if not path.is_absolute():
                path = paths.cwd / path
            if self._is_gdb(path):
                yield path
            elif path.is_dir():
                for p in path.iterdir():
                    if self._is_gdb(p):
                        yield p

    def load_fgdb(self, layer) -> list[dict]:
        depth = layer.depth if hasattr(layer, "depth") else 0
        return list(self._read_fgdb(layer.label, layer._external_labels, depth))

    def load_shapefile(self, layer) -> list[dict]:
        return list(self._read_shapefile(layer.label))

    def save(self, layer) -> None:
        self._write_to_shapefile(layer)

    def _read_fgdb(
        self, name: str, external_labels: list[str], depth: int
    ) -> Generator:
        for gdb_path in self.gdb_paths:
            records = self._parse_layers(gdb_path, external_labels, depth)
            yield from self._parse_records(records, name)

    def _parse_layers(
        self, path: Path, external_labels: list[str], depth: int
    ) -> Generator:
        for label in external_labels:
            if isinstance(label, dict):
                layer, depth_label = label["layer"], label["depth"]
                records = self._read_spatial_file(path, layer=layer)
                for record in records:
                    if record["properties"][depth_label] >= depth:
                        yield record
            else:
                yield from self._read_spatial_file(path, layer=label)

    def _read_shapefile(self, label: str) -> Generator:
        file_path = self._shapefile_path(label)
        if file_path.exists():
            yield from self._read_spatial_file(file_path)

    def _read_spatial_file(self, path: Path, **kwargs) -> Generator:
        with fiona.open(path, "r", **kwargs) as source:
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=RuntimeWarning)
                for record in source.filter(bbox=self.bounding_box):
                    yield record
        return

    def _shapefile_writer(self, file_path, geometry_type):
        return fiona.open(
            file_path,
            "w",
            schema=self._as_record("int", geometry_type),
            driver="ESRI Shapefile",
            crs={"init": "epsg:25833"},
        )

    def _write_to_shapefile(self, shape):
        geometry = shape.mapping
        file_path = self._shapefile_path(shape.label)
        with self._shapefile_writer(file_path, geometry["type"]) as sink:
            sink.write(self._as_record(shape.depth, geometry))

    @staticmethod
    def _as_record(depth, geometry):
        return {"properties": {"depth": depth}, "geometry": geometry}

    @staticmethod
    def _is_gdb(path: Path) -> bool:
        return path.is_dir() and path.suffix == ".gdb"

    @staticmethod
    def _parse_records(records, name):
        for i, record in enumerate(records):
            print(f"\rNumber of {name} records read: {i + 1}", end="")
            yield record
        return

    @staticmethod
    def _shapefile_path(label):
        return paths.shapefiles / label / (label + ".shp")
