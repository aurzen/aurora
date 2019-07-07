import copy
import pickle
import pprint
import traceback
import TOKENS

# DEPRECATED

class Config:
    server_configs = {}

    def __init__(self, botname, config_defaults=None):
        self.name = botname
        self.DEFAULTS = config_defaults
        self.TOKEN = getattr(TOKENS, self.name)

        pass

    def of(self, guild) -> dict:
        if not guild:
            return {}
        if guild.id not in self.server_configs.keys():
            self.initialize_default(guild_id=guild.id)
            self.save()
        return self.server_configs[guild.id]

    def initialize_default(self, guild_id):
        self.server_configs[guild_id] = copy.deepcopy(self.DEFAULTS)
        self.save()

    def reset_key(self, guild_id, key):
        try:
            self.server_configs[guild_id][key] = copy.deepcopy(self.DEFAULTS[key])
        except KeyError:
            print(traceback.format_exc())
            del self.server_configs[guild_id][key]

    def reset(self, guild_id):
        self.initialize_default(guild_id)

    def clean(self):
        self.server_configs = {}
        self.save()
        return self

    def save(self):
        with open(f"{self.name}_configs.pickle", "wb") as f:
            pickle.dump(self.server_configs, f)
        return self

    def load(self):
        try:
            with open(f"{self.name}_configs.pickle", "rb") as f:
                self.server_configs = pickle.load(f)
        except IOError:
            pass
        return self

    def generate_readable(self, guild_id=None):
        if not guild_id:
            return pprint.pformat(self.server_configs)
        else:
            return pprint.pformat(self.server_configs[guild_id])

