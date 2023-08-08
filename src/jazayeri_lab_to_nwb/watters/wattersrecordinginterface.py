"""Primary class for Watters Plexon probe data."""
import os
import xmltodict
import shutil
import json
import numpy as np
from pynwb import NWBFile
from pathlib import Path
from typing import Optional, Union

from neuroconv.datainterfaces import OpenEphysRecordingInterface
from neuroconv.utils import FolderPathType


DEFAULT_CHANMAP = np.concatenate(
    [  # [8:-1:1 32:-1:25 9:24]
        np.arange(8, 0, -1),
        np.arange(32, 24, -1),
        np.arange(9, 25, 1),
    ]
)
RECORD_SIZE = 1024
HEADER_SIZE = 1024
continuous_dtype = [
    ("timestamp", "int64"),
    ("nb_sample", "uint16"),
    ("rec_num", "uint16"),
    ("samples", ">i2", RECORD_SIZE),
    ("markers", "uint8", 10),
]


def get_channel_info(folder_path: FolderPathType):
    """https://github.com/nwatters01/catalystneuro/blob/main/phys_preprocessing/open_ephys_utils/prep_open_ephys.m"""
    # check that this dir has .continuous files
    assert any(folder_path.glob("*.continuous")), f"No `.continuous` files found in {folder_path}"
    name_stem = next(folder_path.glob("*.continuous")).stem
    name_stem = f"{name_stem.split('_')[0]}_" + "{}.continuous"

    # find the settings.xml file
    settings_file = folder_path / "settings.xml"
    assert settings_file.exists(), f"No `settings.xml` file found in {folder_path}"
    with open(settings_file) as f:
        xmldata = f.read()
        settings = xmltodict.parse(xmldata)["SETTINGS"]

    # find .openephys file
    openephys_file = folder_path / "Continuous_Data.openephys"
    assert openephys_file.exists(), f"No `Continuous_Data.openephys` file found in {folder_path}"
    with open(openephys_file) as f:
        xmldata = f.read()
        experiment = xmltodict.parse(xmldata)["EXPERIMENT"]

    # find channel info in settings to map channel number to name
    # for correct streams, e.g. 100_1.continuous -> 100_CH1.continuous
    channel_info = experiment["RECORDING"]["PROCESSOR"]["CHANNEL"]  # assume that recording, processor are not list
    num_to_name = {}
    for channel in channel_info:
        file_name = channel.get("@filename")  # *_{channel_num}.continuous
        channel_num = file_name.split(".")[0].split("_")[1]
        channel_name = channel.get("@name")
        num_to_name[channel_num] = channel_name
    for key in num_to_name.keys():  # sanity check
        assert (folder_path / name_stem.format(key)).exists(), f"{folder_path / name_stem.format(key)}"

    # get channel and probe mapping
    if len(num_to_name) == 32:  # 32-channel V-probe
        channel_maps = DEFAULT_CHANMAP
        probe_maps = np.zeros(len(channel_maps))
    elif len(num_to_name) == 40:  # 16-channel V-probe
        channel_maps = np.arange(9, 25, 1)
        probe_maps = np.zeros(len(channel_maps))
    elif len(num_to_name) == 64:  # 64-channel V-probe
        channel_maps = np.concatenate([DEFAULT_CHANMAP + 32, DEFAULT_CHANMAP])
        probe_maps = np.zeros(len(channel_maps))
    elif len(num_to_name) == 72:  # 64-channel V-probe
        channel_maps = np.concatenate([DEFAULT_CHANMAP + 32, DEFAULT_CHANMAP])
        probe_maps = np.zeros(len(channel_maps))
    elif len(num_to_name) == 144:  # 64-channel V-probe, two runs
        channel_maps = np.concatenate([DEFAULT_CHANMAP + 32, DEFAULT_CHANMAP])
        probe_maps = np.zeros(len(channel_maps))
    elif len(num_to_name) == 136:  # Two 64-channel V-probes
        channel_maps = np.concatenate(
            [
                DEFAULT_CHANMAP + 32,
                DEFAULT_CHANMAP,
                DEFAULT_CHANMAP + 96,
                DEFAULT_CHANMAP + 64,
            ]
        )
        probe_maps = np.array([0, 1]).repeat(64)
    else:
        raise AssertionError(f"Invalid number of channels: {len(file_list)}")
    channel_map_dict = dict(
        zip(
            [f"CH{i}" for i in channel_maps],
            [f"CH{i}" for i in range(1, len(channel_maps) + 1)],
        )
    )
    probe_map_dict = dict(
        zip(
            [f"CH{i}" for i in channel_maps],
            probe_maps,
        )
    )
    for key in channel_map_dict.keys():
        assert key in num_to_name.values(), f"{key} not found in `num_to_name.values()`"

    channel_map_dict = {key: channel_map_dict.get(num_to_name[key], num_to_name[key]) for key in num_to_name.keys()}
    return channel_map_dict, probe_map_dict, settings, experiment


def make_temporary_openephys_legacy_tree(folder_path: FolderPathType):
    """Rename .continuous files for channel mapping"""
    # check that the folder has .continuous files
    # and identify the immediate parent folders of the data
    assert any(folder_path.rglob("*.continuous")), f"No `.continuuous` files found in {folder_path}"

    # make temporary directory for symlinks
    temp_dir = folder_path / "temp_dir"
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True)

    # loop through matching directories
    data_dirs = set([p.parent for p in folder_path.rglob("*.continuous")])
    for data_dir in data_dirs:
        # get channel mappings
        channel_map_dict = get_channel_info(data_dir)[0]

        # make symlinks, with renaming
        file_list = list(data_dir.glob("*.*"))
        for data_file in file_list:
            if data_file.suffix == ".continuous":
                root_name = data_file.stem
                processor_id, ch_name = root_name.split("_")
                assert ch_name in channel_map_dict.keys()
                ch_name = channel_map_dict[ch_name]
                new_root_name = f"{processor_id}_{ch_name}"
            else:
                new_root_name = data_file.stem
            symlink_path = temp_dir / data_file.parent.relative_to(folder_path) / (new_root_name + data_file.suffix)
            symlink_path.parent.mkdir(parents=True, exist_ok=True)
            symlink_path.symlink_to(data_file)

    return temp_dir


def make_temporary_openephys_binary_tree(folder_path: FolderPathType, dat_folder_paths: list[FolderPathType]):
    """Make .dat files compatible with OpenEphys binary format"""
    # find all .dat files
    dat_files = set()
    for dat_folder_path in dat_folder_paths:
        assert any(dat_folder_path.rglob("*.dat")), f"No `.dat` files found in {folder_path}"
        dat_files.update(set(list(dat_folder_path.rglob("*.dat"))))
    probe_dat_map = {dat_file.parent.name: dat_file for dat_file in dat_files}
    probes = sorted(probe_dat_map.keys())
    dat_files = [probe_dat_map[p] for p in probes]

    # get probe channel count info from original dir
    assert any(folder_path.rglob("*.continuous")), f"No `.continuuous` files found in {folder_path}"
    data_dirs = set([p.parent for p in folder_path.rglob("*.continuous")])
    assert len(data_dirs) == 1, "Multiple directories with `.continuous` files found"
    data_dir = data_dirs.pop()
    channel_map_dict, probe_map_dict, settings, experiment = get_channel_info(data_dir)
    node_num = int(data_dir.name.split("_")[-1])

    # extract probe info
    n_probes = len(np.unique(list(probe_map_dict.values())))
    assert len(probes) == n_probes, f"Number of `.dat` files does not match number of probes"

    # extract recording, processor, and channel info
    recording = experiment["RECORDING"]
    sample_rate = float(recording.get("@samplerate"))
    channel_info = experiment["RECORDING"]["PROCESSOR"]["CHANNEL"]
    sigchain = settings["SIGNALCHAIN"]
    processors = sigchain["PROCESSOR"]
    if not isinstance(processors, list):
        processors = [processors]
    source_processor = None
    for processor in processors:
        if processor.get("@name", "").startswith("Sources"):  # TODO: not sure how reliable this is
            source_processor = processor
            break
    assert source_processor is not None, "No matching source processor found `settings.xml`"
    source_processor_name = source_processor.get("@name").split("/")[-1]
    source_processor_id = source_processor.get("@NodeId")
    # channel_info = set_source_processor["CHANNEL_INFO"]["CHANNEL"]

    # make timestamps
    cont_file = next(folder_path.rglob("*.continuous"))
    filesize = os.stat(cont_file).st_size
    size = (filesize - HEADER_SIZE) // np.dtype(continuous_dtype).itemsize
    data_chan = np.memmap(cont_file, mode="r", offset=HEADER_SIZE, dtype=continuous_dtype, shape=(size,))
    # first_timestamp = data_chan[0]["timestamp"]
    timestamps = np.arange(len(data_chan)) / sample_rate  # + first_timestamp / sample_rate
    timestamps = timestamps.astype(np.float64, copy=False)

    # make temporary directory to house symlinks
    temp_root_dir = dat_folder_paths[0].parent / "temp_dir"
    if temp_root_dir.exists():
        shutil.rmtree(temp_root_dir)
    temp_root_dir.mkdir(parents=True)
    temp_settings_path = temp_root_dir / "settings.xml"
    temp_settings_path.symlink_to(data_dir / "settings.xml")
    temp_recording_dir = temp_root_dir / "experiment1" / "recording1"
    temp_recording_dir.mkdir(parents=True)

    # make structure.oebin file
    # first initialize basic structure
    version = settings["INFO"]["VERSION"]
    structure = {"GUI version": version}
    continuous = [
        {
            "folder_name": probe + "/",
            "sample_rate": sample_rate,
            "source_processor_name": source_processor_name,
            "source_processor_id": source_processor_id,
            "source_processor_sub_idx": 0,
            "recorded_processor": "Record Node",
            "recorded_processor_id": node_num,
            "num_channels": 0,
            "channels": [],
        }
        for probe in probes
    ]

    # add channels to continuous field
    for channel in channel_info:
        name = channel.get("@name")
        if "ADC" in name:
            continue
        assert "CH" in name
        # number = channel.get("@number")
        # gain = float(channel.get("@gain"))
        # index = int(number) + 1
        # channel_name = channel_map_dict.get(str(index))
        file_name = channel.get("@filename")
        number = file_name.split(".")[0].split("_")[1]
        gain = 1.0  # float(channel.get("@bitVolts"))
        channel_name = channel_map_dict.get(number)
        remapped_index = int(channel_name.strip("CH"))
        probe_num = probe_map_dict.get(channel_name)
        continuous_dict = continuous[probe_num]
        continuous_dict["num_channels"] += 1
        continuous_dict["channels"].append(
            {
                "channel_name": channel_name,
                "description": "Headstage data channel",
                "identifier": "genericdata.continuous",
                "history": f"{source_processor_name} -> Record Node",
                "bit_volts": gain,
                "units": "uV",
                "source_processor_index": remapped_index - 1,  # dunno if these matter?
                "recorded_processor_index": remapped_index - 1,
            }
        )
    structure["continuous"] = continuous

    # make dummy event data (because neo requires it)
    structure["events"] = [
        {
            "folder_name": "dummy/",
            "channel_name": "dummy",
            "description": "dummy",
            "identifier": "dummy",
            "sample_rate": sample_rate,
            "type": "int16",
            "num_channels": 1,
            "source_processor": "dummy",
        }
    ]
    temp_events_dir = temp_recording_dir / "events" / "dummy"
    temp_events_dir.mkdir(parents=True)
    np.save(temp_events_dir / "timestamps.npy", np.empty((0,)))
    np.save(temp_events_dir / "channels.npy", np.empty((0,)))

    # leave spikes empty and save structure.oebin file
    structure["spikes"] = []
    oebin_path = temp_recording_dir / "structure.oebin"
    with open(oebin_path, "w") as f:
        json.dump(structure, f, indent=2)

    # symlink `.dat` files
    temp_continuous_dir = temp_recording_dir / "continuous"
    temp_continuous_dir.mkdir(parents=True)
    for probe, dat_file in probe_dat_map.items():
        dat_dir = temp_continuous_dir / probe
        dat_dir.mkdir(parents=True)
        dat_path = dat_dir / "continuous.dat"
        dat_path.symlink_to(dat_file)
        np.save((dat_dir / "timestamps.npy"), timestamps)
    return temp_root_dir


def make_temporary_openephys_tree(folder_path: FolderPathType, dat_folder_paths: Optional[list[FolderPathType]] = None):
    folder_path = Path(folder_path)
    assert any(folder_path.rglob("*.continuous")), f"No `.continuous` files found in {folder_path}"
    if dat_folder_paths is None:
        return make_temporary_openephys_legacy_tree(folder_path)
    else:
        assert isinstance(dat_folder_paths, list)
        dat_folder_paths = [Path(path) for path in dat_folder_paths]
        for path in dat_folder_paths:
            dat_files = list(path.rglob("*.dat"))
            assert len(dat_files) >= 1, f"No `.dat` files found in {path}"
            assert len(dat_files) <= 1, f"Multiple `.dat` files found in {path}"
        return make_temporary_openephys_binary_tree(folder_path, dat_folder_paths)


class WattersOpenEphysRecordingInterface(OpenEphysRecordingInterface):

    ExtractorName = "OpenEphysBinaryRecordingExtractor"

    def __new__(
        cls,
        folder_path: FolderPathType,
        dat_folder_paths: Optional[list[FolderPathType]] = None,
        stream_name: Optional[str] = None,
        verbose: bool = True,
        es_key: str = "ElectricalSeries",
        make_temporary_tree: bool = False,
    ):
        """
        Abstract class that defines which interface class to use for a given Open Ephys recording.
        For "legacy" format (.continuous files) the interface redirects to OpenEphysLegacyRecordingInterface.
        For "binary" format (.dat files) the interface redirects to OpenEphysBinaryRecordingInterface.

        Parameters
        ----------
        folder_path : FolderPathType
            Path to OpenEphys directory (.continuous or .dat files).
        stream_name : str, optional
            The name of the recording stream.
            When the recording stream is not specified the channel stream is chosen if available.
            When channel stream is not available the name of the stream must be specified.
        verbose : bool, default: True
        """
        if make_temporary_tree:
            folder_path = make_temporary_openephys_tree(folder_path, dat_folder_paths)
        print(folder_path)
        return super().__new__(cls, folder_path=folder_path, stream_name=stream_name, verbose=verbose, es_key=es_key)


if __name__ == "__main__":
    make_temporary_openephys_tree(
        folder_path="/shared/catalystneuro/JazLab/monkey0/2022-06-01/raw_data/open_ephys/2022-06-01_13-46-03/Record_Node_104/",
        # dat_folder_paths=None,
        dat_folder_paths=[
            "/shared/catalystneuro/JazLab/monkey0/2022-06-01/raw_data/v_probe_0/",
            "/shared/catalystneuro/JazLab/monkey0/2022-06-01/raw_data/v_probe_1/",
        ],
    )
