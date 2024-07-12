import copy
import re
from pysubs2 import SSAFile, SSAStyle, SSAEvent


def info_select_current_info(ssafile: SSAFile, **kwargs) -> list:
    return [ssafile.info]


def info_action_save(ssafile: SSAFile, info: dict, **kwargs) -> dict:
    return copy.copy(info)


def info_action_update(ssafile: SSAFile, info: dict, **kwargs):
    info.update(kwargs)

    return info


def styles_select_all(ssafile: SSAFile, **kwargs):
    return [ssafile.styles[k] for k in ssafile.styles]


def styles_select_top(ssafile: SSAFile, **kwargs):

    counts = {}
    for event in ssafile.events:

        if event.style in counts:
            counts[event.style] += 1
        else:
            counts[event.style] = 1

    value = max(counts.values())
    key = next(k for k, v in counts.items() if v == value)

    return [ssafile.styles.get(key)]


def styles_action_scale(ssafile: SSAFile, style: SSAStyle, **kwargs):

    y_ratio = float(kwargs["y_new"]) / float(kwargs["y_old"])
    x_ratio = float(kwargs["x_new"]) / float(kwargs["x_old"])

    style.fontsize = round(style.fontsize * y_ratio)
    style.marginv = round(style.marginv * y_ratio)
    style.marginl = round(style.marginl * x_ratio)
    style.marginr = round(style.marginr * x_ratio)

    return style


def events_action_scale(ssafile: SSAFile, event: SSAEvent, **kwargs):

    y_ratio = float(kwargs["y_new"]) / float(kwargs["y_old"])
    x_ratio = float(kwargs["x_new"]) / float(kwargs["x_old"])

    event.marginv = round(event.marginv * y_ratio)
    event.marginl = round(event.marginl * x_ratio)
    event.marginr = round(event.marginr * x_ratio)

    return event


def styles_action_update(ssafile: SSAFile, style: SSAStyle, **kwargs):
    style.__dict__.update(kwargs)

    return style


def styles_remove(ssafile: SSAFile, style: SSAStyle, **kwargs):
    for key in ssafile.styles.keys():
        if ssafile.styles[key] is style:
            del ssafile.styles[key]

    return style


def events_select_all(ssafile: SSAFile, **kwargs):
    return ssafile.events


def events_filter_regex(ssafile: SSAFile, event: SSAEvent, regex="", **kwargs):
    return bool(re.match(regex, event.text))


def events_filter_properties(ssafile: SSAFile, event: SSAEvent, **kwargs):

    fil = True

    if "is_comment" in kwargs:
        fil = fil and event.is_comment == kwargs["is_comment"]

    if "is_drawing" in kwargs:
        fil = fil and event.is_drawing == kwargs["is_drawing"]

    return fil


def events_action_regex_substitution(
    ssafile: SSAFile, event: SSAEvent, regex="", replace=""
):
    event.text = re.sub(regex, replace, event.text)

    return event


def events_action_delete(ssafile: SSAFile, event: SSAEvent, regex="", replace=""):
    ssafile.events.remove(event)
