
CONVERSION_PARAMS = {
    data_interface_classes = dict(
        RecordingVP0=DatRecordingInterface,
        SortingVP0=neuroconv.datainterfaces.KiloSortSortingInterface,
        RecordingVP1=DatRecordingInterface,
        SortingVP1=neuroconv.datainterfaces.KiloSortSortingInterface,
        RecordingNP=neuroconv.datainterfaces.SpikeGLXRecordingInterface,
        LF=neuroconv.datainterfaces.SpikeGLXRecordingInterface,
        SortingNP=neuroconv.datainterfaces.KiloSortSortingInterface,
        EyePosition=timeseries_interface.EyePositionInterface,
        PupilSize=timeseries_interface.PupilSizeInterface,
        RewardLine=timeseries_interface.RewardLineInterface,
        Audio=timeseries_interface.AudioInterface,
        Trials=trials_interface.TrialsInterface,
        Display=display_interface.DisplayInterface,
    )
}

