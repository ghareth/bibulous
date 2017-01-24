#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# pylint: disable-msg=C0321
# pylint: max-line-length=120
# pylint: max-module-lines=10000
# See the LICENSE.rst file for licensing information.


from __future__ import unicode_literals, print_function, division
from builtins import str as unicode
from builtins import range
from past.builtins import basestring

import re
import os
import sys
import codecs       ## for importing UTF8-encoded files
import locale       ## for language internationalization and localization
import getopt       ## for getting command-line options
import copy         ## for the "deepcopy" command
import platform     ## for determining the OS of the system
from pprint import pprint       # for debugging

import bibulous_tools as bibtools

class Bib(object):
    '''
    Bibdict is to hold bibliography database and can standalone from Bibulous.

    '''
    def __init__(self, disable= None):
        
        '''
        disable  :  list or None
        
        '''
        
        if disable != None:
            self.disable = disable
        else:
            self.disable = []
            
        
        self.data = {'preamble':''}
        
        self.anybrace_pattern = re.compile(r'(?<!\\)[{}]', re.UNICODE)
        self.anybraceorquote_pattern = re.compile(r'(?<!\\)[{}"]', re.UNICODE)
        self.abbrevkey_pattern = re.compile(r'(?<!\\)[,#]', re.UNICODE)
        self.integer_pattern = re.compile(r'^-?[0-9]+', re.UNICODE)
                
        self.abbrevs = {'jan':'1', 'feb':'2', 'mar':'3', 'apr':'4', 'may':'5', 'jun':'6',
                        'jul':'7', 'aug':'8', 'sep':'9', 'oct':'10', 'nov':'11', 'dec':'12'}
        
        
        
        self.searchkeys = []        ## when culling data, this is the list of keys to limit parsing to 
        
        self.filename = ''                      ## the current filename (for error messages)
        self.i = 0                              ## counter for line in file (for error messages)        
        
    def clear(self):
        
        self.data = {'preamble':''}
        
    ## =============================
    def parse_bibfile(self, filename, culldata = False, searchkeys = None, parse_only_entrykeys = False, options = None):
        '''
        Parse a ".bib" file to generate a dictionary representing a bibliography database.

        Parameters
        ----------
        filename : str
            The filename of the .bib file to parse.
        '''
        self.filename = filename
        self.culldata = culldata
        if searchkeys != None:
            self.searchkeys = searchkeys
        else:
            self.searchkeys = []
        if options != None:
            self.options = options
        else:
            self.options = {}
        self.parse_only_entrykeys = parse_only_entrykeys
        

        ## Need to use the "codecs" module to handle UTF8 encoding/decoding properly. Using mode='rU' with the common
        ## "open()" file function doesn't do this probperly, though I don't know why.
        
        filehandle = codecs.open(os.path.normpath(self.filename), 'r', 'utf-8')

        ## This next block parses the lines in the file into a dictionary. The tricky part here is that the BibTeX
        ## format allows for multiline entries. So we have to look for places where a line does not end in a comma, and
        ## check the following line to see if it a continuation of that line. Unfortunately, this means we need to read
        ## the whole file into memory --- not just one line at a time.
        entry_brace_level = 0

        ## The variable "entrystr" contains all of the contents of the entry between the entrytype definition "@____{"
        ## and the closing brace "}". Once we've obtained all of the (in general multiline) contents, then we hand them
        ## off to parse_bibentry() to format them.
        entrystr = ''
        entrytype = None
        self.i = 0           ## line number counter --- for error messages only
        entry_counter = 0
        abbrev_counter = 0

        for line in filehandle:
            self.i += 1

            ## Ignore empty and comment lines.
            if not line: continue
            if line.strip().startswith('%'): continue
            
            #Workaround for bug in Papers3 that includes a stray backslash when using ampersands      
            line = line.replace(r'\{\&}',r'{\&}')
        
            #Workaround for bug in Papers3 that exports BibTeX with non-escaped percentage signs
            percent = re.compile (r'(?<!\\)%', re.UNICODE)
            line = re.sub(percent, r"\%", line)               
            
            if line.startswith('}') and entry_brace_level == 1:
                ## If a line *starts* with a closing brace, then assume the intent is to close the current entry.
                entry_brace_level = 0
                self.parse_bibentry(entrystr, entrytype)       ## close out the entry
                if (entrytype.lower() == 'string'):
                    abbrev_counter += 1
                elif (entrytype.lower() not in ('preamble','acronym')):
                    entry_counter += 1
                entrystr = ''
                if (line[1:].strip() != ''):
                    bibtools.warning('Warning 001a: line#' + unicode(self.i) + ' of "' + self.filename + '" has data outside'
                          ' of an entry {...} block. Skipping all contents until the next entry ...', self.disable)
                continue

            ## Don't strip off leading and ending whitespace until after checking if '}' begins a line (as in the block
            ## above).
            line = line.strip()

            if line.startswith('@'):
                brace_idx = line.find('{')             ## assume a form like "@ENTRYTYPE{"
                if (brace_idx == -1):
                    bibtools.warning('Warning 002a: open brace not found for the entry beginning on line#' + \
                         unicode(self.i) + ' of "' + self.filename + '". Skipping to next entry ...',
                         self.disable)
                    entry_brace_level = 0
                    continue
                entrytype = line[1:brace_idx].lower().strip()   ## extract string between "@" and "{"
                line = line[brace_idx+1:]
                entry_brace_level = 1

            ## If we are not currently inside an active entry, then skip the line and wait until the the next entry.
            if (entry_brace_level == 0):
                if (line.strip() != ''):
                    bibtools.warning('Warning 001b: line#' + unicode(self.i) + ' of "' + self.filename + '" has data ' + \
                                'outside of an entry {...} block. Skipping all contents until the next entry ...',
                                self.disable)
                continue

            ## Look if the entry ends with this line. If so, append it to "entrystr" and call the entry parser. If not,
            ## then simply append to the string and continue.
            endpos = len(line)

            for match in re.finditer(self.anybrace_pattern, line):
                if (match.group(0)[-1] == '}'):
                    entry_brace_level -= 1
                elif (match.group(0)[-1] == '{'):
                    entry_brace_level += 1
                if (entry_brace_level == 0):
                    ## If we've found the final brace, then check if there is anything after it.
                    if (line[match.end():].strip() != ''):
                        bibtools.warning('Warning 002b: line#' + unicode(self.i) + ' of "' + self.filename + \
                             '" has data outside of an entry {...} block. Skipping all ' + \
                             'contents until the next entry ...', self.disable)
                    endpos = match.end()
                    break

            ## If we have returned to brace level 0, then finish appending the contents and send the entire set to the
            ## parser.
            if (entry_brace_level == 0):
                entrystr += line[:endpos-1]      ## the "-1" here to remove the final closing brace
                self.parse_bibentry(entrystr, entrytype)
                if (entrytype.lower() == 'string'):
                    abbrev_counter += 1
                elif (entrytype.lower() not in ('preamble','acronym')):
                    entry_counter += 1
                entrystr = ''
            else:
                entrystr += line[:endpos] + '\n'

        filehandle.close()

        print('Found %i entries and %i abbrevs in %s' % (entry_counter, abbrev_counter, filename))
        #print('    Bibdata now has %i keys' % (len(self.data) - 1))

        return

    ## =============================
    def parse_bibentry(self, entrystr, entrytype):
        '''
        Given a string representing the entire contents of the BibTeX-format bibliography entry, parse the contents and
        place them into the bibliography preamble string, the set of abbreviations, and the bibliography database
        dictionary.

        Parameters
        ----------
        entrystr : str
            The string containing the entire contents of the bibliography entry.
        entrytype : str
            The type of entry (`article`, `preamble`, etc.).
        '''

        if not entrystr:
            return

        if (entrytype == 'comment'):
            pass
        elif (entrytype == 'preamble'):
            ## In order to use the same "parse_bibfield()" function as all the other options, add a fake key onto the
            ## front of the string before calling "parse_bibfield()".
            fd = self.parse_bibfield('fakekey = ' + entrystr)
            if fd: self.data['preamble'] += '\n' + fd['fakekey']
        elif (entrytype == 'string'):
            fd = self.parse_bibfield(entrystr)
            for fdkey in fd:
                if (fdkey in self.abbrevs):
                    bibtools.warning('Warning 032a: line#' + unicode(self.i) + ' of "' + self.filename +
                                ': the abbreviation "' + fdkey + '" = "' + self.abbrevs[fdkey] + '" is being '
                                'overwritten as "' + fdkey + '" = "' + fd[fdkey] + '"', self.disable)
            if fd: self.abbrevs.update(fd)
        elif (entrytype == 'acronym'):
            ## Acronym entrytypes have an identical form to "string" types, but we map them into a dictionary like a
            ## regular field, so we can access them as regular database entries.
            fd = self.parse_bibfield(entrystr)
            entrykey = list(fd)[0]
            newentry = {'name':entrykey, 'description':fd[entrykey], 'entrytype':'acronym'}
            if (entrykey in self.data):
                bibtools.warning('Warning 032b: line#' + unicode(self.i) + ' of "' + self.filename +
                            ': the acronym "' + entrykey + '" = "' + self.data[entrykey] + '" is being '
                            'overwritten as "' + entrykey + '" = "' + fd[entrykey] + '"', self.disable)
            if fd: self.data[entrykey] = newentry
        else:
            ## First get the entry key. Then send the remainder of the entry string to the parser.
            idx = entrystr.find(',')
            if (idx == -1) and ('\n' not in entrystr):
                bibtools.warning('Warning 035: the entry starting on line #' + unicode(self.i) + ' of file "' + \
                     self.filename + '" provides only an entry key ("' + entrystr + '" and no item contents.', \
                     self.disable)
            elif (idx == -1):
                bibtools.warning('Warning 003: the entry ending on line #' + unicode(self.i) + ' of file "' + \
                     self.filename + '" is does not have an "," for defining the entry key. '
                     'Skipping ...', self.disable)
                return(fd)

            ## Get the entry key. If we are culling the database (self.culldata == True) and the entry key is not among
            ## the citation keys, then exit --- we don't need to add this to the database.
            entrykey = entrystr[:idx].strip()

            ## If the entry is not among the list of keys to parse, then don't bother. Skip to the next entry to save
            ## time.
            if self.culldata and self.searchkeys and (entrykey not in self.searchkeys):
                return

            entrystr = entrystr[idx+1:]

            if not entrykey:
                bibtools.warning('Warning 004a: the entry ending on line #' + unicode(self.i) + ' of file "' + \
                     self.filename + '" has an empty key. Ignoring and continuing ...', self.disable)
                return
            elif (entrykey in self.data):
                bibtools.warning('Warning 004b: the entry ending on line #' + unicode(self.i) + ' of file "' + \
                     self.filename + '" has the same key ("' + entrykey + '") as a previous ' + \
                     'entry. Overwriting the entry and continuing ...', self.disable)

            ## Create the dictionary for the database entry. Add the entrytype and entrykey. The latter is primarily
            ## useful for debugging, so we don't have to send the key separately from the entry itself.
            preexists = (entrykey in self.data)
            self.data[entrykey] = {}
            self.data[entrykey]['entrytype'] = entrytype
            self.data[entrykey]['entrykey'] = entrykey

            if not self.parse_only_entrykeys:
                fd = self.parse_bibfield(entrystr, entrykey)
                if preexists:
                    bibtools.warning('Warning 032c: line#' + unicode(self.i) + ' of "' + self.filename + ': the entry "' +
                                entrykey + '" is being overwritten with a new definition', self.disable)
                if fd: self.data[entrykey].update(fd)

        return

    ## =============================
    def parse_bibfield(self, entrystr, entrykey=''):
        '''
        For a given string representing the raw contents of a BibTeX-format bibliography entry, parse the contents into
        a dictionary of key:value pairs corresponding to the field names and field values.

        Parameters
        ----------
        entrystr : str
            The string containing the entire contents of the bibliography entry.
        entrykey : str
            The key of the bibliography entry being parsed (useful for error messages).

        Returns
        -------
        fd : dict
            The dictionary of "field name" and "field value" pairs.
        '''

        entrystr = entrystr.strip()
        fd = {}             ## the dictionary for holding key:value string pairs

        while entrystr:
            ## First locate the field key.
            idx = entrystr.find('=')
            if (idx == -1):
                bibtools.warning('Warning 005: the entry ending on line #' + unicode(self.i) + ' of file "' + \
                     self.filename + '" is an abbreviation-type entry but does not have an "=" '
                     'for defining the end of the abbreviation key. Skipping ...', self.disable)
                return(fd)

            fieldkey = entrystr[:idx].strip()
            if (fieldkey in fd):
                bibtools.warning('Warning 033: line#' + unicode(self.i) + ' of "' + self.filename + ': the "' + fieldkey +
                            '" field of entry "' + entrykey + '" is duplicated', self.disable)

            fieldstr = entrystr[idx+1:].strip()

            if not self.options['case_sensitive_field_names']:
                fieldkey = fieldkey.lower()

            if not fieldstr:
                entrystr = ''
                continue

            ## Next we go through the field contents, which may involve concatenating. When we reach the end of an
            ## individual field, we return the "result string" and truncate the entry string to remove the part we just
            ## finished parsing.
            resultstr = ''
            while fieldstr:
                firstchar = fieldstr[0]

                if (firstchar == ','):
                    ## Reached the end of the field, truncate the entry string return to the outer loop over fields.
                    fd[fieldkey] = resultstr
                    entrystr = fieldstr[1:].strip()
                    break
                elif (firstchar == '#'):
                    ## Reached a concatenation operator. Just skip it.
                    fieldstr = fieldstr[1:].strip()
                elif (firstchar == '"'):
                    ## Search for the content string that resolves the double-quote delimiter. Once you've found the
                    ## end delimiter, append the content string to the result string.
                    endpos = len(fieldstr)
                    entry_brace_level = 0
                    for match in re.finditer(self.anybraceorquote_pattern, fieldstr[1:]):
                        if (match.group(0)[-1] == '}'):
                            entry_brace_level -= 1
                        elif (match.group(0)[-1] == '{'):
                            entry_brace_level += 1
                        if (match.group(0)[-1] == '"') and (entry_brace_level == 0):
                            endpos = match.end()
                            break
                    resultstr += ' ' + fieldstr[1:endpos]
                    fieldstr = fieldstr[endpos+1:].strip()
                    if not fieldstr: entrystr = ''
                elif (firstchar == '{'):
                    ## Search for the endbrace that resolves the brace level. Once you've found it, add the intervening
                    ## contents to the result string.
                    endpos = len(fieldstr)
                    entry_brace_level = 1
                    for match in re.finditer(self.anybrace_pattern, fieldstr[1:]):
                        if (match.group(0)[-1] == '}'):
                            entry_brace_level -= 1
                        elif (match.group(0)[-1] == '{'):
                            entry_brace_level += 1
                        if (entry_brace_level == 0):
                            endpos = match.end()
                            break
                    resultstr += ' ' + fieldstr[1:endpos]
                    fieldstr = fieldstr[endpos+1:].strip()
                    if not fieldstr: entrystr = ''
                else:
                    ## If the fieldstr doesn't begin with '"' or '{' or '#', then the next set of characters must be an
                    ## abbreviation key. An abbrev key ends with a whitespace followed by either '#' or ',' (or the end
                    ## of the field). Anything else is a syntax error.
                    endpos = len(fieldstr)
                    end_of_field = False

                    ## The "abbrevkey_pattern" searches for the first '#' or ',' that is not preceded by a backslash. If
                    ## this pattern is found, then we've found the *end* of the abbreviation key.
                    if not re.search(self.abbrevkey_pattern, fieldstr):
                        ## If the "abbrevkey" is an integer, then it's not actually an abbreviation. Convert it to a
                        ## string and insert the number itself.
                        abbrevkey = fieldstr
                        if re.match(self.integer_pattern, abbrevkey):
                            resultstr += unicode(abbrevkey)
                        else:
                            if abbrevkey in self.abbrevs:
                                resultstr += self.abbrevs[abbrevkey].strip()
                            else:
                                bibtools.warning('Warning 006: for the entry ending on line #' + unicode(self.i) + \
                                    ' of file "' + self.filename + '", cannot find the abbreviation key "' +
                                    abbrevkey + '". Skipping ...', self.disable)
                                resultstr = self.options['undefstr']
                        fieldstr = ''
                        end_of_field = True
                    else:
                        (fieldstr, resultstr, end_of_field) = self.replace_abbrevs_with_full(fieldstr, resultstr)

                    ## Since we found the comma at the end of this field's contents, we break here to return to the loop
                    ## over fields.
                    if end_of_field:
                        entrystr = fieldstr.strip()
                        break

            ## Strip off any unnecessary white space and remove any newlines.
            resultstr = resultstr.strip().replace('\n',' ')

            ## Having braces around quotes can cause problems when parsing nested quotes, and do not provide any
            ## additional functionality.
            if ('{"}') in resultstr:
                resultstr = resultstr.replace('{"}', '"')
            if ("{'}") in resultstr:
                resultstr = resultstr.replace("{'}", "'")
            if ('{`}') in resultstr:
                resultstr = resultstr.replace('{`}', '`')

            fd[fieldkey] = resultstr

            ## If the field defines a cross-reference, then add it to the "searchkeys", so that when we are culling the
            ## database for faster parsing, we do not ignore the cross-referenced entries.
            if (fieldkey == 'crossref'):
                self.searchkeys.append(resultstr)

        return(fd)

    ## =============================
    def replace_abbrevs_with_full(self, fieldstr, resultstr):
        '''
        Given an input str, locate the abbreviation key within it and replace the abbreviation with its full form.

        Once the abbreviation key is found, remove it from the "fieldstr" and add the full form to the "resultstr".

        Parameters
        ==========
        fieldstr : str
            The string to search for the abbrevation key.
        resultstr : str
            The thing to hold the abbreviation's full form. (Note that it might not be empty on input.)

        Returns
        =======
        fieldstr : str
            The string to search for the abbrevation key.
        resultstr : str
            The thing to hold the abbreviation's full form.
        end_of_field : bool
            Whether the abbreviation key was at the end of the current field.
        '''

        end_of_field = False

        ## The "abbrevkey_pattern" seaerches for the first '#' or ',' that is not preceded by a backslash. If this
        ## pattern is found, then we've found the *end* of the abbreviation key.
        for match in re.finditer(self.abbrevkey_pattern, fieldstr):
            endpos = match.end()
            if (match.group(0)[0] == '#'):
                abbrevkey = fieldstr[:endpos-1].strip()
                ## If the "abbreviation" is an integer, then it's not an abbreviation but rather a number, and just
                ## return it as-is.
                if abbrevkey.isdigit() or not self.options['use_abbrevs']:
                    resultstr += unicode(abbrevkey)
                elif (abbrevkey not in self.abbrevs):
                    bibtools.warning('Warning 016a: for the entry ending on line #' + unicode(self.i) + ' of file "' + \
                         self.filename + '", cannot find the abbreviation key "' + abbrevkey + '". Skipping ...',
                         self.disable)
                    resultstr += self.options['undefstr']
                else:
                    resultstr += self.abbrevs[abbrevkey].strip()
                fieldstr = fieldstr[endpos+1:].strip()
                break
            elif (match.group(0)[0] == ','):
                abbrevkey = fieldstr[:endpos-1].strip()
                ## If the "abbreviation" is an integer, then it's not an abbreviation
                ## but rather a number, and just return it as-is.
                if abbrevkey.isdigit() or not self.options['use_abbrevs']:
                    resultstr += unicode(abbrevkey)
                elif (abbrevkey not in self.abbrevs):
                    bibtools.warning('Warning 016b: for the entry ending on line #' + unicode(self.i) + ' of file "' + \
                         self.filename + '", cannot find the abbreviation key "' + abbrevkey + '". Skipping ...',
                         self.disable)
                    resultstr += self.options['undefstr']
                else:
                    resultstr += self.abbrevs[abbrevkey].strip()

                fieldstr = fieldstr[endpos+1:].strip()
                end_of_field = True
                break
            else:
                raise SyntaxError('if-else mismatch inside replace_abbrevs_with_full().')

        return(fieldstr, resultstr, end_of_field)

if (__name__ == '__main__'):
    print('sys.argv=', sys.argv)
    
    if (len(sys.argv) > 1):
        try:
            (opts, args) = getopt.getopt(sys.argv[1:], '', ['locale='])
        except getopt.GetoptError as err:
            ## Print help information and exit.
            print(err)              ## this will print something like "option -a not recognized"
            print('Bibulous can be called with')
            print('    bibulous.py myfile.aux --locale=mylocale')
            print('where "locale" is an optional variable.')
            sys.exit(2)

        for o,a in opts:
            if (o == '--locale'):
                uselocale = a
            else:
                assert False, "unhandled option"

        arg_bibfile = args[0]
    else:
        ## Use the test example input.
        arg_bibfile = './test/underscore.bib'
        
    main_bibdata = Bib()
    main_bibdata.parse_bibfile(arg_bibfile, culldata=False , searchkeys=None , 
                              parse_only_entrykeys=False , 
                              options=bibtools.default_options )
    print('DONE')
    
    print(main_bibdata.data['icpp-mpi-atomicity']['url'])