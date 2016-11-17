from __future__ import print_function
import os
from bsddb3 import db
from taxodb.utils import Utils

__author__ = "Emmanuel Quevillon"
__email__ = "tuco@pasteur.fr"


class Silva(object):
    """
    Silva class used to work with silva 16S databases file.

    This class is able to parse FASTA file header and create Berkeley DB file in order
    to be used with taxo_pack utils.

    Fasta files available at:
    http://www.arb-silva.de/fileadmin/silva_databases/current/Exports/LSURef_111_tax_silva.fasta.tgz
    http://www.arb-silva.de/fileadmin/silva_databases/current/Exports/SSURef_111_NR_tax_silva.fasta.tgz

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
                    # Fasta header: >accession_number.start_position.stop_position taxonomic; organism name
                    fld = line[1:].split()

                    # !! Format updated for biomaj : >silva||FJ805841.1.4128 instead of >FJ805841.1.4128
                    fld_acc = fld[0].split(self.hsep)
                    if len(fld_acc) == 2:
                        acc = fld_acc[1].split('.')[0]
                    else:
                        acc = fld[0].split('.')[0]

                    end_line = ' '.join(fld[1:])
                    new_fld = end_line.split(';')
                    taxo = ';'.join(new_fld[:-1])
                    os = new_fld[-1]
                    if acc and taxo and os:
                        self.db.put(acc, '%s%s%s' % (os, self.dsep, taxo))
        except IOError as err:
            Utils.error("Error while opening FASTA file %s: %s" % (self.fasta, str(err)))
        Utils.verbose("BDB created!")
        return True
