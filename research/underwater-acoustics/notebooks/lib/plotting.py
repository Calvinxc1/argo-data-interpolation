from __future__ import annotations

from typing import Literal

import matplotlib.cm as cm
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.cm import ScalarMappable
from matplotlib.figure import Figure
from matplotlib.image import AxesImage


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
