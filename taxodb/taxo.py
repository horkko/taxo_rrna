from __future__ import print_function
from taxodb.silva import Silva
from taxodb.greengenes import GreenGenes
from taxodb.ncbi import NCBI
from taxodb.utils import Utils


class Taxo(object):
    """Wrapping class for creating inheriting classes such as Silva and GreenGenes"""

    def __init__(self, kwargs):
        """
        Default taxodb class
        :param name:
        :param input:
        :param bdb:
        """
        if not kwargs['dbtype']:
            Utils.error("A taxodb name is required")
        self.args = kwargs
        self.dbtype = str(kwargs['dbtype']).lower()
        self._clean_args()

    def get_db(self):
        """

        :return:
        """
        if self.dbtype == 'silva':
            return Silva(**self.args)
        if self.dbtype == 'greengenes':
            return GreenGenes(**self.args)
        if self.dbtype == 'ncbi':
            return NCBI(**self.args)
        Utils.error("Unsupported taxonomy database %s" % self.dbtype)

    def _clean_args(self):
        """
        Remove unsupported args for specific db type

        :return:
        """
        del self.args['dbtype']
        del self.args['verbose']

        if self.dbtype == 'silva' or self.dbtype == 'greengenes':
            for arg in ['use_lineage', 'format', 'taxofmt', 'flatdb', 'nodes', 'names']:
                if arg in self.args:
                    del self.args[arg]
        if self.dbtype == 'ncbi':
            del self.args['fasta']
        return True

