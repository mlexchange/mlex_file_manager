class Dataset:
    def __init__(self, uri, cumulative_data_count):
        """
        Base class for data set schema definition
        Args:
            uri:                    Data set URI
            cumulative_data_count:  Cumulative data count
        """
        self.uri = uri
        self.cumulative_data_count = cumulative_data_count
        pass
