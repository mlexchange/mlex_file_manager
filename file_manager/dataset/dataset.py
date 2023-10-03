
class Dataset:
    def __init__(self, uri, type='file', tags=[], project=None, uid=None, **kwargs):
        '''
        Base class for data set schema definition
        Args:
            uid:            Splash UID of data set
            uri:            URI of the data set
            data_type:      file or tiled
            tags:           List of tags assigned to the data set
            project_id:     Project id to track data set of interest
        '''
        self.uid = uid
        self.uri = uri
        self.type = type
        self.tags = tags
        self.project = project
        pass