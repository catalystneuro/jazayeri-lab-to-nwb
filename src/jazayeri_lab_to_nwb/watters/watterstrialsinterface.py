"""Primary class for converting experiment-specific behavior."""
import json
import numpy as np
from pathlib import Path
from pynwb import NWBFile

from neuroconv.basedatainterface import BaseDataInterface
from neuroconv.utils import DeepDict, FolderPathType


class WattersTrialsInterface(BaseDataInterface):
    def __init__(self, folder_path: FolderPathType):
        super().__init__(folder_path=folder_path)

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata: dict):
        # check that all data exist
        folder_path = Path(self.source_data["folder_path"])
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
        for field in all_fields:
            assert (folder_path / field).exists(), f"Could not find {folder_path / field}"

        # load into a dictionary
        data_dict = {}
        for field in all_fields:
            with open(folder_path / field, "r") as f:
                data_dict[field] = json.load(f)

        # add trial columns
        nwbfile.add_trial_column(
            name="broke_fixation", description="Whether the subject broke fixation before the response period."
        )
        nwbfile.add_trial_column(
            name="response_error",
            description="Euclidean distance between subject's response fixation position and the true target object's position, in units of display sidelength.",
        )
        nwbfile.add_trial_column(
            name="response_location",
            description="Position of the subject's response fixation, in units of display sidelength, with (0,0) being the bottom left corner of the display.",
        )
        nwbfile.add_trial_column(
            name="response_object",
            description="The index of the stimulus object nearst to the subject's response. Indices correspond to the object ordering in the stimuli description fields of the trials table.",
        )
        nwbfile.add_trial_column(
            name="object_blank",
            description="Whether the object locations were visible in the delay phase as blank disks.",
        )
        nwbfile.add_trial_column(name="stimulus_time", description="Time of stimulus presentation.")
        nwbfile.add_trial_column(name="delay_start_time", description="Time of the beginning of the delay period.")
        nwbfile.add_trial_column(name="cue_time", description="Time of cue object presentation.")
        nwbfile.add_trial_column(name="response_time", description="Time of subject's response.")
        nwbfile.add_trial_column(name="reveal_time", description="Time of reveal of correct object position.")
        nwbfile.add_trial_column(name="reward_duration", description="Duration of juice reward, in seconds.")
        nwbfile.add_trial_column(name="reward_time", description="Time of reward delivery.")
        nwbfile.add_trial_column(
            name="stimuli_position",
            index=True,
            description="Positions of the stimuli objects. Values are (x,y) coordinates in unites of screen sidelength, with (0,0) being the bottom left corner.",
        )
        nwbfile.add_trial_column(
            name="stimuli_velocity",
            index=True,
            description="Velocity of the stimuli objects. Values are (x,y) velocity vectors, in units of screen sidelength per simulation timestep.",
        )
        nwbfile.add_trial_column(
            name="stimuli_id",
            index=True,
            description="Object IDs of the stimuli objects, 'a' for apple, 'b' for blueberry, and 'c' for orange.",
        )
        nwbfile.add_trial_column(
            name="stimuli_target",
            index=True,
            description="Boolean for each stimulus object indicating whether it is the target object.",
        )

        # add trials to table
        n_trials = len(data_dict["task/trials.start_times.json"])
        for i in range(n_trials):
            start_time = data_dict["task/trials.start_times.json"][i]
            get_by_index = lambda lst, idx: np.nan if (idx >= len(lst)) else lst[idx]
            none_to_nan = lambda val, dim: val or (np.nan if dim <= 1 else np.full((dim,), np.nan).tolist())
            nwbfile.add_trial(
                start_time=start_time,
                stop_time=start_time + data_dict["task/trials.relative_phase_times.json"][i][-1],
                broke_fixation=data_dict["behavior/trials.broke_fixation.json"][i],
                response_error=none_to_nan(data_dict["behavior/trials.response.error.json"][i], 1),
                response_location=none_to_nan(data_dict["behavior/trials.response.location.json"][i], 2),
                response_object=none_to_nan(data_dict["behavior/trials.response.object.json"][i], 1),
                object_blank=data_dict["task/trials.object_blanks.json"][i],
                stimulus_time=get_by_index(data_dict["task/trials.relative_phase_times.json"][i], 0),
                delay_start_time=get_by_index(data_dict["task/trials.relative_phase_times.json"][i], 1),
                cue_time=get_by_index(data_dict["task/trials.relative_phase_times.json"][i], 2),
                response_time=get_by_index(data_dict["task/trials.relative_phase_times.json"][i], 3),
                reveal_time=get_by_index(data_dict["task/trials.relative_phase_times.json"][i], 4),
                reward_duration=none_to_nan(data_dict["task/trials.reward.duration.json"][i], 1),
                reward_time=none_to_nan(data_dict["task/trials.reward.time.json"][i], 1),
                stimuli_position=[[d["x"], d["y"]] for d in data_dict["task/trials.stimuli_init.json"][i]],
                stimuli_velocity=[[d["x_vel"], d["y_vel"]] for d in data_dict["task/trials.stimuli_init.json"][i]],
                stimuli_id=[d["id"] for d in data_dict["task/trials.stimuli_init.json"][i]],
                stimuli_target=[d["target"] for d in data_dict["task/trials.stimuli_init.json"][i]],
            )

        return nwbfile
