#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Corinne Maufrais
# Institut Pasteur, DSI/CIB
# maufrais@pasteur.fr
# Updated by Emmanuel Quevillon <tuco@pasteur.fr>

import argparse
import sys
from bsddb3 import db                   # the Berkeley db data base
from pympler import asizeof
import humanfriendly


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
        print >> sys.stdout, "Size of returned list %s" % str(humanfriendly.format_size(asizeof.asizeof(info), binary=True))
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
            bdb.put(entry['acc'], '%s_@#$_%s' % (entry['os'], entry['taxo']))
    except db.DBAccessError as err:
        print >> sys.stderr, "Error while opening Berkeley database: %s" % str(err)
        sys.exit(1)
    except db.DBError as err:
        print >> sys.stderr, "Error while inserting value: %s" % str(err)
        sys.exit(1)
    finally:
        print >> sys.stdout, "Size of final BDB %s" % str(humanfriendly.format_size(asizeof.asizeof(bdb), binary=True))
        bdb.close()
    return True


def extract_silva(fh=None, sep='||'):
    """
    Parse FASTA header for Silva 16S database
    :param fh: File handle
    :type fh: file
    :param sep: Fasta header separator, default '||'
    :type sep: str
    :return: List of ids parsed
    :rtype: list
    """
    if not fh or not isinstance(fh, file):
        print >> sys.stderr, "File handle expected"

    info = []
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
            info.append({'acc': acc, 'taxo': taxo, 'os': os})
    return info


def extract_gg(fh=None, sep=''):
    """
    Parse FASTA header for Greengenes 16S database
    :param fh: File handle
    :type fh: file
    :param sep: Fasta header separator, default ''
    :type sep: str
    :return: List of ids parsed
    :rtype: list
    """
    if not fh or not isinstance(fh, file):
        print >> sys.stderr, "File handle expected"

    info = []
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
            info.append({'acc': acc, 'taxo': taxo, 'os': os})
    return info


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
                                 dest="accVos_oc",
                                 help="Output file: Berleley db format",
                                 metavar="<file>",
                                 required=True)
    general_options.add_argument("-n", "--db_name", dest="db_name",
                                 help="16S database name. Supported [silva, silva_lsu, silva_ssu, greengenes]",
                                 metavar="<db name>",
                                 type=str,
                                 required=True,
                                 choices=['silva', 'silva_lsu', 'silva_ssu', 'greengenes'])

    args = parser.parse_args()

    ids = parse_file(input=args.fasta, dbname=args.db_name)
    create_bdb(ids=ids, name=args.accVos_oc, mode=0666)
    sys.exit(0)

