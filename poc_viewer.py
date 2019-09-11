#! /usr/bin/env python3
pocUtilsVersion = 2.2
    
import argparse
try: import configparser
except: import ConfigParser as configparser
import sys
import json
import os
import platform
from collections import OrderedDict
import traceback
import glob
import subprocess

import cmd
try:
    import readline
    import atexit
except ImportError:
    readline = None

try: import prettytable
except: 
    print('')
    print('Please install python pretty table (pip3 install ptable)')
    print('')
    sys.exit(1)

try: from fuzzywuzzy import fuzz
except: hasFuzzy = False
else: hasFuzzy = True

#--senzing python classes
g2pythonPath = '/opt/senzing/g2/python'
if not os.getenv('PYTHONPATH') and os.path.exists(g2pythonPath):
    sys.path.insert(1, g2pythonPath)
try: 
    from G2Database import G2Database
    from G2Engine import G2Engine
    from G2Exception import G2Exception
except:
    print('')
    print('Please export PYTHONPATH=<path to senzing python directory>')
    print('')
    sys.exit(1)

# ==============================
class colors: 
    code = {}
    #--styles
    code['reset'] = '\033[0m'
    code['bold'] ='\033[01m'
    code['dim'] = '\033[02m'
    code['italics'] = '\033[03m'
    code['underline'] = '\033[04m'
    code['blink'] = '\033[05m'
    code['reverse'] = '\033[07m'
    code['strikethrough'] = '\033[09m'
    code['invisible'] = '\033[08m'
    #--foregrounds
    code['fg.black'] = '\033[30m'
    code['fg.red'] = '\033[31m'
    code['fg.green'] = '\033[32m'
    code['fg.yellow'] = '\033[33m'
    code['fg.blue'] = '\033[34m'
    code['fg.magenta'] = '\033[35m'
    code['fg.cyan'] = '\033[36m'
    code['fg.lightgrey'] = '\033[37m'
    code['fg.darkgrey'] = '\033[90m'
    code['fg.lightred'] = '\033[91m'
    code['fg.lightgreen'] = '\033[92m'
    code['fg.lightyellow'] = '\033[93m'
    code['fg.lightblue'] = '\033[94m'
    code['fg.lightmagenta'] = '\033[95m'
    code['fg.lightcyan'] = '\033[96m'
    code['fg.white'] = '\033[97m'
    #--backgrounds
    code['bg.black'] = '\033[40m'
    code['bg.red'] = '\033[41m'
    code['bg.green'] = '\033[42m'
    code['bg.orange'] = '\033[43m'
    code['bg.blue'] = '\033[44m'
    code['bg.magenta'] = '\033[45m'
    code['bg.cyan'] = '\033[46m'
    code['bg.lightgrey'] = '\033[47m'
    code['bg.darkgrey'] = '\033[100m'
    code['bg.lightred'] = '\033[101m'
    code['bg.lightgreen'] = '\033[102m'
    code['bg.yellow'] = '\033[103m'
    code['bg.lightblue'] = '\033[104m'
    code['bg.lightmagenta'] = '\033[105m'
    code['bg.lightcyan'] = '\033[106m'
    code['bg.white'] = '\033[107m'

def colorize(string, colorList = None):
    if colorList: 
        prefix = ''.join([colors.code[i.strip().lower()] for i in colorList.split(',')])
        suffix = colors.code['reset']
        return '{}{}{}'.format(prefix, string, suffix) 
    return string

# ==============================
class ColoredTable(prettytable.PrettyTable):

    def __init__(self, field_names=None, **kwargs):
        new_options = ['title_color', 'header_color']

        super(ColoredTable, self).__init__(field_names, **kwargs)

        self._title_color = kwargs['title_color'] or None
        self._header_color = kwargs['header_color'] or None

        self._options.extend(new_options)

        # hrule styles
        self.FRAME = 0
        self.ALL = 1

    def _stringify_title(self, title, options):

        lines = []
        lpad, rpad = self._get_padding_widths(options)
        if options["border"]:
            if options["vrules"] == self.ALL:
                options["vrules"] = self.FRAME
                lines.append(self._stringify_hrule(options))
                options["vrules"] = self.ALL
            elif options["vrules"] == self.FRAME:
                lines.append(self._stringify_hrule(options))
        bits = []
        endpoint = options["vertical_char"] if options["vrules"] in (self.ALL, self.FRAME) else " "
        bits.append(endpoint)
        title = " " * lpad + title + " " * rpad
        if options['title_color']:
            bits.append(colorize(self._justify(title, len(self._hrule) - 2, "c"), options['title_color']))
        else:
            bits.append(self._justify(title, len(self._hrule) - 2, "c"))

        bits.append(endpoint)
        lines.append("".join(bits))
        return "\n".join(lines)

    def _stringify_header(self, options):

        bits = []
        lpad, rpad = self._get_padding_widths(options)
        if options["border"]:
            if options["hrules"] in (self.ALL, self.FRAME):
                bits.append(self._hrule)
                bits.append("\n")
            if options["vrules"] in (self.ALL, self.FRAME):
                bits.append(options["vertical_char"])
            else:
                bits.append(" ")
        # For tables with no data or field names
        if not self._field_names:
            if options["vrules"] in (self.ALL, self.FRAME):
                bits.append(options["vertical_char"])
            else:
                bits.append(" ")
        for field, width, in zip(self._field_names, self._widths):
            if options["fields"] and field not in options["fields"]:
                continue
            if self._header_style == "cap":
                fieldname = field.capitalize()
            elif self._header_style == "title":
                fieldname = field.title()
            elif self._header_style == "upper":
                fieldname = field.upper()
            elif self._header_style == "lower":
                fieldname = field.lower()
            else:
                fieldname = field

            #if options['header_color']:
            #    fieldname = colorify(fieldname, options['header_color'])
            if options['header_color']:
                bits.append(colorize(" " * lpad
                            + self._justify(fieldname, width, self._align[field])
                            + " " * rpad, options['header_color']))
            else:
                bits.append(" " * lpad
                            + self._justify(fieldname, width, self._align[field])
                            + " " * rpad)
            if options["border"]:
                if options["vrules"] == self.ALL:
                    bits.append(options["vertical_char"])
                else:
                    bits.append(" ")
        # If vrules is FRAME, then we just appended a space at the end
        # of the last field, when we really want a vertical character
        if options["border"] and options["vrules"] == self.FRAME:
            bits.pop()
            bits.append(options["vertical_char"])
        if options["border"] and options["hrules"] is not None:
            bits.append("\n")
            bits.append(self._hrule)
        return "".join(bits)

# ==============================
class G2CmdShell(cmd.Cmd):

    def __init__(self):
        cmd.Cmd.__init__(self)

        # this is how you get command history on windows 
        if platform.system() == 'Windows':
            self.use_rawinput = False

        self.intro = '\nWelcome to the Senzing Proof of Concept (POC) viewer. Type help or ? to list commands.\n'
        self.prompt = '(poc) '

        #--store config dicts for fast lookup
        self.cfgData = cfgData
        self.dsrcLookup = {}
        for cfgRecord in self.cfgData['G2_CONFIG']['CFG_DSRC']:
            self.dsrcLookup[cfgRecord['DSRC_ID']] = cfgRecord 
        self.dsrcCodeLookup = {}
        for cfgRecord in self.cfgData['G2_CONFIG']['CFG_DSRC']:
            self.dsrcCodeLookup[cfgRecord['DSRC_CODE']] = cfgRecord 
        self.etypeLookup = {}
        for cfgRecord in self.cfgData['G2_CONFIG']['CFG_ETYPE']:
            self.etypeLookup[cfgRecord['ETYPE_ID']] = cfgRecord 
        self.erruleLookup = {}
        for cfgRecord in self.cfgData['G2_CONFIG']['CFG_ERRULE']:
            self.erruleLookup[cfgRecord['ERRULE_ID']] = cfgRecord 
        self.ftypeLookup = {}
        for cfgRecord in self.cfgData['G2_CONFIG']['CFG_FTYPE']:
            self.ftypeLookup[cfgRecord['FTYPE_ID']] = cfgRecord 
        self.ftypeCodeLookup = {}
        for cfgRecord in self.cfgData['G2_CONFIG']['CFG_FTYPE']:
            self.ftypeCodeLookup[cfgRecord['FTYPE_CODE']] = cfgRecord 

        self.cfuncLookup = {}
        for cfgRecord in self.cfgData['G2_CONFIG']['CFG_CFUNC']:
            self.cfuncLookup[cfgRecord['CFUNC_ID']] = cfgRecord 

        self.scoredFtypeCodes = {}
        for cfgRecord in self.cfgData['G2_CONFIG']['CFG_CFCALL']:
            cfgRecord['FTYPE_CODE'] = self.ftypeLookup[cfgRecord['FTYPE_ID']]['FTYPE_CODE']
            cfgRecord['CFUNC_CODE'] = self.cfuncLookup[cfgRecord['CFUNC_ID']]['CFUNC_CODE']
            self.scoredFtypeCodes[cfgRecord['FTYPE_CODE']] = cfgRecord 

        self.ambiguousFtypeID = self.ftypeCodeLookup['AMBIGUOUS_ENTITY']['FTYPE_ID']

        #--misc
        self.sqlCommitSize = 1000
        self.__hidden_methods = ('do_shell')
        self.doDebug = False
        self.searchMatchLevels = {1: 'Match', 2: 'Possible Match', 3: 'Possibly Related', 4: 'Name Only'}
        self.relatedMatchLevels = {1: 'Ambiguous Match', 2: 'Possible Match', 3: 'Possibly Related', 4: 'Name Only', 11: 'Disclosed Relation'}
        self.validMatchLevelParameters = {}
        self.validMatchLevelParameters['0'] = 'SINGLE_SAMPLE'
        self.validMatchLevelParameters['1'] = 'DUPLICATE_SAMPLE'
        self.validMatchLevelParameters['2'] = 'AMBIGUOUS_MATCH_SAMPLE'
        self.validMatchLevelParameters['3'] = 'POSSIBLE_MATCH_SAMPLE'
        self.validMatchLevelParameters['4'] = 'POSSIBLY_RELATED_SAMPLE'
        self.validMatchLevelParameters['SINGLE'] = 'SINGLE_SAMPLE'
        self.validMatchLevelParameters['DUPLICATE'] = 'DUPLICATE_SAMPLE'
        self.validMatchLevelParameters['AMBIGUOUS'] = 'AMBIGUOUS_MATCH_SAMPLE'
        self.validMatchLevelParameters['POSSIBLE'] = 'POSSIBLE_MATCH_SAMPLE'
        self.validMatchLevelParameters['POSSIBLY'] = 'POSSIBLY_RELATED_SAMPLE'
        self.validMatchLevelParameters['RELATED'] = 'POSSIBLY_RELATED_SAMPLE'
        self.validMatchLevelParameters['S'] = 'SINGLE_SAMPLE'
        self.validMatchLevelParameters['D'] = 'DUPLICATE_SAMPLE'
        self.validMatchLevelParameters['A'] = 'AMBIGUOUS_MATCH_SAMPLE'
        self.validMatchLevelParameters['P'] = 'POSSIBLE_MATCH_SAMPLE'
        self.validMatchLevelParameters['R'] = 'POSSIBLY_RELATED_SAMPLE'
        self.lastSearchResult = []
        self.usePrettyTable = True
        self.currentReviewList = None

        #--get settings
        settingsFileName = '.' + sys.argv[0].lower().replace('.py','') + '_settings'
        self.settingsFileName = os.path.join(os.path.expanduser("~"), settingsFileName)
        try: self.settingsFileData = json.load(open(self.settingsFileName))
        except: self.settingsFileData = {}

        #--set the color scheme
        self.colors = {}
        if not ('colorScheme' in self.settingsFileData and self.settingsFileData['colorScheme'].upper() in ('DARK', 'LIGHT')):
            self.settingsFileData['colorScheme'] = 'dark'
        self.do_colorScheme(self.settingsFileData['colorScheme'])

        #--get last pocSnapshot data unless specified on command line
        if args.snapshot_file_name:
            self.settingsFileData['pocSnapshotFile'] = args.snapshot_file_name
        if 'pocSnapshotFile' in self.settingsFileData and os.path.exists(self.settingsFileData['pocSnapshotFile']):
            self.do_load(self.settingsFileData['pocSnapshotFile'])
        else:
            self.pocSnapshotFile = None
            self.pocSnapshotData = {}

        #--get last pocSnapshot data
        if 'pocAuditFile' in self.settingsFileData and os.path.exists(self.settingsFileData['pocAuditFile']):
            self.do_load(self.settingsFileData['pocAuditFile'])
        else:
            self.pocAuditFile = None
            self.pocAuditData = {}

        #--set the last table name
        self.lastTableName = os.path.join(os.path.expanduser("~"), 'pocTable.txt')

    # -----------------------------
    def do_quit(self, arg):
        return True

    # -----------------------------
    def emptyline(self):
        return

    # -----------------------------
    def cmdloop(self):

        while True:
            try: 
                cmd.Cmd.cmdloop(self)
                break
            except KeyboardInterrupt:
                ans = userInput('\n\nAre you sure you want to exit?  ')
                if ans in ['y','Y', 'yes', 'YES']:
                    break
            except TypeError as ex:
                printWithNewLines("ERROR: " + str(ex))
                type_, value_, traceback_ = sys.exc_info()
                for item in traceback.format_tb(traceback_):
                    printWithNewLines(item)

    def preloop(self):

        if readline:
            global histfile
            histFileName = '.' + sys.argv[0].lower().replace('.py','') + '_history'
            histfile = os.path.join(os.path.expanduser("~"), histFileName)
            if not os.path.isfile(histfile):
                open(histfile, 'a').close()
            hist_size = 2000
            readline.read_history_file(histfile)
            readline.set_history_length(hist_size)

            atexit.register(readline.set_history_length, hist_size)
            atexit.register(readline.write_history_file, histfile)
        else:
            printWithNewLines('INFO: Command history isn\'t available. Try installing python readline module.', 'B')

    def postloop(self):
        with open(self.settingsFileName, 'w') as f:
            json.dump(self.settingsFileData, f)

    #Hide do_shell from list of APIs. Seperate help section for it
    def get_names(self):
        return [n for n in dir(self.__class__) if n not in self.__hidden_methods]

    def help_KnowledgeCenter(self):
        printWithNewLines('Senzing Knowledge Center: https://senzing.zendesk.com/hc/en-us', 'B')

    def help_Support(self):
        printWithNewLines('Senzing Support Request: https://senzing.zendesk.com/hc/en-us/requests/new', 'B')


    def help_Arguments(self):
        print(
              '\nWhere you see <value> in the help output replace <value> with your value.\n' \
              '\nFor example the help for addAttribute is: \n' \
              '\taddAttribute {"attribute": "<attribute_name>"}\n' \
              '\nReplace <attribute_name> to be the name of your new attribute\n' \
              '\taddAttribute {"attribute": "myNewAttribute"}\n' \
              )

    def help_Shell(self):
        printWithNewLines('Run OS shell commands: ! <command>', 'B')

    def help_History(self):
        print(
              '\nThe commands for managing the session history in the history file.\n'
              '\n\thistClear\n'
              '\t\tClears the current working session history and the history file. This deletes all history, be careful!\n'
              '\n\thistDedupe\n'
              '\t\tThe history can accumulate duplicate entries over time, use this to remove the dupes.\n' 
             )

    def do_shell(self,line):
        '\nRun OS shell commands: !<command>\n'
        output = os.popen(line).read()
        printWithNewLines(output, 'B')

    def do_histDedupe(self, arg):

        if readline:
            ans = userInput('\nThis will deduplicate both this session history and the history file, are you sure?')
            if ans in ['y','Y', 'yes', 'YES']:
    
                with open(histfile) as hf:
                    linesIn = (line.rstrip() for line in hf)
                    uniqLines = OrderedDict.fromkeys( line for line in linesIn if line )
    
                    readline.clear_history()
                    for ul in uniqLines:
                        readline.add_history(ul)
    
                printWithNewLines('Session history and session file both deduplicated.', 'B')
            else:
                printWithNewLines('History session and history file have NOT been deduplicated.', 'B')
        else:
            printWithNewLines('History isn\'t available in this session.', 'B')


    def do_histClear(self, arg):

        if readline:
            ans = userInput('\nThis will clear both this session history and the history file, are you sure?')
            if ans in ['y','Y', 'yes', 'YES']:
                readline.clear_history()
                readline.write_history_file(histfile)
                printWithNewLines('Session history and session file both cleared.', 'B')
            else:
                printWithNewLines('History session and history file have NOT been cleared.', 'B')
        else:
            printWithNewLines('History isn\'t available in this session.', 'B')


    def do_histShow(self, arg):

        if readline:
            print('')
            for i in range(readline.get_current_history_length()):
                printWithNewLines(readline.get_history_item(i + 1))
            print('')
        else:
            printWithNewLines('History isn\'t available in this session.', 'B')

# ===== global commands =====

    # -----------------------------
    def do_version (self,arg):
        printWithNewLines('POC Utilities version %s' % pocUtilsVersion, 'B')

    # -----------------------------
    def do_colorScheme (self,arg):
        '\nSets the color scheme lighter or darker. Darker works better on lighter backgrounds and vice-versa.' \
        '\n\nSyntax:' \
        '\n\tcolorScheme dark' \
        '\n\tcolorScheme light\n'

        if not argCheck('do_colorScheme', arg, self.do_colorScheme.__doc__):
            printWithNewLines('colorScheme set to ' + self.settingsFileData['colorScheme'], 'B')
            return

        arg = arg.upper()

        #--best for dark backgrounds
        self.colors['none'] = None
        if arg == 'LIGHT':
            self.settingsFileData['colorScheme'] = 'light'
            self.colors['tableTitle'] = 'fg.lightblue,italics,bold'
            self.colors['columnHeader'] = 'bg.darkgrey,fg.white,bold'
            self.colors['rowDescriptor'] = 'fg.lightblue,bold'
            self.colors['good'] = 'fg.lightgreen'
            self.colors['bad'] = 'fg.lightred'
            self.colors['caution'] = 'fg.lightyellow'
            self.colors['highlight1'] = 'fg.lightmagenta'
            self.colors['highlight2'] = 'fg.lightcyan'

        #--best for light backgrounds
        elif arg == 'DARK':
            self.settingsFileData['colorScheme'] = 'dark'
            self.colors['tableTitle'] = 'fg.blue,italics,bold'
            self.colors['columnHeader'] = 'bg.darkgrey,fg.white,bold'
            self.colors['rowDescriptor'] = 'fg.blue,bold'
            self.colors['good'] = 'fg.green'
            self.colors['bad'] = 'fg.red'
            self.colors['caution'] = 'fg.yellow'
            self.colors['highlight1'] = 'fg.magenta'
            self.colors['highlight2'] = 'fg.cyan'
        else:
            printWithNewLines('Color scheme %s not valid!' % (arg), 'B')
            return

    # -----------------------------
    def do_load (self,arg):
        '\nLoads statistical json files computed by pocSnapshot.py or pocAudit.py.' \
        '\n\nSyntax:' \
        '\n\tload <pocSnapshot json file>' \
        '\n\tload <pocAudit json file>\n'
        if not argCheck('do_load', arg, self.do_load.__doc__):
            return

        statpackFileName = arg
        if not os.path.exists(statpackFileName):
            printWithNewLines('file %s not found!' % (statpackFileName), 'B')
            return

        try: jsonData = json.load(open(statpackFileName), encoding="utf-8")
        except:
            printWithNewLines('Invalid json in %s' % statpackFileName, 'B')
            return

        if 'SOURCE' in jsonData and jsonData['SOURCE'] in ('pocCalculate', 'pocSnapshot'):
            self.settingsFileData['pocSnapshotFile'] = statpackFileName
            self.pocSnapshotFile = statpackFileName
            self.pocSnapshotData = jsonData
            printWithNewLines('%s sucessfully loaded!' % statpackFileName, 'B')
        elif 'SOURCE' in jsonData and jsonData['SOURCE'] == 'pocAudit':
            self.settingsFileData['pocAuditFile'] = statpackFileName
            self.pocAuditFile = statpackFileName
            self.pocAuditData = jsonData
            printWithNewLines('%s sucessfully loaded!' % statpackFileName, 'B')
        else:
            printWithNewLines('Invalid statistics file %s' % statpackFileName, 'B')

    # -----------------------------
    def complete_load(self, text, line, begidx, endidx):
        before_arg = line.rfind(" ", 0, begidx)
        if before_arg == -1:
            return # arg not found

        fixed = line[before_arg+1:begidx]  # fixed portion of the arg
        arg = line[before_arg+1:endidx]
        pattern = arg + '*'

        completions = []
        for path in glob.glob(pattern):
            path = _append_slash_if_dir(path)
            completions.append(path.replace(fixed, "", 1))
        return completions

    # -----------------------------
    def do_auditSummary (self,arg):
        '\nDisplays the stats and examples of an audit performed with pocAudit.py' \
        '\n\nSyntax:' \
        '\n\tauditSummary       (with no parameters displays the overall stats)' \
        '\n\tauditSummary merge (shows examples of splits or merges or both)\n'

        if not self.pocAuditData or 'AUDIT' not in self.pocAuditData:
            printWithNewLines('Please load a json file created with pocAudit.py to use this feature', 'B')
            return

        #--display the summary if no arguments
        if not arg:
            
            tblTitle = 'Audit Results from %s' % self.pocAuditFile
            tblColumns = []
            tblColumns.append({'name': 'Statistic1', 'width': 25, 'align': 'left'})
            tblColumns.append({'name': 'Entities', 'width': 25, 'align': 'right'})
            tblColumns.append({'name': 'Clusters', 'width': 25, 'align': 'right'})
            tblColumns.append({'name': 'Pairs', 'width': 25, 'align': 'right'})
            tblColumns.append({'name': colorize('-', 'invisible'), 'width': 5, 'align': 'center'})
            tblColumns.append({'name': 'Statistic2', 'width': 25, 'align': 'left'})
            tblColumns.append({'name': 'Accuracy', 'width': 25, 'align': 'right'})
            tblRows = []

            row = []
            row.append(colorize('Prior Count', self.colors['none']))
            row.append(fmtStatistic(self.pocAuditData['ENTITY']['STANDARD_COUNT']) if 'ENTITY' in self.pocAuditData else '0')
            row.append(fmtStatistic(self.pocAuditData['CLUSTERS']['STANDARD_COUNT']))
            row.append(fmtStatistic(self.pocAuditData['PAIRS']['STANDARD_COUNT']))
            row.append('')
            row.append(colorize('Prior Positives', self.colors['none']))
            row.append(fmtStatistic(self.pocAuditData['ACCURACY']['PRIOR_POSITIVE']))
            tblRows.append(row)

            row = []
            row.append(colorize('Newer Count', self.colors['none']))
            row.append(fmtStatistic(self.pocAuditData['ENTITY']['RESULT_COUNT']) if 'ENTITY' in self.pocAuditData else '0')
            row.append(fmtStatistic(self.pocAuditData['CLUSTERS']['RESULT_COUNT']))
            row.append(fmtStatistic(self.pocAuditData['PAIRS']['RESULT_COUNT']))
            row.append('')
            row.append(colorize('New Positives', self.colors['highlight1']))
            row.append(colorize(fmtStatistic(self.pocAuditData['ACCURACY']['NEW_POSITIVE']), self.colors['highlight1']))
            tblRows.append(row)

            row = []
            row.append(colorize('Common Count', self.colors['none']))
            row.append(fmtStatistic(self.pocAuditData['ENTITY']['COMMON_COUNT']) if 'ENTITY' in self.pocAuditData else '0')
            row.append(fmtStatistic(self.pocAuditData['CLUSTERS']['COMMON_COUNT']))
            row.append(fmtStatistic(self.pocAuditData['PAIRS']['COMMON_COUNT']))
            row.append('')
            row.append(colorize('New Negatives', self.colors['caution']))
            row.append(colorize(fmtStatistic(self.pocAuditData['ACCURACY']['NEW_NEGATIVE']), self.colors['caution']))
            tblRows.append(row) 

            row = []
            row.append(colorize('Precision', self.colors['none']))
            row.append(self.pocAuditData['ENTITY']['PRECISION'] if 'ENTITY' in self.pocAuditData else '0')
            row.append(self.pocAuditData['CLUSTERS']['PRECISION'])
            row.append(self.pocAuditData['PAIRS']['PRECISION'])
            row.append('')
            row.append(colorize('Precision', self.colors['highlight2']))
            row.append(colorize(self.pocAuditData['ACCURACY']['PRECISION'], self.colors['highlight2']))
            tblRows.append(row)

            row = []
            row.append(colorize('Recall', self.colors['none']))
            row.append(self.pocAuditData['ENTITY']['RECALL'] if 'ENTITY' in self.pocAuditData else '0')
            row.append(self.pocAuditData['CLUSTERS']['RECALL'])
            row.append(self.pocAuditData['PAIRS']['RECALL'])
            row.append('')
            row.append(colorize('Recall', self.colors['highlight2']))
            row.append(colorize(self.pocAuditData['ACCURACY']['RECALL'], self.colors['highlight2']))
            tblRows.append(row)

            row = []
            row.append(colorize('F1 Score', self.colors['none']))
            row.append(self.pocAuditData['ENTITY']['F1-SCORE'] if 'ENTITY' in self.pocAuditData else '0')
            row.append(self.pocAuditData['CLUSTERS']['F1-SCORE'])
            row.append(self.pocAuditData['PAIRS']['F1-SCORE'])
            row.append('')
            row.append(colorize('F1 Score', self.colors['highlight2']))
            row.append(colorize(self.pocAuditData['ACCURACY']['F1-SCORE'], self.colors['highlight2']))
            tblRows.append(row)
            self.renderTable(tblTitle, tblColumns, tblRows)

            tblTitle = 'SPLIT AND MERGED ENTITIES'
            tblColumns = []
            tblColumns.append({'name': 'Category', 'width': 25, 'align': 'left'})
            tblColumns.append({'name': 'Count', 'width': 25, 'align': 'right'})
            tblRows = []
            for category in self.pocAuditData['AUDIT']:
                if category == 'SPLIT':
                    displayColor = self.colors['caution']
                elif category == 'MERGE':
                    displayColor = self.colors['highlight1']
                elif category == 'SPLIT+MERGE':
                    displayColor = self.colors['caution']
                else:
                    displayColor = self.colors['bad']
                tblRows.append([colorize(category, displayColor), colorize(fmtStatistic(self.pocAuditData['AUDIT'][category]['COUNT']), displayColor)])
            self.renderTable(tblTitle, tblColumns, tblRows)

        else:
            argList = arg.upper().split()
            if argList[0] not in self.pocAuditData['AUDIT']:
                printWithNewLines('%s not found, please choose a valid split or merge category' % arg, 'B')
                return

            category = argList[0]
            if category == 'SPLIT':
                displayColor = self.colors['caution']
            elif category == 'MERGE':
                displayColor = self.colors['highlight1']
            elif category == 'SPLIT+MERGE':
                displayColor = self.colors['caution']
            else:
                displayColor = self.colors['bad']

            #--get top 10 sub categories
            i = 0
            subCategoryList = []
            for subCategory in sorted(self.pocAuditData['AUDIT'][category]['SUB_CATEGORY'], key=lambda x: self.pocAuditData['AUDIT'][category]['SUB_CATEGORY'][x]['COUNT'], reverse=True):
                i += 1
                if i <= 10:
                    subCategoryList.append({'INDEX': i, 'NAME': subCategory, 'LIST': [subCategory], 'COUNT': self.pocAuditData['AUDIT'][category]['SUB_CATEGORY'][subCategory]['COUNT']})
                elif i == 11:
                    subCategoryList.append({'INDEX': i, 'NAME': 'OTHERS', 'LIST': [subCategory], 'COUNT': self.pocAuditData['AUDIT'][category]['SUB_CATEGORY'][subCategory]['COUNT']})
                else:
                    subCategoryList[10]['LIST'].append(subCategory)
                    subCategoryList[10]['COUNT'] += self.pocAuditData['AUDIT'][category]['SUB_CATEGORY'][subCategory]['COUNT']

            #--display sub-categories
            if len(argList) == 1:
                tblTitle = category + ' ENTITY SUB-CATEGORIES'
                tblColumns = []
                tblColumns.append({'name': 'Index', 'width': 10, 'align': 'center'})
                tblColumns.append({'name': 'Category', 'width': 25, 'align': 'left'})
                tblColumns.append({'name': 'Sub-category', 'width': 75, 'align': 'left'})
                tblColumns.append({'name': 'Count', 'width': 25, 'align': 'right'})
                tblRows = []
                for subCategoryRow in subCategoryList:
                    tblRows.append([str(subCategoryRow['INDEX']), colorize(category, displayColor), subCategoryRow['NAME'], fmtStatistic(subCategoryRow['COUNT'])])
                self.renderTable(tblTitle, tblColumns, tblRows)

                return

            #--find the detail records to display
            subCategoryIndex = -1
            if argList[1].isdigit() and int(argList[1]) >= 1 and int(argList[1]) <= 11:
                subCategoryIndex = int(argList[1]) - 1
            else:                
                for i in range(len(subCategoryList)):
                    if argList[1].upper() == subCategoryList[i]:
                        subCategoryIndex = i
                        break

            if subCategoryIndex == -1:
                printWithNewLines('%s not found, please choose a valid split or merge sub-category' % arg, 'B')
                return

            #--gather sample records
            sampleRecords = []
            for subCategory in self.pocAuditData['AUDIT'][category]['SUB_CATEGORY']:
                if subCategory in subCategoryList[subCategoryIndex]['LIST']:
                    sampleRecords += self.pocAuditData['AUDIT'][category]['SUB_CATEGORY'][subCategory]['SAMPLE']

            #--display sample records
            currentSample = 0
            while True:

                self.auditResult(sampleRecords[currentSample])
                exportRecords = list(set([x['newer_id'] for x in sampleRecords[currentSample]]))

                while True:
                    reply = userInput('Select (P)revious, (N)ext, (R)eload, (S)crolling view, (W)hy view, (E)xport records, (Q)uit ... ')
                    if reply:
                        removeFromHistory()

                    if reply.upper().startswith('R'): #--reload
                        break
                    elif reply.upper().startswith('P'): #--previous
                        if currentSample == 0:
                            printWithNewLines('no prior records!', 'B')
                        else:
                            currentSample = currentSample - 1
                            break
                    elif reply.upper().startswith('N'): #--next
                        if currentSample == len(sampleRecords) - 1:
                            printWithNewLines('no more records!', 'B')
                        else:
                            currentSample += 1
                            break
                    elif reply.upper().startswith('Q'): #--quit
                        break

                    #--special actions 
                    elif reply.upper().startswith('S'): #--scrolling view
                        self.do_scroll('')
                    elif reply.upper().startswith('W'): #--why view
                        self.do_why(','.join(exportRecords))
                    elif reply.upper().startswith('E'): #--export
                        fileName = None
                        if 'TO' in reply.upper():
                            fileName = reply[reply.upper().find('TO') + 2:].strip()
                        else:                            
                            fileName = 'auditSample-%s.json' % sampleRecords[currentSample][0]['audit_id']
                            fileName = os.path.join(os.path.expanduser("~"), fileName)
                        self.do_export(','.join(exportRecords) + 'to ' + fileName)

                if reply.upper().startswith('Q'):
                    break

    # -----------------------------
    def auditResult (self, arg):

        auditRecords = arg
        exportRecords = []

        tblTitle = 'Audit Result ID %s %s' % (auditRecords[0]['audit_id'], auditRecords[0]['audit_category'])
        tblColumns = []
        tblColumns.append({'name': 'DataSource', 'width': 30, 'align': 'left'})
        tblColumns.append({'name': 'Record ID', 'width': 30, 'align': 'left'})
        tblColumns.append({'name': 'Prior ID', 'width': 20, 'align': 'left'})
        tblColumns.append({'name': 'Prior Score', 'width': 25, 'align': 'left'})
        tblColumns.append({'name': 'Newer ID', 'width': 20, 'align': 'left'})
        tblColumns.append({'name': 'Newer Score', 'width': 25, 'align': 'left'})
        tblColumns.append({'name': 'Audit result', 'width': 10, 'align': 'left'})

        sql1 = 'Select '
        sql1 += ' a.DSRC_ID, '
        sql1 += ' a.RECORD_ID, '
        sql1 += ' b.OBS_ENT_ID '
        sql1 += 'from DSRC_RECORD a '
        sql1 += 'join OBS_ENT b on b.ENT_SRC_KEY = a.ENT_SRC_KEY and b.DSRC_ID = a.DSRC_ID and b.ETYPE_ID = a.ETYPE_ID '
        sql1 += 'where a.RECORD_ID = ? and a.DSRC_ID = ?'
        sql1a = sql1.replace(' and a.DSRC_ID = ?', '') #--if data source not present

        sql2 = 'select '
        sql2 += '  b.FTYPE_ID, '
        sql2 += '  b.LIB_FEAT_ID, '
        sql2 += '  b.FEAT_DESC '
        sql2 += 'from OBS_FEAT_EKEY a '
        sql2 += 'join LIB_FEAT b on b.LIB_FEAT_ID = a.LIB_FEAT_ID '
        sql2 += 'where a.OBS_ENT_ID = ? '
        sql2 += 'order by b.FTYPE_ID '

        #--get the features
        updatedRecords = []
        ftypesUsed = []
        for auditRecord in auditRecords:
            if 'data_source' in auditRecord:
                try: auditRecord['dsrc_id'] = self.dsrcCodeLookup[auditRecord['data_source']]['DSRC_ID']
                except: 
                    printWithNewLines('data source %s not found!' % auditRecord['data_source'], 'B')
                    auditRecord['dsrc_id'] = None
            else:
                auditRecord['dsrc_id'] = None
                dataSourcePresent = False

            if auditRecord['dsrc_id']:
                dsrcRecord = g2Dbo.fetchNext(g2Dbo.sqlExec(sql1, [auditRecord['record_id'], int(auditRecord['dsrc_id'])]))
            else:
                dsrcRecord = g2Dbo.fetchNext(g2Dbo.sqlExec(sql1a, [auditRecord['record_id'],]))

            auditRecord['features'] = {}
            if not dsrcRecord:
                auditRecord['record_id'] = '** ' + auditRecord['record_id']
            else:
                lastFtypeCode = None
                featureString = ''
                featureList = g2Dbo.fetchAllDicts(g2Dbo.sqlExec(sql2, [dsrcRecord['OBS_ENT_ID'],]))
                for feature in featureList:
                    ftypeCode = self.ftypeLookup[feature['FTYPE_ID']]['FTYPE_CODE']
                    if ftypeCode in self.scoredFtypeCodes:
                        if feature['FTYPE_ID'] not in ftypesUsed:
                           ftypesUsed.append(feature['FTYPE_ID'])
                        if ftypeCode not in auditRecord['features']:
                            auditRecord['features'][ftypeCode] = []
                        auditRecord['features'][ftypeCode].append(feature['FEAT_DESC'])
            updatedRecords.append(auditRecord)

        #--add the columns to the table format and do the final formatting
        ftypesUsed = sorted(ftypesUsed)
        for ftypeID in ftypesUsed:
            ftypeCode = self.ftypeLookup[ftypeID]['FTYPE_CODE']
            tblColumns.append({'name': ftypeCode, 'width': 50, 'align': 'left'})

        statusSortOrder = {}
        statusSortOrder['same'] = '1'
        statusSortOrder['new negative'] = '2'
        statusSortOrder['new positive'] = '3'
        statusSortOrder['missing'] = '4'

        tblRows = []
        for auditRecord in sorted(updatedRecords, key=lambda k: [statusSortOrder[k['audit_result']], str(k['prior_id']), str(k['newer_id'])]):
            if auditRecord['audit_result'].upper() == 'NEW POSITIVE':
                auditResultColor = self.colors['highlight1']
            elif auditRecord['audit_result'].upper() == 'NEW NEGATIVE':
                auditResultColor = self.colors['caution']
            elif auditRecord['audit_result'].upper() == 'MISSING':
                auditResultColor = self.colors['bad']
            else:
                auditResultColor = 'bold'
            row = []
            row.append(auditRecord['data_source'] if 'data_source' in auditRecord else '')
            row.append(auditRecord['record_id'])
            row.append(auditRecord['prior_id'])
            row.append(auditRecord['prior_score'])
            row.append(auditRecord['newer_id'])
            row.append(auditRecord['newer_score'])
            row.append(colorize(str(auditRecord['audit_result']), auditResultColor))

            for ftypeID in ftypesUsed:
                ftypeCode = self.ftypeLookup[ftypeID]['FTYPE_CODE']
                ftypeExcl = self.ftypeLookup[ftypeID]['FTYPE_EXCL']
                cfuncCode = self.scoredFtypeCodes[ftypeCode]['CFUNC_CODE'] if ftypeCode in self.scoredFtypeCodes else 'none'
                columnValue = ''
                if ftypeCode in auditRecord['features']:
                    #columnValue = '\n'.join(auditRecord['features'][ftypeCode])
                    for featureDesc in auditRecord['features'][ftypeCode]:
                        if not featureDesc:
                            continue

                        if columnValue:
                            columnValue += '\n'

                        anyFound = False
                        matchFound = False
                        diffFound = False
                        for otherRecord in updatedRecords:
                            if otherRecord['record_id'] != auditRecord['record_id'] and ftypeCode in otherRecord['features']:
                                for otherDesc in otherRecord['features'][ftypeCode]:
                                    anyFound = True
                                    if fuzzyCompare(ftypeCode, cfuncCode, featureDesc, otherDesc):
                                        matchFound = True
                                        break
                                    else: 
                                        diffFound = True
                                if matchFound:
                                    break

                        if not anyFound:
                            displayColor = self.colors['caution']
                        elif matchFound:
                            displayColor = self.colors['good']
                        elif diffFound and ftypeExcl.upper().startswith('Y'):
                            displayColor = self.colors['bad']
                        else: 
                            displayColor = self.colors['none']
                        columnValue += colorize(featureDesc, displayColor)

                row.append(columnValue)                

            tblRows.append(row)

        self.renderTable(tblTitle, tblColumns, tblRows)

        return

    # -----------------------------
    def do_entitySizeBreakdown (self,arg):
        '\nDisplays the stats for entities based on their size (how many records they contain).' \
        '\n\nSyntax:' \
        '\n\tentitySizeBreakdown                    (with no parameters displays the overall stats)' \
        '\n\tentitySizeBreakdown = 3                (use =, > or < # to select examples of entities of a certain size)' \
        '\n\tentitySizeBreakdown > 10 review        (to just browse the review items of entities greater than size 10)' \
        '\n\tentitySizeBreakdown = review name+addr (to just browse the name+addr review items of any size)' \
        '\n\nNotes: ' \
        '\n\tReview items are suggestions of records to look at because they contain multiple names, addresses, dobs, etc.' \
        '\n\tThey may be overmatches or they may just be large entities with lots of values.\n'

        if not self.pocSnapshotData or 'ENTITY_SIZE_BREAKDOWN' not in self.pocSnapshotData:
            printWithNewLines('Please load a json file created with pocSnapshot.py to use this feature', 'B')
            return

        if 'ENTITY_SIZE_DISPLAY' not in self.pocSnapshotData['ENTITY_SIZE_BREAKDOWN'][0]:
            printWithNewLines('The statistics loaded contain an older entity size structure this viewer cannot display', 'S')
            printWithNewLines('Please use the latest pocSnapshot.py to re-compute with the latest entity size breakdown structure', 'E')
            return

        #--display the summary if no arguments
        if not arg:
            
            tblTitle = 'Entity Size Breakdown from %s' % self.pocSnapshotFile
            tblColumns = []
            tblColumns.append({'name': 'Entity Size', 'width': 10, 'align': 'center'})
            tblColumns.append({'name': 'Entity Count', 'width': 10, 'align': 'center'})
            tblColumns.append({'name': 'Review Count', 'width': 10, 'align': 'center'})
            tblColumns.append({'name': 'Review Reasons', 'width': 75, 'align': 'left'})

            tblRows = []
            for entitySizeData in sorted(self.pocSnapshotData['ENTITY_SIZE_BREAKDOWN'], key=lambda k: k['ENTITY_SIZE'], reverse = True):
                row = []
                row.append('%s' % (entitySizeData['ENTITY_SIZE_DISPLAY']))
                row.append('%s' % (entitySizeData['ENTITY_COUNT'], ))
                row.append('%s' % (entitySizeData['REVIEW_COUNT'], ))
                reviewReasons = []
                for reviewReason in entitySizeData['REVIEW_REASONS']:
                    reviewReasons.append('%s %s' % (len(entitySizeData['REVIEW_REASONS'][reviewReason]), reviewReason))
                row.append(' | '.join(reviewReasons))    
                tblRows.append(row)
            self.renderTable(tblTitle, tblColumns, tblRows)

        else:
            sign = '='
            size = 0
            reviewOnly = False
            reviewReason = ''
            argList = arg.split()
            for token in argList:
                if token[0:2] in ('>=', '<='):
                    sign = token[0:2]
                    if len(token) > 2 and token[2:].isnumeric():
                        size = int(token[2:])
                elif token[0:1] in ('>', '<', '='):
                    sign = token[0:1]
                    if len(token) > 1 and token[1:].isnumeric():
                        size = int(token[1:])
                elif token.isnumeric():
                    size = int(token)
                elif token.upper() == "REVIEW":
                    reviewOnly = True
                else:
                    reviewReason = token.upper()

            if reviewReason and not reviewOnly:
                reviewOnly = True

            if reviewOnly and not size:
                size = 1
                sign = '>'

            #if not size or (reviewReason and not reviewOnly):
            #    printWithNewLines('%s is an invalid argument' % arg, 'B')
            #    return

            sampleRecords = []
            for entitySizeData in self.pocSnapshotData['ENTITY_SIZE_BREAKDOWN']:

                #--determine if all or review only entities
                if not reviewOnly:
                    theseRecords = [{"entity_id": str(i), "entity_size": entitySizeData['ENTITY_SIZE'], "review_only": reviewOnly, "review_reason": None} for i in entitySizeData['SAMPLE_ENTITIES']]
                else:
                    theseRecords = []
                    for thisReason in entitySizeData['REVIEW_REASONS']:
                        add2List = True
                        if reviewReason:
                            add2List = reviewReason in thisReason
                        if add2List:
                            theseRecords.extend([{"entity_id": str(i), "entity_size": entitySizeData['ENTITY_SIZE'], "review_only": reviewOnly, "review_reason": thisReason} for i in entitySizeData['REVIEW_REASONS'][thisReason]])
                            #print(theseRecords )
                if not theseRecords:
                    continue

                #--add these entities if qualifies entity size argument
                if sign in ('=', '>=', '<=') and entitySizeData['ENTITY_SIZE'] == size:
                    sampleRecords = theseRecords
                    break
                elif sign in ('<', '<=') and entitySizeData['ENTITY_SIZE'] < size:
                    sampleRecords = theseRecords + sampleRecords 
                elif sign in ('>', '>=') and entitySizeData['ENTITY_SIZE'] > size:
                    sampleRecords = sampleRecords + theseRecords 

            if len(sampleRecords) == 0:
                printWithNewLines('No records found for entitySizeBreakdown %s' % arg, 'B')
            else:

                currentSample = 0
                while True:
                    exportRecords = [sampleRecords[currentSample]['entity_id']]

                    self.currentReviewList = 'ENTITY SIZE %s' % sampleRecords[currentSample]['entity_size']
                    if sampleRecords[currentSample]['review_reason']:
                        self.currentReviewList += ' - REVIEW FOR: ' + sampleRecords[currentSample]['review_reason']

                    returnCode = self.do_get(exportRecords[0])
                    if returnCode != 0:
                        printWithNewLines('The statistics loaded are out of date for this entity','E')

                    while True:
                        reply = userInput('Select (P)revious, (N)ext, (R)eload, (S)crolling view, (W)hy view, (E)xport data, (Q)uit ...')
                        if reply:
                            removeFromHistory()

                        if reply.upper().startswith('R'): #--reload
                            break
                        elif reply.upper().startswith('P'): #--previous
                            if currentSample == 0:
                                printWithNewLines('no prior records!', 'B')
                            else:
                                currentSample = currentSample - 1
                                break
                        elif reply.upper().startswith('N'): #--next
                            if currentSample == len(sampleRecords) - 1:
                                printWithNewLines('no more records!', 'B')
                            else:
                                currentSample += 1
                                break
                        elif reply.upper().startswith('Q'): #--quit
                            break

                        #--special actions 
                        elif reply.upper().startswith('S'): #--scrolling view
                            self.do_scroll('')
                        elif reply.upper().startswith('W'): #--why view
                            self.do_why(','.join(exportRecords))
                        elif reply.upper().startswith('E'): #--export
                            fileName = None
                            if 'TO' in reply.upper():
                                fileName = reply[reply.upper().find('TO') + 2:].strip()
                            else:                            
                                fileName = '%s.json' % '-'.join(exportRecords)
                                fileName = os.path.join(os.path.expanduser("~"), fileName)
                            self.do_export(','.join(exportRecords) + 'to ' + fileName)

                    if reply.upper().startswith('Q'):
                        break
                self.currentReviewList = None

    # -----------------------------
    def do_dataSourceSummary (self, arg):
        '\nDisplays the stats for the different match levels within each data source.' \
        '\n\nSyntax:' \
        '\n\tdataSourceSummary (with no parameters displays the overall stats)' \
        '\n\tdataSourceSummary <dataSourceCode> <matchLevel>  where 0=Singletons, 1=Duplicates, 2=Ambiguous Matches, 3 = Possible Matches, 4=Possibly Relateds\n'

        if not self.pocSnapshotData or 'DATA_SOURCES' not in self.pocSnapshotData:
            printWithNewLines('Please load a json file created with pocSnapshot.py to use this feature', 'B')
            return

        #--display the summary if no arguments
        if not arg:

            tblTitle = 'Data source summary from %s' % self.pocSnapshotFile
            tblColumns = []
            tblColumns.append({'name': 'Data Source', 'width': 25, 'align': 'center'})
            tblColumns.append({'name': 'Records', 'width': 15, 'align': 'center'})
            tblColumns.append({'name': 'Entities', 'width': 15, 'align': 'center'})
            tblColumns.append({'name': 'Compression', 'width': 15, 'align': 'center'})
            tblColumns.append({'name': 'Singletons', 'width': 15, 'align': 'center'})
            tblColumns.append({'name': 'Duplicates', 'width': 15, 'align': 'center'})
            tblColumns.append({'name': 'Ambiguous', 'width': 15, 'align': 'center'})
            tblColumns.append({'name': 'Possibles', 'width': 15, 'align': 'center'})
            tblColumns.append({'name': 'Relationships', 'width': 15, 'align': 'center'})

            tblRows = []
            for dataSource in sorted(self.pocSnapshotData['DATA_SOURCES']):
                row = []
                row.append(dataSource)
                row.append(self.pocSnapshotData['DATA_SOURCES'][dataSource]['RECORD_COUNT'] if 'RECORD_COUNT' in self.pocSnapshotData['DATA_SOURCES'][dataSource] else 0)
                row.append(self.pocSnapshotData['DATA_SOURCES'][dataSource]['ENTITY_COUNT'] if 'ENTITY_COUNT' in self.pocSnapshotData['DATA_SOURCES'][dataSource] else 0)
                row.append(self.pocSnapshotData['DATA_SOURCES'][dataSource]['COMPRESSION'] if 'COMPRESSION' in self.pocSnapshotData['DATA_SOURCES'][dataSource] else 0)
                row.append(self.pocSnapshotData['DATA_SOURCES'][dataSource]['SINGLE_COUNT'] if 'SINGLE_COUNT' in self.pocSnapshotData['DATA_SOURCES'][dataSource] else 0)
                if 'DUPLICATE_COUNT' in self.pocSnapshotData['DATA_SOURCES'][dataSource]:
                    row.append(self.pocSnapshotData['DATA_SOURCES'][dataSource]['DUPLICATE_COUNT'] if 'DUPLICATE_COUNT' in self.pocSnapshotData['DATA_SOURCES'][dataSource] else 0)
                    row.append(self.pocSnapshotData['DATA_SOURCES'][dataSource]['AMBIGUOUS_MATCH_COUNT'] if 'AMBIGUOUS_MATCH_COUNT' in self.pocSnapshotData['DATA_SOURCES'][dataSource] else 0)
                    row.append(self.pocSnapshotData['DATA_SOURCES'][dataSource]['POSSIBLE_MATCH_COUNT'] if 'POSSIBLE_MATCH_COUNT' in self.pocSnapshotData['DATA_SOURCES'][dataSource] else 0)
                    row.append(self.pocSnapshotData['DATA_SOURCES'][dataSource]['POSSIBLY_RELATED_COUNT'] if 'POSSIBLY_RELATED_COUNT' in self.pocSnapshotData['DATA_SOURCES'][dataSource] else 0)
                else:
                    row.append(self.pocSnapshotData['DATA_SOURCES'][dataSource]['DUPLICATE_ENTITY_COUNT'] if 'DUPLICATE_ENTITY_COUNT' in self.pocSnapshotData['DATA_SOURCES'][dataSource] else 0)
                    row.append(self.pocSnapshotData['DATA_SOURCES'][dataSource]['AMBIGUOUS_MATCH_ENTITY_COUNT'] if 'AMBIGUOUS_MATCH_ENTITY_COUNT' in self.pocSnapshotData['DATA_SOURCES'][dataSource] else 0)
                    row.append(self.pocSnapshotData['DATA_SOURCES'][dataSource]['POSSIBLE_MATCH_ENTITY_COUNT'] if 'POSSIBLE_MATCH_ENTITY_COUNT' in self.pocSnapshotData['DATA_SOURCES'][dataSource] else 0)
                    row.append(self.pocSnapshotData['DATA_SOURCES'][dataSource]['POSSIBLY_RELATED_ENTITY_COUNT'] if 'POSSIBLY_RELATED_ENTITY_COUNT' in self.pocSnapshotData['DATA_SOURCES'][dataSource] else 0)

                tblRows.append(row)
            
            if not arg:
                self.renderTable(tblTitle, tblColumns, tblRows)
            else:
                return tblColumns, tblRows

        else:

            argTokens = arg.split()
            if len(argTokens) != 2:
                printWithNewLines('%s is an invalid argument' % arg, 'B')
                return

            dataSource = argTokens[0].upper()
            if dataSource not in self.pocSnapshotData['DATA_SOURCES']:
                printWithNewLines('%s is not a valid data source' % dataSource, 'B')
                return

            matchLevel = argTokens[1].upper()
            matchLevelCode = None
            for matchLevelParameter in self.validMatchLevelParameters:
                if matchLevel.startswith(matchLevelParameter):
                    matchLevelCode = self.validMatchLevelParameters[matchLevelParameter]
                    break
            if not matchLevelCode:
                printWithNewLines('%s is not a valid match level' % matchLevel, 'B')
                return

            try: sampleRecords = [k for k in self.pocSnapshotData['DATA_SOURCES'][dataSource][matchLevelCode]]
            except:
                printWithNewLines('no samples found for %s' % arg, 'B')
                return

            if len(sampleRecords) == 0:
                printWithNewLines('no entities to display!', 'B')
            else:

                self.currentReviewList = 'DATA SOURCE SUMMARY FOR: %s (%s)' % (dataSource, matchLevelCode) 
                currentSample = 0
                while True:
                    if matchLevelCode in ('SINGLE_SAMPLE', 'DUPLICATE_SAMPLE'):
                        exportRecords = [str(sampleRecords[currentSample])]
                        returnCode = self.do_get(exportRecords[0])
                    else:
                        exportRecords = sampleRecords[currentSample].split()[:2]
                        if matchLevelCode == 'AMBIGUOUS_MATCH_SAMPLE':
                            ambiguousList =self.getAmbiguousEntitySet(exportRecords[0]) #--is this the ambiguous entity
                            if ambiguousList:
                                exportRecords = ambiguousList
                            else:
                                ambiguousList =self.getAmbiguousEntitySet(exportRecords[1]) #--or is this the ambiguous entity
                                if ambiguousList:
                                    exportRecords = ambiguousList
                                else:
                                    pass #--if its neither, just show the original two entities
                        returnCode = self.do_compare(','.join(exportRecords))
                    if returnCode != 0:
                        printWithNewLines('The statistics loaded are out of date for this record!','E')
                    while True:
                        reply = userInput('Select (P)revious, (N)ext, (R)eload, (S)crolling view, (W)hy view, (E)xport data, (Q)uit ...')
                        if reply:
                            removeFromHistory()

                        if reply.upper().startswith('R'): #--reload
                            break
                        elif reply.upper().startswith('P'): #--previous
                            if currentSample == 0:
                                printWithNewLines('no prior records!', 'B')
                            else:
                                currentSample = currentSample - 1
                                break
                        elif reply.upper().startswith('N'): #--next
                            if currentSample == len(sampleRecords) - 1:
                                printWithNewLines('no more records!', 'B')
                            else:
                                currentSample += 1
                                break
                        elif reply.upper().startswith('Q'): #--quit
                            break

                        #--special actions 
                        elif reply.upper().startswith('S'): #--scrolling view
                            self.do_scroll('')
                        elif reply.upper().startswith('W'): #--why view
                            self.do_why(','.join(exportRecords))
                        elif reply.upper().startswith('E'): #--export
                            fileName = None
                            if 'TO' in reply.upper():
                                fileName = reply[reply.upper().find('TO') + 2:].strip()
                            else:                            
                                fileName = '%s.json' % '-'.join(exportRecords)
                                fileName = os.path.join(os.path.expanduser("~"), fileName)
                            self.do_export(','.join(exportRecords) + 'to ' + fileName)

                    if reply.upper().startswith('Q'):
                        break
            self.currentReviewList = None

    # -----------------------------
    def do_crossSourceSummary (self,arg):
        '\nDisplays the stats for the different match levels across data sources.' \
        '\n\nSyntax:' \
        '\n\tcrossSourceSummary (with no parameters displays the overall stats)' \
        '\n\tcrossSourceSummary <dataSource1> <dataSource2> <matchLevel>  where 1=Matches, 2=Ambiguous Matches, 3 = Possible Matches, 4=Possibly Relateds\n'
 
        if not self.pocSnapshotData or 'DATA_SOURCES' not in self.pocSnapshotData:
            printWithNewLines('Please load a json file created with pocSnapshot.py to use this feature', 'B')
            return

        #--display the summary if no arguments
        if not arg or len(arg.split()) == 1:

            tblTitle = 'Cross Source Summary from %s' % self.pocSnapshotFile
            tblColumns = []
            tblColumns.append({'name': 'Data Source1', 'width': 25, 'align': 'center'})
            tblColumns.append({'name': 'Data Source2', 'width': 25, 'align': 'center'})
            tblColumns.append({'name': 'Duplicates', 'width': 15, 'align': 'center'})
            tblColumns.append({'name': 'Ambiguous', 'width': 15, 'align': 'center'})
            tblColumns.append({'name': 'Possibles', 'width': 15, 'align': 'center'})
            tblColumns.append({'name': 'Relationships', 'width': 15, 'align': 'center'})

            tblRows = []
            for dataSource1 in sorted(self.pocSnapshotData['DATA_SOURCES']):
                if arg and dataSource1 != arg.upper():
                    continue
                for dataSource2 in sorted(self.pocSnapshotData['DATA_SOURCES'][dataSource1]['CROSS_MATCHES']):

                    #for key in self.pocSnapshotData['DATA_SOURCES'][dataSource1]['CROSS_MATCHES'][dataSource2]:
                    #    if type(self.pocSnapshotData['DATA_SOURCES'][dataSource1]['CROSS_MATCHES'][dataSource2][key]) != list:
                    #        print ('%s = %s' % (key, self.pocSnapshotData['DATA_SOURCES'][dataSource1]['CROSS_MATCHES'][dataSource2][key]))

                    row = []
                    row.append(dataSource1)
                    row.append(dataSource2)
                    if 'MATCH_COUNT' in self.pocSnapshotData['DATA_SOURCES'][dataSource1]['CROSS_MATCHES'][dataSource2]:
                        row.append(self.pocSnapshotData['DATA_SOURCES'][dataSource1]['CROSS_MATCHES'][dataSource2]['MATCH_COUNT'] if 'MATCH_COUNT' in self.pocSnapshotData['DATA_SOURCES'][dataSource1]['CROSS_MATCHES'][dataSource2] else 0)
                        row.append(self.pocSnapshotData['DATA_SOURCES'][dataSource1]['CROSS_MATCHES'][dataSource2]['AMBIGUOUS_MATCH_COUNT'] if 'AMBIGUOUS_MATCH_COUNT' in self.pocSnapshotData['DATA_SOURCES'][dataSource1]['CROSS_MATCHES'][dataSource2] else 0)
                        row.append(self.pocSnapshotData['DATA_SOURCES'][dataSource1]['CROSS_MATCHES'][dataSource2]['POSSIBLE_MATCH_COUNT'] if 'POSSIBLE_MATCH_COUNT' in self.pocSnapshotData['DATA_SOURCES'][dataSource1]['CROSS_MATCHES'][dataSource2] else 0)
                        row.append(self.pocSnapshotData['DATA_SOURCES'][dataSource1]['CROSS_MATCHES'][dataSource2]['POSSIBLY_RELATED_COUNT'] if 'POSSIBLY_RELATED_COUNT' in self.pocSnapshotData['DATA_SOURCES'][dataSource1]['CROSS_MATCHES'][dataSource2] else 0)
                    else:
                        row.append(self.pocSnapshotData['DATA_SOURCES'][dataSource1]['CROSS_MATCHES'][dataSource2]['MATCH_ENTITY_COUNT'] if 'MATCH_ENTITY_COUNT' in self.pocSnapshotData['DATA_SOURCES'][dataSource1]['CROSS_MATCHES'][dataSource2] else 0)
                        row.append(self.pocSnapshotData['DATA_SOURCES'][dataSource1]['CROSS_MATCHES'][dataSource2]['AMBIGUOUS_MATCH_ENTITY_COUNT'] if 'AMBIGUOUS_MATCH_COUNT' in self.pocSnapshotData['DATA_SOURCES'][dataSource1]['CROSS_MATCHES'][dataSource2] else 0)
                        row.append(self.pocSnapshotData['DATA_SOURCES'][dataSource1]['CROSS_MATCHES'][dataSource2]['POSSIBLE_MATCH_ENTITY_COUNT'] if 'POSSIBLE_MATCH_ENTITY_COUNT' in self.pocSnapshotData['DATA_SOURCES'][dataSource1]['CROSS_MATCHES'][dataSource2] else 0)
                        row.append(self.pocSnapshotData['DATA_SOURCES'][dataSource1]['CROSS_MATCHES'][dataSource2]['POSSIBLY_RELATED_ENTITY_COUNT'] if 'POSSIBLY_RELATED_ENTITY_COUNT' in self.pocSnapshotData['DATA_SOURCES'][dataSource1]['CROSS_MATCHES'][dataSource2] else 0)

                    tblRows.append(row)
            self.renderTable(tblTitle, tblColumns, tblRows)

        else:

            argTokens = arg.split()
            if len(argTokens) != 3:
                printWithNewLines('%s is an invalid argument' % arg, 'B')
                return

            dataSource1 = argTokens[0].upper()
            if dataSource1 not in self.pocSnapshotData['DATA_SOURCES']:
                printWithNewLines('%s is not a valid data source' % dataSource1, 'B')
                return

            dataSource2 = argTokens[1].upper()
            if dataSource2 not in self.pocSnapshotData['DATA_SOURCES'][dataSource1]['CROSS_MATCHES']:
                printWithNewLines('%s is not a matching data source' % dataSource2, 'B')
                return

            matchLevel = argTokens[2].upper()
            matchLevelCode = None
            for matchLevelParameter in self.validMatchLevelParameters:
                if matchLevel.startswith(matchLevelParameter):
                    matchLevelCode = self.validMatchLevelParameters[matchLevelParameter]
                    break

            if not matchLevelCode:
                printWithNewLines('%s is not a valid match level' % matchLevel, 'B')
                return

            #--duplicates are matches for cross source
            if matchLevelCode == 'DUPLICATE_SAMPLE':
                matchLevelCode = 'MATCH_SAMPLE'

            try: sampleRecords = [k for k in self.pocSnapshotData['DATA_SOURCES'][dataSource1]['CROSS_MATCHES'][dataSource2][matchLevelCode]]
            except:
                printWithNewLines('no samples found for %s' % arg, 'B')
                return

            if len(sampleRecords) == 0:
                printWithNewLines('no entities to display!', 'B')
            else:

                self.currentReviewList = 'CROSS SOURCE SUMMARY for: %s-%s  (%s)' % (dataSource1, dataSource2, matchLevelCode) 
                currentSample = 0
                while True:

                    if matchLevelCode in ('MATCH_SAMPLE'):
                        exportRecords = [str(sampleRecords[currentSample])]
                        returnCode = self.do_get(exportRecords[0])
                    else:
                        exportRecords = sampleRecords[currentSample].split()[:2]
                        returnCode = self.do_compare(','.join(exportRecords))
                    if returnCode != 0:
                        printWithNewLines('The statistics loaded are out of date for this entity','E')

                    while True:
                        reply = userInput('Select (P)revious, (N)ext, (R)eload, (S)crolling view, (W)hy view, (E)xport data, (Q)uit ...')
                        if reply:
                            removeFromHistory()

                        if reply.upper().startswith('R'): #--reload
                            break
                        elif reply.upper().startswith('P'): #--previous
                            if currentSample == 0:
                                printWithNewLines('no prior records!', 'B')
                            else:
                                currentSample = currentSample - 1
                                break
                        elif reply.upper().startswith('N'): #--next
                            if currentSample == len(sampleRecords) - 1:
                                printWithNewLines('no more records!', 'B')
                            else:
                                currentSample += 1
                                break
                        elif reply.upper().startswith('Q'): #--quit
                            break

                        #--special actions 
                        elif reply.upper().startswith('S'): #--scrolling view
                            self.do_scroll('')
                        elif reply.upper().startswith('W'): #--why view
                            self.do_why(','.join(exportRecords))
                        elif reply.upper().startswith('E'): #--export
                            fileName = None
                            if 'TO' in reply.upper():
                                fileName = reply[reply.upper().find('TO') + 2:].strip()
                            else:                            
                                fileName = '%s.json' % '-'.join(exportRecords)
                                fileName = os.path.join(os.path.expanduser("~"), fileName)
                            self.do_export(','.join(exportRecords) + 'to ' + fileName)

                    if reply.upper().startswith('Q'):
                        break
                self.currentReviewList = None

    # -----------------------------
    def do_search(self,arg):
        '\nSearches for entities by their attributes.' \
        '\n\nSyntax:' \
        '\n\tsearch Joe Smith (without a json structure performs a search on name alone)' \
        '\n\tsearch {"name_full": "Joe Smith"}' \
        '\n\tsearch {"name_org": "ABC Company"}' \
        '\n\tsearch {"name_last": "Smith", "name_first": "Joe", "date_of_birth": "1992-12-10"}' \
        '\n\tsearch {"name_org": "ABC Company", "addr_full": "111 First St, Anytown, USA 11111"}' \
        '\n\nNotes: ' \
        '\n\tSearching by name alone may not locate a specific entity.' \
        '\n\tTry adding a date of birth, address, or phone number if not found by name alone.\n'

        if not argCheck('do_search', arg, self.do_search.__doc__):
            return

        try:
            parmData = dictKeysUpper(json.loads(arg)) if arg.startswith('{') else {"PERSON_NAME_FULL": arg, "ORGANIZATION_NAME_ORG": arg}
        except (ValueError, KeyError) as e:
            argError(arg, e)
        else:

            print('')
            print('Searching ...')
            try: 
                response = bytearray()
                retcode = g2Engine.searchByAttributes(json.dumps(parmData), response)
                response = response.decode() if response else ''
            except G2Exception as err:
                print(str(err))
            else:
                jsonResponse = json.loads(response)
                #--print(response)
                
                #--constants for descriptions and sort orders
                dataSourceOrder = [] #--place your data sources here!

                tblTitle = 'SEARCH RESULTS'
                tblColumns = []
                tblColumns.append({'name': 'Index', 'width': 5, 'align': 'center'})
                tblColumns.append({'name': 'Entity ID', 'width': 15, 'align': 'center'})
                tblColumns.append({'name': 'Entity Name', 'width': 75, 'align': 'left'})
                tblColumns.append({'name': 'Data Sources', 'width': 50, 'align': 'left'})
                tblColumns.append({'name': 'Match Key', 'width': 50, 'align': 'left'})
                tblColumns.append({'name': 'Match Score', 'width': 15, 'align': 'center'})

                matchList = []
                searchIndex = 0
                for resolvedEntity in jsonResponse['SEARCH_RESPONSE']['RESOLVED_ENTITIES']:
                    searchIndex += 1

                    #--create a list of data sources we found them in
                    dataSources = {}
                    for record in resolvedEntity['RECORDS']:
                        dataSource = record['DATA_SOURCE']
                        if dataSource not in dataSources:
                            dataSources[dataSource] = [record['RECORD_ID']]
                        else:
                            dataSources[dataSource].append(record['RECORD_ID'])

                    dataSourceList = []
                    for dataSource in dataSources:
                        if len(dataSources[dataSource]) == 1:
                            dataSourceList.append(dataSource + ': ' + dataSources[dataSource][0])
                        else:
                            dataSourceList.append(dataSource + ': ' + str(len(dataSources[dataSource])) + ' records')

                    #--determine the matching criteria
                    matchLevel = self.searchMatchLevels[resolvedEntity['MATCH_LEVEL']]
                    matchKey = resolvedEntity['MATCH_KEY'][1:] if resolvedEntity['MATCH_KEY'] else '' 
                    nameScore = 0
                    matchedName = ''
                    if 'NAME' in resolvedEntity['MATCH_SCORES']:
                        for scoreRecord in resolvedEntity['MATCH_SCORES']['NAME']:
                            if scoreRecord['GNR_FN'] > nameScore:
                                nameScore = scoreRecord['GNR_FN']
                                matchedName = scoreRecord['CANDIDATE_FEAT']
                    matchScore = str(((5-resolvedEntity['MATCH_LEVEL']) * 100) + int(resolvedEntity['MATCH_SCORE'])) + '-' + str(1000+nameScore)[-3:]

                    #--create the possible match entity one-line summary
                    row = []
                    row.append(str(searchIndex))
                    row.append(str(resolvedEntity['ENTITY_ID']))
                    row.append(resolvedEntity['ENTITY_NAME'] + (('\n aka: ' + matchedName) if matchedName and matchedName != resolvedEntity['ENTITY_NAME'] else ''))
                    row.append('\n'.join(dataSourceList))
                    row.append(matchKey)
                    row.append(matchScore)
                    matchList.append(row)

                if len(matchList) == 0:
                    print('\tNo matches found or there were simply too many to return')
                    print('\tPlease include additional search parameters if you feel this entity is in the database')
                else:

                    #--sort the list by match score descending
                    matchList = sorted(matchList, key=lambda x: x[5], reverse=True)
                    self.lastSearchResult = []
                    for i in range(len(matchList)):
                        matchList[i][0] = str(i+1)
                        self.lastSearchResult.append(matchList[i][1])
                    self.renderTable(tblTitle, tblColumns, matchList, 10)


                print('')

            if self.doDebug:
                showMeTheThings(parmData)

    # -----------------------------
    def do_get(self,arg):

        '\nDisplays a particular entity by entity_id or by data_source and record_id.' \
        '\n\nSyntax:' \
        '\n\tget <entity_id>' \
        '\n\tget <dataSource> <recordID>' \
        '\n\tget search <search index>' \
        '\n\tget detail <entity_id>' \
        '\n\tget detail <dataSource> <recordID>' \
        '\n\nNotes: ' \
        '\n\tget search is a shortcut to the entity ID at the search index provided. Must be valid for the last search performed' \
        '\n\tget detail displays every record for the entity while a get alone displays a summary of the entity by dataSource.\n'

        if not argCheck('do_get', arg, self.do_get.__doc__):
            return

        #--no return code if called direct
        calledDirect = sys._getframe().f_back.f_code.co_name != 'onecmd'

        if 'DETAIL ' in arg.upper():
            showDetail = True
            arg = arg.upper().replace('DETAIL ','')
        else: 
            showDetail = False

        if len(arg.split()) == 2 and arg.split()[0].upper() == 'SEARCH':
            lastToken = arg.split()[1]
            if not lastToken.isdigit() or lastToken == '0' or int(lastToken) > len(self.lastSearchResult):
                printWithNewLines('Select a valid index from the prior search results to use this feature', 'B')
                return -1 if calledDirect else 0
            else:
                arg = self.lastSearchResult[int(lastToken)-1]

        if len(arg.split()) == 1:
            try: 
                response = bytearray()
                retcode = g2Engine.getEntityByEntityID(int(arg), response)
                response = response.decode() if response else ''
            except G2Exception as err:
                printWithNewLines(str(err), 'B')
                return -1 if calledDirect else 0

        elif len(arg.split()) == 2:
            try: 
                response = bytearray()
                retcode = g2Engine.getEntityByRecordID(arg.split()[0], arg.split()[1], response)
                response = response.decode() if response else ''
            except G2Exception as err:
                printWithNewLines(str(err), 'B')
                return -1 if calledDirect else 0
        else:
            argError(arg, 'incorrect number of parameters')
            return 0

        if len(response) == 0:
            printWithNewLines('0 records found %s' % response, 'B')
            return -1 if calledDirect else 0
        else:
            if showDetail: 
                self.showEntityDetail(response)    
            else:
                self.showEntitySummary(response)

        return 0

    # -----------------------------
    def showEntitySummary(self, entityJsonStr):

        resolvedJson = json.loads(str(entityJsonStr))

        entityID = str(resolvedJson['RESOLVED_ENTITY']['ENTITY_ID'])
        tblTitle = 'Entity ID %s - %s' % (entityID, resolvedJson['RESOLVED_ENTITY']['ENTITY_NAME'])
        tblColumns = []
        tblColumns.append({'name': 'Record ID', 'width': 50, 'align': 'left'})
        tblColumns.append({'name': 'Entity Data', 'width': 75, 'align': 'left'})
        tblColumns.append({'name': 'Additional Data', 'width': 75, 'align': 'left'})

        #--group by data source
        dataSources = {}
        recordList = []
        for record in resolvedJson['RESOLVED_ENTITY']['RECORDS']:
            if record['DATA_SOURCE'] not in dataSources:
                dataSources[record['DATA_SOURCE']] = []
            dataSources[record['DATA_SOURCE']].append(record)

        #--summarize by data source
        for dataSource in sorted(dataSources):
            recordIdList = []
            primaryNameData = []
            otherNameData = []
            attributeData = []
            identifierData = []
            addressData = []
            phoneData = []
            otherData = []
            for record in dataSources[dataSource]:
                recordIdList.append(record['RECORD_ID'])
                for item in record['NAME_DATA']:
                    if item.upper().startswith('PRIMARY'):
                        primaryNameData.append(item)
                    else:
                        otherNameData.append(item)
                for item in record['ATTRIBUTE_DATA']:
                    attributeData.append(item)
                for item in record['IDENTIFIER_DATA']:
                    identifierData.append(item)
                for item in record['ADDRESS_DATA']:
                    addressData.append('ADDRESS: ' + item)
                for item in record['PHONE_DATA']:
                    phoneData.append('PHONE: ' + item)
                for item in record['OTHER_DATA']:
                    if not self.isInternalAttribute(item):
                        otherData.append(item)

            row = []
            if len(recordIdList) > 20:
                row.append('\n'.join([dataSource] + sorted(recordIdList)[:20] + ['+%s more ' % str(len(recordIdList) - 20)]))
            else:
                row.append('\n'.join([dataSource] + sorted(recordIdList)))

            row.append('\n'.join(sorted(set(primaryNameData)) + sorted(set(otherNameData)) + sorted(set(attributeData)) + sorted(set(identifierData)) + sorted(set(addressData)) + sorted(set(phoneData))))

            otherData = set(otherData) #--de-dupe
            if len(otherData) > 20:
                row.append('\n'.join(sorted(otherData)[:20] + ['+%s more ' % str(len(otherData) - 20)]))
            else:
                row.append('\n'.join(sorted(otherData)))

            recordList.append(row)
        self.renderTable(tblTitle, tblColumns, recordList)

        #--show relationships if there are any and not reviewing a list
        if 'RELATED_ENTITIES' in resolvedJson and len(resolvedJson['RELATED_ENTITIES']) > 0 and not self.currentReviewList:
            self.showRelatedEntities(resolvedJson['RELATED_ENTITIES'], tblTitle)

    # -----------------------------
    def showEntityDetail(self, entityJsonStr):

        resolvedJson = json.loads(str(entityJsonStr))

        tblTitle = 'ENTITY_ID %s - %s' % (resolvedJson['RESOLVED_ENTITY']['ENTITY_ID'], resolvedJson['RESOLVED_ENTITY']['ENTITY_NAME'])
        tblColumns = []
        tblColumns.append({'name': 'Record ID', 'width': 50, 'align': 'left'})
        tblColumns.append({'name': 'Entity Data', 'width': 75, 'align': 'left'})
        tblColumns.append({'name': 'Additional Data', 'width': 75, 'align': 'left'})

        jsonData1 = {}
        jsonData2 = []

        recordList = []
        for record in resolvedJson['RESOLVED_ENTITY']['RECORDS']:
            if not jsonData1:
                jsonData1 = record['JSON_DATA']
            else:
                jsonData2.append({'DATA_SOURCE': record['DATA_SOURCE'], 'RECORD_ID': record['RECORD_ID']})

            row = []
            row.append(record['DATA_SOURCE'] + '\n' + record['RECORD_ID'] + ('\n (' + record['MATCH_KEY'][1:] + ')' if record['MATCH_KEY'] else ''))
            row.append('\n'.join(record['NAME_DATA'] + record['ATTRIBUTE_DATA'] + record['IDENTIFIER_DATA'] + ['ADDRESS: ' + x for x in record['ADDRESS_DATA']] + ['PHONE: '+ x for x in record['PHONE_DATA']]))
            row.append('\n'.join(record['OTHER_DATA']))
            recordList.append(row)
        self.renderTable(tblTitle, tblColumns, recordList, 5)

        #--not trying to analyze entities here
        #if 'RELATED_ENTITIES' in resolvedJson and len(resolvedJson['RELATED_ENTITIES']) > 0:
        #    self.showRelatedEntities(resolvedJson['RELATED_ENTITIES'], tblTitle)

    # -----------------------------
    def showRelatedEntities(self, relatedJson, tblTitle):

        #--determine what, if any relationships exist
        relationships = []
        for relatedEntity in relatedJson:
            relationship = {}
            relationship['MATCH_LEVEL'] = relatedEntity['MATCH_LEVEL']
            relationship['MATCH_SCORE'] = relatedEntity['MATCH_SCORE']
            relationship['MATCH_KEY'] = relatedEntity['MATCH_KEY']
            relationship['ERRULE_CODE'] = relatedEntity['ERRULE_CODE']
            relationship['ENTITY_ID'] = relatedEntity['ENTITY_ID']
            relationship['ENTITY_NAME'] = relatedEntity['ENTITY_NAME']
            relationship['DATA_SOURCES'] = []
            for dataSource in relatedEntity['RECORD_SUMMARY']:
                relationship['DATA_SOURCES'].append('%s(%s)' %(dataSource['DATA_SOURCE'], dataSource['RECORD_COUNT']))
                
            relationships.append(relationship)

        print('')
        reply = userInput('%s relationships found, press D to display %s or enter to skip ... ' % (len(relationships), ('it' if len(relationships) ==1 else 'them')))
        if reply:
            removeFromHistory()
        print('')

        if reply.upper().startswith('D'):

            tblTitle = tblTitle.replace('Records Resolved', 'Entities Related')
            tblColumns = []
            tblColumns.append({'name': 'Entity ID', 'width': 15, 'align': 'left'})
            tblColumns.append({'name': 'Entity Name', 'width': 75, 'align': 'left'})
            tblColumns.append({'name': 'Data Sources', 'width': 75, 'align': 'left'})
            tblColumns.append({'name': 'Match Level', 'width': 25, 'align': 'left'})
            tblColumns.append({'name': 'Match Key', 'width': 50, 'align': 'left'})
            tblColumns.append({'name': 'ER RUle', 'width': 25, 'align': 'left'})

            relatedRecordList = []
            for relationship in sorted(relationships, key = lambda k: k['MATCH_LEVEL']):
                row = []
                row.append(str(relationship['ENTITY_ID']))
                row.append(relationship['ENTITY_NAME'])
                row.append('|'.join(sorted(relationship['DATA_SOURCES'])))
                row.append(self.relatedMatchLevels[relationship['MATCH_LEVEL']])
                row.append(relationship['MATCH_KEY'])
                row.append(relationship['ERRULE_CODE'])
                relatedRecordList.append(row)
                
            self.renderTable(tblTitle, tblColumns, relatedRecordList)

    # -----------------------------
    def getAmbiguousEntitySet(self, entityID):
        sql1 = 'select 1 from RES_FEAT_EKEY where RES_ENT_ID = ? and FTYPE_ID = ?'
        if g2Dbo.fetchNext(g2Dbo.sqlExec(sql1, [entityID, self.ambiguousFtypeID])):
            sql2 = 'select a.REL_ENT_ID from RES_REL_EKEY a join RES_RELATE b on b.RES_REL_ID = a.RES_REL_ID where a.RES_ENT_ID = ? and b.IS_AMBIGUOUS = 1'
            relEntityList = g2Dbo.fetchAllRows(g2Dbo.sqlExec(sql2, [entityID,]))
            if relEntityList:
                entitySet = [entityID]
                for relEntity in relEntityList:
                    entitySet.append(str(relEntity[0]))
                return entitySet
        return None

    # -----------------------------
    def do_compare(self,arg):
        '\nCompares a set of entities by placing them side by side in a columnar format.'\
        '\n\nSyntax:' \
        '\n\tcompare <entity_id1> <entity_id2>' \
        '\n\tcompare search ' \
        '\n\tcompare search <top (n)>'
        if not argCheck('do_compare', arg, self.do_compare.__doc__):
            return -1

        showDetail = False #--old flag, replaced by why service which shows interal features

       #--no return code if called direct
        calledDirect = sys._getframe().f_back.f_code.co_name != 'onecmd'

        fileName = None
        if type(arg) == str and 'TO' in arg.upper():
            fileName = arg[arg.upper().find('TO') + 2:].strip()
            fileName = arg[:arg.upper().find('TO')].strip()

        if type(arg) == str and 'SEARCH' in arg.upper():
            lastToken = arg.split()[len(arg.split())-1]
            if lastToken.isdigit():
                entityList = self.lastSearchResult[:int(lastToken)]
            else:
                entityList = self.lastSearchResult
        else:
            try: 
                if ',' in arg:
                    entityList = list(map(int, arg.split(',')))
                else:
                    entityList = list(map(int, arg.split()))
            except:
                printWithNewLines('error parsing argument [%s] into entity id numbers' % arg, 'S') 
                printWithNewLines('  expected comma or space delimited integers', 'E') 
                return -1 if calledDirect else 0

        if len(entityList) == 0:
            printWithNewLines('%s contains no valid entities' % arg, 'B') 
            return -1 if calledDirect else 0

        compareList = []
        for entityId in entityList:
            try:
                response = bytearray()
                retcode = g2Engine.getEntityByEntityID(int(entityId), response)
                response = response.decode() if response else ''
            except G2Exception as err:
                printWithNewLines(str(err), 'B')
                return -1 if calledDirect else 0
            else:
                if len(response) == 0:
                    printWithNewLines('0 records found for %s' % entityId, 'B')
                    return -1 if calledDirect else 0

            jsonData = json.loads(response)

            entityData = {}
            entityData['entityID'] = jsonData['RESOLVED_ENTITY']['ENTITY_ID']
            entityData['dataSources'] = {}
            entityData['nameData'] = []
            entityData['attributeData'] = []
            entityData['identifierData'] = []
            entityData['addressData'] = []
            entityData['phoneData'] = []
            entityData['relationshipData'] = []
            entityData['otherData'] = []
            entityData['crossRelations'] = []
            entityData['otherRelations'] = []
 
            for record in jsonData['RESOLVED_ENTITY']['RECORDS']:
                if record['DATA_SOURCE'] not in entityData['dataSources']:
                    entityData['dataSources'][record['DATA_SOURCE']] = [record['RECORD_ID']]
                else:
                    entityData['dataSources'][record['DATA_SOURCE']].append(record['RECORD_ID'])
                if 'NAME_DATA' in record:
                    for item in record['NAME_DATA']:
                        if item not in entityData['nameData']:
                            entityData['nameData'].append(item)
                if 'ATTRIBUTE_DATA' in record:
                    for item in record['ATTRIBUTE_DATA']:
                        if item not in entityData['attributeData']:
                            entityData['attributeData'].append(item)
                if 'IDENTIFIER_DATA' in record:
                    for item in record['IDENTIFIER_DATA']:
                        if item not in entityData['identifierData']:
                            entityData['identifierData'].append(item)
                if 'ADDRESS_DATA' in record:
                    for item in record['ADDRESS_DATA']:
                        if item not in entityData['addressData']:
                            entityData['addressData'].append(item)
                if 'PHONE_DATA' in record:
                    for item in record['PHONE_DATA']:
                        if item not in entityData['phoneData']:
                            entityData['phoneData'].append(item)
                if 'RELATIONSHIP_DATA' in record:
                    for item in record['RELATIONSHIP_DATA']:
                        if item not in entityData['relationshipData']:
                            entityData['relationshipData'].append(item)
                if 'OTHER_DATA' in record:
                    for item in record['OTHER_DATA']:
                        if (showDetail or not self.isInternalAttribute(item)) and item not in entityData['otherData']:
                            entityData['otherData'].append(item)

            for relatedEntity in jsonData['RELATED_ENTITIES']:
                if relatedEntity['ENTITY_ID'] in entityList:
                    entityData['crossRelations'].append('%s to %s on %s (%s)' % (self.relatedMatchLevels[relatedEntity['MATCH_LEVEL']], relatedEntity['ENTITY_ID'], relatedEntity['MATCH_KEY'][1:], relatedEntity['ERRULE_CODE']))
                else:
                    entityData['otherRelations'].append({"MATCH_LEVEL": self.relatedMatchLevels[relatedEntity['MATCH_LEVEL']], "MATCH_KEY": relatedEntity['MATCH_KEY'][1:], "ERRULE_CODE": relatedEntity['ERRULE_CODE'], "ENTITY_ID": relatedEntity['ENTITY_ID'], "ENTITY_NAME": relatedEntity['ENTITY_NAME']})

            #--let them know these entities are not related to each other
            if len(entityData['crossRelations']) == 0:
                entityData['crossRelations'].append('not related to the others')

            compareList.append(entityData)


        #--determine if there are any relationships in common
        for entityData1 in compareList:
            entityData1['relsInCommon'] = []
            for entityData2 in compareList:
                if entityData2['entityID'] == entityData1['entityID']:
                    continue
                for relation1 in entityData1['otherRelations']:
                    for relation2 in entityData2['otherRelations']:
                        possibleMatchRelation = False
                        if relation1['ENTITY_ID'] == relation2['ENTITY_ID']:
                            possibleMatchRelation = True
                        elif False:  #--ability to see if they are bothe related to a billy or a mary (by name) is turned off so ambiguous is more clear
                            if hasFuzzy:
                                possibleMatchRelation = fuzz.token_set_ratio(relation1['ENTITY_NAME'], relation2['ENTITY_NAME']) >= 90
                            else:
                                possibleMatchRelation = relation1['ENTITY_NAME'] == relation2['ENTITY_NAME']

                        if possibleMatchRelation and relation1 not in entityData1['relsInCommon']:
                            entityData1['relsInCommon'].append(relation1)

        #--create the column data arrays
        dataSourcesRow = []
        nameDataRow = []
        attributeDataRow = []
        identifierDataRow = []
        addressDataRow = []
        phoneDataRow = []
        relationshipDataRow = []
        otherDataRow = []
        crossRelsRow = []
        commonRelsRow = []
        for entityData in compareList:
            dataSourcesList = []
            for dataSource in sorted(entityData['dataSources']):
                for recordID in sorted(entityData['dataSources'][dataSource])[:5]:
                    dataSourcesList.append(dataSource + ': ' + recordID)
                if len(entityData['dataSources'][dataSource]) > 5:
                    dataSourcesList.append(dataSource + ': +%s more ' % str(len(entityData['dataSources'][dataSource]) - 5))
            dataSourcesRow.append('\n'.join(dataSourcesList))

            nameDataRow.append('\n'.join(sorted(entityData['nameData'])))
            attributeDataRow.append('\n'.join(sorted(entityData['attributeData'])))
            identifierDataRow.append('\n'.join(sorted(entityData['identifierData'])))
            addressDataRow.append('\n'.join(sorted(entityData['addressData'])))
            phoneDataRow.append('\n'.join(sorted(entityData['phoneData'])))
            relationshipDataRow.append('\n'.join(sorted(entityData['relationshipData'])))
            otherDataRow.append('\n'.join(sorted(entityData['otherData'])))
            crossRelsRow.append('\n'.join(sorted(entityData['crossRelations'])))

            commonRelsList = []
            for relation in sorted(entityData['relsInCommon'], key=lambda x: x['ENTITY_ID']):
                #commonRelsList.append('%(MATCH_LEVEL)s to %(ENTITY_ID)s %(ENTITY_NAME)s on %(ERRULE_CODE)s' % relation)
                commonRelsList.append('%s to %s on %s (%s)' % (relation['MATCH_LEVEL'], relation['ENTITY_ID'], relation['MATCH_KEY'], relation['ERRULE_CODE']))

            commonRelsRow.append('\n'.join(commonRelsList))

        #--initialize table
        columnWidth = 75
        if True: #--disable adjustment in favor of less last table
            if len(entityList) <= 1:
                columnWidth = 100
            elif len(entityList) <= 3:
                columnWidth = 75
            elif len(entityList) <= 4:
                columnWidth = 50
            else:
                columnWidth = 25

        tblTitle = 'Comparison of listed entities'
        tblColumns = []
        tblColumns.append({'name': 'Entity ID', 'width': 15, 'align': 'left'})
        for entityId in entityList:
            tblColumns.append({'name': str(entityId), 'width': columnWidth, 'align': 'left'})

        #--add the data
        tblRows = []
        tblRows.append(['Data Sources'] + dataSourcesRow)
        if len(''.join(nameDataRow)) > 0:
            tblRows.append(['Names'] + nameDataRow)
        if len(''.join(attributeDataRow)) > 0:
            tblRows.append(['Attributes'] + attributeDataRow)
        if len(''.join(identifierDataRow)) > 0:
            tblRows.append(['Identifiers'] + identifierDataRow)
        if len(''.join(addressDataRow)) > 0:
            tblRows.append(['Addresses'] + addressDataRow)
        if len(''.join(phoneDataRow)) > 0:
            tblRows.append(['Phones'] + phoneDataRow)
        if len(''.join(otherDataRow)) > 0:
            tblRows.append(['OtherData'] + otherDataRow)
        if len(''.join(relationshipDataRow)) > 0:
            tblRows.append(['Disclosed Rels'] + relationshipDataRow)
        if len(''.join(crossRelsRow)) > 0:
           tblRows.append(['Cross Rels'] + crossRelsRow)
        if len(''.join(commonRelsRow)) > 0:
            tblRows.append(['Common Rels'] + commonRelsRow)
        
        self.renderTable(tblTitle, tblColumns, tblRows)

        return 0

    # -----------------------------
    def do_why(self,arg):
        '\nShows all the internals values for the entities desired in order to explain why they did or did not resolve.' \
        '\n\nSyntax:' \
        '\n\twhy <entity_id1>               (shows why the records in the entity resolved together)' \
        '\n\twhy <entity_id1> <entity_id2>  (shows how the different entities are related and/or why they did not resolve)' \
        '\n\nColor legend:' \
        '\n\tgreen indicates the values should have matched and contributed to the overall score' \
        '\n\tred indicates the values should not have matched and hurt the overall score' \
        '\n\tcyan indicates the values only helped get the record on the candidate list' \
        '\n\tyellow indicates the values only belonged to that record and did not contribute to the overall match' \
        '\n\tdimmed values were ignored (see the bracket legend below)' \
        '\n\nBracket legend:' \
        '\n\t[99] indicates how many entities share this value' \
        '\n\t[~] indicates that this value was not used to find candidates as too many entities share it' \
        '\n\t[!] indicates that this value was not not even scored as way too many entities share it' \
        '\n\t[#] indicates that this value was supressed in favor of a more complete value' \
        '\n\nNotes:' \
        '\n\tThe comparisons performed by this feature currently only approximate the actual comparison made by the engine.\n' 
        if type(arg) != list and not argCheck('do_why', arg, self.do_why.__doc__):
            return -1

        #--no return code if called direct
        calledFrom = sys._getframe().f_back.f_code.co_name
        calledDirect = calledFrom != 'onecmd'

        #--see if already a list ... it will be if it came from audit
        if type(arg) == list:
            entityList = arg
        else:

            fileName = None
            if type(arg) == str and 'TO' in arg.upper():
                fileName = arg[arg.upper().find('TO') + 2:].strip()
                fileName = arg[:arg.upper().find('TO')].strip()

            if type(arg) == str and 'SEARCH' in arg.upper():
                lastToken = arg.split()[len(arg.split())-1]
                if lastToken.isdigit():
                    entityList = self.lastSearchResult[:int(lastToken)]
                else:
                    entityList = self.lastSearchResult
            else:
                try: 
                    if ',' in arg:
                        entityList = list(map(int, arg.split(',')))
                    else:
                        entityList = list(map(int, arg.split()))
                except:
                    printWithNewLines('error parsing argument [%s] into entity id numbers' % arg, 'S') 
                    printWithNewLines('  expected comma or space delimited integers', 'E') 
                    return -1 if calledDirect else 0

        singleEntityAnalysis = False
        tblColumns = []
        tblRows = []

        #--make sure all entities exist if called direct as loaded stats may be out of date
        if calledDirect:
            allFound = True
            for entityId in entityList:
                if not g2Dbo.fetchNext(g2Dbo.sqlExec('select 1 from RES_ENT_OKEY where RES_ENT_ID = ?', [entityId,])):
                    printWithNewLines('missing entity id %s' % entityId, ('N' if not allFound else 'S'))
                    allFound = False
            if not allFound:
                printWithNewLines('Loaded statistics are out of date!', 'B')
                return -1

        if len(entityList) == 1:
            singleEntityAnalysis = True
            tblTitle = 'Analysis of entity ID ' + str(entityList[0])
            tblColumns.append({'name': 'Internal ID', 'width': 20, 'align': 'left'})
            sql = 'Select '
            sql += ' a.OBS_ENT_ID, '
            sql += ' b.DSRC_ID, '
            sql += ' a.MATCH_KEY '
            sql += 'from RES_ENT_OKEY a '
            sql += 'join OBS_ENT b on b.OBS_ENT_ID = a.OBS_ENT_ID '
            sql += 'where a.RES_ENT_ID = ? '
            sql += 'order by a.OBS_ENT_ID '

            obsList = g2Dbo.fetchAllDicts(g2Dbo.sqlExec(sql, [entityList[0],]))
            entityList = []
            storedMatchKeyRow = ['MATCH_KEY (logged)']
            for obsRow in obsList:
                entityList.append(obsRow['OBS_ENT_ID'])
                tblColumns.append({'name': obsRow['OBS_ENT_ID'], 'width': 75, 'align': 'left'})
                storedMatchKeyRow.append(obsRow['MATCH_KEY'][1:] if obsRow['MATCH_KEY'] else None)
            if len(entityList) == 0:
                print('no records found!')
                print('')
                return -1 if calledDirect else 0 

            #--set feature SQL for below
            feat_sql = 'Select '
            feat_sql += ' a.OBS_ENT_ID as RES_ENT_ID, '
            feat_sql += ' a.FTYPE_ID, '
            feat_sql += ' a.UTYPE_CODE, '
            feat_sql += ' b.FEAT_DESC, '
            feat_sql += ' b.FELEM_VALUES, '
            feat_sql += ' c.NUM_RES_ENT * NUM_RES_ENT_OOM ENTITY_COUNT, ' 
            feat_sql += ' c.CANDIDATE_CAP_REACHED, '
            feat_sql += ' c.SCORING_CAP_REACHED '
            feat_sql += 'from OBS_FEAT_EKEY a '
            feat_sql += 'join LIB_FEAT b on b.LIB_FEAT_ID = a.LIB_FEAT_ID '
            feat_sql += 'left join RES_FEAT_STAT c on c.LIB_FEAT_ID = a.LIB_FEAT_ID '
            feat_sql += 'where a.OBS_ENT_ID in (%s) ' % ','.join(['?'] * len(set(entityList)))

        #--its a list of entities so asking why not
        else:
            tblTitle = 'Analysis of listed entities'
            tblColumns.append({'name': 'Entity ID', 'width': 20, 'align': 'left'})
            for entityId in entityList:
                tblColumns.append({'name': entityId, 'width': 75, 'align': 'left'})

            #--set feature SQL for below
            feat_sql = 'Select '
            feat_sql += ' a.RES_ENT_ID, '
            feat_sql += ' a.SUPPRESSED, '
            feat_sql += ' a.FTYPE_ID, '
            feat_sql += ' a.UTYPE_CODE, '
            feat_sql += ' b.FEAT_DESC, '
            feat_sql += ' b.FELEM_VALUES, '
            feat_sql += ' c.NUM_RES_ENT * NUM_RES_ENT_OOM ENTITY_COUNT, ' 
            feat_sql += ' c.CANDIDATE_CAP_REACHED, '
            feat_sql += ' c.SCORING_CAP_REACHED '
            feat_sql += 'from RES_FEAT_EKEY a '
            feat_sql += 'join LIB_FEAT b on b.LIB_FEAT_ID = a.LIB_FEAT_ID '
            feat_sql += 'left join RES_FEAT_STAT c on c.LIB_FEAT_ID = a.LIB_FEAT_ID '
            feat_sql += 'where a.RES_ENT_ID in (%s) ' % ','.join(['?'] * len(set(entityList)))

        #--create a row for the data sources
        tblRow = ['DATA SOURCES']
        for entityId in entityList:

            dsrc_sql = 'select ' 
            dsrc_sql += ' a.DSRC_ID, '
            dsrc_sql += ' b.RECORD_ID '
            dsrc_sql += 'from OBS_ENT a '
            dsrc_sql += 'join DSRC_RECORD b on b.ENT_SRC_KEY = a.ENT_SRC_KEY and b.DSRC_ID = a.DSRC_ID and b.ETYPE_ID = a.ETYPE_ID '
            if singleEntityAnalysis:
                dsrc_sql += 'where a.OBS_ENT_ID = ?'
            else:
                dsrc_sql += 'where a.OBS_ENT_ID in (select OBS_ENT_ID from RES_ENT_OKEY where RES_ENT_ID = ?) '
            dataSources = {}
            cursor = g2Dbo.sqlExec(dsrc_sql, [entityId,])
            rowData = g2Dbo.fetchNext(cursor)
            while rowData:
                rowData['DATA_SOURCE'] = self.dsrcLookup[rowData['DSRC_ID']]['DSRC_CODE'] if rowData['DSRC_ID'] in self.dsrcLookup else '?'
                if rowData['DATA_SOURCE'] not in dataSources:
                    dataSources[rowData['DATA_SOURCE']] = []
                dataSources[rowData['DATA_SOURCE']].append(rowData['RECORD_ID'])
                rowData = g2Dbo.fetchNext(cursor)
            cellValue = ''
            for dataSource in sorted(dataSources):
                if cellValue:
                    cellValue += '\n'
                if len(dataSources[dataSource]) == 1:
                    cellValue += '%s: %s' % (dataSource, dataSources[dataSource][0])
                else:
                    cellValue += '%s: %s records' % (dataSource, len(dataSources[dataSource]))
            tblRow.append(cellValue)
        tblRows.append(tblRow)

        #--create a feature array for comparison
        ftypeList = {}
        cursor = g2Dbo.sqlExec(feat_sql, list(set(entityList)))
        rowData = g2Dbo.fetchNext(cursor)
        while rowData:
            if not rowData['FEAT_DESC']: #--ambiguous has no feat_desc
                if rowData['FTYPE_ID'] == self.ambiguousFtypeID: #--first element is the ftype that mad it ambiguous
                    try: triggeringFtypeCode = self.ftypeLookup[int(rowData['FELEM_VALUES'].split('|')[0].split(':')[1])]['FTYPE_CODE']
                    except: pass
                    else: rowData['FEAT_DESC'] = 'comflicting %ss' % triggeringFtypeCode
                if not rowData['FEAT_DESC']: #--if still not set
                    rowData['FEAT_DESC'] = rowData['FELEM_VALUES']
            if rowData['FTYPE_ID'] not in ftypeList:
                ftypeList[rowData['FTYPE_ID']] = {}
            if rowData['RES_ENT_ID'] not in ftypeList[rowData['FTYPE_ID']]:
                ftypeList[rowData['FTYPE_ID']][rowData['RES_ENT_ID']] = []
            ftypeList[rowData['FTYPE_ID']][rowData['RES_ENT_ID']].append(rowData)
            rowData = g2Dbo.fetchNext(cursor)
        
        #--initialize matchKeys
        matchingFeats = {}
        nonMatchingFeats = {}
        candidateFeats = {}
        for entityId in entityList:
            matchingFeats[entityId] = []
            nonMatchingFeats[entityId] = []
            candidateFeats[entityId] = []

        #--for each feature
        for ftypeId in sorted(ftypeList):
            ftypeCode = self.ftypeLookup[ftypeId]['FTYPE_CODE']
            ftypeExcl = True if str(self.ftypeLookup[ftypeId]['FTYPE_EXCL']).upper() in ('YES', 'Y', '1') else False
            usedForCand = True if str(self.ftypeLookup[ftypeId]['USED_FOR_CAND']).upper() in ('YES', 'Y', '1') else False
            cfuncCode = self.scoredFtypeCodes[ftypeCode]['CFUNC_CODE'] if ftypeCode in self.scoredFtypeCodes else None

            #--do comparison
            for entityID1 in ftypeList[ftypeId]:
                for i in range(len(ftypeList[ftypeId][entityID1])):

                    # determine if matched any other entities
                    matched = False
                    featData1 = ftypeList[ftypeId][entityID1][i]
                    ftypeList[ftypeId][entityID1][i]['MATCH_CODE'] = 3 #--no match
                    for entityID2 in ftypeList[ftypeId]:
                        if entityID2 != entityID1:
                            for featData2 in ftypeList[ftypeId][entityID2]:
                                if fuzzyCompare(ftypeCode, cfuncCode, featData1['FEAT_DESC'], featData2['FEAT_DESC']):
                                    ftypeList[ftypeId][entityID1][i]['MATCH_CODE'] = 1 #--matched
                                    matched = True
                                    break
                                else:
                                    ftypeList[ftypeId][entityID1][i]['MATCH_CODE'] = 2 #--different
                        if matched:
                            break

                    #--create a feature description with flags that show if generic or supressed
                    displayFeatDesc = featData1['FEAT_DESC']
                    ignoredCode = 0
                    if featData1['ENTITY_COUNT']:
                        displayFeatDesc += ' ['
                        displayFeatDesc += ('~' if featData1['CANDIDATE_CAP_REACHED'] == 'Y' else '')
                        displayFeatDesc += ('!' if featData1['SCORING_CAP_REACHED'] == 'Y' else '')
                        displayFeatDesc += ('#' if 'SUPPRESSED' in featData1 and featData1['SUPPRESSED'] == 'Y' else '')
                        displayFeatDesc += str(featData1['ENTITY_COUNT']) + ']'
                        if featData1['SCORING_CAP_REACHED'] == 'Y' or ('SUPPRESSED' in featData1 and featData1['SUPPRESSED'] == 'Y'):
                            ignoredCode = 2 #--not scored
                        elif featData1['CANDIDATE_CAP_REACHED'] == 'Y':
                            ignoredCode = 1 #--not a candidate builder

                    ftypeList[ftypeId][entityID1][i]['DISPLAY_FEAT_DESC'] = displayFeatDesc
                    ftypeList[ftypeId][entityID1][i]['IGNORED_CODE'] = ignoredCode

            #--format output
            tblRow = [ftypeCode]
            for entityId in entityList:
                overrideExcl = False #--for when address is exclusive due to business usage type
                bestMatch = 3 #--across all instances of this feature for this entity
                cellValues = []
                if entityId in ftypeList[ftypeId]:
                    for featData in sorted(ftypeList[ftypeId][entityId], key=lambda k: (k['MATCH_CODE'], k['IGNORED_CODE'])):
                        ##print(featData['RES_ENT_ID'], featData['MATCH_CODE'], featData['IGNORED_CODE'], featData['DISPLAY_FEAT_DESC'])
                        displayFeatDesc = featData['DISPLAY_FEAT_DESC']
                        ignoredCode = featData['IGNORED_CODE']

                        #--just show the ambiguous entity feature as bad
                        if ftypeId == self.ambiguousFtypeID:
                            cellValues.append(colorize(displayFeatDesc, self.colors['bad']))
                        elif featData['MATCH_CODE'] == 1: #--matched
                            if cfuncCode: #--if scored
                                if ignoredCode == 2:  #--not actually scored
                                    cellValues.append(colorize(displayFeatDesc, self.colors['good'] + ',dim'))
                                else:
                                    cellValues.append(colorize(displayFeatDesc, self.colors['good']))
                                    bestMatch = 1
                            else: #--just a candidate builder
                                if ignoredCode != 0: #--went generic
                                    cellValues.append(colorize(displayFeatDesc, self.colors['highlight2'] + ',dim'))
                                else:
                                    cellValues.append(colorize(displayFeatDesc, self.colors['highlight2']))
                                    bestMatch = 1

                        elif featData['MATCH_CODE'] == 2: #--not matched (different)
                            overrideExcl = ftypeCode == 'ADDRESS' and featData['UTYPE_CODE'].upper() == 'BUSINESS'
                            if cfuncCode and (ftypeExcl or overrideExcl): #--if scored and exclusive
                                if ignoredCode == 2:  #--not actually scored
                                    cellValues.append(colorize(displayFeatDesc, self.colors['bad'] + ',dim'))
                                else:
                                    cellValues.append(colorize(displayFeatDesc, self.colors['bad']))
                                    if bestMatch != 1:
                                        bestMatch = 2
                            else: #--just a candidate builder that didn't match
                                cellValues.append(displayFeatDesc)

                        else: #--no match attempt, only belongs to this entity
                            cellValues.append(colorize(displayFeatDesc, self.colors['caution']))

                #-add this entity's features to that row
                tblRow.append('\n'.join(cellValues))

                #--update match key dictionaries
                if cfuncCode:
                    if bestMatch == 1:
                        matchingFeats[entityId].append(ftypeCode)
                    elif bestMatch == 2 and (ftypeExcl or overrideExcl):
                        nonMatchingFeats[entityId].append(ftypeCode)
                if usedForCand and bestMatch == 1:
                    candidateFeats[entityId].append(ftypeCode)

            #--add this feature's data to the table
            if ftypeId == self.ambiguousFtypeID:
                tblRows.insert(0, tblRow)
            else:
                tblRows.append(tblRow)

        #--compute likey match keys 
        tblRow = ['MATCH_KEY (current)']
        for entityId in entityList:
            matchKey = ''
            if matchingFeats[entityId]:
                matchKey += colorize('+' + '+'.join(matchingFeats[entityId]), self.colors['good'])
            if nonMatchingFeats[entityId]:
                matchKey += colorize('-' + '-'.join(nonMatchingFeats[entityId]), self.colors['bad'])
            if len(candidateFeats[entityId]) == 0 and len(entityList) > 1:
                matchKey += (('\n' if len(matchKey) > 0 else '') + colorize('no candidates!', 'bg.red,fg.white'))
            #tblRow.append(colorize(matchKey, self.colors['highlight1']))
            tblRow.append(matchKey)

        tblRows.insert(0, tblRow)

        #--show the stored match keys for single entity analysis
        if singleEntityAnalysis:
            tblRows.insert(1, storedMatchKeyRow)

        #--show the cross relationships if comparing across entities
        else:
            tblRow = ['CROSS RELS']
            for entityId in entityList:
                sql = 'select ' 
                sql += ' a.REL_ENT_ID, '
                sql += ' b.LAST_ERRULE_ID, '
                sql += ' b.MATCH_KEY '
                sql += 'from RES_REL_EKEY a '
                sql += 'join RES_RELATE b on b.RES_REL_ID = a.RES_REL_ID '
                sql += 'where a.RES_ENT_ID = ? '
                cellValue = ''
                cursor = g2Dbo.sqlExec(sql, [entityId,])
                rowData = g2Dbo.fetchNext(cursor)
                while rowData:
                    rowData['ERRULE_CODE'] = self.erruleLookup[rowData['LAST_ERRULE_ID']]['ERRULE_CODE'] if rowData['LAST_ERRULE_ID'] in self.erruleLookup else '?'
                    if rowData['REL_ENT_ID'] in entityList:
                        if cellValue:
                            cellValue += '\n'
                        cellValue += '%s on %s (%s)' % (rowData['REL_ENT_ID'], rowData['MATCH_KEY'], rowData['ERRULE_CODE'])

                    rowData = g2Dbo.fetchNext(cursor)
                tblRow.append(cellValue)
            tblRows.insert(1, tblRow)

        #--display the table
        self.renderTable(tblTitle, tblColumns, tblRows)

        return 0

    # -----------------------------
    def do_score(self,arg): #--disabled 
        '\n\tscore [{"name_last": "Smith", "name_first": "Joseph"}, {"name_last": "Smith", "name_first": "Joe"}]' 
        #'\n\tscore entity1 entity2'

        if not argCheck('do_score', arg, self.do_score.__doc__):
            return

        #--see if they gave us json
        try: 
            jsonData = json.loads(arg)
            addRecordJson = jsonData[0]
            searchRecordJson = jsonData[1]
        except:
            print('json parameters are invalid, see example in help')
            return

        #--try to parse the string they gave us 
        if not jsonData:
            if ',' in arg:
                searchItems = [x.strip() for x in arg.split(',')]
            elif ' ' in arg:
                searchItems = [x.strip() for x in arg.split(' ')]
            else:
                searchItems = []

            if len(searchItems) != 2:
                print('string parameters are invalid, see example in help')
                return 

            searchItems[0] = searchItems[0].strip('"')
            searchItems[1] = searchItems[1].strip('"')

            if searchItems[0].isnumeric():
                addRecordJson = {}
                searchRecordJson = {}
                print('score by entity not yet available')
                return

            else:
                addRecordJson = {"NAME_FULL": names[0]}
                searchRecordJson = {"NAME_FULL": names[1]}

        #--add the other_id candidate builder
        dataSourceCode = 'TEST'
        recordID = 'scoreNameRecordID'
        otherID = '__nameTestID__'
        addRecordJson['OTHER_ID_NUMBER'] = otherID
        addRecordStr = json.dumps(addRecordJson).upper()
        searchRecordJson['OTHER_ID_NUMBER'] = otherID
        searchRecordStr = json.dumps(searchRecordJson).upper()

        #--add the first record
        try: 
            retcode = g2Engine.addRecord(dataSourceCode, recordID, addRecordStr)
        except G2Exception as err:
            print(str(err))
            return

        #--search it up and display the scores
        try: 
            response = bytearray()
            retcode = g2Engine.searchByAttributes(searchRecordStr, response)
            response = response.decode() if response else ''
        except G2Exception as err:
            print(str(err))
            return
        else:
            isTheOne = False
            jsonResponse = json.loads(response)
            for resolvedEntity in jsonResponse['SEARCH_RESPONSE']['RESOLVED_ENTITIES']:
                for record in resolvedEntity['RECORDS']:
                    if record['DATA_SOURCE'] == dataSourceCode and record['RECORD_ID'] == recordID:
                        isTheOne = True
                        break
                if isTheOne:
                    for featureCode in resolvedEntity['MATCH_SCORES']:
                        if featureCode=='OTHER_ID':
                            continue
                        for scoreRecord in resolvedEntity['MATCH_SCORES'][featureCode]:
                            scoreRecord['FEATURE_CODE'] = featureCode
                            print(json.dumps(scoreRecord, indent =4))
                            displayed = True
                    break

            if not isTheOne:
                print('Something went wrong, contact Ant!')

        #--delete the temporary record
        try: 
            response = g2Engine.deleteRecord(dataSourceCode, recordID)
        except G2Exception as err:
            print(str(err))
            return

    # -----------------------------
    def renderTable(self, tblTitle, tblColumns, tblRows, pageRecords = 0):

        #--setup the table
        tableWidth = 0
        columnHeaderList = []
        for i in range(len(tblColumns)):
            tableWidth += tblColumns[i]['width']
            tblColumns[i]['name'] = str(tblColumns[i]['name'])
            columnHeaderList.append(tblColumns[i]['name'])
        tableObject = ColoredTable(title_color=self.colors['tableTitle'], header_color=self.colors['columnHeader'])
        tableObject.hrules = prettytable.ALL
        tableObject.title = tblTitle
        tableObject.field_names = columnHeaderList
    
        thisTable = tableObject.copy()
        neverPrinted = True
        justPrinted = False
        rowCnt = 0
        for row in tblRows:
            rowCnt += 1
            row[0] = '\n'.join([colorize(i, self.colors['rowDescriptor']) for i in row[0].split('\n')])

            if self.usePrettyTable:
                thisTable.add_row(row)
            else:
                thisTable.append_row(row)
            if pageRecords !=0 and rowCnt % pageRecords == 0:
                if neverPrinted:
                    neverPrinted = False

                #--format with data in the table before printing
                for columnData in tblColumns:
                    thisTable.max_width[str(columnData['name'])] = columnData['width']
                    thisTable.align[str(columnData['name'])] = columnData['align'][0:1].lower()
                print(thisTable)
                justPrinted = True
                #--write to last table so can be viewed with less if necessary
                with open(self.lastTableName,'w') as file:
                    file.write(thisTable.get_string())

                print('')
                reply = userInput('%s more records to display, press enter to continue or Q to quit ... ' % (len(tblRows) - rowCnt))
                print('')
                if reply:
                    removeFromHistory()
                if reply and reply.upper().startswith('Q'):
                    break
                thisTable = tableObject.copy()
                justPrinted = False

        if not justPrinted:

            #--format with data in the table
            print('')
            if self.currentReviewList:
                print(colorize(self.currentReviewList, 'bold'))
            for columnData in tblColumns:
                thisTable.max_width[str(columnData['name'])] = columnData['width']
                thisTable.align[str(columnData['name'])] = columnData['align'][0:1].lower()
            print(thisTable.get_string())

            #--write to last table so can be viewed with less if necessary
            with open(self.lastTableName,'w') as file:
                file.write(thisTable.get_string())

            if pageRecords !=0:
                print('')
                print('%s rows returned, complete!' % len(tblRows))
                print('')
            else:
                print('')

        return

    # -----------------------------
    def do_scroll(self,arg):
        if os.path.exists(self.lastTableName):
            os.system('less -SR %s' % self.lastTableName)

    # -----------------------------
    def do_export(self,arg):
        '\nExports the json records that make up the selected entities for debugging, reloading, etc.' \
        '\n\nSyntax:' \
        '\n\texport <entity_id> <entity_id> ... to <fileName>' \
        '\n\texport search to <fileName>' \
        '\n\texport search top (n)> to <fileName>\n'
        if not argCheck('do_export', arg, self.do_export.__doc__):
            return

        fileName = None
        if type(arg) == str and 'TO' in arg.upper():
            fileName = arg[arg.upper().find('TO') + 2:].strip()
            arg = arg[:arg.upper().find('TO')].strip()

        if type(arg) == str and 'SEARCH' in arg.upper():
            lastToken = arg.split()[len(arg.split())-1]
            if lastToken.isdigit():
                entityList = self.lastSearchResult[:int(lastToken)]
            else:
                entityList = self.lastSearchResult
        else:
            try: 
                if ',' in arg:
                    entityList = list(map(int, arg.split(',')))
                else:
                    entityList = list(map(int, arg.split()))
            except:
                print('')
                print('error parsing argument [%s] into entity id numbers' % arg) 
                print('  expected comma or space delimited integers') 
                print('')
                return

        if not fileName:
            if len(entityList) == 1:
                fileName = str(entityList[0]) + '.json'
            else:
                fileName = 'records.json'
            
        try: f = open(fileName, 'w')
        except IOError as err:
            print('cannot write to %s - %s' % (fileName, err))
            return

        recordCount = 0
        for entityId in entityList:
            try:
                response = bytearray()
                retcode = g2Engine.getEntityByEntityID(int(entityId), response)
                response = response.decode() if response else ''
            except G2Exception as err:
                print(str(err))
            else:
                if len(response) == 0:
                    print('0 records found for %s' % entityId)
                else:

                    #--add related records lists for keylines and move record_id and entity_name back into json_data
                    resolvedData = json.loads(response)
                    for i in range(len(resolvedData['RESOLVED_ENTITY']['RECORDS'])):
                        f.write(json.dumps(resolvedData['RESOLVED_ENTITY']['RECORDS'][i]['JSON_DATA']) + '\n')
                        recordCount += 1
        f.close

        print('')
        print('%s records written to %s' % (recordCount, fileName))
        print('')

    # -----------------------------
    def getRecordList(self, table, field = None, value = None):

        recordList = []
        for i in range(len(self.cfgData['G2_CONFIG'][table])):
            if field and value:
                if self.cfgData['G2_CONFIG'][table][i][field] == value:
                    recordList.append(self.cfgData['G2_CONFIG'][table][i])
            else:
                recordList.append(self.cfgData['G2_CONFIG'][table][i])
        return recordList

    # -----------------------------
    def xx_listAttributes(self,arg):  #--disabled
        '\n\tlistAttributes\n'

        print('')
        for attrRecord in sorted(self.getRecordList('CFG_ATTR'), key = lambda k: k['ATTR_ID']):
            print(self.getAttributeJson(attrRecord))
        print('')

    # -----------------------------
    def getAttributeJson(self, attributeRecord):

        if 'ADVANCED' not in attributeRecord:
            attributeRecord['ADVANCED'] = 0
        if 'INTERNAL' not in attributeRecord:
            attributeRecord['INTERNAL'] = 0
            
        jsonString = '{'
        jsonString += '"id": "%s"' % attributeRecord['ATTR_ID']
        jsonString += ', "attribute": "%s"' % attributeRecord['ATTR_CODE']
        jsonString += ', "class": "%s"' % attributeRecord['ATTR_CLASS']
        jsonString += ', "feature": "%s"' % attributeRecord['FTYPE_CODE']
        jsonString += ', "element": "%s"' % attributeRecord['FELEM_CODE']
        jsonString += ', "required": "%s"' % attributeRecord['FELEM_REQ'].title()
        jsonString += ', "default": "%s"' % attributeRecord['DEFAULT_VALUE']
        jsonString += ', "advanced": "%s"' % ('Yes' if attributeRecord['ADVANCED'] == 1 else 'No') 
        jsonString += ', "internal": "%s"' % ('Yes' if attributeRecord['INTERNAL'] == 1 else 'No')
        jsonString += '}'
        
        return jsonString

    # -----------------------------
    def isInternalAttribute(self, attrStr):
        if ':' in attrStr:
            attrStr = attrStr.split(':')[0]
        attrRecords = self.getRecordList('CFG_ATTR', 'ATTR_CODE', attrStr.upper())
        if attrRecords and attrRecords[0]['INTERNAL'].upper().startswith('Y'):
            return True
        return False 

# ===== utility functions =====


def argCheck(func, arg, docstring):

    if len(arg.strip()) == 0:
        print('\nMissing argument(s) for %s, command syntax: %s \n' % (func, '\n\n' + docstring[1:]))
        return False
    else:
        return True

def argError(errorArg, error):

    printWithNewLines('Incorrect argument(s) or error parsing argument: %s' % errorArg, 'S')
    printWithNewLines('Error: %s' % error, 'E')

def fmtStatistic(amt):
    amt = int(amt)
    if amt > 1000000:
        return "{:,.2f}m".format(round(amt/1000000,2))
    else:
        return "{:,}".format(amt)

def pad(val, len):
    if type(val) != str:
        val = str(val)
    return (val + (' ' * len))[:len]

def lpad(val, len):
    if type(val) != str:
        val = str(val)
    return ((' ' * len) + val)[-len:]

def printWithNewLines(ln, pos=''):

    pos.upper()
    if pos == 'S' or pos == 'START' :
        print('\n' + ln)
    elif pos == 'E' or pos == 'END' :
        print(ln + '\n')
    elif pos == 'B' or pos == 'BOTH' :
        print('\n' + ln + '\n')
    else:
        print(ln)

def dictKeysUpper(dict):
    return {k.upper():v for k,v in dict.items()}

def showMeTheThings(data, loc=''):
    printWithNewLines('<---- DEBUG')
    printWithNewLines('Func: %s' % sys._getframe(1).f_code.co_name)
    if loc != '': printWithNewLines('Where: %s' % loc) 
    if type(data) == list:
        printWithNewLines(('[%s]\n' * len(data)) % tuple(data)) 
    else:
        printWithNewLines('Data: %s' % str(data))
    printWithNewLines('---->', 'E')

def removeFromHistory(idx = 0):
    if readline:
        if not idx:
            idx = readline.get_current_history_length()-1
        readline.remove_history_item(idx)

def _append_slash_if_dir(p):
    if p and os.path.isdir(p) and p[-1] != os.sep:
        return p + os.sep
    else:
        return p

def fuzzyCompare(ftypeCode, cfuncCode, str1, str2):

    if hasFuzzy and cfuncCode:
        if cfuncCode in ('GNR_COMP', 'ADDR_COMP', 'GROUP_ASSOCIATION_COMP'):
            closeEnough = fuzz.token_set_ratio(str1, str2) >= 80
        elif cfuncCode in ('DOB_COMP'):
            if len(str1) == len(str2):
                closeEnough = fuzz.token_set_ratio(str1, str2) >= 90
            else:
                closeEnough = str1[0:max(len(str1), len(str2))] == str2[0:max(len(str1), len(str2))]
        elif cfuncCode in ('SSN_COMP'):
            closeEnough = fuzz.token_set_ratio(str1, str2) >= 90
        elif cfuncCode in ('ID_COMP'):
            closeEnough = fuzz.ratio(str1, str2) >= 90
        elif cfuncCode in ('PHONE_COMP'):
            closeEnough = str1[-7:] == str2[-7:]
            #closeEnough = ''.join(i for 1 in str1 if i.isdigit())[-7:] == ''.join(i for i in str2 if i.isdigit())[-7:]
        else:
            closeEnough = str1 == str2
    else:
            closeEnough = str1 == str2
    return closeEnough

# ===== The main function =====
if __name__ == '__main__':
    appPath = os.path.dirname(os.path.abspath(sys.argv[0]))

    #--defaults
    iniFileName = int(os.getenv('SZ_INI_FILE_NAME')) if os.getenv('SZ_INI_FILE_NAME', None) else '/opt/senzing/g2/python/G2Module.ini'

    #--capture the command line arguments
    argParser = argparse.ArgumentParser()
    argParser.add_argument('-c', '--ini_file_name', dest='ini_file_name', default=iniFileName, help='name of the g2.ini file, defaults to %s' % iniFileName)
    argParser.add_argument('-s', '--snapshot_file_name', dest='snapshot_file_name', default=None, help='the name of a json statistics file computed by poc_snapshot.py')
    args = argParser.parse_args()
    iniFileName = args.ini_file_name
    snapShotFileName = args.snapshot_file_name

    #--validate snapshot file if specified
    if snapShotFileName and not os.path.exists(snapShotFileName):
        print('')
        print('Snapshot file %s not found!' % snapShotFileName)
        print('')
        sys.exit(1)

    #--get parameters from ini file
    if not os.path.exists(iniFileName):
        print('')
        print('ini file %s not found!' % iniFileName)
        print('')
        sys.exit(1)
    iniParser = configparser.ConfigParser()
    iniParser.read(iniFileName)
    try: g2dbUri = iniParser.get('SQL', 'CONNECTION')
    except: 
        print('')
        print('CONNECTION parameter not found in [SQL] section of the ini file')
        print('')
        sys.exit(1)

    try: configTableFile = iniParser.get('SQL', 'G2CONFIGFILE')
    except: 
        print('')
        print('G2CONFIGFILE parameter not found in [SQL] section of the ini file')
        print('')
        sys.exit(1)

    #--get the config
    try: cfgData = json.load(open(configTableFile), encoding="utf-8")
    except ValueError as e:
        print('')
        print('G2CONFIGFILE: %s has invalid json' % configTableFile)
        print(e)
        print('')
        sys.exit(1)
    except IOError as e:
        print('')
        print('G2CONFIGFILE: %s was not found' % configTableFile)
        print(e)
        print('')
        sys.exit(1)

    #--try to open the database
    g2Dbo = G2Database(g2dbUri)
    if not g2Dbo.success:
        print('')
        print('Could not connect to database')
        print('')
        sys.exit(1)

    #--try initialize and prime the g2engine
    try:
        g2Engine = G2Engine()
        g2Engine.init('poc_viewer', iniFileName, False)
    except G2Exception as err:
        print('')
        print('Could not initialize the G2 Engine')
        print(str(err))
        print('')
        sys.exit(1)

    #--python3 uses input, raw_input was removed
    userInput = input
    if sys.version_info[:2] <= (2,7):
        userInput = raw_input

    #--cmdloop()
    subprocess.Popen(["echo", "-ne", "\e[?7l"])  #--text wrapping off
    G2CmdShell().cmdloop()
    subprocess.Popen(["echo", "-ne", "\e[?7h"])  #--text wrapping on
    print('')

    try: g2Engine.destroy()
    except: pass
    try: g2Dbo.close()
    except: pass

    sys.exit()
