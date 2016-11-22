#! /usr/bin/env python

import argparse
import sys
from taxodb.utils import Utils
from taxodb.taxo import Taxo


if __name__ == '__main__':
    epilog = """
    Creates Berkeley DB taxonomy database for 16S databases (Silva and GreenGenes)
    as well as NCBI taxonomy.

    Silva (http://www.arb-silva.de/fileadmin/silva_databases/current/Exports):
    - LSURef_111_tax_silva.fasta.tgz
    and/or
    -SSURef_111_NR_tax_silva.fasta.tgz

    Greengenes (ftp://greengenes.microbio.me/greengenes_release/current):
    - gg_13_5_with_header.fasta.gz

    NCBI taxonomy (ftp://ftp.ncbi.nlm.nih.gov/pub/taxonomy):
    - taxdump.tar.gz
    """

    parser = argparse.ArgumentParser(prog='taxodb_rrna.py',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                     description="Creates Berkeley DB taxonomy databases.",
                                     epilog=epilog)

    parser.add_argument_group(title="Options", description=None)

    parser.add_argument("-i", "--fasta_db_file",
                        dest="fasta",
                        help="Fasta file with 16S sequences. Unsupported with -t/--db_type ncbi.",
                        metavar="<file>",
                        type=str)
    parser.add_argument("-l", "--use_lineage",
                        dest="use_lineage",
                        action="store_true",
                        default=False,
                        help="Use lineage method")
    parser.add_argument("-n", "--names",
                        dest="names",
                        help="names.dmp file. Supported only with -t/--db_type ncbi.",
                        metavar="<file>",
                        type=str)
    parser.add_argument("-d", "--nodes",
                        dest="nodes",
                        help="nodes.dmp file. Supported only with -t/--db_type ncbi.",
                        metavar="<file>",
                        type=str)
    parser.add_argument("-k", "--flatdb",
                        dest="flatdb",
                        help="Output file: flat databank format. Supported only with -t/--db_type ncbi.",
                        metavar="<file>",
                        type=str)
    parser.add_argument("-b", "--bdb",
                        dest="bdb",
                        help="Output file: Berleley db format",
                        metavar="<file>",
                        required=False)
    parser.add_argument("-t", "--db_type",
                        dest="dbtype",
                        help="16S database name. Supported [greengenes, ncbi, silva]",
                        metavar="<db type>",
                        type=str,
                        required=True,
                        choices=['greengenes', 'ncbi', 'silva'])
    parser.add_argument("-f", "--format",
                        dest="taxofmt",
                        help="""
                        By default, reports only full taxonomy ie taxonomies that have 'species',
                        'subspecies' or 'no rank' at the final position.
                        Otherwise, reports all taxonomies even if they are partial.
                        Supported only with -t/--db_type ncbi.
                        """,
                        metavar="string",
                        type=str,
                        choices=['full', 'partial'],
                        default='full'
                        )
    parser.add_argument("-v", "--verbose",
                        dest="verbose",
                        action="store_true",
                        default=False,
                        help="Set verbose mode on")
    args = parser.parse_args()
    if args.fasta and (args.nodes or args.names or args.flatdb):
        Utils.error("Incompatible options -i and -n/-d/-k")
    Utils.VERBOSE = args.verbose
    taxodb = Taxo(args.__dict__).get_db()

    if args.bdb:
        taxodb.create_bdb()
    if taxodb.get_name() == 'ncbi' and args.flatdb:
        Utils.start_timer()
        taxodb.create_flat_file()
        print("[%s] Flat file %s created in %.3f sec" % (taxodb.get_name(), args.flatdb, Utils.elapsed_time()))

    sys.exit(0)

