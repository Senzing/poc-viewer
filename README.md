# poc-viewer

## Overview

The [poc_viewer.py](poc_viewer.py) utility is an interactive command line utility that works along with the poc-snapshot utility to display interesting statistics and examples of the entities in a Senzing repository at strategic times, such as after an initial load, a configuration change, a system upgrade, etc.

The poc-snapshot utility https://github.com/Senzing/poc-snapshot computes the following reports ...
- **dataSourceSummary** This report shows the matches, possible matches and relationships within each data source.
- **crossSourceSummary** This report shows the matches, possible matches and relationships across data sources.
- **entitySizeBreakdown** This report categorizes entities by their size (how many records they contain) and selects a list of entities to review that may be over-matched due to multiple names, addresses, DOBs, etc. 

The poc-viewer can also be used by support personnel at any time to perform the following tasks ...
- **search** Find an entity by name, DOB, address, etc.
- **get** Display an entity's records in either summary or detail format.
- **compare** – Compare two or more entities side by side.
- **why** – Display the internal engine keys and stats about an entity to help determine why it did or did not match another. 
- **export** – Export the json records that make up an entity for debugging or reingesting after configuration tweaks are made.

Usage:

```console
python poc_viewer.py --help
usage: poc_viewer.py [-h] [-c INI_FILE_NAME] [-s SNAPSHOT_FILE_NAME]

optional arguments:
  -h, --help            show this help message and exit
  -c INI_FILE_NAME, --ini_file_name INI_FILE_NAME
                        name of the g2.ini file, defaults to
                        /opt/senzing/g2/python/G2Module.ini
  -s SNAPSHOT_FILE_NAME, --snapshot_file_name SNAPSHOT_FILE_NAME
                        the name of a json statistics file computed by
                        poc_snapshot.py
```

## Contents

1. [Prerequisites](#Prerequisites)
2. [Installation](#Installation)
3. [Typical use](#Typical-use)

### Prerequisites
- python 3.6 or higher
- Senzing API version 1.7 or higher
- python pretty table module (pip3 install ptable)
- python fuzzywuzzy module (pip3 install fuzzywuzzy)
- python levenshtein module (pip3 install python-levenshtein)

### Installation

1. Simply place the the following files in a directory of your choice ...  (Ideally along with poc-snapshot.py)
    - [poc_viewer.py](poc_viewer.py) 

2. Set PYTHONPATH environment variable to python directory where you installed Senzing.
    - Example: export PYTHONPATH=/opt/senzing/g2/python

3. Set the SZ_INI_FILE_NAME environment variable for the senzing instance you want to explore.
    - Example: export SZ_INI_FILE_NAME=/opt/senzing/g2/python/G2Module.ini

4. Source the appropriate Senzing environment file. 
    - Example: source /opt/senzing/g2/setupEnv

Its a good idea to place these settings in your .bashrc file to make sure the enviroment is always setup and ready to go.


### Typical use
```console
python3 poc_viewer.py 

Welcome to the Senzing Proof of Concept (POC) viewer. Type help or ? to list commands.

(poc)
```
Optional parameters ...
- The -c configuration parameter is only required if the SZ_INI_FILE_NAME environment variable is not set.
- The -s snapshot file parameter is for convenience if you just took a snapshot and want to load it. If you forget this, you can use the load command while in the viewer itself.  The viewer also remembers the last file loaded, so its not required every time.

Next type "help" to see the available commands ...
```console
(poc) help

Documented commands (type help <topic>):
========================================
auditSummary  crossSourceSummary   export  load    search
colorScheme   dataSourceSummary    get     score   why   
compare       entitySizeBreakdown  help    scroll
```
Type "help" on a specific command to find out how to use it ...
```console
(poc) help search

Searches for entities by their attributes.

Syntax:
    search Joe Smith (without a json structure performs a search on name alone)
    search {"name_full": "Joe Smith"}
    search {"name_org": "ABC Company"}
    search {"name_last": "Smith", "name_first": "Joe", "date_of_birth": "1992-12-10"}
    search {"name_org": "ABC Company", "addr_full": "111 First St, Anytown, USA 11111"}

Notes: 
    Searching by name alone may not locate a specific entity.
    Try adding a date of birth, address, or phone number if not found by name alone.
```

Next thing to do is to just start exploring your database!  Here are a few tips ...

**adhoc flow ...**
1. search joe smith *(where "joe smith" is the name of an entity you want to lookup)*
2. get 123 *(where 123 is one of the entity_ids returned by the search)*
3. why 123 *(if entity 123 consists of multiple records and you want to know why they resolved)*
4. compare 123,145 *(where 123 and 145 are two entity_ids you want to compare)*
5. why 123,145 *(where 123 and 145 are two entity_ids you want to see why they did not resolve)*

*Notes:* 
- Be sure to type "help why" to understand what the colors and symbols mean.
- Use "scroll" immediately after any table that is cut off as screen wrapping has been turned off. This will allow you to see the entire table and pan left and right, up and down.

**browsing statistics and examples ...**
1. load /project/snapshots/snapshot1.json *(where snapshot1.json is a file created by poc_snapshot.py)*
2. dataSourceSummary *(when a list of the data sources and their statistics are desired)* 
3. dataSourceSummary customer duplicates *(to view a list of duplicate records in the customer data source)*
4. Select (N)ext or (P)revious to move through the examples.
5. Select (W)hy on any example you want more explanation for.
6. Select (S)croll on any table that is cut off as screen wrapping has been turned off.
7. Select (Q)uit to get out of the report.

Final note: the auditSummary report is not publicly available. It provides a way to compare snapshots between runs. Please contact support if you desire this functionality. 
