"""Primary script to run to convert an entire session for of data using the NWBConverter."""

import datetime
import glob
import json
import logging
from pathlib import Path
from typing import Union
from uuid import uuid4
from zoneinfo import ZoneInfo

from neuroconv.utils import load_dict_from_file, dict_deep_update

from jazayeri_lab_to_nwb.watters import WattersNWBConverter

# Set logger level for info is displayed in console
logging.getLogger().setLevel(logging.INFO)


def _get_single_file(directory, suffix=""):
    """Get path to a file in given directory with given suffix.

    Raisees error if not exactly one satisfying file.
    """
    files = list(glob.glob(str(directory / f"*{suffix}")))
    if len(files) == 0:
        raise ValueError(f"No {suffix} files found in {directory}")
    if len(files) > 1:
        raise ValueError(f"Multiple {suffix} files found in {directory}")
    return files[0]


def session_to_nwb(
    data_dir: Union[str, Path],
    output_dir_path: Union[str, Path],
    stub_test: bool = False,
    overwrite: bool = False,
):

    logging.info("")
    logging.info(f"data_dir = {data_dir}")
    logging.info(f"output_dir_path = {output_dir_path}")
    logging.info(f"stub_test = {stub_test}")

    data_dir = Path(data_dir)
    output_dir_path = Path(output_dir_path)
    if stub_test:
        output_dir_path = output_dir_path / "nwb_stub"
    output_dir_path.mkdir(parents=True, exist_ok=True)

    session_id = f"ses-{data_dir.name}"
    raw_nwbfile_path = output_dir_path / f"{session_id}_raw.nwb"
    processed_nwbfile_path = output_dir_path / f"{session_id}_processed.nwb"
    logging.info(f"raw_nwbfile_path = {raw_nwbfile_path}")
    logging.info(f"processed_nwbfile_path = {processed_nwbfile_path}")

    raw_source_data = dict()
    raw_conversion_options = dict()
    processed_source_data = dict()
    processed_conversion_options = dict()

    for probe_num in range(2):
        # Add V-Probe Recording
        probe_data_dir = data_dir / "raw_data" / f"v_probe_{probe_num}"
        if not probe_data_dir.exists():
            continue
        logging.info(f"\nAdding V-probe {probe_num} recording")

        logging.info("    Raw data")
        recording_file = _get_single_file(probe_data_dir, suffix=".dat")
        recording_source_data = {
            f"RecordingVP{probe_num}": dict(
                file_path=recording_file,
                probe_metadata_file=str(data_dir / "data_open_source" / "probes.metadata.json"),
                probe_key=f"probe{(probe_num + 1):02d}",
                probe_name=f"vprobe{probe_num}",
                es_key=f"ElectricalSeriesVP{probe_num}",
            )
        }
        raw_source_data.update(recording_source_data)
        processed_source_data.update(recording_source_data)
        raw_conversion_options.update({f"RecordingVP{probe_num}": dict(stub_test=stub_test)})
        processed_conversion_options.update(
            {f"RecordingVP{probe_num}": dict(stub_test=stub_test, write_electrical_series=False)}
        )

        # Add V-Probe Sorting
        logging.info("    Spike sorted data")
        processed_source_data.update(
            {
                f"SortingVP{probe_num}": dict(
                    folder_path=str(data_dir / "spike_sorting_raw" / f"v_probe_{probe_num}"),
                    keep_good_only=False,
                )
            }
        )
        processed_conversion_options.update({f"SortingVP{probe_num}": dict(stub_test=stub_test, write_as="processing")})

    # Add SpikeGLX Recording
    logging.info("Adding SpikeGLX recordings")
    logging.info("    AP data")
    probe_data_dir = data_dir / "raw_data" / "spikeglx" / "*" / "*"
    ap_file = _get_single_file(probe_data_dir, suffix=".ap.bin")
    raw_source_data.update(dict(RecordingNP=dict(file_path=ap_file)))
    processed_source_data.update(dict(RecordingNP=dict(file_path=ap_file)))
    raw_conversion_options.update(dict(RecordingNP=dict(stub_test=stub_test)))
    processed_conversion_options.update(dict(RecordingNP=dict(stub_test=stub_test, write_electrical_series=False)))

    # Add LFP
    logging.info("    LFP data")
    lfp_file = _get_single_file(probe_data_dir, suffix=".lf.bin")
    raw_source_data.update(dict(LF=dict(file_path=lfp_file)))
    processed_source_data.update(dict(LF=dict(file_path=lfp_file)))
    raw_conversion_options.update(dict(LF=dict(stub_test=stub_test)))
    processed_conversion_options.update(dict(LF=dict(stub_test=stub_test, write_electrical_series=False)))

    # Add Sorting
    logging.info("    Spike sorted data")
    processed_source_data.update(
        dict(
            SortingNP=dict(
                folder_path=str(data_dir / "spike_sorting_raw" / "np"),
                keep_good_only=False,
            )
        )
    )
    processed_conversion_options.update(dict(SortingNP=dict(stub_test=stub_test, write_as="processing")))

    # Add Behavior
    logging.info("Adding behavior")
    behavior_path = str(data_dir / "data_open_source" / "behavior")
    processed_source_data.update(dict(EyePosition=dict(folder_path=behavior_path)))
    processed_conversion_options.update(dict(EyePosition=dict()))

    processed_source_data.update(dict(PupilSize=dict(folder_path=behavior_path)))
    processed_conversion_options.update(dict(PupilSize=dict()))

    # Add Trials
    logging.info("Adding task data")
    processed_source_data.update(dict(Trials=dict(folder_path=str(data_dir / "data_open_source"))))
    processed_conversion_options.update(dict(Trials=dict()))

    processed_converter = WattersNWBConverter(source_data=processed_source_data, sync_dir=str(data_dir / "sync_pulses"))

    # Add datetime to conversion
    metadata = processed_converter.get_metadata()
    metadata["NWBFile"]["session_id"] = session_id

    # Subject name
    if "monkey0" in str(data_dir):
        metadata["Subject"]["subject_id"] = "Perle"
    elif "monkey1" in str(data_dir):
        metadata["Subject"]["subject_id"] = "Elgar"

    # EcePhys
    probe_metadata_file = data_dir / "data_open_source" / "probes.metadata.json"
    with open(probe_metadata_file, "r") as f:
        probe_metadata = json.load(f)
    neuropixel_metadata = [entry for entry in probe_metadata if entry["label"] == "probe00"][0]
    for entry in metadata["Ecephys"]["ElectrodeGroup"]:
        if entry["device"] == "Neuropixel-Imec":
            # TODO: uncomment when fixed in pynwb
            # entry.update(dict(position=[(
            #     neuropixel_metadata["coordinates"][0],
            #     neuropixel_metadata["coordinates"][1],
            #     neuropixel_metadata["depth_from_surface"],
            # )]
            logging.warning("\n\n    PROBE COORDINATES NOT IMPLEMENTED\n\n")

    # Update default metadata with the editable in the corresponding yaml file
    editable_metadata_path = Path(__file__).parent / "watters_metadata.yaml"
    editable_metadata = load_dict_from_file(editable_metadata_path)
    metadata = dict_deep_update(metadata, editable_metadata)

    # check if session_start_time was found/set
    if "session_start_time" not in metadata["NWBFile"]:
        try:
            date = datetime.datetime.strptime(data_dir.name, "%Y-%m-%d")
            date = date.replace(tzinfo=ZoneInfo("US/Eastern"))
        except:
            raise ValueError(
                "Session start time was not auto-detected. Please provide it " "in `watters_metadata.yaml`"
            )
        metadata["NWBFile"]["session_start_time"] = date

    # Run conversion
    logging.info("Running processed conversion")
    processed_converter.run_conversion(
        metadata=metadata,
        nwbfile_path=processed_nwbfile_path,
        conversion_options=processed_conversion_options,
        overwrite=overwrite,
    )

    logging.info("Running raw data conversion")
    metadata["NWBFile"]["identifier"] = str(uuid4())
    raw_converter = WattersNWBConverter(source_data=raw_source_data, sync_dir=str(data_dir / "sync_pulses"))
    raw_converter.run_conversion(
        metadata=metadata,
        nwbfile_path=raw_nwbfile_path,
        conversion_options=raw_conversion_options,
        overwrite=overwrite,
    )


if __name__ == "__main__":

    # Parameters for conversion
    data_dir = Path("/om2/user/nwatters/catalystneuro/initial_data_transfer/" "monkey0/2022-06-01/")
    output_dir_path = Path("/om/user/nwatters/nwb_data/watters_perle_combined/")
    stub_test = True
    overwrite = True

    session_to_nwb(
        data_dir=data_dir,
        output_dir_path=output_dir_path,
        stub_test=stub_test,
        overwrite=overwrite,
    )
