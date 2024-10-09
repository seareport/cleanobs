from __future__ import annotations

import holoviews as hv  # type: ignore[import-untyped]
import pandas as pd
import panel as pn
from bokeh.models.formatters import NumeralTickFormatter

from ._data import dump_trans
from ._data import load
from ._data import load_era5
from ._data import load_raw
from ._data import load_trans
from ._data import transform
from ._detide import calc_surge
from ._detide import load_constituents


# from bokeh.models import CrosshairTool
# from bokeh.models import Span
# CROSSHAIR = CrosshairTool(overlay=[Span(dimension="width"), Span(dimension="height")])

hv.extension("bokeh", inline=True)
pn.extension(throttled=True, inline=True, ready_notification="Ready")

YFORMATTER = NumeralTickFormatter(format="0.00")

hv.opts.defaults(
    hv.opts.Curve(
        responsive=True,
        show_grid=True,
        tools=["hover", "crosshair", "undo"],
        active_tools=["box_zoom"],
        # yformatter=YFORMATTER,
    ),
    hv.opts.Path(
        responsive=True,
        show_grid=True,
        # yformatter=YFORMATTER,
    ),
    hv.opts.RGB(responsive=True, show_grid=True),
    hv.opts.Image(responsive=True, show_grid=True),
    hv.opts.Scatter(
        responsive=True,
        show_grid=True,
        # yformatter=YFORMATTER,
    ),
    hv.opts.Spikes(responsive=True, show_grid=True),
    hv.opts.VLine(color="grey", line_width=2, line_dash="dashed"),
)


def show(*objs, threaded=True, **kwargs) -> pn.StoppableThread | pn.Server:  # type: ignore[name-defined]
    kwargs["threaded"] = threaded
    return pn.serve(pn.Column(*objs), **kwargs)


def dshow(*objs, threaded=True, **kwargs):
    from holoviews.operation.datashader import datashade  # type: ignore[import-untyped]

    kwargs["threaded"] = threaded
    return pn.serve(pn.Column(*[datashade(obj) for obj in objs]), **kwargs)


def rshow(*objs, threaded=True, **kwargs):
    from holoviews.operation.datashader import rasterize

    kwargs["threaded"] = threaded
    return pn.serve(pn.Column(*[rasterize(obj) for obj in objs]), **kwargs)


def get_rolling_era5_msl(era5: pd.DataFrame, days: int = 3):
    era5_rolling = (
        era5[["msl"]].rolling(pd.Timedelta(days=days), center=True).min().assign(value=0).reset_index()
    )
    path = hv.Path(era5_rolling, vdims=["msl"])
    path = path.opts(
        line_width=5,
        height=50,
        colorbar=False,
        colorbar_position="top",
        colorbar_opts={"width": 500, "location": "top_center", "height": 10},
        cmap="reds",
        # duh... https://github.com/holoviz/holoviews/issues/4862#issuecomment-1800276275
        color=hv.dim("msl"),
        clim=(100_000, 96_000),
        yaxis=False,
        xaxis=False,
        gridstyle={"ygrid_line_width": 0},
        show_grid=True,
        title="MSL (kPa)",
        tools=["hover"],
    )
    return path


def get_rolling_era5_wind(era5: pd.DataFrame, days: int = 3):
    era5_rolling = (
        era5[["wind_mag"]].rolling(pd.Timedelta(days=days), center=True).max().assign(value=0).reset_index()
    )
    path = hv.Path(era5_rolling, vdims=["wind_mag"])
    path = path.opts(
        line_width=5,
        height=50,
        colorbar=False,
        colorbar_position="top",
        colorbar_opts={"width": 500, "location": "top_center", "height": 10},
        cmap="blues",
        # duh... https://github.com/holoviz/holoviews/issues/4862#issuecomment-1800276275
        color=hv.dim("wind_mag"),
        clim=(10, 20),
        yaxis=False,
        xaxis=False,
        gridstyle={"ygrid_line_width": 0},
        show_grid=True,
        title="Wind Magnitude (m/s^2)",
        tools=["hover"],
        hover_tooltips=[("Wind Magnitude", "@wind_mag{0.0f}")],  # use @{ } for dims with spaces
        hover_formatters={"wind_mag": "printf"},  # use 'printf' formatter for '@{adj close}' field
    )
    return path


def get_rolling_surge_std(detided: pd.DataFrame, days: int = 1):
    rolling = (
        detided[["utide_surge"]]
        .rolling(pd.Timedelta(days=days), center=True)
        .std()
        .assign(value=0)
        .reset_index()
    )
    path = hv.Path(rolling, vdims=["utide_surge"])
    path = path.opts(
        line_width=5,
        height=100,
        colorbar=True,
        colorbar_position="top",
        colorbar_opts={"width": 500, "location": "top_center", "height": 10},
        cmap="blues",
        # duh... https://github.com/holoviz/holoviews/issues/4862#issuecomment-1800276275
        color=hv.dim("utide_surge"),
        clim=(0.04, None),
        yaxis=False,
        xaxis=False,
        gridstyle={"ygrid_line_width": 0},
        show_grid=True,
        # title="Wind Magnitude (m/s^2)",
        tools=["hover"],
        # hover_tooltips=[("Surge STD", "@utide_surge{0.0f}")],  # use @{ } for dims with spaces
        # hover_formatters={"utide_surge": "printf"},  # use 'printf' formatter for '@{adj close}' field
    )
    return path


def _on_add_timestamps(sr, trans, selection):
    if selection.index:
        trans.add_timestamps(sr.index[selection.index])


def _on_add_date_range(sr, trans, selection):
    if selection.index:
        start, end = sorted(
            (
                sr.index[selection.index[0]],
                sr.index[selection.index[-1]],
            ),
        )
        trans.add_date_range(start=start, end=end)


def _on_add_tsunami(sr, trans, selection):
    if selection.index:
        start = sr.index[selection.index[0]]  # .to_pydatetime().isoformat()
        end = sr.index[selection.index[-1]]  # .to_pydatetime().isoformat()
        trans.add_tsunami(start=start, end=end)


def _on_serialize(trans):
    dump_trans(trans)


# def clean(
#     unique_id: str,
#     start: pd.Timestamp,
#     months: int = 6,
#     offset: int = 15,
#     **kwargs,
# ) -> None:
#     """
#     Clean up data for a specific period
#
#     Parameters
#     ----------
#     unique_id:
#         The unique_id of the tide gauge station
#     start:
#         The start date
#     months:
#         The size of the window
#     offset:
#         The size of the offset in days
#     """
#     # Calculate limits
#     start = pd.Timestamp(start)
#     if start.tz is None:
#         start = start.tz_localize(tz="utc")
#     else:
#         start = start.tz_convert(tz="utc")
#     inner_start = start
#     inner_end = start + pd.DateOffset(months=months)
#     outer_start = inner_start - pd.Timedelta(days=offset)
#     outer_end = inner_end + pd.Timedelta(days=offset)
#     # load data
#     trans = load_trans(unique_id)
#     df = load_raw(unique_id).loc[outer_start:outer_end]
#     dft = transform(df, trans)
#     sr = dft.clean
#     era5 = load_era5(unique_id).loc[outer_start:outer_end][["msl", "wind_mag"]]
#
#     selection = hv.streams.Selection1D()
#
#     add_timestamps_button = pn.widgets.Button(name="Add timestamps", button_type="warning")
#     add_date_range_button = pn.widgets.Button(name="Add date range", button_type="warning")
#     add_tsunami_button = pn.widgets.Button(name="Add tsunami", button_type="warning")
#     compare_button = pn.widgets.Button(name="Compare", button_type="success")
#     serialize_button = pn.widgets.Button(name="Serialize", button_type="danger")
#
#     add_timestamps_button.on_click(lambda _: _on_add_timestamps(sr=sr, trans=trans, selection=selection))
#     add_date_range_button.on_click(lambda _: _on_add_date_range(sr=sr, trans=trans, selection=selection))
#     add_tsunami_button.on_click(lambda _: _on_add_tsunami(sr=sr, trans=trans, selection=selection))
#     compare_button.on_click(
#         lambda _: compare(unique_id=unique_id, start=start, months=months, offset=offset)
#     )
#     serialize_button.on_click(lambda _: _on_serialize(trans))
#
#     curve = hv.Curve(sr).opts(
#         tools=["hover", "crosshair", "undo"],
#     )
#     points = hv.Scatter(sr).opts(
#         tools=["hover", "box_select"],
#         active_tools=["box_zoom"],
#         color="gray",
#         nonselection_color="gray",
#         selection_color="red",
#         selection_alpha=1.0,
#         nonselection_alpha=0.3,
#         labelled=[],
#         show_legend=False,
#         size=2,
#     )
#     selection.source = points
#
#     return show(
#         pn.Row(
#             add_timestamps_button,
#             add_date_range_button,
#             add_tsunami_button,
#             pn.HSpacer(width_policy="max"),
#             compare_button,
#             serialize_button,
#         ),
#         get_rolling_era5_wind(era5[["wind_mag"]]),
#         get_rolling_era5_msl(era5[["msl"]]),
#         hv.Overlay(
#             (
#                 hv.VLine(outer_start),
#                 hv.VLine(inner_start),
#                 curve,
#                 points,
#                 hv.VLine(inner_end),
#                 hv.VLine(outer_end),
#             )
#         ),
#     )


def clean(
    unique_id: str,
    start: str | pd.Timestamp,
    include_surge: bool = False,
    months: int = 6,
    offset: int = 15,
) -> None:
    """
    Clean up data for a specific period

    Parameters
    ----------
    unique_id:
        The unique_id of the tide gauge station
    start:
        The start date
    months:
        The size of the window
    offset:
        The size of the offset in days
    """
    # Calculate limits
    start = pd.Timestamp(start)
    if start.tz is None:
        start = start.tz_localize(tz="utc")
    else:
        start = start.tz_convert(tz="utc")
    inner_start = start
    inner_end = start + pd.DateOffset(months=months)
    outer_start = inner_start - pd.Timedelta(days=offset)
    outer_end = inner_end + pd.Timedelta(days=offset)
    # load data
    era5 = load_era5(unique_id).loc[outer_start:outer_end][["msl", "wind_mag"]]  # type: ignore[misc]
    trans = load_trans(unique_id)
    df = load_raw(unique_id).loc[outer_start:outer_end]  # type: ignore[misc]
    # df = df.reindex(
    #     df.index.union(pd.date_range(df.index[0], df.index[-1], freq=df.attrs["raw_main_interval"]))
    # ).sort_index()
    dft = transform(df, trans)
    sr = dft.clean

    if include_surge:
        const = load_constituents(unique_id)
        dft = calc_surge(dft.loc[inner_start:inner_end], const, "utide")  # type: ignore[misc]
        surge_curve = hv.Curve(dft.utide_surge).opts(xlabel="", ylabel="")
        utide_curve = hv.Curve(dft.utide).opts(xlabel="", ylabel="", color="green")
        # surge_std_bar = get_rolling_surge_std(dft[["utide_surge"]])
        surge_std_bar = None
        std = dft.utide_surge.std()
        mean = dft.utide_surge.mean()
        maximum = dft.utide_surge.max()
        minimum = dft.utide_surge.min()
    else:
        surge_curve = None
        utide_curve = None
        surge_std_bar = None
        std = dft.clean.std()
        mean = dft.clean.mean()
        maximum = dft.clean.max()
        minimum = dft.clean.min()

    add_timestamps_button = pn.widgets.Button(name="Add timestamps", button_type="warning")
    add_date_range_button = pn.widgets.Button(name="Add date range", button_type="warning")
    add_tsunami_button = pn.widgets.Button(name="Add tsunami", button_type="warning")
    compare_button = pn.widgets.Button(name="Compare", button_type="success")
    serialize_button = pn.widgets.Button(name="Serialize", button_type="danger")

    selection = hv.streams.Selection1D()
    add_timestamps_button.on_click(lambda _: _on_add_timestamps(sr=sr, trans=trans, selection=selection))
    add_date_range_button.on_click(lambda _: _on_add_date_range(sr=sr, trans=trans, selection=selection))
    add_tsunami_button.on_click(lambda _: _on_add_tsunami(sr=sr, trans=trans, selection=selection))
    compare_button.on_click(
        lambda _: compare(unique_id=unique_id, start=start, months=months, offset=offset),
    )
    serialize_button.on_click(lambda _: _on_serialize(trans))

    curve = hv.Curve(sr)
    points = hv.Scatter(sr).opts(
        tools=["hover", "box_select"],
        color="gray",
        nonselection_color="gray",
        selection_color="red",
        selection_alpha=1.0,
        nonselection_alpha=0.3,
        labelled=[],
        show_legend=False,
        size=2,
    )
    selection.source = points
    era5_wind_bar = get_rolling_era5_wind(era5[["wind_mag"]])
    era5_msl_bar = get_rolling_era5_msl(era5[["msl"]])

    title = f"## {unique_id} {inner_start.strftime('%Y-%m')}\n #### mean: {mean:0.3f} std: {std:0.3f} max: {maximum:0.2f} min: {minimum:0.2f}"
    return show(
        pn.Row(
            add_timestamps_button,
            add_date_range_button,
            add_tsunami_button,
            pn.HSpacer(width_policy="max"),
            pn.pane.Markdown(title),
            pn.HSpacer(width_policy="max"),
            compare_button,
            serialize_button,
        ),
        era5_wind_bar,
        era5_msl_bar,
        surge_std_bar,
        surge_curve,
        hv.Overlay(
            (
                hv.VLine(outer_start),
                hv.VLine(inner_start),
                curve,
                points * utide_curve if utide_curve else points,
                hv.VLine(inner_end),
                hv.VLine(outer_end),
            ),
        ),
    )


def compare(
    unique_id: str,
    start: pd.Timestamp,
    months: int = 6,
    offset: int = 15,
) -> None:
    # Calculate limits
    start = pd.Timestamp(start)
    if start.tz is None:
        start = start.tz_localize(tz="utc")
    else:
        start = start.tz_convert(tz="utc")
    inner_start = start
    inner_end = start + pd.DateOffset(months=months)
    outer_start = inner_start - pd.Timedelta(days=offset)
    outer_end = inner_end + pd.Timedelta(days=offset)
    # load data
    trans = load_trans(unique_id)
    df = load_raw(unique_id).loc[outer_start:outer_end]  # type: ignore[misc]
    dft = transform(df, trans).drop(columns="raw")
    era5 = load_era5(unique_id).loc[outer_start:outer_end][["msl", "wind_mag"]]  # type: ignore[misc]
    return show(
        get_rolling_era5_wind(era5[["wind_mag"]]),
        get_rolling_era5_msl(era5[["msl"]]),
        hv.Overlay(
            (
                hv.VLine(outer_start),
                hv.VLine(inner_start),
                hv.Curve(dft.clean, label="clean"),
                hv.Curve(dft.date_ranges, label="date_ranges"),
                hv.Curve(dft.timestamps, label="timestamps"),
                hv.Curve(dft.tsunamis, label="tsunamis"),
                hv.VLine(inner_end),
                hv.VLine(outer_end),
                # .opts(tools=["hover", "crosshair", "undo"]
            ),
        ),
    )


def quick_plot(df_or_unique_id: str | pd.DataFrame, column: str):
    if isinstance(df_or_unique_id, str):
        df = load(df_or_unique_id)[column]
    else:
        df = df_or_unique_id[column]
    if df.index.tz is not None:  # type: ignore[attr-defined]
        df.index = df.index.tz_convert(None)  # type: ignore[attr-defined]
    curve = hv.Curve(df)
    spikes = hv.Spikes(df)
    attrs = df.attrs
    if attrs:
        title = f"{attrs['provider_id']}-{attrs.get('sensor', ' ')} lon: {attrs['lon']} lat: {attrs['lat']}"
    else:
        title = ""
    layout = (curve + spikes).opts(title=title).cols(1)
    return dshow(layout)
