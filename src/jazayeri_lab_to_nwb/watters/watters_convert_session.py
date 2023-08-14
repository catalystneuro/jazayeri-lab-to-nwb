"""Primary script to run to convert an entire session for of data using the NWBConverter."""
from pathlib import Path
from typing import Union
import datetime
import glob
from zoneinfo import ZoneInfo

from neuroconv.utils import load_dict_from_file, dict_deep_update

from jazayeri_lab_to_nwb.watters import WattersNWBConverter


def session_to_nwb(data_dir_path: Union[str, Path], output_dir_path: Union[str, Path], stub_test: bool = False):

    probe_num = 0

    data_dir_path = Path(data_dir_path)
    output_dir_path = Path(output_dir_path)
    if stub_test:
        output_dir_path = output_dir_path / "nwb_stub"
    output_dir_path.mkdir(parents=True, exist_ok=True)

    session_id = f"20220601-vprobe{probe_num}"
    nwbfile_path = output_dir_path / f"{session_id}.nwb"

    source_data = dict()
    conversion_options = dict()

    # Add Recording
    recording_files = list(glob.glob(str(data_dir_path / "raw_data" / f"v_probe_{probe_num}" / "*.dat")))
    assert len(recording_files) > 0, f"No .dat files found in {data_dir_path}"
    assert len(recording_files) == 1, f"Multiple .dat files found in {data_dir_path}"
    source_data.update(dict(Recording=dict(file_path=str(recording_files[0]))))
    conversion_options.update(dict(Recording=dict(stub_test=stub_test)))

    # Add LFP
    # source_data.update(dict(LFP=dict()))
    # conversion_options.update(dict(LFP=dict()))

    # Add Sorting
    source_data.update(
        dict(
            Sorting=dict(
                folder_path=str(data_dir_path / "spike_sorting_raw" / f"v_probe_{probe_num}"),
                keep_good_only=True,
            )
        )
    )
    conversion_options.update(dict(Sorting=dict(stub_test=stub_test, write_as="processing")))

    # Add Behavior
    # source_data.update(dict(Behavior=dict()))
    # conversion_options.update(dict(Behavior=dict()))

    converter = WattersNWBConverter(source_data=source_data)

    # Add datetime to conversion
    metadata = converter.get_metadata()
    date = datetime.datetime(year=2022, month=6, day=1, tzinfo=ZoneInfo("US/Eastern"))
    metadata["NWBFile"]["session_start_time"] = date
    metadata["NWBFile"]["session_id"] = session_id

    # Subject name
    if "monkey0" in str(data_dir_path):
        metadata["Subject"]["subject_id"] = "Perle"
    elif "monkey1" in str(data_dir_path):
        metadata["Subject"]["subject_id"] = "Elgar"

    # Update default metadata with the editable in the corresponding yaml file
    editable_metadata_path = Path(__file__).parent / "watters_metadata.yaml"
    editable_metadata = load_dict_from_file(editable_metadata_path)
    metadata = dict_deep_update(metadata, editable_metadata)

    # Run conversion
    converter.run_conversion(metadata=metadata, nwbfile_path=nwbfile_path, conversion_options=conversion_options)


if __name__ == "__main__":

    # Parameters for conversion
    data_dir_path = Path("/shared/catalystneuro/JazLab/monkey0/2022-06-01/")
    output_dir_path = Path("~/conversion_nwb/jazayeri-lab-to-nwb/watters_perle_vprobe0/").expanduser()
    stub_test = True

    session_to_nwb(
        data_dir_path=data_dir_path,
        output_dir_path=output_dir_path,
        stub_test=stub_test,
    )
