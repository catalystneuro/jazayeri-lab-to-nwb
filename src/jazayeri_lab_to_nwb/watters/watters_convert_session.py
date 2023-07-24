"""Primary script to run to convert an entire session for of data using the NWBConverter."""
from pathlib import Path
from typing import Union
import datetime
from zoneinfo import ZoneInfo

from neuroconv.utils import load_dict_from_file, dict_deep_update

from jazayeri_lab_to_nwb.watters import WattersNWBConverter


def session_to_nwb(data_dir_path: Union[str, Path], output_dir_path: Union[str, Path], stub_test: bool = False):

    data_dir_path = Path(data_dir_path)
    output_dir_path = Path(output_dir_path)
    if stub_test:
        output_dir_path = output_dir_path / "nwb_stub"
    output_dir_path.mkdir(parents=True, exist_ok=True)

    session_id = "monkey0_2022_06_01"
    nwbfile_path = output_dir_path / f"{session_id}.nwb"

    source_data = dict()
    conversion_options = dict()

    # Add Recording
    # source_data.update(dict(Recording=dict(file_path=str(
    #     data_dir_path / "raw_data" / "spikeglx" / "2022_06_01_perle_g0" /
    #     "2022_06_01_perle_g0_imec0" / "2022_06_01_perle_g0_t0.imec0.ap.bin"
    # ))))
    # conversion_options.update(dict(Recording=dict(stub_test=True)))

    # Add LFP
    # source_data.update(dict(LFP=dict(file_path=str(
    #     data_dir_path / "raw_data" / "spikeglx" / "2022_06_01_perle_g0" /
    #     "2022_06_01_perle_g0_imec0" / "2022_06_01_perle_g0_t0.imec0.lf.bin"
    # ))))
    # conversion_options.update(dict(LFP=dict(write_as="lfp", stub_test=True)))

    # Add NIDQ
    # source_data.update(dict(NIDQ=dict(file_path=str(
    #     data_dir_path / "raw_data" / "spikeglx" / "2022_06_01_perle_g0" /
    #     "2022_06_01_perle_g0_t0.nidq.bin"
    # ))))
    # conversion_options.update(dict(NIDQ=dict(stub_test=True)))

    # Add V-probe recording
    source_data.update(
        dict(
            OERecording=dict(
                folder_path=str(data_dir_path / "raw_data" / "open_ephys" / "2022-06-01_13-46-03" / "Record_Node_104"),
                stream_name="Signals CH",
            )
        )
    )
    conversion_options.update(dict(OERecording=dict(stub_test=True)))

    # Add Sorting
    # source_data.update(dict(Sorting=dict()))
    # conversion_options.update(dict(Sorting=dict()))

    # Add Behavior
    # source_data.update(dict(Behavior=dict()))
    # conversion_options.update(dict(Behavior=dict()))

    converter = WattersNWBConverter(source_data=source_data)

    # Add datetime to conversion
    metadata = converter.get_metadata()
    datetime.datetime(year=2020, month=1, day=1, tzinfo=ZoneInfo("US/Eastern"))
    date = datetime.datetime.today()  # TO-DO: Get this from author
    metadata["NWBFile"]["session_start_time"] = date

    # Update default metadata with the editable in the corresponding yaml file
    editable_metadata_path = Path(__file__).parent / "watters_metadata.yaml"
    editable_metadata = load_dict_from_file(editable_metadata_path)
    metadata = dict_deep_update(metadata, editable_metadata)

    # Run conversion
    converter.run_conversion(metadata=metadata, nwbfile_path=nwbfile_path, conversion_options=conversion_options)


if __name__ == "__main__":

    # Parameters for conversion
    data_dir_path = Path("/shared/catalystneuro/JazLab/monkey0/2022-06-01/")
    output_dir_path = Path("~/conversion_nwb/jazayeri-lab-to-nwb/watters_openephys/").expanduser()
    stub_test = False

    session_to_nwb(
        data_dir_path=data_dir_path,
        output_dir_path=output_dir_path,
        stub_test=stub_test,
    )
