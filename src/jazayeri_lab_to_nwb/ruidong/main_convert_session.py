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

import logging
import os
import sys
from pathlib import Path

from pynwb import NWBHDF5IO
import get_session_paths
import nwb_converter
import conversion_utils
import numpy as np
from neuroconv.utils import dict_deep_update, load_dict_from_file

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
    elif isinstance(x, np.float64):
        x = float(x)
    elif isinstance(x, np.ndarray):
        x = [serialize(y) for y in x]
    elif isinstance(x, dict):
        x = {k: serialize(v) for k, v in x.items()}
    elif isinstance(x, list):
        x = [serialize(v) for v in x]
    return x


class NWBConversionParams:
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


_SUBJECT_TO_SEX = {
    "Offenbach": "F",
    "Lalo": "M",
}
_SUBJECT_TO_AGE = {
    "Offenbach": "P6Y",
    "Lalo": "P11Y",
}


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
        conversion_utils.read_session_start_time(path=session_paths.start_time)
    )

    # metadata["Ecephys"]["ElectricalSeriesVP"] = "Raw voltage data from V-Probe"

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
        Subject, either 'Offenbach' or 'Lalo'.
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

    joystick_id = 0 if subject == "Offenbach" else 1

    # Get paths
    session_paths = get_session_paths.get_session_paths(subject, session)
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

    logging.info("Adding behavior data")
    eye_path = str(session_paths.eye_path)
    # add eye and joystick data if this path exists
    if os.path.exists(os.path.join(eye_path, "eyex_v.npy")):
        conversion_params.processed_source_data["EyePosition"] = dict(
            folder_path=eye_path
        )
        joystick_path = str(session_paths.joystick_path)
        conversion_params.processed_source_data["JoystickPosition"] = dict(
            folder_path=joystick_path, id=joystick_id
        )
    # Add trials data
    logging.info("Adding trials data")
    # Reads in trial-structured behavioral data as a dictionary of lists
    trials = conversion_utils.read_trials_data(session_id)
    # session_paths, subject=subject, session=session)

    conversion_params.add_processed(
        key="Trials",
        value=dict(trials=trials, folder_path=str(session_paths.behavior)),
    )

    # This works but requires editing nwb package locally
    # this file: /Users/rc/miniconda/envs/nwb/lib/python3.10/site-packages/spikeinterface/extractors/phykilosortextractors.py
    ks_path = str(session_paths.ks_path)
    conversion_params.processed_source_data["SortingVP"] = dict(
        folder_path=ks_path,
        keep_good_only=False,
    )

    conversion_params.processed_conversion_options[f"SortingVP"] = dict(
        stub_test=stub_test, write_as="units"
    )
    # Create data converters
    processed_params = serialize(conversion_params.processed_source_data)
    processed_converter = nwb_converter.NWBConverter(
        source_data=processed_params,
    )
    raw_source_data = {}
    recording_file = session_paths.ece_path
    recording_file = str(recording_file)
    conversion_params.add_raw(
        key=f"RecordingVP",
        value=dict(
            file_path=recording_file,
            probe_key=f"probe",
            probe_name=f"vprobe",
            channel_count=64,
            ypitch=50,
            dtype="double",
            es_key=f"ElectricalSeriesVP",
        ),
        stub_test=stub_test,
    )
    raw_source_data[f"RecordingVP"] = dict(
        file_path=recording_file,
        probe_key=f"probe",
        probe_name=f"vprobe",
        es_key=f"ElectricalSeriesVP",
    )

    raw_converter = nwb_converter.NWBConverter(
        source_data=raw_source_data,
    )
    raw_conversion_options = conversion_params.raw_conversion_options
    raw_conversion_options[f"RecordingVP"] = dict(stub_test=stub_test)

    # Update metadata
    metadata = processed_converter.get_metadata()
    metadata = _update_metadata(
        metadata, subject, session, session_id, session_paths
    )

    # Run conversion
    logging.info("Running processed conversion")
    processed_converter.run_conversion(
        metadata=metadata,
        nwbfile_path=processed_nwb_path,
        conversion_options=conversion_params.processed_conversion_options,
        overwrite=overwrite,
    )

    # Read in NWB file
    read_io = NWBHDF5IO(processed_nwb_path)
    nwbfile = read_io.read()

    # Add processing module with binned spikes extension to file
    ecephys_processing_module = nwbfile.create_processing_module(
        name="ecephys",
        description="Intermediate data derived from extracellular electrophysiology recordings.",
    )

    binned_aligned_spikes_fdbk = conversion_utils.read_binned_data(
        subject, session, "fdbk"
    )
    ecephys_processing_module.add(binned_aligned_spikes_fdbk)

    # this works:
    binned_aligned_spikes_choice = conversion_utils.read_binned_data(
        subject, session, "choice"
    )
    ecephys_processing_module.add(binned_aligned_spikes_choice)

    # Remove old NWB file and overwrite with new, modified one
    os.remove(processed_nwb_path)
    with NWBHDF5IO(processed_nwb_path, mode="w") as write_io:
        write_io.export(
            src_io=read_io, nwbfile=nwbfile, write_args={"link_data": False}
        )

    logging.info("Running raw data conversion")
    metadata = raw_converter.get_metadata()
    metadata = _update_metadata(
        metadata, subject, session, session_id, session_paths
    )
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
