from pathlib import Path
from typing import Optional

import btrack
import napari
from btrack.utils import segmentation_to_objects
from magicgui import magicgui
from magicgui.widgets import FunctionGui

from btrack.config import load_config
from btrack import datasets

default_config = load_config(datasets.cell_config())


def run_tracker(objects, config_file_path):
    with btrack.BayesianTracker() as tracker:
        # configure the tracker using a config file
        tracker.configure_from_file(config_file_path)
        tracker.max_search_radius = 50

        # append the objects to be tracked
        tracker.append(objects)

        # set the volume
        tracker.volume = ((0, 1600), (0, 1200), (-1e5, 64.0))

        # track them (in interactive mode)
        tracker.track_interactive(step_size=100)

        # generate hypotheses and run the global optimizer
        tracker.optimize()

        # get the tracks in a format for napari visualization
        data, properties, graph = tracker.to_napari(ndim=2)
        return data, properties, graph


def track() -> FunctionGui:
    @magicgui(
        call_button=True,
        persist=True,
        dt=dict(value=default_config.motion_model.dt, step=0.01),
        reset_button=dict(widget_type="PushButton", text="Reset defaults"),
    )
    def widget(
        viewer: napari.Viewer,
        segmentation: napari.layers.Image,
        dt: float,
        reset_button,
    ):
        segmented_objects = segmentation_to_objects(segmentation.data[:100, ...])
        data, properties, graph = run_tracker(segmented_objects, datasets.cell_config())
        viewer.add_tracks(
            data=data, properties=properties, graph=graph, name=f"{segmentation}_btrack"
        )

    return widget
