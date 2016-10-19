#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Corinne Maufrais
# Institut Pasteur, DSI/CIB
# maufrais@pasteur.fr
# Updated by Emmanuel Quevillon <tuco@pasteur.fr>

import argparse
from bsddb3 import db                   # the Berkeley db data base


def extract_silva(line):
    # Fasta header: >accession_number.start_position.stop_position taxonomic; organism name
    fld = line[1:].split()

    # !! Format updated for biomaj : >silva||FJ805841.1.4128 instead of >FJ805841.1.4128
    fld_acc = fld[0].split('||')
    if len(fld_acc) == 2:
        acc = fld_acc[1].split('.')[0]
    else:
        acc = fld[0].split('.')[0]

    end_line = ' '.join(fld[1:])
    new_fld = end_line.split(';')
    taxo = ';'.join(new_fld[:-1])
    os = new_fld[-1]
    return acc, taxo, os

def extract_gg(line):
    definition = {'k__': 'Kingdom', 'p__': 'Phylum', 'c__': 'Class', 'o__': 'Order', 'f__': 'Family',
                  'g__': 'Genus', 's__': 'species classification system', 'otu_': 'Operational Taxonomic Units'}
    # >4038 X89044.1 termite hindgut clone sp5_18 k__Bacteria; p__Spirochaetes; c__Spirochaetes (class); o__Spirochaetales; f__Spirochaetaceae; g__Treponema; s__sp5; otu_4136
    # >prokMSA_id gb_acc taxo otu
    fld = line[1:].split()

    # !! Format updated for biomaj : >gg||123 instead of >123
    fld_acc = fld[0].split('||')
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
    taxo = taxo.replace('k__', '')
    taxo = taxo.replace('p__', '')
    taxo = taxo.replace('c__', '')
    taxo = taxo.replace('o__', '')
    taxo = taxo.replace('f__', '')
    taxo = taxo.replace('g__', '')
    taxo = taxo.replace('s__', '')
    return acc, taxo, os

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
                                 dest="fastafh",
                                 help="Fasta file with 16S sequences",
                                 metavar="file",
                                 type=file,
                                 required=True)
    general_options.add_argument("-b", "--bdb",
                                 dest="accVos_oc",
                                 help="Output file: Berleley db format",
                                 metavar="File",
                                 default='accVosoc.bdb')
    general_options.add_argument("-n", "--db_name", dest="db_name",
                                 help="16S database type",
                                 metavar="string",
                                 type=str,
                                 choices=['silva', 'silva_lsu', 'silva_ssu','greengenes'])

    args = parser.parse_args()

    # Get an instance of BerkeleyDB
    accVos_ocBDB = db.DB()
    # Create a database in file "osVSocDB" with a Hash access method
    #       There are also, B+tree and Recno access methods
    accVos_ocBDB.open(args.accVos_oc, None, db.DB_HASH, db.DB_CREATE, mode=0666)

    line = args.fastafh.readline()
    acc, oc, os = '', '', ''
    while line:
        if line[0] == '>':
            if 'silva' in args.db_name :
                acc, oc, os = extract_silva(line)
            if args.db_name == 'greengenes':
                acc, oc, os = extract_gg(line)

        if acc and oc and os:
            accVos_ocBDB.put(acc, '%s_@#$_%s' % (os, oc))
            acc, oc, os = '', '', ''
        line = args.fastafh.readline()

    accVos_ocBDB.close()
