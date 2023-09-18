"""Primary script to run to convert an entire session for of data using the NWBConverter."""
from pathlib import Path
from typing import Union
import datetime
import glob
import json
from zoneinfo import ZoneInfo

from neuroconv.utils import load_dict_from_file, dict_deep_update

from jazayeri_lab_to_nwb.watters import WattersNWBConverter


def session_to_nwb(data_dir_path: Union[str, Path], output_dir_path: Union[str, Path], stub_test: bool = False):

    data_dir_path = Path(data_dir_path)
    output_dir_path = Path(output_dir_path)
    if stub_test:
        output_dir_path = output_dir_path / "nwb_stub"
    output_dir_path.mkdir(parents=True, exist_ok=True)

    session_id = f"ses-{data_dir_path.name}"
    raw_nwbfile_path = output_dir_path / f"{session_id}_raw.nwb"
    processed_nwbfile_path = output_dir_path / f"{session_id}_processed.nwb"

    raw_source_data = dict()
    raw_conversion_options = dict()
    processed_source_data = dict()
    processed_conversion_options = dict()

    for probe_num in range(2):
        # Add V-Probe Recording
        if not (data_dir_path / "raw_data" / f"v_probe_{probe_num}").exists():
            continue
        recording_files = list(glob.glob(str(data_dir_path / "raw_data" / f"v_probe_{probe_num}" / "*.dat")))
        assert len(recording_files) > 0, f"No .dat files found in {data_dir_path}"
        assert len(recording_files) == 1, f"Multiple .dat files found in {data_dir_path}"
        recording_source_data = {
            f"RecordingVP{probe_num}": dict(
                file_path=str(recording_files[0]),
                probe_metadata_file=str(data_dir_path / "data_open_source" / "probes.metadata.json"),
                probe_key=f"probe{(probe_num+1):02d}",
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
        processed_source_data.update(
            {
                f"SortingVP{probe_num}": dict(
                    folder_path=str(data_dir_path / "spike_sorting_raw" / f"v_probe_{probe_num}"),
                    keep_good_only=False,
                )
            }
        )
        processed_conversion_options.update({f"SortingVP{probe_num}": dict(stub_test=stub_test, write_as="processing")})

    # Add Recording
    recording_files = list(glob.glob(str(data_dir_path / "raw_data" / "spikeglx" / "*" / "*" / "*.ap.bin")))
    assert len(recording_files) > 0, f"No .ap.bin files found in {data_dir_path}"
    assert len(recording_files) == 1, f"Multiple .ap.bin files found in {data_dir_path}"
    raw_source_data.update(dict(RecordingNP=dict(file_path=str(recording_files[0]))))
    processed_source_data.update(dict(RecordingNP=dict(file_path=str(recording_files[0]))))
    raw_conversion_options.update(dict(RecordingNP=dict(stub_test=stub_test)))
    processed_conversion_options.update(dict(RecordingNP=dict(stub_test=stub_test, write_electrical_series=False)))

    # Add LFP
    lfp_files = list(glob.glob(str(data_dir_path / "raw_data" / "spikeglx" / "*" / "*" / "*.lf.bin")))
    assert len(lfp_files) > 0, f"No .lf.bin files found in {data_dir_path}"
    assert len(lfp_files) == 1, f"Multiple .lf.bin files found in {data_dir_path}"
    raw_source_data.update(dict(LFP=dict(file_path=str(lfp_files[0]))))
    processed_source_data.update(dict(LFP=dict(file_path=str(lfp_files[0]))))
    raw_conversion_options.update(dict(LFP=dict(write_as="lfp", stub_test=stub_test)))
    processed_conversion_options.update(dict(LFP=dict(stub_test=stub_test, write_electrical_series=False)))

    # Add Sorting
    processed_source_data.update(
        dict(
            SortingNP=dict(
                folder_path=str(data_dir_path / "spike_sorting_raw" / "np"),
                keep_good_only=False,
            )
        )
    )
    processed_conversion_options.update(dict(SortingNP=dict(stub_test=stub_test, write_as="processing")))

    # Add Behavior
    processed_source_data.update(
        dict(EyePosition=dict(folder_path=str(data_dir_path / "data_open_source" / "behavior")))
    )
    processed_conversion_options.update(dict(EyePosition=dict()))

    processed_source_data.update(dict(PupilSize=dict(folder_path=str(data_dir_path / "data_open_source" / "behavior"))))
    processed_conversion_options.update(dict(PupilSize=dict()))

    # Add Trials
    processed_source_data.update(dict(Trials=dict(folder_path=str(data_dir_path / "data_open_source"))))
    processed_conversion_options.update(dict(Trials=dict()))

    processed_converter = WattersNWBConverter(
        source_data=processed_source_data, sync_dir=str(data_dir_path / "sync_pulses")
    )

    # Add datetime to conversion
    metadata = processed_converter.get_metadata()  # use processed b/c it has everything
    try:
        date = datetime.datetime.strptime(data_dir_path.name, "%Y-%m-%d%").astimezone(ZoneInfo("US/Eastern"))
        print(f"auto detecting date as {date}")
    except:
        date = datetime.datetime(year=2022, month=6, day=1, tzinfo=ZoneInfo("US/Eastern"))
    metadata["NWBFile"]["session_start_time"] = date
    metadata["NWBFile"]["session_id"] = session_id

    # Subject name
    if "monkey0" in str(data_dir_path):
        metadata["Subject"]["subject_id"] = "Perle"
    elif "monkey1" in str(data_dir_path):
        metadata["Subject"]["subject_id"] = "Elgar"

    # EcePhys
    probe_metadata_file = data_dir_path / "data_open_source" / "probes.metadata.json"
    with open(probe_metadata_file, "r") as f:
        probe_metadata = json.load(f)
    neuropixel_metadata = [entry for entry in probe_metadata if entry["label"] == "probe00"][0]
    for entry in metadata["Ecephys"]["ElectrodeGroup"]:
        if entry["device"] == "Neuropixel-Imec":
            # entry.update(dict(position=[(
            #     neuropixel_metadata["coordinates"][0],
            #     neuropixel_metadata["coordinates"][1],
            #     neuropixel_metadata["depth_from_surface"],
            # )]
            pass  # TODO: uncomment when fixed in pynwb

    # Update default metadata with the editable in the corresponding yaml file
    editable_metadata_path = Path(__file__).parent / "watters_metadata.yaml"
    editable_metadata = load_dict_from_file(editable_metadata_path)
    metadata = dict_deep_update(metadata, editable_metadata)

    # Run conversion
    processed_converter.run_conversion(
        metadata=metadata, nwbfile_path=processed_nwbfile_path, conversion_options=processed_conversion_options
    )

    raw_converter = WattersNWBConverter(source_data=raw_source_data, sync_dir=str(data_dir_path / "sync_pulses"))
    raw_converter.run_conversion(
        metadata=metadata, nwbfile_path=raw_nwbfile_path, conversion_options=raw_conversion_options
    )


if __name__ == "__main__":

    # Parameters for conversion
    data_dir_path = Path("/shared/catalystneuro/JazLab/monkey0/2022-06-01/")
    # data_dir_path = Path("/shared/catalystneuro/JazLab/monkey1/2022-06-05/")
    output_dir_path = Path("~/conversion_nwb/jazayeri-lab-to-nwb/watters_perle_combined/").expanduser()
    stub_test = True

    session_to_nwb(
        data_dir_path=data_dir_path,
        output_dir_path=output_dir_path,
        stub_test=stub_test,
    )
