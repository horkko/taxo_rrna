from __future__ import print_function
import os
from bsddb3 import db
from taxodb.utils import Utils

__author__ = "Emmanuel Quevillon"
__email__ = "tuco@pasteur.fr"


class NCBI(object):
    """
    NCBI class used to work with NCBI taxonomy files (names.dmp and nodes.dmp)

    This class is able to parse NCBI's taxonomy files and create Berkeley DB file in order to be be used
    with taxo_pack utils.

    dmp files are available at:
    ftp://ftp.ncbi.nlm.nih.gov/pub/taxonomy/taxdump.tar.gz

    @author: Corinne Maufrais, Original author (maufrais@pasteur.fr)
    @author: Emmanuel Quevillon, rewrite and packing (tuco@pasteur.fr)
    @copyright: Institut Pasteur, DSI/CIB
    """

    DEFAULT_SEPARATOR = '\t|\t'
    DB_VALUE_SEPARATOR = ''
    TAX_FMT_SUPPORTED = ['full', 'partial']
    # Allowed names for Organism Specie (names.dmp)
    AUTH_OS_NAMES = ['scientific name', 'equivalent name', 'synonym', 'authority', 'common name']

    def __init__(self, names=None, nodes=None, bdb=None, header_sep=DEFAULT_SEPARATOR, db_sep=DB_VALUE_SEPARATOR,
                 taxofmt='full', flatdb=None, mode=0666):
        """
        Create a new NCBI object to parse dmp taxonomy files and create Berkeley DB file

        :param names: names.dmp file to parse
        :type names: str
        :param nodes: nodes.dmp file to parse
        :type nodes: str
        :param flatdb: Flat db (EMBL like' file name
        :type flatdb: str
        :param bdb: Berkeley DB file name
        :type bdb: str
        :param header_sep: Separator used to parse ID from FASTA header, default '||'
        :type header_sep: str
        :param db_sep: String used to split organism (os) and taxonomy (taxo) values in Berkeley database,
        default '_@#$_'
        :type db_sep: str
        :param taxofmt: Format for taxonomy information report, default 'full'
        :type taxofmt: str
        :param mode: Unix mode to create Berkeley database file, default 0666
        :type mode: int
        :raise: SystemExit if `input` file is not found
        SystemExit if `bdb` file can not be created or opened
        """
        self.names = names
        self.nodes = nodes
        self.flatdb = flatdb
        self.bdb = bdb
        self.hsep = header_sep
        self.dsep = db_sep
        self.taxofmt = taxofmt
        self.mode = mode
        # self.use_lineage = use_lineage
        self.db_size = 0
        self.pnodes = {}
        self.taxids = []
        # self.lineage = {}
        self.oc = {}

        if not self.names:
            Utils.error("names.dmp input file is required")
        if not self.nodes:
            Utils.error("nodes.dmp input file is required")
        if not os.path.isfile(self.names):
            Utils.error("Can't find %s" % self.names)
        if not os.path.isfile(self.nodes):
            Utils.error("Can't find %s" % self.nodes)
        # if not self.bdb:
        #     Utils.error("A Berkeley database file name is required")
        if self.taxofmt not in NCBI.TAX_FMT_SUPPORTED:
            Utils.error("Taxonomy format %s not supported (%s)" % (self.taxofmt, NCBI.TAX_FMT_SUPPORTED))
        self.db = db.DB()

    def create_bdb(self, bdb=None, mode=None):
        """
        This method create NCBI Taxonomy Berkeley database file

        :param bdb: A berkeley database file name
        :type bdb: str
        :param mode: Unix mode to create Berkeley database file, default 0666
        :type mode: int
        :return: True
        :rtype: bool
        """
        if bdb:
            self.bdb = bdb
        if mode:
            self.mode = mode

        try:
            self._parse_nodes()
            self._parse_names()
            # if self.use_lineage:
            #     self._build_lineage_and_oc()
            Utils.verbose("Creating Berkeley database ... ")
            Utils.start_timer()
            self.db.open(self.bdb, None, db.DB_HASH, db.DB_CREATE, mode=self.mode)
            for taxid in self.taxids:
                # if not self.lineage:
                li, oc = self._extract_LI_and_OC(taxid)
                for los in self.pnodes[taxid]['names'].values():
                    for org_sp in los:
                        # if self.lineage:
                        #     self.db.put(org_sp, "; ".join(self.oc[taxid]))
                        # else:
                        self.db.put(org_sp, oc)
            Utils.verbose("Elapsed time %.3f sec" % Utils.elapsed_time())
        except db.DBAccessError as err:
            Utils.error("Can't open Berkeley db %s: %s" % (self.bdb, str(err)))
        except db.DBError as err:
            Utils.error("Error while inserting value in Berkeley db: %s" % str(err))
        finally:
            self.db.close()

    def create_flat_file(self, flatdb=None, char=80):
        """
        Creates a flat file, EMBL format like

        :param flatdb: Flat file (EMBL like) name
        :type flatdb: str
        :param char: Number of characters per line, default 80
        :type char: int
        :return: True
        :rtype: bool
        :raise SystemExit: if cannot write output file
        """
        if flatdb:
            self.flatdb = flatdb
        if not self.flatdb:
            Utils.error("Flat file (EMBL like) not set")
        if not len(self.taxids):
            self._parse_nodes()
            self._parse_names()
            # if self.use_lineage:
            #     self._build_lineage_and_oc()
        try:
            with open(self.flatdb, 'w') as flatfh:
                for taxid in self.taxids:
                    # if not self.use_lineage:
                    li, oc = self._extract_LI_and_OC(taxid)
                    # else:
                    #     oc = self.oc[taxid]
                    #     li = self.lineage[taxid]
                    print('ID   %s;' % str(taxid), file=flatfh)
                    print('XX', file=flatfh)
                    self._print_line(flatfh, li, 'LI', car=char)
                    print('XX', file=flatfh)
                    print('OS   %s;' % self._extract_OS(taxid), file=flatfh)
                    self._print_line(flatfh, oc, 'OC', car=char)
                    print('//', file=flatfh)
        except OSError as err:
            Utils.error("Can't open %s: %s" % (self.flatdb, str(err)))
        return True

    def get_name(self):
        """
        Returns the inheriting class name

        :return: Class name from inherited object
        :rtype: str
        """
        return str(self.__class__.__name__)

    # def _build_lineage_and_oc(self):
    #     """
    #     Build lineage and organism classification for taxonomy
    #
    #     :return: True
    #     :rtype: bool
    #     """
    #     Utils.verbose("Building lineage and OC ...")
    #     Utils.start_timer()
    #     for taxid in self.taxids:
    #         # if taxid == 1:
    #         #     break
    #         # Utils.verbose("[for] %s" % taxid)
    #         lineage = []
    #         oc = []
    #         tid = taxid
    #         while tid in self.pnodes and tid != '1':
    #             id_parent = self.pnodes[tid]['id_parent']
    #             if self.pnodes[tid]['id_parent'] != '1':
    #                 lineage.append(id_parent)
    #             # Utils.verbose("[while] %s/%s" % (tid, id_parent))
    #             if id_parent == tid:
    #                 tid = '1'
    #             else:
    #                 tid = id_parent
    #                 if tid != '1' and tid in self.pnodes:
    #                     org_species = self._extract_OS(tid)
    #                     # default
    #                     # org_species = self.pnodes[taxid]['names'].keys()[0][0]
    #                     for name in NCBI.AUTH_OS_NAMES:
    #                         if name in self.pnodes[taxid]['names']:
    #                             org_species = self.pnodes[taxid]['names'][name][0]
    #                     if self.pnodes[id_parent]['rank'] != 'no rank':
    #                         org_species += ' (%s)' % self.pnodes[tid]['rank']
    #                     oc.append(org_species)
    #         lineage.reverse()
    #         oc.reverse()
    #         self.lineage[taxid] = lineage
    #         self.oc[taxid] = oc
    #     Utils.verbose("Elapsed time %.3f sec" % Utils.elapsed_time())
    #     return True

    def _extract_LI_and_OC(self, taxid):
        """
        Extract lineage and Organism classification for a taxonomy ID

        :param taxid: Taxonomy ID
        :type taxid: str
        :return:
        :rtype: str
        """
        li = ''  # list of parent taxid
        oc = ''
        while taxid in self.pnodes and taxid != '1':
            if self.pnodes[taxid]['id_parent'] != '1':
                li = self.pnodes[taxid]['id_parent'] + '; ' + li
            if self.pnodes[taxid]['id_parent'] == taxid:
                # taxid = '1'
                break
            else:
                taxid = self.pnodes[taxid]['id_parent']
                if taxid != '1' and taxid in self.pnodes:
                    org_sp = self._extract_OS(taxid)
                    if self.pnodes[taxid]['rank'] != 'no rank':
                        oc = "%s (%s); %s" % (org_sp, self.pnodes[taxid]['rank'], oc)
                    else:
                        oc = "%s; %s" % (org_sp, oc)
        return li, oc

    def _extract_OS(self, taxid):
        """
        Extract Organism Species for a taxonomy ID

        :param taxid: Taxonomy ID
        :type taxid: str
        :return: Class name of organism
        :rtype: str
        """
        if taxid in self.pnodes:
            for name in NCBI.AUTH_OS_NAMES:
                if name in self.pnodes[taxid]['names']:
                    return self.pnodes[taxid]['names'][name][0]
            Utils.verbose("Not in AUTH_OS_NAMES for %s" % taxid)
            return self.pnodes[taxid]['names'].keys()[0][0]

    def _parse_nodes(self, taxofmt=None):
        """
        Parses nodes.dmp file

        :param taxofmt: Format for taxonomy information report
        :type taxofmt: str
        :return: True
        :rtype: bool
        :raise: SystemExit if error with opening file
        """
        if taxofmt:
            self.taxofmt = taxofmt
        Utils.verbose("Paring nodes.dmp ...")
        Utils.start_timer()
        try:
            with open(self.nodes, 'rb') as fh:
                for line in fh:
                    fld = line[:-1].split(self.hsep)
                    if fld[0] in self.pnodes:
                        Utils.warn("Duplicate tax_id: %s" % fld[0])
                    else:
                        # name == {'name class': 'OS'} ex: {'scientific name': 'Theileria parva.'}
                        self.pnodes[fld[0]] = {'id_parent': fld[1], 'rank': fld[2], 'names': {}}
                        if self.taxofmt == 'full':
                            if (fld[2] == 'species' or fld[2] == 'no rank' or fld[2] == 'subspecies') and fld[0] != '1':
                                self.taxids.append(fld[0])
                        else:
                            if fld[0] != '1':
                                self.taxids.append(fld[0])
        except IOError as err:
            Utils.error("Error while opening %s file: %s" % (str(err), self.nodes))
        Utils.verbose("Elapsed time %.3f sec" % Utils.elapsed_time())
        return True

    def _parse_names(self, nodes=None):
        """
        Parses names.dmp file

        :param nodes: Nodes dict from nodes.dmp file
        :type nodes: dict
        :return: True
        :raise: SystemExit if error with opening file
        """
        if nodes:
            self.pnodes = nodes
        Utils.verbose("Parsing %s ..." % self.names)
        Utils.start_timer()
        try:
            with open(self.names, 'rb') as fh:
                for line in fh:
                    fld = line[:-3].split(self.hsep)
                    if fld[0] in self.pnodes:
                        if fld[3] in self.pnodes[fld[0]]['names']:
                            self.pnodes[fld[0]]['names'][fld[3]].append(fld[1])  # use scientific name if exist
                        else:
                            self.pnodes[fld[0]]['names'][fld[3]] = [fld[1]]
                    else:
                        Utils.warn("No corresponding tax_id: %s" % fld[0])
        except IOError as err:
            Utils.error("Error while opening %s file: %s" % (str(err), self.names))
        Utils.verbose("Elapsed time %.3f sec" % Utils.elapsed_time())
        return True

    def _print_line(self, outfh, line, tag, car=80):
        i = 0
        while i < len(line):
            st = line[i:i+car-5]
            if st[-1] in (';', ' ', '\n'):
                print('%s   %s' % (tag, st.strip()), file=outfh)
            else:
                while st[-1] not in (';', ' '):
                    st = st[:-1]
                    i -= 1
                print('%s   %s' % (tag, st.strip()), file=outfh)
            i += car - 5
