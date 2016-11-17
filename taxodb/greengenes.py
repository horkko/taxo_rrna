from __future__ import print_function
import os
from bsddb3 import db
from taxodb.utils import Utils

__author__ = "Emmanuel Quevillon"
__email__ = "tuco@pasteur.fr"


class GreenGenes(object):
    """
    GreenGenes class used to work with greengenes 16S database file.

    This class is able to parse FASTA file header and create Berkeley DB file in order
    to be used with taxo_pack utils.

    Fasta file available at ftp://greengenes.microbio.me/greengenes_release/current/gg_13_5_with_header.fasta.gz

    @author: Corinne Maufrais, Original author (maufrais@pasteur.fr)
    @author: Emmanuel Quevillon, rewrite and packing (tuco@pasteur.fr)
    @copyright: Institut Pasteur, DSI/CIB
    """

    DEFAULT_SEPARATOR = '||'
    DB_VALUE_SEPARATOR = '_@#$_'

    def __init__(self, fasta=None, bdb=None, header_sep=DEFAULT_SEPARATOR, db_sep=DB_VALUE_SEPARATOR, mode=0666):
        """
        Create a new SILVA object to parse FASTA file headers and create Berkeley DB file

        :param fasta: FASTA file to parse
        :type fasta: str
        :param bdb: Berkeley DB file name
        :type bdb: str
        :param header_sep: Separator used to parse ID from FASTA header, default '||'
        :type header_sep: str
        :param db_sep: String used to split organism (os) and taxonomy (taxo) values in Berkeley database,
                       default '_@#$_'
        :type db_sep: str
        :param mode: Unix mode to create Berkeley database file, default 0666
        :type mode: int
        :raise: SystemExit if `fasta` file is not found
                SystemExit if `bdb` file can not be created or opened
        """
        self.fasta = fasta
        self.bdb = bdb
        self.hsep = header_sep
        self.dsep = db_sep
        self.mode = mode
        self.db_size = 0

        if not self.fasta:
            Utils.error("An FASTA input file is required")
        if not os.path.isfile(self.fasta):
            Utils.error("Can't find %s" % self.fasta)
        if not self.bdb:
            Utils.error("A Berkeley database file name is required")
        self.db = db.DB()

    def create_bdb(self, bdb=None, mode=None):
        """
        This method creates SILVA Berkeley database file

        :param bdb: A Berkeley database file name
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
            self.db.open(self.bdb, None, db.DB_HASH, db.DB_CREATE, mode=self.mode)
            Utils.verbose("Creating Berkeley database ... ")
            Utils.start_timer()
            self._parse_and_create_bdb()
            Utils.verbose("Elapsed time %.3f sec" % Utils.elapsed_time())
        except db.DBAccessError as err:
            Utils.error("Can't open Berkeley db %s: %s" % (self.bdb, str(err)))
        except db.DBError as err:
            Utils.error("Error while inserting value in Berkeley db: %s" % str(err))
        finally:
            self.db.close()

    def get_name(self):
        """
        Returns the inheriting class name

        :return: Class name from inherited object
        :rtype: str
        """
        return str(self.__class__.__name__)

    def _parse_and_create_bdb(self):
        """
        This method parses FASTA headers file and create the Berkeley database on the fly

        :return:
        """
        try:
            Utils.verbose("Opening %s" % self.fasta)
            with open(self.fasta, 'rb') as fh:
                for line in fh:
                    if line[0] != '>':
                        continue
                    # >4038 X89044.1 termite hindgut clone sp5_18 k__Bacteria; p__Spirochaetes; c__Spirochaetes (class); o__Spirochaetales; f__Spirochaetaceae; g__Treponema; s__sp5; otu_4136
                    # >prokMSA_id gb_acc taxo otu
                    fld = line[1:].split()

                    # !! Format updated for biomaj : >gg||123 instead of >123
                    fld_acc = fld[0].split(self.hsep)
                    if len(fld_acc) == 2 and fld_acc[1].isdigit():
                        acc = fld_acc[1]
                    else:
                        acc = fld[0]
                    end_line = ' '.join(fld[2:])
                    k_index = end_line.index('k__')
                    os = end_line[:k_index].strip()
                    try:
                        otu_index = end_line.index('otu_')
                        taxo = end_line[k_index:otu_index]
                    except IndexError as err:
                        # new format: 02/07/14: no 'otu_' field
                        # >4038 X89044.1 termite hindgut clone sp5_18 k__Bacteria; p__Spirochaetes; c__Spirochaetes (class); o__Spirochaetales; f__Spirochaetaceae; g__Treponema; s__sp5
                        taxo = end_line[k_index:]
                    taxo = taxo.replace('k__', '').replace('p__', '').replace('c__', '').replace('o__', '').replace('f__', '') \
                        .replace('g__', '').replace('s__', '')
                    if acc and taxo and os:
                        self.db.put(acc, '%s%s%s' % (os, self.dsep, taxo))
        except IOError as err:
            Utils.error("Error while opening FASTA file %s: %s" % (self.fasta, str(err)))
        return True