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

    @property
    def column_descriptions(self):
        column_descriptions = {
            "gocuettl": "Time of go cue.",
            "joy1offttl": "Time of joystick release",
            "joy1onttl": "Time of joystick press",
            "stim1onttl": "Time of stimulus onset",
            "start_time": "Time of trial start, equal to stimulus onset",

            # Add condition variables
            "ta": "Actual vector (seconds)",
            "tp": "Produced vector (seconds)",
            "curr": "Start landmark",
            "target": "Target landmark",
            "rt": "Response time = joystick press time - go cue time",
            "delay": ".4-1.4s delay for go cue. Drawn from an exponential distribution",
            "trial_type": "1=linear map visible (NTS), 2=centre visible, periphery occluded, 3=fully occluded (MNAV)",
            "seqq": "which sequence: 1,2,3 or 4",
            "attempt": "# of attempts to perform the trial",
            "succ": "binary: successful trial or not",
            "numrepeat": "# of times the same condition was repeated, sometimes implemented to prevent deliberate aborts",
            "validtrials_mm": "binary: trial labeled as valid or lapse based on Gaussian Mixture Model fit to tp distrbutions",
            
        }

        return column_descriptions
