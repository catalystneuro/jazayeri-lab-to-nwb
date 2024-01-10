"""Class for converting data about display frames."""

import itertools
import json
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from neuroconv.datainterfaces.text.timeintervalsinterface import (
    TimeIntervalsInterface,
)
from neuroconv.utils import FolderPathType
from pynwb import NWBFile


class DisplayInterface(TimeIntervalsInterface):
    """Class for converting data about display frames.

    All events that occur exactly once per display update are contained in this
    interface.
    """

    KEY_MAP = {
        "frame_closed_loop_gaze_position": "closed_loop_eye_position",
        "frame_task_phase": "task_phase",
        "frame_display_times": "start_time",
    }

    def __init__(self, folder_path: FolderPathType, verbose: bool = True):
        super().__init__(file_path=folder_path, verbose=verbose)

    def get_metadata(self) -> dict:
        metadata = super().get_metadata()
        metadata["TimeIntervals"] = dict(
            display=dict(
                table_name="display",
                table_description="data about each displayed frame",
            )
        )
        return metadata

    def get_timestamps(self) -> np.ndarray:
        return super(DisplayInterface, self).get_timestamps(
            column="start_time"
        )

    def set_aligned_starting_time(self, aligned_starting_time: float) -> None:
        self.dataframe.start_time += aligned_starting_time

    def _read_file(self, file_path: FolderPathType):
        # Create dataframe with data for each frame
        trials = json.load(open(Path(file_path) / "trials.json", "r"))
        frames = {
            k_mapped: list(itertools.chain(*[d[k] for d in trials]))
            for k, k_mapped in DisplayInterface.KEY_MAP.items()
        }

        return pd.DataFrame(frames)

    def add_to_nwbfile(
        self,
        nwbfile: NWBFile,
        metadata: Optional[dict] = None,
        tag: str = "display",
    ):
        return super(DisplayInterface, self).add_to_nwbfile(
            nwbfile=nwbfile,
            metadata=metadata,
            tag=tag,
            column_descriptions=self.column_descriptions,
        )

    @property
    def column_descriptions(self):
        column_descriptions = {
            "closed_loop_eye_position": (
                "For each frame, the eye position in the close-loop task "
                "engine. This was used to for real-time eye position "
                "computations, such as saccade detection and reward delivery."
            ),
            "task_phase": "The phase of the task for each frame.",
            "start_time": "Time of display update for each frame.",
        }

        return column_descriptions
