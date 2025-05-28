import re
from typing import Any

from pysubs2 import SSAEvent, SSAFile, SSAStyle

from .user_actions import *


def info_select_current_info(ssafile: SSAFile, **kwargs) -> list[dict[str, Any]]:
    return [ssafile.info]


def info_action_update(ssafile: SSAFile, items: list[dict[str, Any]], **kwargs) -> list:
    for info in items:
        info.update(kwargs)

    return items


def styles_select_all(ssafile: SSAFile, **kwargs) -> list[SSAStyle]:
    return [ssafile.styles[k] for k in ssafile.styles]


def styles_select_top(ssafile: SSAFile, **kwargs) -> list[SSAStyle]:
    counts = {}
    for event in ssafile.events:
        if event.style in counts:
            counts[event.style] += 1
        else:
            counts[event.style] = 1

    value = max(counts.values())
    key = next(k for k, v in counts.items() if v == value)

    return [ssafile.styles[key]]


def styles_action_scale_margins(
    ssafile: SSAFile, items: list[SSAStyle], **kwargs
) -> list:
    """Scale margins for all styles in the items list."""
    y_ratio = float(kwargs["y_new"]) / float(kwargs["y_old"])
    x_ratio = float(kwargs["x_new"]) / float(kwargs["x_old"])

    for style in items:
        if isinstance(style, SSAStyle):
            style.fontsize = round(style.fontsize * y_ratio)
            style.marginv = round(style.marginv * y_ratio)
            style.marginl = round(style.marginl * x_ratio)
            style.marginr = round(style.marginr * x_ratio)

    return items


def styles_action_scale(ssafile: SSAFile, items: list[SSAStyle], **kwargs) -> list:
    styles_action_scale_margins(ssafile, items, **kwargs)

    return items


def events_action_scale_position(
    ssafile: SSAFile, items: list[SSAEvent], **kwargs
) -> list:
    """Scale position for all events in the items list."""
    y_ratio = float(kwargs["y_new"]) / float(kwargs["y_old"])
    x_ratio = float(kwargs["x_new"]) / float(kwargs["x_old"])

    for event in items:
        if isinstance(event, SSAEvent):
            m: re.Match
            for m in re.finditer(r"\\pos\(([0-9\.]+),([0-9\.]+)\)", str(event.text)):
                x_pos = float(m.group(1)) * x_ratio
                y_pos = float(m.group(2)) * y_ratio

                new_pos = f"\\pos({x_pos:.1f},{y_pos:.1f})"
                event.text = event.text.replace(str(m.group(0)), new_pos)
    return items


def events_action_scale_margins(
    ssafile: SSAFile, items: list[SSAEvent], **kwargs
) -> list:
    """Scale margins for all events in the items list."""
    y_ratio = float(kwargs["y_new"]) / float(kwargs["y_old"])
    x_ratio = float(kwargs["x_new"]) / float(kwargs["x_old"])

    for event in items:
        if isinstance(event, SSAEvent):
            event.marginv = round(event.marginv * y_ratio)
            event.marginl = round(event.marginl * x_ratio)
            event.marginr = round(event.marginr * x_ratio)
    return items


def events_action_scale(ssafile: SSAFile, items: list[SSAEvent], **kwargs) -> list:
    """Scale both margins and position for all events in the items list."""
    events_action_scale_margins(ssafile, items, **kwargs)
    events_action_scale_position(ssafile, items, **kwargs)
    return items


def styles_action_update_properties(
    ssafile: SSAFile, items: list[SSAStyle], **kwargs
) -> list:
    """Update properties for all styles in the items list."""
    for style in items:
        if isinstance(style, SSAStyle):
            style.__dict__.update(kwargs)
    return items


def styles_remove(ssafile: SSAFile, items: list[SSAStyle], **kwargs) -> list:
    """Remove all styles in the items list."""
    for style in items:
        if isinstance(style, SSAStyle):
            for key in list(ssafile.styles.keys()):
                if ssafile.styles[key] is style:
                    del ssafile.styles[key]
                    break

    return items


def events_select_all(ssafile: SSAFile, **kwargs) -> list[SSAEvent]:
    return ssafile.events


def events_filter_regex(
    ssafile: SSAFile, items: list[SSAEvent], regex: str = "", **kwargs
) -> list[SSAEvent]:
    """Filter events by regex pattern."""
    return [
        event
        for event in items
        if isinstance(event, SSAEvent) and bool(re.match(regex, event.text))
    ]


def events_filter_properties(
    ssafile: SSAFile, items: list[SSAEvent], **kwargs
) -> list[SSAEvent]:
    """Filter events by properties."""
    results = []

    for event in items:
        if not isinstance(event, SSAEvent):
            continue

        fil = True

        if "is_comment" in kwargs:
            fil = fil and event.is_comment == kwargs["is_comment"]

        if "is_drawing" in kwargs:
            fil = fil and event.is_drawing == kwargs["is_drawing"]

        if fil:
            results.append(event)

    return results


def events_action_regex_substitution(
    ssafile: SSAFile,
    items: list[SSAEvent],
    regex: str = "",
    replace: str = "",
    **kwargs,
) -> list:
    """Apply regex substitution to all events in the items list."""
    for event in items:
        if isinstance(event, SSAEvent):
            event.text = re.sub(regex, replace, event.text)
    return items


def events_action_delete(ssafile: SSAFile, items: list[SSAEvent], **kwargs) -> list:
    """Delete all events in the items list."""
    for event in items:
        if isinstance(event, SSAEvent) and event in ssafile.events:
            ssafile.events.remove(event)

    return items


def events_action_update_properties(
    ssafile: SSAFile, items: list[SSAEvent], **kwargs
) -> list:
    """Update properties for all events in the items list."""
    for event in items:
        if isinstance(event, SSAEvent):
            event.__dict__.update(kwargs)

    return items


def events_misc_remove_miscellaneous_events(ssafile: SSAFile, **kwargs) -> None:
    """Remove miscellaneous events - this doesn't operate on items."""
    ssafile.remove_miscellaneous_events()
