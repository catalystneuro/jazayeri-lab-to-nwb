"""Entrypoint to convert an entire session of data to NWB.

This converts a session to NWB format and writes the nwb files to
    /om/user/nwatters/nwb_data_multi_prediction/{$SUBJECT}/{$SESSION}
Two NWB files are created:
    $SUBJECT_$SESSION_raw.nwb --- Raw physiology
    $SUBJECT_$SESSION_processed.nwb --- Task, behavior, and sorted physiology
These files can be automatically uploaded to a DANDI dataset.

Usage:
    $ python main_convert_session.py $SUBJECT $SESSION
    where $SUBJECT is the subject name and $SESSION is the session date
    YYYY-MM-DD. For example:
    $ python main_convert_session.py Perle 2022-06-01

    Please read and consider changing the following variables:
        _REPO
        _STUB_TEST
        _OVERWRITE
    See comments below for descriptions of these variables.
"""


import glob
import json
import logging
import os
import sys
from pathlib import Path
from uuid import uuid4

import get_session_paths
import numpy as np
import nwb_converter
from neuroconv.utils import dict_deep_update, load_dict_from_file

# Data repository. Either 'globus' or 'openmind'
_REPO = "openmind"
# Whether to run all the physiology data or only a stub
_STUB_TEST = False
# Whether to overwrite output nwb files
_OVERWRITE = True

# Set logger level for info is displayed in console
logging.getLogger().setLevel(logging.INFO)

_SUBJECT_TO_SEX = {
    "elgar": "M",
}
_SUBJECT_TO_AGE = {
    "elgar": "P10Y",  # Born 5/2/2012
}


def _get_single_file(directory, suffix=""):
    """Get path to a file in given directory with given suffix.

    Raises error if not exactly one satisfying file.
    """
    files = list(glob.glob(str(directory / f"*{suffix}")))
    if len(files) == 0:
        raise ValueError(f"No {suffix} files found in {directory}")
    if len(files) > 1:
        raise ValueError(f"Multiple {suffix} files found in {directory}")
    return files[0]


def _update_metadata(metadata, subject, session_id, session_paths):
    """Update metadata."""

    # Add subject_id, session_id, sex, and age
    metadata["NWBFile"]["session_id"] = str(session_id)
    metadata["Subject"]["subject_id"] = subject
    metadata["Subject"]["sex"] = _SUBJECT_TO_SEX[subject]
    metadata["Subject"]["age"] = _SUBJECT_TO_AGE[subject]

    # Add probe locations
    probe_metadata_file = session_paths.session_data / "phys_metadata.json"
    probe_metadata = json.load(open(probe_metadata_file, "r"))
    for entry in metadata["Ecephys"]["ElectrodeGroup"]:
        if entry["device"] == "Neuropixel-Imec":
            neuropixel_metadata = probe_metadata
            coordinate_system = neuropixel_metadata["coordinate_system"]
            coordinates = np.round(
                neuropixel_metadata["coordinates"][:2], decimals=2
            )
            depth_from_surface = neuropixel_metadata["depth"]
            entry["description"] = (
                f"{entry['description']}\n"
                f"{coordinate_system}\n"
                f"coordinates = {coordinates}\n"
                f"depth_from_surface = {depth_from_surface}"
            )
            entry["position"] = [
                coordinates[0],
                coordinates[1],
                depth_from_surface,
            ]

    # Update default metadata with the editable in the corresponding yaml file
    editable_metadata_path = Path(__file__).parent / "metadata.yaml"
    editable_metadata = load_dict_from_file(editable_metadata_path)
    metadata = dict_deep_update(metadata, editable_metadata)

    # Ensure session_start_time exists in metadata
    if "session_start_time" not in metadata["NWBFile"]:
        raise ValueError(
            "Session start time was not auto-detected. Please provide it "
            "in `metadata.yaml`"
        )

    return metadata


def _add_spikeglx_data(
    raw_source_data,
    raw_conversion_options,
    processed_source_data,
    processed_conversion_options,
    session_paths,
    stub_test,
):
    """Add SpikeGLX recording data."""
    logging.info("Adding SpikeGLX data")

    # Raw data
    spikeglx_dir = Path(
        _get_single_file(session_paths.raw_data / "spikeglx", suffix="imec0")
    )
    ap_file = _get_single_file(spikeglx_dir, suffix="*.ap.bin")
    lfp_file = _get_single_file(spikeglx_dir, suffix="*.lf.bin")
    raw_source_data["RecordingNP"] = dict(file_path=ap_file)
    raw_source_data["LF"] = dict(file_path=lfp_file)
    processed_source_data["RecordingNP"] = dict(file_path=ap_file)
    processed_source_data["LF"] = dict(file_path=lfp_file)
    raw_conversion_options["RecordingNP"] = dict(stub_test=stub_test)
    raw_conversion_options["LF"] = dict(stub_test=stub_test)
    processed_conversion_options["RecordingNP"] = dict(
        stub_test=stub_test, write_electrical_series=False
    )
    processed_conversion_options["LF"] = dict(
        stub_test=stub_test, write_electrical_series=False
    )

    # Processed data
    sorting_path = (
        session_paths.spike_sorting_raw
        / "spikeglx/kilosort2_5_0/sorter_output"
    )
    if os.path.exists(sorting_path):
        logging.info("Adding spike sorted data")
        processed_source_data["SortingNP"] = dict(
            folder_path=str(sorting_path),
            keep_good_only=False,
        )
        processed_conversion_options["SortingNP"] = dict(
            stub_test=stub_test, write_as="processing"
        )


def session_to_nwb(
    subject: str,
    session: str,
    stub_test: bool = False,
    overwrite: bool = True,
):
    """
    Convert a single session to an NWB file.

    Parameters
    ----------
    subject : string
        Subject, either 'Perle' or 'Elgar'.
    session : string
        Session date in format 'YYYY-MM-DD'.
    stub_test : boolean
        Whether or not to generate a preview file by limiting data write to a
        few MB.
        Default is False.
    overwrite : boolean
        If the file exists already, True will delete and replace with a new
        file, False will append the contents.
        Default is True.
    """
    logging.info(f"stub_test = {stub_test}")
    logging.info(f"overwrite = {overwrite}")

    # Get paths
    session_paths = get_session_paths.get_session_paths(
        subject, session, repo=_REPO
    )
    logging.info(f"session_paths: {session_paths}")

    # Get paths for nwb files to write
    session_paths.output.mkdir(parents=True, exist_ok=True)
    session_id = str(session)
    if stub_test:
        session_id = f"{session_id}-stub"
    else:
        session_id = f"{session}-full"
    raw_nwb_path = (
        session_paths.output / f"sub-{subject}_ses-{session_id}_ecephys.nwb"
    )
    processed_nwb_path = (
        session_paths.output
        / f"sub-{subject}_ses-{session_id}_ecephys.nwb"
    )
    logging.info(f"raw_nwb_path = {raw_nwb_path}")
    logging.info(f"processed_nwb_path = {processed_nwb_path}")
    logging.info("")

    # Initialize empty data dictionaries
    raw_source_data = {}
    raw_conversion_options = {}
    processed_source_data = {}
    processed_conversion_options = {}

    # Add SpikeGLX data
    _add_spikeglx_data(
        raw_source_data=raw_source_data,
        raw_conversion_options=raw_conversion_options,
        processed_source_data=processed_source_data,
        processed_conversion_options=processed_conversion_options,
        session_paths=session_paths,
        stub_test=stub_test,
    )

    # Add behavior data
    logging.info("Adding behavior data")
    behavior_task_path = str(session_paths.behavior_task_data)
    processed_source_data["EyePosition"] = dict(
        folder_path=behavior_task_path)
    processed_conversion_options["EyePosition"] = dict()
    processed_source_data["PupilSize"] = dict(
        folder_path=behavior_task_path)
    processed_conversion_options["PupilSize"] = dict()
    processed_source_data["RewardLine"] = dict(
        folder_path=behavior_task_path)
    processed_conversion_options["RewardLine"] = dict()
    processed_source_data["Audio"] = dict(
        folder_path=behavior_task_path)
    processed_conversion_options["Audio"] = dict()

    # Add trials data
    logging.info("Adding trials data")
    processed_source_data["Trials"] = dict(
        folder_path=str(session_paths.behavior_task_data)
    )
    processed_conversion_options["Trials"] = dict()

    # Add display data
    logging.info("Adding display data")
    processed_source_data["Display"] = dict(
        folder_path=str(session_paths.behavior_task_data)
    )
    processed_conversion_options["Display"] = dict()

    # Create data converters
    processed_converter = nwb_converter.NWBConverter(
        source_data=processed_source_data,
        sync_dir=session_paths.sync_pulses,
    )
    raw_converter = nwb_converter.NWBConverter(
        source_data=raw_source_data,
        sync_dir=str(session_paths.sync_pulses),
    )

    # Update metadata
    metadata = processed_converter.get_metadata()
    metadata = _update_metadata(
        metadata=metadata,
        subject=subject,
        session_id=session_id,
        session_paths=session_paths,
    )

    # Run conversion
    logging.info("Running processed conversion")
    processed_converter.run_conversion(
        metadata=metadata,
        nwbfile_path=processed_nwb_path,
        conversion_options=processed_conversion_options,
        overwrite=overwrite,
    )

    logging.info("Running raw data conversion")
    metadata["NWBFile"]["identifier"] = str(uuid4())
    raw_converter.run_conversion(
        metadata=metadata,
        nwbfile_path=raw_nwb_path,
        conversion_options=raw_conversion_options,
        overwrite=overwrite,
    )


if __name__ == "__main__":
    """Run session conversion."""
    subject = sys.argv[1]
    session = sys.argv[2]
    logging.info(f"\nStarting conversion for {subject}/{session}\n")
    session_to_nwb(
        subject=subject,
        session=session,
        stub_test=_STUB_TEST,
        overwrite=_OVERWRITE,
    )
    logging.info(f"\nFinished conversion for {subject}/{session}\n")
