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
        _DANDISET_ID
    See comments below for descriptions of these variables.
"""

import datetime
import glob
import json
import logging
import os
import sys
from pathlib import Path
from typing import Union
from uuid import uuid4
from zoneinfo import ZoneInfo

import get_session_paths
import nwb_converter
from neuroconv.tools.data_transfers import automatic_dandi_upload
from neuroconv.utils import dict_deep_update, load_dict_from_file

# Data repository. Either 'globus' or 'openmind'
_REPO = "globus"
# Whether to run all the physiology data or only a stub
_STUB_TEST = True
# Whether to overwrite output nwb files
_OVERWRITE = True
# ID of the dandiset to upload to, or None to not upload
_DANDISET_ID = None  # '000620'

# Set logger level for info is displayed in console
logging.getLogger().setLevel(logging.INFO)

_SUBJECT_TO_SEX = {
    "Perle": "F",
    "Elgar": "M",
}
_SUBJECT_TO_AGE = {
    "Perle": "P10Y",  # Born 6/11/2012
    "Elgar": "P10Y",  # Born 5/2/2012
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


def _add_v_probe_data(
    raw_source_data,
    raw_conversion_options,
    processed_source_data,
    processed_conversion_options,
    session_paths,
    probe_num,
    stub_test,
):
    """Add V-Probe session data."""
    probe_data_dir = session_paths.raw_data / f"v_probe_{probe_num}"
    if not probe_data_dir.exists():
        return
    logging.info(f"Adding V-probe {probe_num} session data")

    # Raw data
    recording_file = _get_single_file(probe_data_dir, suffix=".dat")
    metadata_path = str(session_paths.data_open_source / "probes.metadata.json")
    raw_source_data[f"RecordingVP{probe_num}"] = dict(
        file_path=recording_file,
        probe_metadata_file=metadata_path,
        probe_key=f"probe{(probe_num + 1):02d}",
        probe_name=f"vprobe{probe_num}",
        es_key=f"ElectricalSeriesVP{probe_num}",
    )
    raw_conversion_options[f"RecordingVP{probe_num}"] = dict(stub_test=stub_test)

    # Processed data
    sorting_path = session_paths.spike_sorting_raw / f"v_probe_{probe_num}" / "ks_3_output_pre_v6_curated"
    processed_source_data[f"RecordingVP{probe_num}"] = raw_source_data[f"RecordingVP{probe_num}"]
    processed_source_data[f"SortingVP{probe_num}"] = dict(
        folder_path=str(sorting_path),
        keep_good_only=False,
    )
    processed_conversion_options[f"RecordingVP{probe_num}"] = dict(stub_test=stub_test, write_electrical_series=False)
    processed_conversion_options[f"SortingVP{probe_num}"] = dict(stub_test=stub_test, write_as="processing")


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
    spikeglx_dir = [x for x in (session_paths.raw_data / "spikeglx").iterdir() if "settling" not in str(x)]
    if len(spikeglx_dir) == 0:
        logging.info("Found no SpikeGLX data")
    elif len(spikeglx_dir) == 1:
        spikeglx_dir = spikeglx_dir[0]
    else:
        raise ValueError(f"Found multiple spikeglx directories {spikeglx_dir}")
    ap_file = _get_single_file(spikeglx_dir, suffix="/*.ap.bin")
    lfp_file = _get_single_file(spikeglx_dir, suffix="/*.lf.bin")
    raw_source_data["RecordingNP"] = dict(file_path=ap_file)
    raw_source_data["LF"] = dict(file_path=lfp_file)
    processed_source_data["RecordingNP"] = dict(file_path=ap_file)
    processed_source_data["LF"] = dict(file_path=lfp_file)
    raw_conversion_options["RecordingNP"] = dict(stub_test=stub_test)
    raw_conversion_options["LF"] = dict(stub_test=stub_test)
    processed_conversion_options["RecordingNP"] = dict(stub_test=stub_test)
    processed_conversion_options["LF"] = dict(stub_test=stub_test)

    # Processed data
    sorting_path = session_paths.spike_sorting_raw / "np_0" / "ks_3_output_v2"
    processed_source_data["SortingNP"] = dict(
        folder_path=str(sorting_path),
        keep_good_only=False,
    )
    processed_conversion_options["SortingNP"] = dict(stub_test=stub_test, write_as="processing")


def session_to_nwb(
    subject: str, session: str, stub_test: bool = False, overwrite: bool = True, dandiset_id: Union[str, None] = None
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
        Whether or not to generate a preview file by limiting data write to a few MB.
        Default is False.
    overwrite : boolean
        If the file exists already, True will delete and replace with a new file, False will append the contents.
        Default is True.
    dandiset_id : string, optional
        If you want to upload the file to the DANDI archive, specify the six-digit ID here.
        Requires the DANDI_API_KEY environment variable to be set.
        To set this in your bash terminal in Linux or macOS, run
            export DANDI_API_KEY=...
        or in Windows
            set DANDI_API_KEY=...
        Default is None.
    """
    if dandiset_id is not None:
        import dandi  # check importability

        assert os.getenv("DANDI_API_KEY"), (
            "Unable to find environment variable 'DANDI_API_KEY'. "
            "Please retrieve your token from DANDI and set this environment "
            "variable."
        )

    logging.info(f"stub_test = {stub_test}")
    logging.info(f"overwrite = {overwrite}")
    logging.info(f"dandiset_id = {dandiset_id}")

    # Get paths
    session_paths = get_session_paths.get_session_paths(subject, session, stub_test=stub_test, repo=_REPO)
    logging.info(f"session_paths: {session_paths}")

    # Get paths for nwb files to write
    session_paths.output.mkdir(parents=True, exist_ok=True)
    raw_nwb_path = session_paths.output / f"{session}_raw.nwb"
    processed_nwb_path = session_paths.output / f"{session}_processed.nwb"
    logging.info(f"raw_nwb_path = {raw_nwb_path}")
    logging.info(f"processed_nwb_path = {processed_nwb_path}")
    logging.info("")

    # Initialize empty data dictionaries
    raw_source_data = {}
    raw_conversion_options = {}
    processed_source_data = {}
    processed_conversion_options = {}

    # Add V-Probe data
    for probe_num in range(2):
        _add_v_probe_data(
            raw_source_data=raw_source_data,
            raw_conversion_options=raw_conversion_options,
            processed_source_data=processed_source_data,
            processed_conversion_options=processed_conversion_options,
            session_paths=session_paths,
            probe_num=probe_num,
            stub_test=stub_test,
        )

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
    behavior_path = str(session_paths.task_behavior_data)
    processed_source_data["EyePosition"] = dict(folder_path=behavior_path)
    processed_conversion_options["EyePosition"] = dict()
    processed_source_data["PupilSize"] = dict(folder_path=behavior_path)
    processed_conversion_options["PupilSize"] = dict()
    processed_source_data["RewardLine"] = dict(folder_path=behavior_path)
    processed_conversion_options["RewardLine"] = dict()
    processed_source_data["Audio"] = dict(folder_path=behavior_path)
    processed_conversion_options["Audio"] = dict()

    # Add trials data
    logging.info("Adding trials data")
    processed_source_data["Trials"] = dict(folder_path=str(session_paths.task_behavior_data))
    processed_conversion_options["Trials"] = dict()

    # Add display data
    logging.info("Adding display data")
    processed_source_data["Display"] = dict(folder_path=str(session_paths.task_behavior_data))
    processed_conversion_options["Display"] = dict()

    # Create processed data converter
    processed_converter = nwb_converter.NWBConverter(
        source_data=processed_source_data,
        sync_dir=session_paths.sync_pulses,
    )

    # Add datetime and subject name to processed converter
    metadata = processed_converter.get_metadata()
    metadata["NWBFile"]["session_id"] = session
    metadata["Subject"]["subject_id"] = subject
    metadata["Subject"]["sex"] = _SUBJECT_TO_SEX[subject]
    metadata["Subject"]["age"] = _SUBJECT_TO_AGE[subject]

    # EcePhys
    probe_metadata_file = session_paths.data_open_source / "probes.metadata.json"
    with open(probe_metadata_file, "r") as f:
        probe_metadata = json.load(f)
    neuropixel_metadata = [x for x in probe_metadata if x["probe_type"] == "Neuropixels"][0]
    for entry in metadata["Ecephys"]["ElectrodeGroup"]:
        if entry["device"] == "Neuropixel-Imec":
            # TODO: uncomment when fixed in pynwb
            # entry.update(dict(position=[(
            #     neuropixel_metadata['coordinates'][0],
            #     neuropixel_metadata['coordinates'][1],
            #     neuropixel_metadata['depth_from_surface'],
            # )]
            logging.info("\n\n")
            logging.warning("   PROBE COORDINATES NOT IMPLEMENTED\n\n")

    # Update default metadata with the editable in the corresponding yaml file
    editable_metadata_path = Path(__file__).parent / "metadata.yaml"
    editable_metadata = load_dict_from_file(editable_metadata_path)
    metadata = dict_deep_update(metadata, editable_metadata)

    # Check if session_start_time was found/set
    if "session_start_time" not in metadata["NWBFile"]:
        try:
            date = datetime.datetime.strptime(session, "%Y-%m-%d")
            date = date.replace(tzinfo=ZoneInfo("US/Eastern"))
        except:
            raise ValueError("Session start time was not auto-detected. Please provide it " "in `metadata.yaml`")
        metadata["NWBFile"]["session_start_time"] = date

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
    raw_converter = nwb_converter.NWBConverter(
        source_data=raw_source_data,
        sync_dir=str(session_paths.sync_pulses),
    )
    raw_converter.run_conversion(
        metadata=metadata,
        nwbfile_path=raw_nwb_path,
        conversion_options=raw_conversion_options,
        overwrite=overwrite,
    )

    # Upload to DANDI
    if dandiset_id is not None:
        logging.info(f"Uploading to dandiset id {dandiset_id}")
        automatic_dandi_upload(
            dandiset_id=dandiset_id,
            nwb_folder_path=session_paths.output,
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
        dandiset_id=_DANDISET_ID,
    )
    logging.info(f"\nFinished conversion for {subject}/{session}\n")
