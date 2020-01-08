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

from bibulous_tools import get_delim_levels
from bibulous_tools import get_variable_name_elements


## =============================

class Bst(object):
    
    def __init__(self, disable= None, debug = False):
    
        '''
            disable  :  list or None
    
            '''
        if disable != None:
            self.disable = disable
        else:
            self.disable = []
        
        self.debug = debug
            
            
        self.bstdict = {}           ## the dictionary containing all information from template files
        
        self.filename = ''                      ## the current filename (for error messages)
        self.i = 0                              ## counter for line in file (for error messages)
        
        
    
    def parse_bstfile(self, filename,
                      options = None,
                      specials = None,
                      specials_list = None,
                      user_script = '',
                      user_variables = None,
                      nested_templates = None,
                      looped_templates = None,
                      namelists = None,
                      implicitly_indexed_vars = ['authorname','editorname']):                     
        
        '''
        Convert a Bibulous-type bibliography style template into a dictionary.
    
        The resulting dictionary consists of keys which are the various entrytypes, and values which are the template
        strings. In addition, any formatting options are stored in the "options" key as a dictionary of
        option_name:option_value pairs.
    
        Parameters
        ----------
        filename : str
            The filename of the Bibulous style template to use.
        '''
    
        self.filename = filename
        
        self.options = options if options != None else {} 
        self.specials = specials if specials != None else copy.deepcopy(bibtools.default_specials)
        self.specials_list = specials_list if specials_list != None else []
        self.user_script = user_script
        self.user_variables = user_variables if user_variables !=None else {}
        self.nested_templates = nested_templates if nested_templates != None else []
        self.looped_templates = looped_templates if looped_templates != None else {}
        self.namelists = namelists if namelists != None else []
        self.implicitly_indexed_vars = implicitly_indexed_vars

        filehandle = codecs.open(os.path.normpath(filename), 'r', 'utf-8')
    
        ## For the "definition_pattern", rather than matching the initial string up to the first whitespace character,
        ## we match a whitespace-equals-whitespace
        definition_pattern = re.compile(r'\s=\s', re.UNICODE)
        section = 'TEMPLATES'
        continuation = False        ## whether the current line is a continuation of the previous
        abort_script = False        ## if an unsafe object is being used, abort the user_script eval
    
        for i,line in enumerate(filehandle):
            ## Ignore any comment lines, and remove any comments from data lines.
            if line.startswith('#'): continue
            if ('#' in line):
                idx = line.index('#')
                line = line[:idx]
                if not line.strip(): continue       ## if the line contained only a comment
    
            if ('EXECUTE {' in line) or ('EXECUTE{' in line) or ('FUNCTION {' in line):
                raise ImportError('The style template file "' + filename + '" appears to be BibTeX format, not '
                                  'Bibulous. Aborting...')
    
            if line.strip().startswith('TEMPLATES:'):
                section = 'TEMPLATES'
                continuation = False
                continue
            elif line.strip().startswith('SPECIAL-TEMPLATES:'):
                section = 'SPECIAL-TEMPLATES'
                continuation = False
                continue
            elif line.strip().startswith('OPTIONS:'):
                section = 'OPTIONS'
                continuation = False
                continue
            elif line.strip().startswith('DEFINITIONS:'):
                section = 'DEFINITIONS'
                continuation = False
                continue
            elif line.strip().startswith('VARIABLES:'):
                section = 'VARIABLES'
                continuation = False
                continue
    
            if (section == 'DEFINITIONS'):
                if ('__' in line):
                    bibtools.warning('Warning 026a: Python script line #' + str(i) + ' of file "' + filename + '" contains'\
                         ' an invalid use of "__".\nAborting script evaluation ...', self.disable)
                    abort_script = True
                if re.search(r'\sos.\S', line, re.UNICODE):
                    bibtools.warning('Warning 026b: Python script line #' + str(i) + ' of file "' + filename + '" contains'\
                         ' an invalid call to the "os" module.\nAborting script evaluation ...', self.disable)
                    abort_script = True
                if re.search(r'\ssys.\S', line, re.UNICODE):
                    bibtools.warning('Warning 026c: Python script line #' + str(i) + ' of file "' + filename + '" contains'\
                         ' an invalid call to the "sys" module.\nAborting script evaluation ...', self.disable)
                    abort_script = True
                if re.search(r'\scodecs.\S', line, re.UNICODE):
                    bibtools.warning('Warning 026c: Python script line #' + str(i) + ' of file "' + filename + '" contains'\
                         ' an invalid call to the "codecs" module.\nAborting script evaluation ...', self.disable)
                    abort_script = True
                if re.search(r'^import\s', line, re.UNICODE):
                    bibtools.warning('Warning 026d: Python script line #' + str(i) + ' of file "' + filename + '" contains'\
                         ' an invalid call to "import".\nAborting script evaluation ...', self.disable)
                    abort_script = True
                if re.search(r'^import\s', line, re.UNICODE):
                    bibtools.warning('Warning 026e: Python script line #' + str(i) + ' of file "' + filename + '" contains'\
                         ' an invalid call to the "open()" function.\nAborting script evaluation ...', self.disable)
                    abort_script = True
    
                self.user_script[0] += line
                if self.debug: print('Adding a line to the BST scripting string: ' + line, end='')
    
            line = line.strip()
    
            if (section == 'VARIABLES'):
                if not line: continue
                matchobj = re.search(definition_pattern, line)
                if (matchobj == None):
                    bibtools.warning('Warning 008a: line #' + str(i) + ' of file "' + filename + '" does not contain' + \
                         ' a valid variable definition.\n Skipping ...', self.disable)
                    continue
                (start,end) = matchobj.span()
                var = line[:start].strip()
                value = line[end:].strip()
                self.user_variables[var] = filter_script(value)
                if self.debug:
                    print('Adding user variable "' + var + '" with value "' + value + '" ...')
            elif (section in ('TEMPLATES','OPTIONS','SPECIAL-TEMPLATES')):
                ## Skip empty lines. It is tempting to put this line above here, but resist the temptation -- putting
                ## it higher above would remove empty lines from the Python scripts in the DEFINITIONS section, which
                ## would make troubleshooting those more difficult.
                if not line: continue
                if not continuation:
                    ## If the line ends with an ellipsis, then remove the ellipsis and set continuation to True.
                    if line.endswith('...'):
                        line = line[:-3].strip()
                        continuation = True
    
                    matchobj = re.search(definition_pattern, line)
                    if (matchobj == None):
                        bibtools.warning('Warning 008b: line #' + str(i) + ' of file "' + filename + '" does not contain' +\
                             ' a valid variable definition.\n Skipping ...', self.disable)
                        continue
    
                    (start,end) = matchobj.span()
                    var = line[:start].strip()
                    value = line[end:].strip()
                else:
                    ## If the line ends with an ellpsis, then remove the ellipsis and set continuation to True.
                    if line.endswith('...'):
                        line = line[:-3].strip()
                        continuation = True
                    else:
                        continuation = False
    
                    value += line.strip()
    
                if (section == 'TEMPLATES'):
                    ## The line defines an entrytype template. Check whether this definition is overwriting an already
                    ## existing definition.
                    if (var in self.bstdict) and (self.bstdict[var] != value):
                        bibtools.warning('Warning 009a: overwriting the existing template variable "' + var + \
                             '" from [' + self.bstdict[var] + '] to [' + value + '] ...', self.disable)
                    self.bstdict[var] = value
    
                    ## Find out if the template has nested option blocks. If so, then add it to
                    ## the list of nested templates.
                    levels = get_delim_levels(value, ('[',']'))
                    if (2 in levels) and (var not in self.nested_templates):
                        self.nested_templates.append(var)
    
                    ## Find out if the template contains an implicit loop (an ellipsis not at the end of a line). If
                    ## so then add it to the list of looped templates.
                    if ('...' in value.strip()[:-3]) and (var not in self.looped_templates):
                        loop_data = get_implicit_loop_data(value)
                        self.looped_templates[var] = loop_data
    
                    if self.debug:
                        print('Setting BST entrytype template "' + var + '" to value "' + value + '"')
    
                elif (section == 'OPTIONS'):
                    ## The variable defines an option rather than an entrytype. Check whether this definition is
                    ## overwriting an already existing definition.
                    if (var in self.options) and (str(self.options[var]) != value):\
                        bibtools.warning('Warning 009b: overwriting the existing template option "' + var + '" from [' + \
                             unicode(self.options[var]) + '] to [' + unicode(value) + '] ...', self.disable)
                    ## If the value is numeric or bool, then convert the datatype from string.
                    if self.debug:
                        print('Setting BST option "' + var + '" to value "' + value + '"')
    
                    if value.isdigit():
                        value = int(value)
                    elif (value in ('True','False')):
                        value = (value == 'True')
    
                    if (var == 'name_separator') and (value == ''):
                        value = ' '
    
                    self.options[var] = value
    
                elif (section == 'SPECIAL-TEMPLATES'):
                    ## The line defines an entrytype template. Check whether this definition is overwriting an already
                    ## existing definition.
                    if (var in self.specials) and (self.specials[var] != value):
                        bibtools.warning('Warning 009c: overwriting the existing special template variable "' + var + \
                             '" from [' + self.specials[var] + '] to [' + value + '] ...', self.disable)
                    self.specials[var] = value
                    if (var not in self.specials_list):
                        self.specials_list.append(var)
    
                    if ('.to_namelist()>' in value):
                        self.namelists.append(var)
    
                    ## Find out if the template has nested option blocks. If so, then add it to
                    ## the list of nested templates.
                    levels = get_delim_levels(value, ('[',']'))
                    if not levels:
                        bibtools.warning('Warning 036: the style template for entrytype "' + var + '" has unbalanced ' + \
                                    'square brackets. Skipping ...', self.disable)
                        self.specials[var] = ''
    
                    if (2 in levels) and (var not in self.nested_templates):
                        self.nested_templates.append(var)
    
                    ## Find out if the template contains an implicit loop (an ellipsis not at the end of a line). If
                    ## so then add it to the list of looped templates.
                    if ('...' in value.strip()[:-3]) and (var not in self.looped_templates):
                        loop_data = get_implicit_loop_data(value)
                        self.looped_templates[var] = loop_data
    
                    ## Find out if the template contains an implicit index. If so then add it to the list of such.
                    if re.search('\.n\.', value) or re.search('\.n>', value):
                        (varname,_) = var.split('.',1)
                        if (varname not in self.implicitly_indexed_vars):
                            self.implicitly_indexed_vars.append(varname)
    
                    if self.debug:
                        print('Setting BST special template "' + var + '" to value "' + value + '"')
    
        filehandle.close()
    
        if abort_script:
            self.user_script = ['']
    
        ## The "terse_inits" options has to override the "period_after_initial" option.
        if ('terse_inits' in self.options) and  self.options['terse_inits']:
            self.options['period_after_initial'] = False
    
        ## Next check to see whether any of the template definitions are simply maps to one of the other definitions.
        ## For example, one BST file may have a line of the form
        ##      inbook = incollection
        ## which implies that the template for "inbook" should be mapped to the same template as defined for the
        ## "incollection" entrytype.
        for key in self.bstdict:
            nwords = len(re.findall(r'\w+', self.bstdict[key]))
            if (nwords == 1) and ('<' not in self.bstdict[key]):
                self.bstdict[key] = self.bstdict[self.bstdict[key]]
    
        ## If the user defined any functions, then we want to evaluate them in a way such that they are available in
        ## other functions.
        
        #if self.user_script and self.options['allow_scripts']:
            #if self.debug:
                #print('Evaluating the user script:\n' + 'v'*50 + '\n' + self.user_script + '^'*50 + '\n')
            #exec(self.user_script, globals())
    
        ## Next validate all of the template strings to check for formatting errors.
        bad_templates = []
        for key in self.bstdict:
            okay = self.validate_templatestr(self.bstdict[key], key)
            if not okay:
                bad_templates.append(key)
    
        for bad in bad_templates:
            self.bstdict[bad] = 'Error: malformed template.'
    
        ## The "special templates" have to be treated differently, since we can't just replace the template with the
        ## "malformed template" message. If the template is not okay, then validate_templatestr() will emit a warning
        ## message. If not okay, then replace the offending template with self.options['undefstr'].
        for key in self.specials:
            okay = self.validate_templatestr(self.specials[key], key)
            if not okay: self.specials[key] = self.options['undefstr']
    
        if self.debug:
            ## When displaying the BST dictionary, show it in sorted form.
            for key in sorted(self.bstdict, key=self.bstdict.get, cmp=locale.strcoll):
                print('entrytype.' + key + ': ' + unicode(self.bstdict[key]))
            for key in sorted(self.options, key=self.options.get):
                print('options.' + key + ': ' + unicode(self.options[key]))
            for key in sorted(self.specials, key=self.specials.get):
                print('specials.' + key + ': ' + unicode(self.specials[key]))
       

        return
    
    #def get_user_script(self):
        #return self.user_script
    
## =============================
    def validate_templatestr(self, templatestr, key):
        '''
        Validate the template string so that it contains no formatting errors.

        Parameters
        ----------
        templatestr : str
            The template string to be validated.
        key : str
            The name of the variable that uses this template.

        Returns
        -------
        okay : bool
            Whether or not the template is properly formatted.
        '''

        okay = True

        ## Make sure that there are the same number of open as closed brackets.
        num_obrackets = templatestr.count('[')
        num_cbrackets = templatestr.count(']')
        if (num_obrackets != num_cbrackets):
            msg = 'In the template for "' + key + '" there are ' + unicode(num_obrackets) + \
                  ' open brackets "[", but ' + unicode(num_cbrackets) + ' close brackets "]" in the formatting string'
            bibtools.warning('Warning 012: ' + msg, self.disable)
            okay = False

        ## Check that no ']' appears before a '['.
        levels = get_delim_levels(templatestr, ('[',']'))
        if (-1 in levels):
            msg = 'A closed bracket "]" occurs before a corresponding open bracket "[" in the ' + \
                  'template string "' + templatestr + '"'
            bibtools.warning('Warning 027: ' + msg, self.disable)
            okay = False

        ## Finally, check that no '[', ']', or '|' appear inside a variable name.
        variables = re.findall(r'<.*?>', templatestr)
        for var in variables:
            if ('[' in var):
                msg = 'An invalid "[" character appears inside the template variable "' + var + '"'
                bibtools.warning('Warning 028a: ' + msg, self.disable)
                okay = False
            if (']' in var):
                msg = 'An invalid "]" character appears inside the template variable "' + var + '"'
                bibtools.warning('Warning 028b: ' + msg, self.disable)
                okay = False
            if ('|' in var):
                msg = 'An invalid "|" character appears inside the template variable "' + var + '"'
                bibtools.warning('Warning 028c: ' + msg, self.disable)
                okay = False
            if ('<' in var[1:-1]):
                msg = 'An invalid "<" character appears inside the template variable "' + var + '"'
                bibtools.warning('Warning 028d: ' + msg, self.disable)
                okay = False

        return(okay)

## =============================
def get_implicit_loop_data(templatestr):
    '''
    From a template containing an implicit loop ('...' notation), build a full-size template without an ellipsis.

    Right now, the code only allows one implicit loop in any given template.

    Parameters
    ----------
    templatestr : str
        The input template string (containing the implicit loop ellipsis notation).

    Returns
    -------
    loop_data : dict
        A dictionary containing all of the information needed to build a loop for a template.

    '''

    idx = templatestr.find('...')
    lhs = templatestr[:idx]
    rhs = templatestr[idx+3:]

    ## In the string to the left of the ellipsis, look for the template variable farthest to the right. Note that
    ## we can't just set "lhs_var = lhs_variables[-1]" because we need to know the *position* of the variable and
    ## not just the variable name. And if the name occurs more than once in the template, then we can't easily get
    ## the position from the name. Thus, we iterate through the string until we encounter the last match, and
    ## return that.
    match = re.search(r'<.*?>', lhs)
    if not match:
        msg = 'Warning 030a: the template string "' + templatestr + '" is malformed. It does not have a ' + \
              'template variable to the left of the ellipsis (implied loop).'
        bibtools.warning(msg)
        return(None)

    for i,match in enumerate(re.finditer(r'<.*?>', lhs)):
        if (i > 1):
            msg = 'Warning 030b: the template string "' + templatestr + '" is malformed. Only one variable is allowed ' + \
                  'but the template has more than one.'
            bibtools.warning(msg)
        lhs_span = match.span()
    lhs_var = match.group()

    ## Get the part of the template that goes before the implicit loop.
    before_loop_stuff = lhs[:lhs_span[0]]

    ## "get_variable_name_elements()" returns a dictionary with keys "index", "name", "prefix", and "suffix".
    lhs_var_dict = get_variable_name_elements(lhs_var[1:-1])

    ## Now that we have the info about the LHS variable, let's also find out the "glue" string that needs to be
    ## inserted between all of the loop elements.
    lhs_glue = lhs[lhs_span[1]:]

    ## In the string to the right of the ellipsis, look for the template variable farthest to the right.
    match = re.search(r'<.*?>', rhs)
    if not match:
        msg = 'Warning 030c: the template string "' + templatestr + '" is malformed. It does not have a ' + \
              'template variable to the right of the ellipsis (implied loop).'
        bibtools.warning(msg)
        return(None)

    rhs_span = match.span()
    rhs_var = match.group()
    rhs_var_dict = get_variable_name_elements(rhs_var[1:-1])

    if (rhs_var_dict['name'] != lhs_var_dict['name']) or (rhs_var_dict['prefix'] != lhs_var_dict['prefix']) or \
            (rhs_var_dict['suffix'] != lhs_var_dict['suffix']):
        msg = 'Warning 030d: the template string "' + templatestr + '" is malformed. The LHS variable "' + \
              lhs_var + '" is not the same as the RHS variable "' + rhs_var + '".'
        bibtools.warning(msg)

    ## Get the RHS "glue" element. If it has curly braces in it, then we differentiate the conditions between when
    ## the number of names is only two (then use only the stuff inside the curly braces) and more than two (then
    ## use all of the glue). In both cases, remove the first and last curly braces before applying the glue.
    rhs_glue = rhs[0:rhs_span[0]]
    if re.search(r'\{.*?\}', rhs_glue):
        glue_start = rhs_glue.find('{')
        glue_end = rhs_glue.rfind('}')
        last_glue_if_only_two = rhs_glue[glue_start+1:glue_end]
        last_glue = rhs_glue[:glue_start] + rhs_glue[glue_start+1:glue_end] + rhs_glue[glue_end+1:]
    else:
        last_glue_if_only_two = rhs_glue
        last_glue = rhs_glue

    ## Get the part of the template that goes after the implicit loop.
    after_loop_stuff = rhs[rhs_span[1]:]

    loop_data = {}
    loop_data['varname'] = lhs_var_dict['name']
    loop_data['start_index'] = lhs_var_dict['index']
    loop_data['end_index'] = rhs_var_dict['index']
    loop_data['glue'] = lhs_glue
    loop_data['var_prefix'] = lhs_var_dict['prefix']
    loop_data['var_suffix'] = lhs_var_dict['suffix']
    loop_data['last_glue'] = last_glue
    loop_data['last_glue_if_only_two'] = last_glue_if_only_two
    loop_data['before_loop_stuff'] = before_loop_stuff
    loop_data['after_loop_stuff'] = after_loop_stuff

    return(loop_data)

## =============================
def filter_script(line):
    '''
    Remove elements from a Python script which are provide the most egregious security flaws; also replace some
    identifiers with their correct namespace representation.

    Parameters
    ----------
    line : str
        The line of source code to filter.

    Returns
    -------
    filtered : str
        The filtered line of source code.
    '''

    line = line.strip()
    os_pattern = re.compile(r'\Wos.', re.UNICODE)
    sys_pattern = re.compile(r'\Wsys.', re.UNICODE)

    if line.startswith('import') or re.search(os_pattern, line) or re.search(sys_pattern, line):
        filtered = ''
    else:
        filtered = line

    ## Replace any use of "entry", "options", "citedict", or "bstdict" with the needed identifier
    ## for the namespace inside format_bibitem().
    filtered = re.sub(r'(?<=\W)entry(?=\W)', 'self.bib.data[c]', line, re.UNICODE)
    filtered = re.sub(r'(?<=\W)options(?=\W)', 'self.options', line, re.UNICODE)
    filtered = re.sub(r'(?<=\W)citedict(?=\W)', 'self.citedict', line, re.UNICODE)
    filtered = re.sub(r'(?<=\W)bstdict(?=\W)', 'self.bst.bstdict', line, re.UNICODE)

    return(filtered)

    
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

        arg_bstfile = args[0]
    else:
        ## Use the test example input.
        arg_bstfile = './test/test_thiruv.aux'
        
    user_script = ''
    user_variables = {}    ## any user-defined variables from the BST file
    specials_list = []
    specials = copy.deepcopy(bibtools.default_specials)
    nested_templates = []  ## which templates have nested option blocks
    looped_templates = {} #['au','ed']  ## which templates have implicit loops        
    namelists = []         ## the namelists defined within the templates
    implicitly_indexed_vars = ['authorname','editorname']
    
    main_bst = Bst()
    main_bst.parse_bstfile(arg_bstfile, bibtools.default_options, specials, specials_list, user_script, user_variables, nested_templates, looped_templates, namelists, implicitly_indexed_vars)
    print('DONE')
