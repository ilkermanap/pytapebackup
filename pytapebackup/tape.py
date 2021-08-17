

class TapeDevice:
    def __init__(self, device):
        """
        Create a tape device class.
        This will be the class that communicates with actual device
        """
        self.device = device
        self.tape = None

    def load(self):
        """
        read the identifier and content from tape.
        update the self.tape with a Tape instance
        """
        pass
    
class Tape:
    def __init__(self, tapeid=None):
        """
        1. block  tar file with tape id
        2. block first archive
        3. block first archive properties (property files inside a tar file)
        .
        .
        .
        n. block  n/2. archive
        n+1. block  n/2 archive properties


        Archive properties file will be used to create the Archive instance
        """
        self.tapeid = tapeid
        self.content = {}
        
class Archive:
    def __init__(self, fname):
        """
        #TODO: define what should be included inside here
        backuptime: when the backup created
        contents: 
        """
        self.backuptime = None
        self.label = None

    def load(self):
        """
        extract the content of the tar file and fill the properties
        """
        pass
