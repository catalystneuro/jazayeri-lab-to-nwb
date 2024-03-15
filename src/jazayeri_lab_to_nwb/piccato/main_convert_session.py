"""Entrypoint to convert an entire session of data to NWB.

This converts a session to NWB format and writes the nwb files to
    /om/user/nwatters/nwb_data_multi_prediction/{$SUBJECT}/{$SESSION}
Two NWB files are created:
    $SUBJECT_$SESSION_ecephys.nwb --- Raw physiology
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
import time
import get_session_paths
import numpy as np
import nwb_converter
from neuroconv.tools.spikeinterface import write_sorting, write_waveforms
from neuroconv.utils import dict_deep_update, load_dict_from_file
from spikeinterface.extractors import read_kilosort
import spikeinterface.core as sc
import pynwb

# Data repository. Either 'globus' or 'openmind'
_REPO = "openmind"
# Whether to run all the physiology data or only a stub
_STUB_TEST = True
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

_BEHAVIOR_TASK_CONV_TYPE = 'behavior+task'
_ECEPHYS_CONV_TYPE = 'ecephys'
_SPIKES_CONV_TYPE = 'spikes'


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


def _add_curated_sorting_data(
        nwbfile_path: Path,
        session_paths: get_session_paths.SessionPaths):
    """Add curated sorting data to spikes NWB file."""
    sorting = read_kilosort(
        folder_path=(
            session_paths.spike_sorting_raw /
            'spikeglx/kilosort2_5_0/sorter_output')
    )

    # Adding curated units
    curated_unit_idxs = list(json.load(open(
        session_paths.postprocessed_data / 'manual_curation.json', 'r')
        ).keys())
    curated_unit_idxs = [int(unit_id) for unit_id in curated_unit_idxs]
    unit_ids = sorting.get_unit_ids()
    curated_unit_ids = [unit_ids[idx] for idx in curated_unit_idxs]

    write_sorting(
        sorting=sorting,
        nwbfile_path=nwbfile_path,
        unit_ids=curated_unit_ids,
        overwrite=False,
        write_as='units',
    )

    # Adding waveform template
    waveform_extractor = sc.load_waveforms(
        session_paths.postprocessed_data / 'waveforms'
    )
    write_waveforms(
        waveform_extractor=waveform_extractor,
        nwbfile_path=nwbfile_path,
        overwrite=False,
        unit_ids=unit_ids,
        write_as='units',
    )

    # Adding stable trials information
    read_io = pynwb.NWBHDF5IO(
        nwbfile_path, mode='r', load_namespaces=True,
    )
    nwbfile = read_io.read()
    stable_trials = json.load(open(
        session_paths.postprocessed_data / 'stability.json', 'r'
    ))
    units_stable_trials = [
        stable_trials[unit_idx] for unit_idx in curated_unit_idxs
    ]
    description = (
        "For each trial, whether this unit was stable in the recording."
    )
    units_data = nwbfile.units
    units_data.add_column(
        name='stable_trials',
        description=description,
        data=units_stable_trials)
    os.remove(nwbfile_path)
    with pynwb.NWBHDF5IO(nwbfile_path, mode='w') as write_io:
        write_io.export(
            src_io=read_io, nwbfile=nwbfile, write_args={'link_data': False},
        )


def _add_spikeglx_data(
    source_data,
    conversion_options,
    conversion_type,
    session_paths,
    stub_test,
):
    """Add SpikeGLX recording data."""
    logging.info("Adding SpikeGLX data")

    # Raw data
    spikeglx_dir = Path(
        _get_single_file(
            session_paths.ecephys_data / "spikeglx", suffix="imec0")
    )
    ap_file = _get_single_file(spikeglx_dir, suffix="*.ap.bin")
    lfp_file = _get_single_file(spikeglx_dir, suffix="*.lf.bin")

    if conversion_type == _ECEPHYS_CONV_TYPE:
        source_data["RecordingNP"] = dict(
            file_path=ap_file,
        )
        source_data["LF"] = dict(file_path=lfp_file)
        conversion_options["RecordingNP"] = dict(stub_test=stub_test)
        conversion_options["LF"] = dict(stub_test=stub_test)
        return
    if conversion_type == _SPIKES_CONV_TYPE:
        source_data["RecordingNP"] = dict(file_path=ap_file)
        source_data["LF"] = dict(file_path=lfp_file)

        conversion_options["RecordingNP"] = dict(
            stub_test=stub_test, write_electrical_series=False
        )

        conversion_options["LF"] = dict(
            stub_test=stub_test, write_electrical_series=False
        )
        sorting_path = (
            session_paths.spike_sorting_raw
            / "spikeglx/kilosort2_5_0/sorter_output"
        )
        if os.path.exists(sorting_path):
            logging.info("Adding spike sorted data")
            source_data["SortingNP"] = dict(
                folder_path=str(sorting_path),
                keep_good_only=False,
            )
            conversion_options["SortingNP"] = dict(
                stub_test=stub_test, write_as="processing"
            )
        return
    if conversion_type == "behavior+task":
        source_data["RecordingNP"] = dict(file_path=ap_file)
        source_data["LF"] = dict(file_path=lfp_file)
        conversion_options["RecordingNP"] = dict(
            stub_test=stub_test, write_electrical_series=False
        )
        conversion_options["LF"] = dict(
            stub_test=stub_test, write_electrical_series=False
        )
        return


def session_to_nwb(
    subject: str,
    session: str,
    conversion_type: str,
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
    conversion_type: string
        Conversion type, either 'ecephys', 'behavior+task', or 'spikes'.
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
    logging.info(f"conversion_type = {conversion_type}")

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
    # Initialize empty data dictionaries

    source_data = {}
    conversion_options = {}
    _add_spikeglx_data(
        source_data=source_data,
        conversion_options=conversion_options,
        conversion_type=conversion_type,
        session_paths=session_paths,
        stub_test=stub_test,
    )
    if conversion_type == _ECEPHYS_CONV_TYPE:
        # Add SpikeGLX data
        nwb_path = (
            session_paths.output /
            f"sub-{subject}_ses-{session_id}_ecephys.nwb")
        _add_spikeglx_data(
            source_data=raw_source_data,
            conversion_options=raw_conversion_options,
            conversion_type="raw",
            session_paths=session_paths,
            stub_test=stub_test,
        )

        converter = nwb_converter.NWBConverter(
            source_data=source_data,
            sync_dir=str(session_paths.sync_pulses),
        )
        logging.info("Running ecephys data conversion")

        # Get metadata
        metadata = converter.get_metadata()
        metadata = _update_metadata(
            metadata=metadata,
            subject=subject,
            session_id=session_id,
            session_paths=session_paths,
        )
        metadata["NWBFile"]["identifier"] = str(uuid4())
        
        for interface_name, data_interface in converter.data_interface_objects.items():
            if 'Recording' in interface_name:
                print(data_interface.sampling_frequency)
        # Run conversion
        converter.run_conversion(
            metadata=metadata,
            nwbfile_path=nwb_path,
            conversion_options=conversion_options,
            overwrite=overwrite,
        )

        return
    if conversion_type == _BEHAVIOR_TASK_CONV_TYPE:
        # Add SpikeGLX data
        nwb_path = (
            session_paths.output
            / f"sub-{subject}_ses-{session_id}_behavior+task.nwb"
        )

        # Add behavior data
        logging.info("Adding behavior data")
        behavior_task_path = str(session_paths.behavior_task_data)
        source_data["EyePosition"] = dict(
            folder_path=behavior_task_path)
        conversion_options["EyePosition"] = dict()
        source_data["PupilSize"] = dict(
            folder_path=behavior_task_path)
        conversion_options["PupilSize"] = dict()
        source_data["RewardLine"] = dict(
            folder_path=behavior_task_path)
        conversion_options["RewardLine"] = dict()
        source_data["Audio"] = dict(
            folder_path=behavior_task_path)
        conversion_options["Audio"] = dict()
        _add_spikeglx_data(
            source_data=source_data,
            conversion_options=conversion_options,
            conversion_type="processed",
            session_paths=session_paths,
            stub_test=stub_test,
        )

        # Add trials data
        logging.info("Adding trials data")
        source_data["Trials"] = dict(
            folder_path=str(session_paths.behavior_task_data)
        )
        conversion_options["Trials"] = dict()

        # Add display data
        logging.info("Adding display data")
        source_data["Display"] = dict(
            folder_path=str(session_paths.behavior_task_data)
        )
        conversion_options["Display"] = dict()

        # Create data converters
        converter = nwb_converter.NWBConverter(
            source_data=source_data,
            sync_dir=session_paths.sync_pulses,
        )

        # Get metadata
        metadata = converter.get_metadata()
        metadata = _update_metadata(
            metadata=metadata,
            subject=subject,
            session_id=session_id,
            session_paths=session_paths,
        )

        # Run conversion
        logging.info("Running behavior+task conversion")
        converter.run_conversion(
            metadata=metadata,
            nwbfile_path=nwb_path,
            conversion_options=conversion_options,
            overwrite=overwrite,
        )
        return
    if conversion_type == _SPIKES_CONV_TYPE:
        nwb_path = (
            session_paths.output
            / f"sub-{subject}_ses-{session_id}_spikes.nwb"
        )
        # Create data converter
        spikes_converter = nwb_converter.NWBConverter(
            source_data=source_data,
            sync_dir=session_paths.sync_pulses,
        )

        # Get metadata
        metadata = spikes_converter.get_metadata()
        metadata = _update_metadata(
            metadata=metadata,
            subject=subject,
            session_id=session_id,
            session_paths=session_paths,
        )

        # Run conversion
        logging.info('Running spikes conversion')
        spikes_converter.run_conversion(
            metadata=metadata,
            nwbfile_path=nwb_path,
            conversion_options=conversion_options,
            overwrite=overwrite,
        )

        # Adding curated spike sorting and waveform data
        time.sleep(10)
        logging.info("Writing curated sorting output to processed NWB")
        _add_curated_sorting_data(
            nwbfile_path=nwb_path,
            session_paths=session_paths,
        )


if __name__ == "__main__":
    """Run session conversion."""
    session = sys.argv[1]
    conversion_type = sys.argv[2]
    subject = session.split("/")[0]
    session = session.split("/")[1]
    logging.info(f"\nStarting conversion for {subject}/{session}\n")
    session_to_nwb(
        subject=subject,
        session=session,
        conversion_type=conversion_type,
        stub_test=_STUB_TEST,
        overwrite=_OVERWRITE,
    )
    logging.info(f"\nFinished conversion for {subject}/{session}\n")
