from functools import partial
import pytest

from anndata import AnnData
import scanpy as sc

import numpy as np
import pandas as pd

from squidpy import pl
from squidpy.gr import spatial_neighbors
from tests.conftest import PlotTester, PlotTesterMeta
from squidpy.pl._spatial_utils import _get_library_id
from squidpy._constants._pkg_constants import Key

C_KEY = "Cluster"


sc.pl.set_rcParams_defaults()
sc.set_figure_params(dpi=40, color_map="viridis")

# WARNING:
# 1. all classes must both subclass PlotTester and use metaclass=PlotTesterMeta
# 2. tests which produce a plot must be prefixed with `test_plot_`
# 3. if the tolerance needs to be change, don't prefix the function with `test_plot_`, but with something else
#    the comp. function can be accessed as `self.compare(<your_filename>, tolerance=<your_tolerance>)`
#    ".png" is appended to <your_filename>, no need to set it


class TestSpatialStatic(PlotTester, metaclass=PlotTesterMeta):
    def test_plot_spatial_scatter_image(self, adata_hne: AnnData):
        pl.spatial_scatter(adata_hne, na_color="lightgrey")

    def test_plot_spatial_scatter_noimage(self, adata_hne: AnnData):
        pl.spatial_scatter(adata_hne, shape=None, na_color="lightgrey")

    def test_plot_spatial_scatter_title_single(self, adata_hne_concat: AnnData):
        pl.spatial_scatter(
            adata_hne_concat,
            shape="hex",
            library_key="batch_key",
            library_id=["V2_Adult_Mouse_Brain"],
            color=["Sox17", "cluster"],
            title="Visium test",
        )

    def test_plot_spatial_scatter_crop(self, adata_hne_concat: AnnData):
        pl.spatial_scatter(
            adata_hne_concat,
            shape="square",
            library_key="batch_key",
            size=[1, 1.25],
            color=["Sox17", "cluster"],
            edges=True,
            edges_width=5,
            title=None,
            outline=True,
            library_first=True,
            outline_width=(0.05, 0.05),
            crop_coord=[(1500, 2800, 1500, 2800), (2000, 2800, 2000, 2800)],
            scalebar_dx=2.0,
            scalebar_kwargs={"scale_loc": "bottom", "location": "lower right"},
        )

    def test_plot_spatial_scatter_group(self, adata_hne_concat: AnnData):
        pl.spatial_scatter(
            adata_hne_concat,
            cmap="inferno",
            shape="hex",
            library_key="batch_key",
            library_id=["V1_Adult_Mouse_Brain", "V2_Adult_Mouse_Brain"],
            size=[1, 1.25],
            color=["Sox17", "cluster"],
            edges=False,
            edges_width=5,
            title=None,
            outline=True,
            outline_width=(0.05, 0.05),
            scalebar_dx=2.0,
            scalebar_kwargs={"scale_loc": "bottom", "location": "lower right"},
        )

    def test_plot_spatial_scatter_nospatial(self, adata_hne_concat: AnnData):
        spatial_neighbors(adata_hne_concat)
        adata_hne_concat.uns.pop("spatial")
        pl.spatial_scatter(
            adata_hne_concat,
            shape=None,
            library_key="batch_key",
            library_id=["V1_Adult_Mouse_Brain", "V2_Adult_Mouse_Brain"],
            edges=True,
            edges_width=3,
            size=[1.0, 50],
            color="cluster",
        )

    def test_plot_spatial_scatter_novisium(self, adata_mibitof: AnnData):
        spatial_neighbors(adata_mibitof, coord_type="generic", radius=50)
        pl.spatial_scatter(
            adata_mibitof,
            cell_id_key="cell_id",
            library_key="library_id",
            library_id=["point8"],
            na_color="lightgrey",
            edges=True,
            edges_width=0.5,
        )

    def test_plot_spatial_segment(self, adata_mibitof: AnnData):
        pl.spatial_segment(
            adata_mibitof,
            cell_id_key="cell_id",
            library_key="library_id",
            na_color="lightgrey",
        )

    def test_plot_spatial_segment_group(self, adata_mibitof: AnnData):
        pl.spatial_segment(
            adata_mibitof,
            color=["Cluster"],
            groups=["Fibroblast", "Endothelial"],
            library_key="library_id",
            cell_id_key="cell_id",
            img=False,
            seg=True,
            figsize=(5, 5),
            legend_na=False,
            scalebar_dx=2.0,
            scalebar_kwargs={"scale_loc": "bottom", "location": "lower right"},
        )

    def test_plot_spatial_segment_crop(self, adata_mibitof: AnnData):
        pl.spatial_segment(
            adata_mibitof,
            color=["Cluster", "cell_size"],
            groups=["Fibroblast", "Endothelial"],
            library_key="library_id",
            cell_id_key="cell_id",
            img=True,
            seg=True,
            seg_outline=True,
            seg_contourpx=15,
            figsize=(5, 5),
            cmap="magma",
            vmin=500,
            crop_coord=[[0, 500, 0, 500], [0, 500, 0, 500], [0, 500, 0, 500]],
            img_alpha=0.5,
        )


class TestSpatialStaticUtils:
    def _create_anndata(self, shape, library_id, library_key):
        n_obs = len(library_id) * 2 if isinstance(library_id, list) else 2
        X = np.empty((n_obs, 3))
        if not isinstance(library_id, list) and library_id is not None:
            library_id = [library_id]
        if library_id is not None:
            obs = pd.DataFrame(library_id * 2, columns=[library_key])
            uns = {Key.uns.spatial: {k: None for k in library_id}}
            return AnnData(X, obs=obs, uns=uns, dtype=X.dtype)
        else:
            return AnnData(X, dtype=X.dtype)

    @pytest.mark.parametrize("shape", ["circle", None])
    @pytest.mark.parametrize("library_id", [None, "1", ["1"], ["1", "2"]])
    @pytest.mark.parametrize("library_key", [None, "batch_key"])
    def test_get_library_id(self, shape, library_id, library_key):
        adata = self._create_anndata(shape, library_id, library_key)
        if not isinstance(library_id, list) and library_id is not None:
            library_id = [library_id]
        _get_libid = partial(
            _get_library_id,
            shape=shape,
            library_id=library_id,
            library_key=library_key,
        )
        if shape is None:
            if library_id is None:
                if library_key is None:
                    assert _get_libid(adata) == [""]
                else:
                    with pytest.raises(ValueError, match="library_key"):
                        _get_libid(adata)
            else:
                assert library_id == _get_libid(adata)
        else:
            if library_id is None:
                with pytest.raises(KeyError, match=Key.uns.spatial):
                    _get_libid(adata)
            else:
                assert library_id == _get_libid(adata)