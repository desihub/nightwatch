class QA(object):
    """This is an abstract base class to define what quantities a
    subclass should define"""
    def __init__(self):
        #- Subclasses should define self.output_type to be one of
        #- PER_AMP, PER_FIBER, PER_SPECTRO, PER_CAMFIBER, PER_CAMERA
        self.output_type = "None"
        pass

    def valid_flavor(self, flavor):
        '''Return True/False if this metric is applicable to this flavor
        of exposure (ZERO, DARK, ARC, FLAT, SCIENCE)'''
        return False

    def run(self, indir):
        '''Run this QA on files in `indir`
        
        TODO: document return values
        '''
        raise NotImplementedError

    def __repr__(self):
        return self.__class__.__name__
