`taxodb_rrna.py` is a simple python script used to format *[Silva](http://www.arb-silva.de)* and *[Greengenes](http://greengenes.secondgenome.com/)* 16S databases.
It requires the *[bsddb3](https://pypi.python.org/pypi/bsddb3/)* python library and *[Berkeley DB library](http://www.oracle.com)* to work.

## INSTALL
1. **Install Berkeley DB**
* *Mac OSX*
```
brew install berkeley-db4
```
* *Ubuntu/Debian*
```
sudo apt-get install libdb-dev
```
* *CentOS*
```
sudo yum install libdb-devel
```
2. Install `bsddb3`
```
pip install bsddb3
```
3. **Install `taxodb_rrna.py`**
```
python setup.py install
```

## GETTING DATA

`taxodb_rrna.py` is able to index files for *Silva*:
1. *[LSURef](http://www.arb-silva.de/fileadmin/silva_databases/current/Exports/LSURef_111_tax_silva.fasta.tgz)*
2. *[SSURef](http://www.arb-silva.de/fileadmin/silva_databases/current/Exports/SSURef_111_NR_tax_silva.fasta.tgz)*

and *Greengenes*:
1. *[GREENGENES_gg16S](ftp://greengenes.microbio.me/greengenes_release/current/gg_13_5_with_header.fasta.gz)*

Download database you want to index:
```
$ wget http://www.arb-silva.de/fileadmin/silva_databases/current/Exports/LSURef_111_tax_silva.fasta.tgz
and/or
$ wget http://www.arb-silva.de/fileadmin/silva_databases/current/Exports/SSURef_111_NR_tax_silva.fasta.tgz
and/or
$ wget ftp://greengenes.microbio.me/greengenes_release/current/gg_13_5_with_header.fasta.gz
```

## USAGE
```
$ python ./taxodb_rrna.py -h
usage: taxodb_rrna.py [-h] -i file [-b File] [-n string]

Creation of taxonomy Berleley DB for Silva and Greengenes 16S databases

optional arguments:
  -h, --help            show this help message and exit

Options:
  -i file, --fasta_db_file file
                        Fasta file with 16S sequences (default: None)
  -b File, --bdb File   Output file: Berleley db format (default:
                        accVosoc.bdb)
  -n string, --db_name string
                        16S database type (default: None)

Creation of taxonomy Berleley DB for Silva and Greengenes 16S databases. Silva
is composed of LSURef and SSURef: http://www.arb-silva.de/fileadmin/silva_data
bases/current/Exports/LSURef_111_tax_silva.fasta.tgz http://www.arb-silva.de/f
ileadmin/silva_databases/current/Exports/SSURef_111_NR_tax_silva.fasta.tgz
Greengenes: ftp://greengenes.microbio.me/greengenes_release/current/gg_13_5_wi
th_header.fasta.gz
```

## RUNNING

Create Berkeley DB database(s):

```
$ python taxodb_rrna.py -i current_GREENGENES_gg16S_unaligned.fasta -n greengenes -b <dbname>.bdb
$ python taxodb_rrna.py -i LSURef_111_tax_silva.fasta -n silva_lsu -b <dbname>.bdb
$ python taxodb_rrna.py -i SSURef_111_NR_tax_silva.fasta -n silva_ssu  -b <dbname>.bdb
```
