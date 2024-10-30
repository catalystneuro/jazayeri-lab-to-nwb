"""Class for converting trial-structured data."""

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


class TrialsInterface(TimeIntervalsInterface):
    """Class for converting trial-structured data.

    All events that occur exactly once per trial are contained in this
    interface.
    """
    def __init__(self, 
                 trials: dict,
                 folder_path: FolderPathType, 
                 verbose: bool = True):
        self._trials = trials
        super().__init__(file_path=folder_path, verbose=verbose)
        
    def get_metadata(self) -> dict:
        metadata = super().get_metadata()
        metadata["TimeIntervals"] = dict(
            trials=dict(
                table_name="trials",
                table_description="data about each trial",
            )
        )
        return metadata

    def get_timestamps(self) -> np.ndarray:
        return super(TrialsInterface, self).get_timestamps(column="start_time")
    
    def _read_file(self, file_path: FolderPathType):
        return pd.DataFrame(self._trials)

    def add_to_nwbfile(
        self,
        nwbfile: NWBFile,
        metadata: Optional[dict] = None,
        tag: str = "trials",
    ):
        return super(TrialsInterface, self).add_to_nwbfile(
            nwbfile=nwbfile,
            metadata=metadata,
            tag=tag,
            column_descriptions=self.column_descriptions,
        )

    # TODO: Add descriptions for all columns
    @property    
    def column_descriptions(self):
        column_descriptions = {
            "h1": "length of left horizontal arm.",
            "h2": "length of left-up vertical arm.",
            "h3": "length of left-down vertical arm.",
            "h4": "length of right horizontal arm.",
            "h5": "length of right-up vertical arm.",
            "h6": "length of right-down vertical arm.",
            "vel": "speed of ball",
            "LR": "whether ball went left or right (-1 vs 1)",
            "LR2": "whether ball went down or up (-1 vs 1)",
            "trial_answer1": "binary:whether final choice was correct",
            "trial_answer2": "binary:whether final choice was correct horizontal direction but incorrect vertical direction",
            "trial_answer3": "binary:whether final choice was incorrect horizontal direction but correct vertical direction",
            "trial_answer4": "binary:whether final choice was incorrect horizontal direction and incorrect vertical direction",
            "geo_present": "time maze was presented",
            "fixation_cue_present": "time fixation cue presented",
            "fix_start": "time monkey started fixation",
            "flash_one": "time of first flash",
            "flash_two": "time of second flash",
            "flash_three": "time of third flash",
            "fixation_off": "time of fixation cue is removed",
            "saccade_init": "time of monkey initiated saccade to choice",
            "answer_time": "time of monkey fixates on choice",
            "trial_end": "time of trial end after feedback period",
            "geo_type": "maze geometry type: 1-6 for the six maze conditions, -99 for a randomly sampled maze",
            "path_type": "Enumeration of ball path (four possible paths) within each of the 6 maze conditions, total of 24 path types. Beginning with maze one, path one is the left-up path, then left-down (path two), then right-up (path three), then right-down (path four), and so on in order of the maze number. Value is -99 for random mazes",
            "rand_geo": "binary:1 if randomly sampled maze",
            "trial_fade": "binary:1 if the ball is visible throughout the trial, 0 if occluded",
            "trial_indices_all": "trial index",
        }

        return column_descriptions
