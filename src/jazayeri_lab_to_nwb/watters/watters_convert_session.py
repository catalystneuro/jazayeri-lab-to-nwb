"""Primary script to run to convert an entire session for of data using the NWBConverter."""
from pathlib import Path
from typing import Union
import datetime
import shutil
from zoneinfo import ZoneInfo

from neuroconv.utils import load_dict_from_file, dict_deep_update

from jazayeri_lab_to_nwb.watters import WattersNWBConverter
from jazayeri_lab_to_nwb.utils.openephys_reformat import make_temporary_openephys_tree


def session_to_nwb(data_dir_path: Union[str, Path], output_dir_path: Union[str, Path], stub_test: bool = False):

    data_dir_path = Path(data_dir_path)
    output_dir_path = Path(output_dir_path)
    if stub_test:
        output_dir_path = output_dir_path / "nwb_stub"
    output_dir_path.mkdir(parents=True, exist_ok=True)

    # session_id = "20220601-vprobe1"
    session_id = "20220605-vprobe0"
    nwbfile_path = output_dir_path / f"{session_id}.nwb"

    source_data = dict()
    conversion_options = dict()

    # Add Recording
    """
    source_data.update(dict(NPRecording=dict(file_path=str(
        # data_dir_path / "raw_data" / "spikeglx" / "2022_06_01_perle_g0" /
        # "2022_06_01_perle_g0_imec0" / "2022_06_01_perle_g0_t0.imec0.ap.bin"
        data_dir_path / "raw_data" / "spikeglx" / "2022_06_05_elgar_task_g0" /
        "2022_06_05_elgar_task_g0_imec0" / "2022_06_05_elgar_task_g0_t0.imec0.ap.bin"
    ))))
    conversion_options.update(dict(NPRecording=dict(stub_test=stub_test)))
    """

    # Add LFP
    """
    source_data.update(dict(LFP=dict(file_path=str(
        # data_dir_path / "raw_data" / "spikeglx" / "2022_06_01_perle_g0" /
        # "2022_06_01_perle_g0_imec0" / "2022_06_01_perle_g0_t0.imec0.lf.bin"
        data_dir_path / "raw_data" / "spikeglx" / "2022_06_05_elgar_task_g0" /
        "2022_06_05_elgar_task_g0_imec0" / "2022_06_05_elgar_task_g0_t0.imec0.lf.bin"
    ))))
    conversion_options.update(dict(LFP=dict(write_as="lfp", stub_test=stub_test)))
    """

    # Add NIDQ
    """
    source_data.update(dict(NIDQ=dict(file_path=str(
        data_dir_path / "raw_data" / "spikeglx" / "2022_06_01_perle_g0" /
        "2022_06_01_perle_g0_t0.nidq.bin"
    ))))
    conversion_options.update(dict(NIDQ=dict(stub_test=stub_test)))
    """

    # Add V-probe recording (legacy)
    """
    temp_dir = make_temporary_openephys_tree(
        # folder_path=(data_dir_path / "raw_data" / "open_ephys" / "2022-06-01_13-46-03" / "Record_Node_104"),
        folder_path=(data_dir_path / "raw_data" / "open_ephys" / "2022-06-05_17-08-57" / "Record_Node_114"),
    )
    source_data.update(
        dict(
            OERecording=dict(
                folder_path=str(temp_dir),
                stream_name="Signals CH",
                es_key="ElectricalSeries",
            )
        )
    )
    conversion_options.update(dict(OERecording=dict(stub_test=stub_test)))
    """

    # Add V-probe recording (binary)

    temp_dir = make_temporary_openephys_tree(
        # folder_path=(data_dir_path / "raw_data" / "open_ephys" / "2022-06-01_13-46-03" / "Record_Node_104"),
        folder_path=(data_dir_path / "raw_data" / "open_ephys" / "2022-06-05_17-08-57" / "Record_Node_114"),
        dat_folder_paths=[
            str(data_dir_path / "raw_data" / "v_probe_0"),
            # str(data_dir_path / "raw_data" / "v_probe_1"),
        ],
    )

    source_data.update(
        dict(
            VP1Recording=dict(
                # folder_path=str(data_dir_path / "raw_data" / "open_ephys" / "2022-06-01_13-46-03" / "Record_Node_104"),
                folder_path=str(temp_dir),
                # dat_folder_paths=[
                #     str(data_dir_path / "raw_data" / "v_probe_0"),
                #     str(data_dir_path / "raw_data" / "v_probe_1"),
                # ],
                stream_name="v_probe_0",
                # es_key="ElectricalSeries",
                # make_temporary_tree=False,
            )
        )
    )
    conversion_options.update(dict(VP1Recording=dict(stub_test=stub_test)))
    """
    source_data.update(
        dict(
            VP2Recording=dict(
                # folder_path=str(data_dir_path / "raw_data" / "open_ephys" / "2022-06-01_13-46-03" / "Record_Node_104"),
                folder_path=str(temp_dir),
                # dat_folder_paths=[
                #     str(data_dir_path / "raw_data" / "v_probe_0"),
                #     str(data_dir_path / "raw_data" / "v_probe_1"),
                # ],
                stream_name="v_probe_1",
                es_key="ElectricalSeries",
                # make_temporary_tree=False,
            )
        )
    )
    conversion_options.update(dict(VP2Recording=dict(stub_test=stub_test)))
    """

    # Add Sorting
    """
    source_data.update(
        dict(
            NPSorting=dict(
                folder_path=str(data_dir_path / "spike_sorting_raw" / "np"),
                keep_good_only=True,
            )
        )
    )
    conversion_options.update(dict(NPSorting=dict(stub_test=stub_test, write_as="processing")))
    """
    source_data.update(
        dict(
            VP1Sorting=dict(
                folder_path=str(data_dir_path / "spike_sorting_raw" / "v_probe_0"),
                keep_good_only=True,
            )
        )
    )
    conversion_options.update(dict(VP1Sorting=dict(stub_test=stub_test, write_as="processing")))
    """
    source_data.update(
        dict(
            VP2Sorting=dict(
                folder_path=str(data_dir_path / "spike_sorting_raw" / "v_probe_1"),
                keep_good_only=True,
            )
        )
    )
    conversion_options.update(dict(VP2Sorting=dict(stub_test=stub_test, write_as="processing")))
    """

    # Add Behavior
    # source_data.update(dict(Behavior=dict()))
    # conversion_options.update(dict(Behavior=dict()))

    converter = WattersNWBConverter(source_data=source_data)

    # Add datetime to conversion
    metadata = converter.get_metadata()
    # date = datetime.datetime(year=2022, month=6, day=1, tzinfo=ZoneInfo("US/Eastern"))
    date = datetime.datetime(year=2022, month=6, day=5, tzinfo=ZoneInfo("US/Eastern"))
    # date = datetime.datetime.today()  # TO-DO: Get this from author
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

    # shutil.rmtree(temp_dir)


if __name__ == "__main__":

    # Parameters for conversion
    # data_dir_path = Path("/shared/catalystneuro/JazLab/monkey0/2022-06-01/")
    data_dir_path = Path("/shared/catalystneuro/JazLab/monkey1/2022-06-05/")
    output_dir_path = Path("~/conversion_nwb/jazayeri-lab-to-nwb/watters1_vprobe0/").expanduser()
    stub_test = False

    session_to_nwb(
        data_dir_path=data_dir_path,
        output_dir_path=output_dir_path,
        stub_test=stub_test,
    )
