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

from jazayeri_lab_to_nwb.utils.openephys_reformat import make_temporary_openephys_tree


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
