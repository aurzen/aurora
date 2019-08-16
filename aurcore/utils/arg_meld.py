import inspect
import itertools
import types
import functools


def _meld_dummy():
    pass


def _meld(source, dest):
    source_spec = inspect.getfullargspec(source)
    dest_spec = inspect.getfullargspec(dest)

    if source_spec.varargs or source_spec.varkw:
        raise ValueError("The source function may not take variable arguments.")

    source_all = source_spec.args
    dest_all = dest_spec.args

    if source_spec.defaults:
        source_pos = source_all[:-len(source_spec.defaults)]
        source_kw = source_all[-len(source_spec.defaults):]
    else:
        source_pos = source_all
        source_kw = []

    if dest_spec.defaults:
        dest_pos = dest_all[:-len(dest_spec.defaults)]
        dest_kw = dest_all[-len(dest_spec.defaults):]
    else:
        dest_pos = dest_all
        dest_kw = []

    args_merged = dest_pos

    for a in itertools.chain(source_pos, dest_kw, source_kw):
        if a not in args_merged:
            args_merged.append(a)

    kwonlyargs_merged = dest_spec.kwonlyargs
    for a in source_spec.kwonlyargs:
        if a not in kwonlyargs_merged:
            kwonlyargs_merged.append(a)

    args_all = tuple(args_merged + kwonlyargs_merged)

    passer_code = types.CodeType(len(args_merged), len(kwonlyargs_merged),
                                 _meld_dummy.__code__.co_nlocals,
                                 _meld_dummy.__code__.co_stacksize,
                                 source.__code__.co_flags,
                                 _meld_dummy.__code__.co_code, (), (),
                                 args_all, dest.__code__.co_filename,
                                 dest.__code__.co_name,
                                 dest.__code__.co_firstlineno,
                                 dest.__code__.co_lnotab)
    passer = types.FunctionType(passer_code, globals())
    dest.__wrapped__ = passer

    # defaults, annotations
    defaults = dest.__defaults__
    if defaults is None:
        defaults = []
    else:
        defaults = list(defaults)
    if source.__defaults__ is not None:
        defaults.extend(source.__defaults__)

    # ensure we take destination’s return annotation
    has_dest_ret = 'return' in dest.__annotations__
    if has_dest_ret:
        dest_ret = dest.__annotations__['return']

    for v in ('__kwdefaults__', '__annotations__'):
        out = getattr(source, v)
        if out is None:
            out = {}
        if getattr(dest, v) is not None:
            out = out.copy()
            out.update(getattr(dest, v))
            setattr(passer, v, out)

    if has_dest_ret:
        passer.__annotations__['return'] = dest_ret
    dest.__annotations__ = passer.__annotations__

    passer.__defaults__ = tuple(defaults)
    if not dest.__doc__:
        dest.__doc__ = source.__doc__
    return dest


def meld_args(src_fn):
    """Merge the signatures of two functions."""
    return functools.partial(_meld, src_fn)
