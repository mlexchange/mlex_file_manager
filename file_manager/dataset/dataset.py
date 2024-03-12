class Dataset:
    def __init__(self, uri, type="file", **kwargs):
        """
        Base class for data set schema definition
        Args:
            uri:            URI of the data set
            data_type:      file or tiled
        """
        self.uri = uri
        self.type = type
        pass
