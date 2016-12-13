#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Corinne Maufrais
# Institut Pasteur, DSI/CIB
# maufrais@pasteur.fr
# Updated by Emmanuel Quevillon <tuco@pasteur.fr>

import argparse
import sys
from bsddb3 import db                   # the Berkeley db data base

DB_VAL_SEP = '%s_@#$_%s'

def parse_file(input=None, dbname=None):
    """
    Parse an input file (default FASTA) and creates it Berkeley database

    :param input: Input file to parser (expected FASTA format)
    :type input: str
    :param dbname: 16S database name ('silva', 'silva_ssu', 'silva_lsu', 'greengenes')
    :type dbname: str
    :return: List of parsed elements from FASTA header
    :rtype: list
    :raise IOError: if `file` does not exists or can not be opened
    """
    supported_dbs = ['silva', 'silva_ssu', 'silva_lsu', 'greengenes']
    if not input:
        print >> sys.stderr, "Input file missing"
        sys.exit(1)
    if not dbname:
        print >> sys.stderr, "16S dbname missing"
    if dbname not in supported_dbs:
        print >> sys.stderr, "16S dbname %s not supported (%s)" % (dbname, supported_dbs)
        sys.exit(1)

    with open(input, 'rb') as fh:
        if 'silva' in dbname:
            info = extract_silva(fh=fh, sep='||')
        elif 'greengenes' in dbname:
            info = extract_gg(fh=fh, sep='||')
        else:
            print >> sys.stderr, "16S dbname %s not supported (%s)" % (dbname, supported_dbs)
        return info


def create_bdb(ids=None, name=None, mode=0666):
    """
    Creates the Berkeley database on disk

    :param ids: List of ids to insert in the database
    :type ids: list of set
    :param name: Name of the database to create
    :type name: str
    :param mode: Permissions on Berkeley database, default 0666
    :type mode: int
    :return: True
    :rtype: bool
    :raise DBAccessError: If can't open Berkeley database
    :raise SystemExit: If ids not given or empty
    """
    if not ids:
        print >> sys.stderr, "IDs list empty or not given"
        sys.exit(1)
    if not name:
        print >> sys.stderr, "A Berkeley database name is required"
        sys.exit(1)
    bdb = db.DB()
    try:
        bdb.open(name, None, db.DB_HASH, db.DB_CREATE, mode=mode)
        for entry in ids:
            bdb.put(entry['acc'], DB_VAL_SEP % (entry['os'], entry['taxo']))
    except db.DBAccessError as err:
        print >> sys.stderr, "Error while opening Berkeley database: %s" % str(err)
        sys.exit(1)
    except db.DBError as err:
        print >> sys.stderr, "Error while inserting value: %s" % str(err)
        sys.exit(1)
    finally:
        bdb.close()
    return True

def extract_silva(input=None, bdb=None, sep='||'):
    """
    Parse FASTA header for Silva 16S database

    :param input: Fasta file
    :type input: str
    :param bdb: Berkeley database file handle
    :type bdb: bdb
    :param sep: Fasta header separator, default '||'
    :type sep: str
    :return: Boolean
    :rtype: bool
    """
    if not input:
        print >> sys.stderr, "Input FASTA file required"
        sys.exit(1)
    with open(input, 'rb') as fh:
        for line in fh:
            if line[0] != '>':
                continue
            # Fasta header: >accession_number.start_position.stop_position taxonomic; organism name
            fld = line[1:].split()

            # !! Format updated for biomaj : >silva||FJ805841.1.4128 instead of >FJ805841.1.4128
            fld_acc = fld[0].split(sep)
            if len(fld_acc) == 2:
                acc = fld_acc[1].split('.')[0]
            else:
                acc = fld[0].split('.')[0]

            end_line = ' '.join(fld[1:])
            new_fld = end_line.split(';')
            taxo = ';'.join(new_fld[:-1])
            os = new_fld[-1]
            if acc and taxo and os:
                bdb.put(acc, DB_VAL_SEP % (os, taxo))
    return True


def extract_gg(input=None, bdb=None, sep='||'):
    """
    Parse FASTA header for Greengenes 16S database

    :param input: Fasta file
    :type input: str
    :param bdb: Berkeley database file handle
    :type bdb: bdb
    :param sep: Fasta header separator, default ''
    :type sep: str
    :return: Boolean
    :rtype: bool
    """
    if not input:
        print >> sys.stderr, "Fasta file expected"
        sys.exit(1)

    with open(input, 'rb') as fh:
        for line in fh:
            if line[0] != '>':
                continue
            definition = {'k__': 'Kingdom', 'p__': 'Phylum', 'c__': 'Class', 'o__': 'Order', 'f__': 'Family',
            'g__': 'Genus', 's__': 'species classification system', 'otu_': 'Operational Taxonomic Units'}
            # >4038 X89044.1 termite hindgut clone sp5_18 k__Bacteria; p__Spirochaetes; c__Spirochaetes (class); o__Spirochaetales; f__Spirochaetaceae; g__Treponema; s__sp5; otu_4136
            # >prokMSA_id gb_acc taxo otu
            fld = line[1:].split()

            # !! Format updated for biomaj : >gg||123 instead of >123
            fld_acc = fld[0].split(sep)
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
            except:
                # new format: 02/07/14: no 'otu_' field
                # >4038 X89044.1 termite hindgut clone sp5_18 k__Bacteria; p__Spirochaetes; c__Spirochaetes (class); o__Spirochaetales; f__Spirochaetaceae; g__Treponema; s__sp5
                taxo = end_line[k_index:]
            taxo = taxo.replace('k__', '').replace('p__', '').replace('c__', '').replace('o__', '').replace('f__', '')\
                       .replace('g__', '').replace('s__', '')
            if acc and taxo and os:
                bdb.put(acc, '%s_@#$_%s' % (os, taxo))
    return True


if __name__ == '__main__':
    epilog = """
    Creates Berkeley DB taxonomy database for Silva and Greengenes 16S databases.

    Silva is composed of LSURef and SSURef:
    http://www.arb-silva.de/fileadmin/silva_databases/current/Exports/LSURef_111_tax_silva.fasta.tgz
    http://www.arb-silva.de/fileadmin/silva_databases/current/Exports/SSURef_111_NR_tax_silva.fasta.tgz

    Greengenes:
    ftp://greengenes.microbio.me/greengenes_release/current/gg_13_5_with_header.fasta.gz"""

    parser = argparse.ArgumentParser(prog='taxodb_rrna.py',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                     description="Creates Berkeley DB taxonomy database for Silva and Greengenes 16S databases.",
                                     epilog=epilog)

    general_options = parser.add_argument_group(title="Options", description=None)

    general_options.add_argument("-i", "--fasta_db_file",
                                 dest="fasta",
                                 help="Fasta file with 16S sequences",
                                 metavar="<file>",
                                 type=str,
                                 required=True)
    general_options.add_argument("-b", "--bdb",
                                 dest="bdb_name",
                                 help="Output file: Berleley db format",
                                 metavar="<file>",
                                 required=True)
    general_options.add_argument("-t", "--db_type", dest="db_type",
                                 help="16S database name. Supported [silva, greengenes]",
                                 metavar="<db type>",
                                 type=str,
                                 required=True,
                                 choices=['silva' 'greengenes'])

    args = parser.parse_args()

    bdb = db.DB()
    try:
        bdb.open(args.bdb_name, None, db.DB_HASH, db.DB_CREATE, mode=0666)
        if 'silva' == args.db_type:
            extract_silva(input=args.fasta, bdb=bdb)
        if 'greengenes' == args.db_type:
            extract_gg(input=args.fasta, bdb=bdb)
    except IOError as err:
        print >> sys.stderr, "Can't open input file %s: %s" % (args.fasta, str(err))
    except db.DBAccessError as err:
        print >> sys.stderr, "Error while opening Berkeley database %s: %s" % (args.accVos_oc, str(err))
        sys.exit(1)
    except db.DBError as err:
        print >> sys.stderr, "Error while inserting value in Berkeley database: %s" % str(err)
        sys.exit(1)
    finally:
        bdb.close()

    sys.exit(0)

