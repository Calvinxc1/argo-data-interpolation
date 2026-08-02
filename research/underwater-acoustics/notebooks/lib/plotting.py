from __future__ import annotations

from pathlib import Path
from typing import Literal, Sequence

import matplotlib.cm as cm
import matplotlib.colors as mcolors
import matplotlib.patheffects as path_effects
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.cm import ScalarMappable
from matplotlib.figure import Figure
from matplotlib.image import AxesImage
from matplotlib.lines import Line2D
from mpl_toolkits.axes_grid1 import make_axes_locatable


def _cell_edges(values: np.ndarray) -> np.ndarray:
    if values.ndim != 1:
        raise ValueError("axis values must be one-dimensional")
    if len(values) == 0:
        raise ValueError("axis values must not be empty")
    if len(values) == 1:
        step = 0.5
        return np.array([values[0] - step, values[0] + step], dtype=float)

    deltas = np.diff(values)
    if np.any(deltas <= 0):
        raise ValueError("axis values must be strictly increasing")

    edges = np.empty(len(values) + 1, dtype=float)
    edges[1:-1] = values[:-1] + deltas / 2
    edges[0] = values[0] - deltas[0] / 2
    edges[-1] = values[-1] + deltas[-1] / 2
    return edges


def _normalize_standard_error(
    standard_error: np.ndarray,
    *,
    se_scale: Literal["panel", "fixed"],
    se_vmin: float | None,
    se_vmax: float | None,
) -> np.ndarray:
    if se_scale == "fixed":
        if se_vmin is None or se_vmax is None:
            raise ValueError("se_vmin and se_vmax are required when se_scale='fixed'")
        lo = float(se_vmin)
        hi = float(se_vmax)
    else:
        finite_error = standard_error[np.isfinite(standard_error)]
        if finite_error.size == 0:
            return np.ones_like(standard_error, dtype=float)
        lo = float(finite_error.min())
        hi = float(finite_error.max())

    if hi < lo:
        raise ValueError("se_vmax must be greater than or equal to se_vmin")
    if hi == lo:
        normalized = np.zeros_like(standard_error, dtype=float)
    else:
        normalized = (standard_error - lo) / (hi - lo)

    normalized = np.clip(normalized, 0.0, 1.0)
    normalized[~np.isfinite(standard_error)] = 1.0
    return normalized


def plot_desaturated_heatmap(
    values: pd.DataFrame,
    standard_error: pd.DataFrame,
    *,
    title: str | None = None,
    cbar_label: str | None = None,
    cmap: str = "turbo",
    value_vmin: float | None = None,
    value_vmax: float | None = None,
    se_scale: Literal["panel", "fixed"] = "panel",
    se_vmin: float | None = None,
    se_vmax: float | None = None,
    neutral_color: tuple[float, float, float] = (0.92, 0.92, 0.92),
    light_mode: bool = False,
    font_scale: float = 1.0,
    add_gridlines: bool = False,
    gridline_labels: bool = True,
    add_land: bool = False,
    land_color: str = "0.85",
    land_zorder: float = 3,
    add_coastline: bool = False,
    coastline_linewidth: float = 0.5,
    coastline_zorder: float = 4,
    extent: tuple[float, float, float, float] | None = None,
    add_colorbar: bool = True,
    cbar_ax: Axes | None = None,
    ax: Axes | None = None,
) -> tuple[Figure, Axes, AxesImage, object | None]:
    if not values.index.equals(standard_error.index) or not values.columns.equals(standard_error.columns):
        raise ValueError("values and standard_error must share identical index and columns")

    latitudes = values.index.to_numpy(dtype=float)
    longitudes = values.columns.to_numpy(dtype=float)
    value_array = values.to_numpy(dtype=float)
    se_array = standard_error.to_numpy(dtype=float)

    finite_values = value_array[np.isfinite(value_array)]
    if finite_values.size == 0:
        raise ValueError("values must contain at least one finite cell")

    if value_vmin is None:
        value_vmin = float(finite_values.min())
    if value_vmax is None:
        value_vmax = float(finite_values.max())
    if value_vmax < value_vmin:
        raise ValueError("value_vmax must be greater than or equal to value_vmin")

    value_norm = mcolors.Normalize(vmin=value_vmin, vmax=value_vmax)
    base_rgba = plt.get_cmap(cmap)(value_norm(value_array))
    se_strength = _normalize_standard_error(
        se_array,
        se_scale=se_scale,
        se_vmin=se_vmin,
        se_vmax=se_vmax,
    )[..., None]

    neutral_rgba = np.ones_like(base_rgba)
    neutral_rgba[..., :3] = neutral_color
    blended_rgba = base_rgba * se_strength + neutral_rgba * (1.0 - se_strength)
    blended_rgba[..., 3] = np.where(np.isfinite(value_array), 1.0, 0.0)

    lon_edges = _cell_edges(longitudes)
    lat_edges = _cell_edges(latitudes)
    image_extent = (lon_edges[0], lon_edges[-1], lat_edges[0], lat_edges[-1])
    map_extent = extent

    created_figure = False
    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 6))
        created_figure = True
    else:
        fig = ax.figure
    ax.set_facecolor(neutral_color)
    foreground_color = "0.1" if light_mode else "0.9"
    gridline_color = "0.35" if light_mode else "0.82"
    gridline_alpha = 0.55 if light_mode else 0.65
    title_size = 14 * font_scale
    label_size = 12 * font_scale
    tick_size = 10 * font_scale

    image = ax.imshow(
        blended_rgba,
        origin="lower",
        extent=image_extent,
        aspect="auto",
        interpolation="nearest",
    )

    if add_gridlines:
        if not hasattr(ax, "gridlines"):
            raise ValueError("add_gridlines=True requires a Cartopy GeoAxes")
        try:
            import cartopy.crs as ccrs
        except ImportError as exc:
            raise ImportError("add_gridlines=True requires cartopy to be installed") from exc

        gridliner = ax.gridlines(
            crs=ccrs.PlateCarree(),
            draw_labels=gridline_labels,
            linewidth=0.5,
            color=gridline_color,
            alpha=gridline_alpha,
            linestyle="--",
        )
        if gridline_labels:
            gridliner.top_labels = False
            gridliner.right_labels = False
            gridliner.xlabel_style = {"color": foreground_color, "size": tick_size}
            gridliner.ylabel_style = {"color": foreground_color, "size": tick_size}
        for artist in getattr(gridliner, "xline_artists", []):
            artist.set_zorder(5)
        for artist in getattr(gridliner, "yline_artists", []):
            artist.set_zorder(5)

    if add_land or add_coastline or map_extent is not None:
        if not hasattr(ax, "add_feature"):
            raise ValueError(
                "add_land, add_coastline, and extent require a Cartopy GeoAxes"
            )
        try:
            import cartopy.crs as ccrs
            import cartopy.feature as cfeature
        except ImportError as exc:
            raise ImportError(
                "map features require cartopy to be installed"
            ) from exc

        if add_land:
            ax.add_feature(cfeature.LAND, facecolor=land_color, zorder=land_zorder)
        if add_coastline:
            ax.add_feature(
                cfeature.COASTLINE,
                linewidth=coastline_linewidth,
                zorder=coastline_zorder,
            )
        if map_extent is not None:
            ax.set_extent(map_extent, crs=ccrs.PlateCarree())

    ax.set_xlabel("Longitude", color=foreground_color, fontsize=label_size)
    ax.set_ylabel("Latitude", color=foreground_color, fontsize=label_size)
    ax.tick_params(colors=foreground_color, labelsize=tick_size)
    for spine in ax.spines.values():
        spine.set_edgecolor(foreground_color)
    if title is not None:
        ax.set_title(title, color=foreground_color, fontsize=title_size)

    colorbar = None
    if add_colorbar:
        scalar_mappable = ScalarMappable(norm=value_norm, cmap=cmap)
        scalar_mappable.set_array([])
        colorbar = fig.colorbar(scalar_mappable, ax=None if cbar_ax is not None else ax, cax=cbar_ax)
        colorbar.ax.set_facecolor(neutral_color)
        colorbar.ax.tick_params(colors=foreground_color, labelcolor=foreground_color, labelsize=tick_size)
        colorbar.outline.set_edgecolor(foreground_color)
        for spine in colorbar.ax.spines.values():
            spine.set_edgecolor(foreground_color)
        if cbar_label is not None:
            colorbar.set_label(cbar_label, color=foreground_color, fontsize=label_size)

    if created_figure:
        fig.tight_layout()

    return fig, ax, image, colorbar


def chart_title(title: str, analysis_date_label: str) -> str:
    return f"{title}\nAnalysis date: {analysis_date_label}"


def matrix_extent(matrix: pd.DataFrame) -> tuple[float, float, float, float]:
    latitudes = matrix.index.to_numpy(dtype=float)
    longitudes = matrix.columns.to_numpy(dtype=float)
    lat_step = float(np.nanmedian(np.diff(latitudes)))
    lon_step = float(np.nanmedian(np.diff(longitudes)))
    return (
        float(longitudes[0] - lon_step / 2),
        float(longitudes[-1] + lon_step / 2),
        float(latitudes[0] - lat_step / 2),
        float(latitudes[-1] + lat_step / 2),
    )


def _add_land_overlay(
    ax: Axes, *, box: Sequence[float | str], grid_alpha: float = 0.6
) -> None:
    try:
        import cartopy.crs as ccrs
        import cartopy.feature as cfeature
    except ImportError as exc:
        raise ImportError("map plotting requires cartopy to be installed") from exc

    ax.add_feature(cfeature.LAND, facecolor="0.78", edgecolor="none", zorder=3)
    ax.add_feature(cfeature.COASTLINE, linewidth=0.55, edgecolor="0.15", zorder=4)
    ax.set_extent(
        (float(box[0]), float(box[1]), float(box[2]), float(box[3])),
        crs=ccrs.PlateCarree(),
    )
    gridliner = ax.gridlines(
        draw_labels=True,
        linewidth=0.25,
        color="white",
        alpha=grid_alpha,
        linestyle="-",
        zorder=5,
    )
    gridliner.top_labels = False
    gridliner.right_labels = False


def save_figure(fig: Figure, *, chart_path: Path, stem: str) -> dict[str, Path]:
    paths = {
        "png": chart_path / f"{stem}.png",
        "svg": chart_path / f"{stem}.svg",
    }
    for output_path in paths.values():
        fig.savefig(output_path, dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor())
    return paths


def plot_matrix(
    matrix: pd.DataFrame,
    *,
    box: Sequence[float | str],
    title: str,
    cbar_label: str,
    cmap: str | mcolors.Colormap,
    interpolation: str,
    vmin: float | None = None,
    vmax: float | None = None,
    fill_missing: float | None = None,
    grid_alpha: float = 0.6,
) -> tuple[Figure, Axes]:
    try:
        import cartopy.crs as ccrs
    except ImportError as exc:
        raise ImportError("map plotting requires cartopy to be installed") from exc

    fig, ax = plt.subplots(figsize=(9, 7), subplot_kw={"projection": ccrs.PlateCarree()})
    fig.patch.set_facecolor("white")
    ax.set_facecolor("0.94")
    values = matrix.to_numpy(dtype=float)
    image_values = (
        np.nan_to_num(values, nan=fill_missing)
        if fill_missing is not None
        else np.ma.masked_invalid(values)
    )

    image = ax.imshow(
        image_values,
        origin="lower",
        extent=matrix_extent(matrix),
        aspect="auto",
        interpolation=interpolation,
        cmap=cmap,
        vmin=vmin,
        vmax=vmax,
        transform=ccrs.PlateCarree(),
        zorder=1,
    )
    ax.set_title(title)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    _add_land_overlay(ax, box=box, grid_alpha=grid_alpha)

    colorbar = fig.colorbar(image, ax=ax)
    colorbar.set_label(cbar_label)
    fig.tight_layout()
    return fig, ax


def _add_support_contours(
    ax: Axes,
    support: pd.DataFrame,
    *,
    contour_levels: list[float],
    contour_labels: list[str] | None = None,
    contour_value_label: str = "W",
    contour_value_precision: int = 3,
    legend_loc: str | None = None,
) -> None:
    try:
        import cartopy.crs as ccrs
    except ImportError as exc:
        raise ImportError("map plotting requires cartopy to be installed") from exc

    support_values = np.ma.masked_invalid(support.to_numpy(dtype=float))
    longitudes = support.columns.to_numpy(dtype=float)
    latitudes = support.index.to_numpy(dtype=float)
    contour_linestyles = ["--", "-", "-."]
    contour_linewidths = [1.15, 1.45, 1.25]
    legend_handles = []
    for index, level in enumerate(contour_levels):
        label = (
            contour_labels[index]
            if contour_labels is not None
            else f"{contour_value_label}={level:.{contour_value_precision}f}"
        )
        linestyle = contour_linestyles[index % len(contour_linestyles)]
        linewidth = contour_linewidths[index % len(contour_linewidths)]
        contour = ax.contour(
            longitudes,
            latitudes,
            support_values,
            levels=[level],
            colors="#111827",
            linewidths=linewidth,
            linestyles=linestyle,
            transform=ccrs.PlateCarree(),
            zorder=2,
        )
        contour.set_path_effects(
            [
                path_effects.Stroke(linewidth=linewidth + 1.7, foreground="white"),
                path_effects.Normal(),
            ]
        )
        legend_handles.append(
            Line2D(
                [0],
                [0],
                color="#111827",
                linewidth=linewidth,
                linestyle=linestyle,
                path_effects=[
                    path_effects.Stroke(linewidth=linewidth + 1.7, foreground="white"),
                    path_effects.Normal(),
                ],
                label=label,
            )
        )
    if legend_loc is not None:
        ax.legend(
            handles=legend_handles,
            loc=legend_loc,
            frameon=True,
            framealpha=0.85,
            facecolor="white",
            edgecolor="0.35",
            fontsize=8,
        )


def plot_matrix_with_support_contours(
    matrix: pd.DataFrame,
    support: pd.DataFrame,
    *,
    box: Sequence[float | str],
    title: str,
    cbar_label: str,
    cmap: str | mcolors.Colormap,
    interpolation: str,
    vmin: float | None = None,
    vmax: float | None = None,
    contour_levels: list[float],
    contour_labels: list[str] | None = None,
    contour_value_label: str = "W",
    contour_value_precision: int = 3,
    legend_loc: str = "lower left",
    grid_alpha: float = 0.6,
) -> tuple[Figure, Axes]:
    if not matrix.index.equals(support.index) or not matrix.columns.equals(support.columns):
        raise ValueError("matrix and support must share identical index and columns")
    try:
        import cartopy.crs as ccrs
    except ImportError as exc:
        raise ImportError("map plotting requires cartopy to be installed") from exc

    values = matrix.to_numpy(dtype=float)
    finite_values = values[np.isfinite(values)]
    if finite_values.size == 0:
        raise ValueError("matrix must contain at least one finite value")

    if vmin is None:
        vmin = float(finite_values.min())
    if vmax is None:
        vmax = float(finite_values.max())

    norm = mcolors.Normalize(vmin=vmin, vmax=vmax)
    image_values = np.ma.masked_invalid(values)

    fig, ax = plt.subplots(figsize=(9, 7), subplot_kw={"projection": ccrs.PlateCarree()})
    fig.patch.set_facecolor("white")
    ax.set_facecolor("0.94")

    image = ax.imshow(
        image_values,
        origin="lower",
        extent=matrix_extent(matrix),
        aspect="auto",
        interpolation=interpolation,
        cmap=cmap,
        norm=norm,
        transform=ccrs.PlateCarree(),
        zorder=1,
    )
    _add_support_contours(
        ax,
        support,
        contour_levels=contour_levels,
        contour_labels=contour_labels,
        contour_value_label=contour_value_label,
        contour_value_precision=contour_value_precision,
        legend_loc=legend_loc,
    )
    ax.set_title(title)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    _add_land_overlay(ax, box=box, grid_alpha=grid_alpha)

    colorbar = fig.colorbar(image, ax=ax)
    colorbar.set_label(cbar_label)

    fig.tight_layout()
    return fig, ax


def _format_raw_support_tick(value: float, _position: int | None = None) -> str:
    if not np.isfinite(value):
        return ""
    if value >= 100:
        return f"{value:.1f}"
    if value >= 1:
        return f"{value:.2g}"
    return f"{value:.2g}"


def plot_support_matrix(
    matrix: pd.DataFrame,
    *,
    box: Sequence[float | str],
    title: str,
    cbar_label: str,
    cmap: mcolors.Colormap,
    norm: mcolors.Normalize,
    colorbar_ticks: list[float],
    colorbar_scale: str = "linear",
    cluster_labels: list[tuple[str, float]] | None = None,
    contour_levels: list[float] | None = None,
    contour_labels: list[str] | None = None,
    contour_value_label: str = "W",
    contour_value_precision: int = 3,
    contour_legend_loc: str | None = None,
    transparent_threshold: float = 0.0,
    grid_alpha: float = 1.0,
    interpolation: str = "nearest",
) -> tuple[Figure, Axes]:
    try:
        import cartopy.crs as ccrs
    except ImportError as exc:
        raise ImportError("map plotting requires cartopy to be installed") from exc

    values = matrix.to_numpy(dtype=float)
    rgba = cmap(norm(values))

    missing_mask = ~np.isfinite(values)
    zero_mask = np.isfinite(values) & (values <= transparent_threshold)
    finite_nonzero_mask = np.isfinite(values) & (values > transparent_threshold)

    rgba[missing_mask] = mcolors.to_rgba("white", alpha=1.0)
    rgba[zero_mask, 3] = 0.0
    rgba[finite_nonzero_mask, 3] = 1.0

    fig, ax = plt.subplots(figsize=(9, 7), subplot_kw={"projection": ccrs.PlateCarree()})
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    ax.imshow(
        rgba,
        origin="lower",
        extent=matrix_extent(matrix),
        aspect="auto",
        interpolation=interpolation,
        transform=ccrs.PlateCarree(),
        zorder=1,
    )
    if contour_levels is not None:
        _add_support_contours(
            ax,
            matrix,
            contour_levels=contour_levels,
            contour_labels=contour_labels,
            contour_value_label=contour_value_label,
            contour_value_precision=contour_value_precision,
            legend_loc=contour_legend_loc,
        )
    ax.set_title(title)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    _add_land_overlay(ax, box=box, grid_alpha=grid_alpha)

    scalar_mappable = plt.cm.ScalarMappable(norm=norm, cmap=cmap)
    scalar_mappable.set_array([])
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="3.4%", pad=0.55, axes_class=plt.Axes)
    if colorbar_scale == "log":
        colorbar_positive_ticks = [tick for tick in colorbar_ticks if tick > 0]
        colorbar_vmin = min(colorbar_positive_ticks)
        colorbar_vmax = max(colorbar_positive_ticks)
        colorbar_edges = np.geomspace(colorbar_vmin, colorbar_vmax, 256)
        colorbar_centers = np.sqrt(colorbar_edges[:-1] * colorbar_edges[1:])
        cax.pcolormesh(
            [0.0, 1.0],
            colorbar_edges,
            colorbar_centers[:, np.newaxis],
            cmap=cmap,
            norm=norm,
            shading="flat",
        )
        cax.set_yscale("log")
        cax.set_ylim(colorbar_vmin, colorbar_vmax)
        cax.set_xlim(0.0, 1.0)
        cax.set_xticks([])
        cax.set_yticks(colorbar_ticks)
        cax.set_ylabel(cbar_label)
        colorbar_ax = cax
    else:
        colorbar = fig.colorbar(scalar_mappable, cax=cax, ticks=colorbar_ticks)
        colorbar.set_label(cbar_label)
        colorbar_ax = colorbar.ax
    colorbar_ax.yaxis.set_major_formatter(mticker.FuncFormatter(_format_raw_support_tick))
    colorbar_ax.minorticks_off()
    if cluster_labels:
        colorbar_ax.set_ylabel("")
        colorbar_ax.set_title(cbar_label, pad=8)
        colorbar_ax.yaxis.set_ticks_position("left")
        colorbar_ax.yaxis.set_label_position("left")
        transform = colorbar_ax.get_yaxis_transform()
        for label, value in cluster_labels:
            colorbar_ax.text(
                1.45,
                value,
                label,
                transform=transform,
                rotation=90,
                ha="center",
                va="center",
                clip_on=False,
            )
    fig.tight_layout()
    return fig, ax


def support_region_cmap(
    *,
    low_anchor: float,
    mid_anchor: float,
    high_anchor: float,
    missing: str = "white",
) -> mcolors.Colormap:
    cmap = mcolors.LinearSegmentedColormap.from_list(
        "support_region",
        [
            (0.0, "#14081f"),
            (low_anchor, "#2457d6"),
            (mid_anchor, "#ff8b1a"),
            (high_anchor, "#2fca62"),
            (1.0, "#b7f45b"),
        ],
        N=256,
    )
    cmap = cmap.with_extremes(
        bad=missing,
        under="#14081f",
        over="#b7f45b",
    )
    cmap.set_bad(color=missing, alpha=1.0)
    return cmap
