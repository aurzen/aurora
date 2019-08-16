def parametrized(dec):
    def layer(*args, **kwargs):
        def repl(f):
            return dec(f, *args, **kwargs)

        return repl

    return layer


def query_dict_softcase(dictionary: dict, key):
    if key in dictionary.keys():
        return dictionary[key]
    if not isinstance(key, str):
        raise KeyError(f"Key {key} not found in dict {dictionary}")
    case_insensitive_dict = {k.lower(): v for k, v in dictionary.items()}
    if key.lower() in case_insensitive_dict.keys():
        return case_insensitive_dict[key.lower()]


def magic_search(key):
    import inspect
    try:
        return dict(inspect.getmembers(
            inspect.stack()[-1][0]))["f_globals"][key]
    except KeyError:
        for i in inspect.stack()[::-1]:
            try:
                return dict(inspect.getmembers(i[0]))["f_locals"][key]
            except KeyError:
                pass
    raise KeyError("Could not find key " + key)


async def aeval(statement, ctx=None):
    magic_search("pers_l").append(await eval(statement))
    return magic_search("pers_l")[-1]


def execute(exec_type, statement, ctx=None, async_loop=None):
    import traceback
    return_val = None
    ms = magic_search
    try:
        if exec_type == "exec":
            exec(statement, globals(), locals())
        if exec_type == "eval":
            return_val = eval(statement)

        if exec_type == "aexec":
            async_loop = ms("client").loop if not async_loop else async_loop
            if len(statement.split("\n")) == 1 and ";" not in statement and not statement.startswith("await"):
                statement = f"await ctx.m.channel.send(({statement}))"
            indent = "    "
            indented_values = "\n".join([indent * 2 + statement for statement in statement.split("\n")])
            wrapped_to_run = ("import asyncio\n"
                              "import traceback\n"
                              "async def main():\n"
                              f"{indent}try:\n"
                              f"{indented_values}\n"
                              f"{indent}except Exception as e:"
                              f"{indent * 2}await ctx.m.channel.send(traceback.format_exc())"
                              f"\n"
                              "async_loop.create_task(main())")
            exec(wrapped_to_run, locals())
            print(f"Set return val in aexec?: {return_val}", flush=True)
            return_val = f"Created task successfully"
    except Exception:
        return_val = traceback.format_exc()
    return str(return_val).replace("Austin", "zen")


def check_int(s):
    s = str(s)
    try:
        return int(s)
    except TypeError:
        return None


def intorstr(x):
    try:
        return int(x)
    except ValueError:
        return x


import datetime


def timeme(dt: datetime.datetime) -> datetime.datetime:
    now = datetime.datetime.now()
    print(now - dt)
    return now


def rgb_percent(percent):
    if percent >= .5:
        return 255, 255 - int((percent - 0.5) * 2 * 255), 0
    else:
        return int(percent * 2 * 255), 255, 0


def threshold_string(string, thresh):
    if len(string) > thresh:
        return string[:thresh] + "..."
    return string


def k_bool(dictionary, key):
    return key in dictionary and dictionary[key]
