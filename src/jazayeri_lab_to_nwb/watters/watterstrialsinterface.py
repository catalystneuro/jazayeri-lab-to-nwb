"""Primary class for converting experiment-specific behavior."""
import json
import numpy as np
import pandas as pd
from pathlib import Path
from pynwb import NWBFile
from typing import Optional

from neuroconv.datainterfaces.text.timeintervalsinterface import TimeIntervalsInterface
from neuroconv.utils import DeepDict, FolderPathType, FilePathType


class WattersTrialsInterface(TimeIntervalsInterface):
    def __init__(self, folder_path: FolderPathType, verbose: bool = True):
        super().__init__(file_path=folder_path, verbose=verbose)

    def get_metadata(self) -> dict:
        metadata = super().get_metadata()
        metadata["TimeIntervals"] = dict(
            trials=dict(
                table_name="trials",
                table_description=f"experimental trials generated from JSON files",
            )
        )

        return metadata

    def _read_file(self, file_path: FolderPathType):
        # define files to read
        folder_path = Path(file_path)
        all_fields = [
            "behavior/trials.broke_fixation.json",
            "behavior/trials.response.error.json",
            "behavior/trials.response.location.json",
            "behavior/trials.response.object.json",
            "task/trials.object_blanks.json",
            "task/trials.start_times.json",
            "task/trials.relative_phase_times.json",
            "task/trials.reward.duration.json",
            "task/trials.reward.time.json",
            "task/trials.stimuli_init.json",
        ]

        # check that all data exist
        for field in all_fields:
            assert (folder_path / field).exists(), f"Could not find {folder_path / field}"

        # load into a dictionary
        data_dict = {}
        for field in all_fields:
            with open(folder_path / field, "r") as f:
                data_dict[field] = json.load(f)

        # define useful helpers
        get_by_index = lambda lst, idx: np.nan if (idx >= len(lst)) else lst[idx]
        none_to_nan = lambda val, dim: val or (np.nan if dim <= 1 else np.full((dim,), np.nan).tolist())

        # process trial data
        processed_data = []
        n_trials = len(data_dict["task/trials.start_times.json"])
        for i in range(n_trials):
            # get trial start time
            start_time = data_dict["task/trials.start_times.json"][i]

            # map response object index to id
            response_object = data_dict["behavior/trials.response.object.json"][i]
            if response_object is None:
                response_object = ""
            else:
                response_object = data_dict["task/trials.stimuli_init.json"][i][response_object]["id"]

            # map stimuli info from list to corresponding ids
            object_info = {"a": {}, "b": {}, "c": {}}
            target_object = None
            for object_dict in data_dict["task/trials.stimuli_init.json"][i]:
                object_id = object_dict["id"]
                assert object_id in object_info.keys()
                object_info[object_id]["position"] = [object_dict["x"], object_dict["y"]]
                object_info[object_id]["velocity"] = [object_dict["x_vel"], object_dict["y_vel"]]
                if object_dict["target"]:
                    target_object = object_id
            assert target_object is not None

            processed_data.append(
                dict(
                    start_time=start_time,
                    stop_time=start_time + data_dict["task/trials.relative_phase_times.json"][i][-1],
                    broke_fixation=data_dict["behavior/trials.broke_fixation.json"][i],
                    response_error=none_to_nan(data_dict["behavior/trials.response.error.json"][i], 1),
                    response_location=none_to_nan(data_dict["behavior/trials.response.location.json"][i], 2),
                    response_object=response_object,
                    object_blank=data_dict["task/trials.object_blanks.json"][i],
                    stimulus_time=start_time + get_by_index(data_dict["task/trials.relative_phase_times.json"][i], 0),
                    delay_start_time=start_time
                    + get_by_index(data_dict["task/trials.relative_phase_times.json"][i], 1),
                    cue_time=start_time + get_by_index(data_dict["task/trials.relative_phase_times.json"][i], 2),
                    response_time=start_time + get_by_index(data_dict["task/trials.relative_phase_times.json"][i], 3),
                    reveal_time=start_time + get_by_index(data_dict["task/trials.relative_phase_times.json"][i], 4),
                    reward_duration=none_to_nan(data_dict["task/trials.reward.duration.json"][i], 1),
                    reward_time=start_time + none_to_nan(data_dict["task/trials.reward.time.json"][i], 1),
                    target_object=target_object,
                    object_a_position=object_info["a"].get("position", [np.nan, np.nan]),
                    object_a_velocity=object_info["a"].get("velocity", [np.nan, np.nan]),
                    object_b_position=object_info["b"].get("position", [np.nan, np.nan]),
                    object_b_velocity=object_info["b"].get("velocity", [np.nan, np.nan]),
                    object_c_position=object_info["c"].get("position", [np.nan, np.nan]),
                    object_c_velocity=object_info["c"].get("velocity", [np.nan, np.nan]),
                )
            )

        return pd.DataFrame(processed_data)

    def add_to_nwbfile(
        self,
        nwbfile: NWBFile,
        metadata: Optional[dict] = None,
        tag: str = "trials",
    ):
        column_descriptions = {
            "broke_fixation": "Whether the subject broke fixation before the response period.",
            "response_error": (
                "Euclidean distance between subject's response fixation position and the true target "
                "object's position, in units of display sidelength."
            ),
            "response_location": (
                "Position of the subject's response fixation, in units of display sidelength, with (0,0) "
                "being the bottom left corner of the display."
            ),
            "response_object": (
                "The ID of the stimulus object nearest to the subject's response, one of 'a' for Apple, "
                "'b' for Blueberry, or 'c' for Orange. If the trial ended prematurely, the field is left blank."
            ),
            "object_blank": "Whether the object locations were visible in the delay phase as blank disks.",
            "stimulus_time": "Time of stimulus presentation.",
            "delay_start_time": "Time of the beginning of the delay period.",
            "cue_time": "Time of cue object presentation.",
            "response_time": "Time of subject's response.",
            "reveal_time": "Time of reveal of correct object position.",
            "reward_duration": "Duration of juice reward, in seconds.",
            "reward_time": "Time of reward delivery.",
            "target_object": (
                "ID of the stimulus object that is the target object, one of 'a' for Apple, 'b' for Blueberry, "
                "or 'c' for Orange."
            ),
            "object_a_position": (
                "Position of stimulus object 'a', or Apple. Values are (x,y) coordinates in units of screen "
                "sidelength, with (0,0) being the bottom left corner. If the object is not presented in a "
                "particular trial, the position is empty."
            ),
            "object_a_velocity": (
                "Velocity of stimulus object 'a', or Apple. Values are (x,y) velocity vectors, in units of "
                "screen sidelength per simulation timestep. If the object is not presented in a particular "
                "trial, the velocity is empty."
            ),
            "object_b_position": (
                "Position of stimulus object 'b', or Blueberry. Values are (x,y) coordinates in units of "
                "screen sidelength, with (0,0) being the bottom left corner. If the object is not presented "
                "in a particular trial, the position is empty."
            ),
            "object_b_velocity": (
                "Velocity of stimulus object 'b', or Blueberry. Values are (x,y) velocity vectors, in units "
                "of screen sidelength per simulation timestep. If the object is not presented in a particular "
                "trial, the velocity is empty."
            ),
            "object_c_position": (
                "Position of stimulus object 'c', or Orange. Values are (x,y) coordinates in units of screen "
                "sidelength, with (0,0) being the bottom left corner. If the object is not presented in a "
                "particular trial, the position is empty."
            ),
            "object_c_velocity": (
                "Velocity of stimulus object 'c', or Orange. Values are (x,y) velocity vectors, in units of "
                "screen sidelength per simulation timestep. If the object is not presented in a particular "
                "trial, the velocity is empty."
            ),
        }

        return super().add_to_nwbfile(
            nwbfile=nwbfile,
            metadata=metadata,
            tag=tag,
            column_descriptions=column_descriptions,
        )
