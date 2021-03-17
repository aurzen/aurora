from __future__ import annotations

import typing as ty

import yaml
import pathlib as pl
import collections as clc
import contextlib
import asyncio.locks
import aurcore
import abc

CACHED_CONFIGS = 100
CONFIG_ROOT = pl.Path("./.aursave")
CONFIG_ROOT.mkdir(exist_ok=True)


class Persist(abc.ABC, metaclass=aurcore.util.Singleton):
   Identifier = ty.TypeVar('Identifier')

   def __init__(self, name: str, base: ty.Dict = None):
      self.config_dir = CONFIG_ROOT / name
      self.config_dir.mkdir(exist_ok=True)
      self.base = base
      self.cached: clc.OrderedDict = clc.OrderedDict()
      self.locks: ty.Dict[str, asyncio.locks.Lock] = clc.defaultdict(asyncio.locks.Lock)

   def get_identifier(self, identifier: Identifier) -> str:
      assert isinstance(identifier, str)
      return identifier

   def _write_config_file(self, config_id: str, data) -> None:
      local_config_path: pl.Path = self.config_dir / f"{config_id}.yaml"
      with local_config_path.open("w") as f:
         yaml.safe_dump(data, f)

   def _load_config_file(self, config_id: str) -> ty.Dict:
      local_config_path: pl.Path = self.config_dir / f"{config_id}.yaml"
      try:
         with local_config_path.open("r") as f:
            local_config = yaml.safe_load(f)
      except FileNotFoundError:
         local_config = {}
      return local_config

   def of(self, identifiable: Identifier) -> ty.Dict[str, ty.Any]:
      identifier = self.get_identifier(identifiable)
      if identifier in self.cached:
         self.cached.move_to_end(identifier, last=False)
         configs = self.cached[identifier]
      else:
         local_config = self._load_config_file(identifier)
         combined_dict = {**self.base, **local_config}
         cleaned_dict = {k: combined_dict[k] for k in self.base}
         if cleaned_dict != local_config:
            self._write_config_file(identifier, cleaned_dict)

         self.cached[identifier] = cleaned_dict
         if len(self.cached) > CACHED_CONFIGS:
            self.cached.popitem()

         configs = cleaned_dict

      return configs

   @contextlib.asynccontextmanager
   async def writeable_conf(self, identifiable: Identifier):
      config_id = self.get_identifier(identifiable)
      async with self.locks[config_id]:
         output_dict = self.of(identifiable)
         try:
            yield output_dict
         finally:
            self._write_config_file(config_id, output_dict)
            self.cached[config_id] = output_dict
