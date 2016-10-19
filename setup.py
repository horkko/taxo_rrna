#!/usr/bin/env python
# -*- coding: utf-8 -*-
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

import sys
if (sys.version_info[0] == 2 and sys.version_info[1] < 7) or (sys.version_info[0] >= 3):
    sys.exit('Python version >= 2.7 and < 3.0')

config = {
    'name': 'taxo_rrna',
    'author': 'Corinne Maufrais',
    'version': '1.2.0',
    'author_email': 'corinne.maufrais@pasteur.fr',
    'url': 'https://github.com/C3BI-pasteur-fr/taxodb_ncbi',
    'download_url': 'https://github.com/C3BI-pasteur-fr/taxodb_ncbi',
    'license': 'GPLv3',
    'description': """
                   taxodb_rrna.py is a simple python script uses to format Silva and Greengenes 16S databases
                   (http://www.arb-silva.de/fileadmin/silva_databases/current/Exports/) and
                   (http://greengenes.lbl.gov/Download/Sequence_Data/Fasta_data_files/)
                   It requires the bsddb3 python library (https://pypi.python.org/pypi/bsddb3/)
                   and Berkeley DB library (http://www.oracle.com) to work.
                   """,
    'package_dir': {'': 'src'},
    'scripts': ['src/taxodb_rrna.py'],
    'install_requires': ['bsddb3']
}

setup(**config)
