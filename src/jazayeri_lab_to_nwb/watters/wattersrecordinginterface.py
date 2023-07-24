"""Primary class for Watters Plexon probe data."""
import xmltodict
import shutil
import numpy as np
from pynwb import NWBFile
from pathlib import Path
from typing import Optional

from neuroconv.datainterfaces import OpenEphysRecordingInterface
from neuroconv.utils import FolderPathType

DEFAULT_CHANMAP = np.concatenate(
    [  # [8:-1:1 32:-1:25 9:24]
        np.arange(8, 0, -1),
        np.arange(32, 24, -1),
        np.arange(9, 25, 1),
    ]
)


def get_channel_mapping(channel_list: list):
    """https://github.com/nwatters01/catalystneuro/blob/main/phys_preprocessing/open_ephys_utils/prep_open_ephys.m"""
    if len(channel_list) == 32:  # 32-channel V-probe
        channel_maps = DEFAULT_CHANMAP
    elif len(channel_list) == 40:  # 16-channel V-probe
        channel_maps = np.arange(9, 25, 1)
    elif len(channel_list) == 64:  # 64-channel V-probe
        channel_maps = np.concatenate([DEFAULT_CHANMAP + 32, DEFAULT_CHANMAP])
    elif len(channel_list) == 72:  # 64-channel V-probe
        channel_maps = np.concatenate([DEFAULT_CHANMAP + 32, DEFAULT_CHANMAP])
    elif len(channel_list) == 144:  # 64-channel V-probe, two runs
        channel_maps = np.concatenate([DEFAULT_CHANMAP + 32, DEFAULT_CHANMAP])
    elif len(channel_list) == 136:  # Two 64-channel V-probes
        channel_maps = np.concatenate(
            [
                DEFAULT_CHANMAP + 32,
                DEFAULT_CHANMAP,
                DEFAULT_CHANMAP + 96,
                DEFAULT_CHANMAP + 64,
            ]
        )
    else:
        raise AssertionError(f"Invalid number of channels: {len(channel_files)}")
    channel_map_dict = dict(
        zip(
            [f"CH{i}" for i in range(1, len(channel_maps) + 1)],
            [f"CH{i}" for i in channel_maps],
        )
    )
    for key in channel_map_dict.keys():
        assert key in channel_list
    return channel_map_dict


def make_temporary_openephys_tree(folder_path: FolderPathType):
    """Rename .continuous files so they correctly indicate streams"""
    # check that the folder has .continuous files
    # and identify the (first) immediate parent folder of the data
    folder_path = Path(folder_path)
    assert any(folder_path.rglob("*.continuous")), "No `.continuuous` files found"
    data_dir = next(folder_path.rglob("*.continuous")).parent

    # find the settings.xml file to get name mappings
    settings_file = data_dir / "settings.xml"
    assert settings_file.exists(), f"No `settings.xml` file found in {data_dir}"
    with open(settings_file) as f:
        xmldata = f.read()
        settings = xmltodict.parse(xmldata)["SETTINGS"]

    # find channel info in settings
    sigchain = settings["SIGNALCHAIN"]
    processors = sigchain["PROCESSOR"]
    if not isinstance(processors, list):
        processors = [processors]
    for processor in processors:
        if processor.get("@name", None) != "Sources/Rhythm FPGA":
            continue
        index_to_name = {}
        channel_info = processor["CHANNEL_INFO"]["CHANNEL"]
        for channel in channel_info:
            index = str(int(channel.get("@number")) + 1)
            name = channel.get("@name")
            index_to_name[index] = name
        break
    assert len(index_to_name) == len(list(data_dir.glob("*.continuous")))

    # get channel mapping
    channel_mapping = get_channel_mapping(list(index_to_name.values()))

    # make temporary directory for symlinks
    temp_dir = folder_path / "temp_dir"
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)

    # make symlinks, with renaming
    file_list = list(data_dir.glob("*.*"))
    for data_file in file_list:
        if data_file.suffix == ".continuous":
            root_name = data_file.stem
            processor_id, ch_name = root_name.split("_")
            assert ch_name in index_to_name
            ch_name = index_to_name[ch_name]
            ch_name = channel_mapping.get(ch_name, ch_name)
            new_root_name = f"{processor_id}_{ch_name}"
        else:
            new_root_name = data_file.stem
        symlink_path = temp_dir / data_file.parent.relative_to(folder_path) / (new_root_name + data_file.suffix)
        symlink_path.parent.mkdir(parents=True, exist_ok=True)
        symlink_path.symlink_to(data_file)

    return temp_dir


class WattersOpenEphysRecordingInterface(OpenEphysRecordingInterface):

    ExtractorName = "OpenEphysBinaryRecordingExtractor"

    def __new__(
        cls,
        folder_path: FolderPathType,
        stream_name: Optional[str] = None,
        verbose: bool = True,
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
        folder_path = Path(folder_path)
        folder_path = make_temporary_openephys_tree(folder_path)
        return super().__new__(cls, folder_path=folder_path, stream_name=stream_name, verbose=verbose)


if __name__ == "__main__":
    make_temporary_openephys_tree(
        "/shared/catalystneuro/JazLab/monkey0/2022-06-01/raw_data/open_ephys/2022-06-01_13-46-03/Record_Node_104/"
    )
