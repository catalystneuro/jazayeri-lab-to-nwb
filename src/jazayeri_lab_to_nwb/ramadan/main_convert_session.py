"""Entrypoint to convert an entire session of data to NWB.

This converts a session to NWB format and writes the nwb files to
    /om/user/nwatters/nwb_data_multi_prediction/staging/sub-$SUBJECT/
Two NWB files are created:
    sub-$SUBJECT_ses-$SESSION_ecephys.nwb --- Raw physiology
    sub-$SUBJECT_ses-$SESSION_behavior+ecephys.nwb --- Task, behavior, and
        sorted physiology

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
import datetime
import logging
import sys
from pathlib import Path
from uuid import uuid4

import get_session_paths
import nwb_converter
import jazayeri_lab_to_nwb.ramadan.conversion_utils as conversion_utils
import numpy as np
from neuroconv.utils import dict_deep_update, load_dict_from_file

# Data repository. Either 'globus' or 'openmind'
_REPO = "openmind"
# Whether to run all the physiology data or only a stub
_STUB_TEST = False
# Whether to overwrite output nwb files
_OVERWRITE = True

# Set logger level for info is displayed in console
logging.getLogger().setLevel(logging.INFO)

def serialize(x):
    """Serialize an input x."""
    if isinstance(x, np.int_):
        x = int(x)
    elif isinstance(x, np.float_):
        x = float(x)
    elif isinstance(x, np.ndarray):
        x = [serialize(y) for y in x]
    elif isinstance(x, dict):
        x = {k: serialize(v) for k, v in x.items()}
    elif isinstance(x, list):
        x = [serialize(v) for v in x]
    return x

class NWBConversionParams():
    """Class to hold parameters for NWB conversion."""
    def __init__(self):
        self.processed_conversion_options = {}
        self.processed_source_data = {}
        self.raw_conversion_options = {}
        self.raw_source_data = {}

    def add_raw(self, key: str, value: dict, **conversion_options: dict):
        """Add raw data to NWB conversion parameters."""
        self.raw_source_data[key] = value
        self.raw_conversion_options[key] = conversion_options

    def add_processed(self, key: str, value: dict, **conversion_options: dict):
        """Add processed data to NWB conversion parameters."""
        self.processed_source_data[key] = value
        self.processed_conversion_options[key] = conversion_options

# TODO: Edit subject to sex mapping and subject to age mapping
_SUBJECT_TO_SEX = {
    "amadeus": "M",
}
_SUBJECT_TO_AGE = {
    "amadeus": "P10Y",  # Born 6/11/2012
}


def add_ecephys_data(
        session_paths: get_session_paths.SessionPaths,
        conversion_params: NWBConversionParams,
        stub_test: bool):
    """
    Add electrophysiology data to an NWB file.

    Parameters:

    Returns:
        None
    """
    conversion_params = _add_v_probe_data(
        conversion_params=conversion_params,
        session_paths=session_paths,
        stub_test=stub_test,
    )

    return conversion_params


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
    conversion_params,
    session_paths,
    stub_test,
):
    """Add V-Probe session data."""
    probe_data_dir = session_paths.ecephys
    if not probe_data_dir.exists():
        logging.info(f"Ecephys data directory {probe_data_dir} does not exist")
        return

    logging.info(f"Adding V-probe session data")

    # Raw data
    recording_file = _get_single_file(probe_data_dir, suffix=".dat")
    probe_num = 0

    # TODO: Add metadata from README about probe
    conversion_params.add_raw(
        key=f"RecordingVP{probe_num}",
        value=dict(
            file_path=recording_file,
            probe_key=f"probe{(probe_num + 1):02d}",
            probe_name=f"vprobe{probe_num}",
            channel_count=32,
            ypitch=100,
            dtype="double",
            es_key=f"ElectricalSeriesVP{probe_num}",
        ),
        stub_test=stub_test,
    )
    conversion_params.add_processed(
        key=f"RecordingVP{probe_num}",
        value=conversion_params.raw_source_data[f"RecordingVP{probe_num}"],
        stub_test=stub_test,
        write_electrical_series=False,
    )

    # Processed data
    sorting_path = (
        session_paths.spike_sorting
        / "kilosorted2"
    )

    conversion_params.add_processed(
        key=f"SortingVP{probe_num}",
        value=dict(
            folder_path=str(sorting_path),
            keep_good_only=False
        ),
        stub_test=stub_test,
        write_as="processing"
    )

    return conversion_params



def _update_metadata(metadata, subject, session, session_id, session_paths):
    """Update metadata."""

    # Add subject_id, session_id, sex, and age
    metadata["NWBFile"]["session_id"] = session_id
    metadata["Subject"]["subject_id"] = subject
    metadata["Subject"]["sex"] = _SUBJECT_TO_SEX[subject]
    metadata["Subject"]["age"] = _SUBJECT_TO_AGE[subject]

    # Update default metadata with the editable in the corresponding yaml file
    editable_metadata_path = Path(__file__).parent / "metadata.yaml"
    editable_metadata = load_dict_from_file(editable_metadata_path)
    metadata = dict_deep_update(metadata, editable_metadata)


    metadata["NWBFile"]["session_start_time"] = (
        conversion_utils.read_session_start_time(session=session)
    )

    # Ensure session_start_time exists in metadata
    if "session_start_time" not in metadata["NWBFile"]:
        raise ValueError(
            "Session start time was not auto-detected. Please provide it "
            "in `metadata.yaml`"
        )

    return metadata


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
        Subject, either 'Faure' or 'Nielsen'.
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
    if stub_test:
        session_id = f"{session}-stub"
    else:
        session_id = f"{session}"
    raw_nwb_path = str(
        session_paths.output / f"sub-{subject}_ses-{session_id}_ecephys.nwb"
    )
    processed_nwb_path = (
        session_paths.output
        / f"sub-{subject}_ses-{session_id}_behavior+ecephys.nwb"
    )
    logging.info(f"raw_nwb_path = {raw_nwb_path}")
    logging.info(f"processed_nwb_path = {processed_nwb_path}")
    logging.info("")

    # Initialize empty data dictionaries
    conversion_params = NWBConversionParams()

    # Add electrophysiology data
    # logging.info("Adding ecephys data")
    # conversion_params = add_ecephys_data(
    #     session_paths=session_paths,
    #     conversion_params=conversion_params,
    #     stub_test=stub_test
    # )


    # Reads in behavioral data
    # logging.info("Adding behavior data")
    # behavior = neupane_conversion.read_behavior_data(
    #     session_paths, subject=subject, session=session)
    # conversion_params = add_behavior_data(
    #     behavior=behavior,
    #     conversion_params=conversion_params,
    #     behavior_path=session_paths.behavior
    # )

    # Add trials data    
    logging.info("Adding trials data")

    # Reads in trial-structured behavioral data as a dictionary of lists 
    trials = conversion_utils.read_trials_data(
        session_paths, subject=subject, session=session)
    conversion_params.add_processed(
        key="Trials",
        value=dict(trials=trials, folder_path=str(session_paths.behavior)),        
    )

    # Create data converters
    processed_params = serialize(conversion_params.processed_source_data)
    processed_converter = nwb_converter.NWBConverter(
        source_data=processed_params,
        sync_dir=session_paths.sync_pulses,
    )
    # raw_converter = nwb_converter.NWBConverter(
    #     source_data=conversion_params.raw_source_data,
    #     sync_dir=str(session_paths.sync_pulses),
    # )

    # Update metadata
    metadata = processed_converter.get_metadata()
    metadata = _update_metadata(
        metadata, 
        subject, 
        session, 
        session_id, 
        session_paths
    )

    # Run conversion
    logging.info("Running processed conversion")
    processed_converter.run_conversion(
        metadata=metadata,
        nwbfile_path=processed_nwb_path,
        conversion_options=conversion_params.processed_conversion_options,
        overwrite=overwrite,
    )

    # logging.info("Running raw data conversion")
    # metadata["NWBFile"]["identifier"] = str(uuid4())
    # raw_converter.run_conversion(
    #     metadata=metadata,
    #     nwbfile_path=raw_nwb_path,
    #     conversion_options=conversion_params.raw_conversion_options,
    #     overwrite=overwrite,
    # )

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