#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# pylint: disable-msg=C0321
# pylint: max-line-length=120
# pylint: max-module-lines=10000
# See the LICENSE.rst file for licensing information.

from builtins import str as unicode

import platform
import locale
import re
from pprint import pprint


## Put in default options settings.

default_options = {}
default_options['use_abbrevs'] = True
default_options['undefstr'] = '???'
default_options['procspie_as_journal'] = False
default_options['backrefstyle'] = 'none'
default_options['backrefs'] = False
default_options['sort_case'] = True
default_options['bibitemsep'] = None
default_options['allow_scripts'] = False
default_options['case_sensitive_field_names'] = False
default_options['use_citeextract'] = True
default_options['etal_message'] = ', \\textit{et al.}'
default_options['edmsg1'] = ', ed.'
default_options['edmsg2'] = ', eds'
default_options['replace_newlines'] = True
default_options['sort_order'] = 'Forward'
default_options['wrap_nested_quotes'] = False
default_options['autocomplete_doi'] = False
default_options['name_separator'] = 'and'

## These options all relate to the default name formatting (the more rigid namelist formatting that does not use
## the implicit indexing and implicit loop structures).
default_options['use_firstname_initials'] = True
default_options['namelist_format'] = 'first_name_first'
default_options['maxauthors'] = 9
default_options['minauthors'] = 9
default_options['maxeditors'] = 5
default_options['mineditors'] = 5
default_options['use_name_ties'] = False
default_options['terse_inits'] = False
default_options['french_initials'] = False
default_options['period_after_initial'] = True



default_specials = {}
default_specials['authorlist'] = '<author.to_namelist()>'
default_specials['editorlist'] = '<editor.to_namelist()>'
default_specials['citelabel'] = '<citenum>'
default_specials['sortkey'] = '<citenum>'
default_specials['au'] = '<authorlist.format_authorlist()>'
default_specials['ed'] = '<editorlist.format_editorlist()>'

## Provide index patterns 
pat = r'[~@%&\-\+\*\#\$\^\?\!\=\:\w]+?'
index_pattern = re.compile(r'(<'+pat+r'\.\d+\.'+pat+r'>)|(<'+pat+r'\.\d+>)|(<'+pat+r'\.(nN)\.'+pat+r'>)|('+pat+r'\.(nN)>)', re.UNICODE)
implicit_index_pattern = re.compile(r'(<'+pat+r'\.n\.'+pat+r'>)|(<'+pat+r'\.n>)', re.UNICODE)

## Not used
#template_variable_pattern = re.compile(r'(?<=<)\.+?(?=>)', re.UNICODE)
#namelist_variable_pattern = re.compile(r'(?<=<)\.+?(?=.to_namelist\(\)>)', re.UNICODE)
#startbrace_pattern = re.compile(r'(?<!\\){', re.UNICODE)
#endbrace_pattern = re.compile(r'(?<!\\)}', re.UNICODE)
#quote_pattern = re.compile(r'(?<!\\)"', re.UNICODE)


## =============================
def warning(msg, disable=None):
    '''
    Print a warning message, with the option to disable any given message.

    Parameters
    ----------
    msg : str
        The warning message to print.
    disable : list of int, optional
        The list of warning message numbers that the user wishes to disable (i.e. ignore).
    '''

    if (disable == None):
        print(msg)
        return

    ## For each number in the "ignore" list, find out if the warning message is one of the ones to ignore. If so, then
    ## do nothing.
    show_warning = True
    for i in disable:
        s = ('Warning %03i' % i)
        if msg.startswith(s):
            show_warning = False
            break

    if show_warning:
        print(msg)

    return

## =============================
def generate_inverse_month_names():
    
    ## Create an inverse dictionary for the month names --- one version will full names, and one with abbreviated
    ## names. For a Unix-based system, the month names are determined by the user's default locale. How to do this
    ## for a MS Windows system?
    
    monthnames = {}
    monthabbrevs = {}    
    
    for i in range(1,13):
        if not (platform.system() == 'Windows'):
            ## The abbreviated form (i.e. 'Jan').
            monthabbrevs[unicode(i)] = locale.nl_langinfo(locale.__dict__['ABMON_'+unicode(i)]).title()
        elif (platform.system() == 'Windows'):
            monthabbrevs = {'1':'Jan', '2':'Feb', '3':'Mar', '4':'Apr', '5':'May', '6':'Jun',
                                 '7':'Jul', '8':'Aug', '9':'Sep', '10':'Oct', '11':'Nov', '12':'Dec'}

        if (platform.system() == 'Windows'):
            monthnames = {'1':'January', '2':'February', '3':'March', '4':'April',
                               '5':'May', '6':'June', '7':'July', '8':'August', '9':'September',
                               '10':'October', '11':'November', '12':'December'}
        else:
            ## The full form (i.e. 'January').
            monthnames[unicode(i)] = locale.nl_langinfo(locale.__dict__['MON_'+unicode(i)]).title()

    return monthnames, monthabbrevs

## ===================================
def get_delim_levels(s, delims=('{','}'), operator=None):
    '''
    Generate a list of level numbers for each character in a string.

    Parameters
    ----------
    s : str
        The string to characterize.
    delims : tuple of two strings
        The (left-hand-side delimiter, right-hand-side delimiter).
    operator : str
        The "operator" string that appears to the left of the delimiter. For example, operator=r'\textbf' allows the \
        code to look for nested structures like `{...}` and simultaneously for structures like `\textbf{...}`, and be \
        able to keep track of which is which.

    Returns
    -------
    levels : list of ints
        A list giving the operator delimiter level (or "brace level" if no operator is given) of each character in \
        the string.
    '''

    stack = []
    oplevels = [0]*len(s)        ## operator level
    brlevels = [0]*len(s)        ## brace level

    ## Locate the left-delimiters and increment the level each time we find one.
    if (operator != None) and (s.count(operator) < 1):
        return(oplevels)

    for j,c in enumerate(s):
        if (c == delims[0]):
            if (operator != None) and (s[j-len(operator):j] == operator):
                stack.append('o')       ## add an "operator" marker to the stack
            else:
                stack.append('b')       ## add a "brace level" marker to the stack
        elif (c == delims[1]):
            ## If the stack is empty but the delimiter level isn't resolved, then the braces are unbalanced.
            if not stack: return([])
            stack.pop()

        if (operator != None): oplevels[j] = stack.count('o')
        brlevels[j] = stack.count('b')

    if (operator != None):
        return(oplevels)
    else:
        return(brlevels)

## ===================================
def get_variable_name_elements(variable):
    '''
    Split the variable name into "name" (left-hand-side part), "iterator" (middle part), and "remainder" (the right-
    hand-side part).

    With these three elements, we will know how to build a template variable inside the implicit loop.

    Parameters
    ----------
    variable : str
        The variable name to be parsed.

    Returns
    -------
    var_dict : dict
        The dictionary containing elements of the variable name, with keys 'varname', 'prefix', 'index', and 'suffix'. \
        The input variable can be reconstructed with name + '.' + prefix + index + suffix.
    '''

    varlist = variable.split('.')
    var_dict = {}
    var_dict['name'] = varlist[0]
    var_dict['index'] = ''
    var_dict['prefix'] = ''
    var_dict['suffix'] = ''

    for i,piece in enumerate(varlist[1:]):
        if piece.isdigit() or (piece == 'n') or (piece == 'N'):
            var_dict['index'] = piece
        elif (var_dict['index'] == ''):
            var_dict['prefix'] += piece + '.'
        else:
            var_dict['suffix'] += '.' + piece

    return(var_dict)


## =============================
def latex_to_utf8(s):
    '''
    Translate LaTeX-markup special characters to their Unicode equivalents.

    Parameters
    ----------
    s : str
        The string to translate.

    Returns
    -------
    s : str
        The translated version of the input.
    '''

    ## Note that the code below uses replace() loops rather than a translation table, since the latter only supports
    ## one-to-one translation, whereas something more flexible is needed here.
    if ('\\' not in s):
        return(s)

    ## First, some easy replacements.
    trans = {r'\$':'$', r'\%':'%', r'\_':'_', r'\&':'&', r'\#':'#', r'!`':'¡', r'?`':'¿'}
    for c in trans:
        if c in s: s = s.replace(c, trans[c])
        
    ## Second, some more replacements.
    trans = {r'{\textquoteright}':"'", r"{\textquotedblleft}":'"',r"{\textquotedblright}":'"',\
             r'{\textendash}':"-"}
    for c in trans:
        if c in s: s = s.replace(c, trans[c])

    ## If there are any double backslashes, place some braces around them to prevent something like "\\aa" from getting
    ## interpreted as a backslash plus "\aa". This makes the string easier to parse and does no harm.
    if r'\\' in s:
        s = s.replace(r'\\',r'{\\}')

    ## First identify all the LaTeX special characters in the string, then replace them all with their Unicode
    ## equivalents. (This is to make sure that they alphabetize correctly for sorting.) The translation dictionary
    ## below uses single-letter accent commands, such as \u{g}. These commands are one of (r'\b', r'\c', r'\d', r'\H',
    ## r'\k', r'\r', r'\u', r'\v'), followed by an open brace, a single character, and a closed brace. These
    ## replacements are done first because some of the special characters use '\i', which would otherwise get replaced
    ## by the "dotless i" Unicode character, and so the replacement dictionary here would not detect the proper LaTeX
    ## code for it.

    ## First, characters with a cedilla or comma below.
    if (r'\c' in s):
        trans = {r'\c{C}':'Ç', r'{\c C}':'Ç', r'\c{c}':'ç', r'{\c c}':'ç', r'\c{E}':'Ȩ', r'{\c E}':'Ȩ',
                 r'\c{e}':'ȩ', r'{\c e}':'ȩ', r'\c{G}':'Ģ', r'{\c G}':'Ģ', r'\c{g}':'ģ', r'{\c g}':'ģ',
                 r'\c{K}':'Ķ', r'{\c K}':'Ķ', r'\c{k}':'ķ', r'{\c k}':'ķ', r'\c{L}':'Ļ', r'{\c L}':'Ļ',
                 r'\c{l}':'ļ', r'{\c l}':'ļ', r'\c{N}':'Ņ', r'{\c N}':'Ņ', r'\c{n}':'ņ', r'{\c n}':'ņ',
                 r'\c{R}':'Ŗ', r'{\c R}':'Ŗ', r'\c{r}':'ŗ', r'{\c r}':'ŗ', r'\c{S}':'Ş', r'{\c S}':'Ş',
                 r'\c{s}':'ş', r'{\c s}':'ş', r'\c{T}':'Ţ', r'{\c T}':'Ţ', r'\c{t}':'ţ', r'{\c t}':'ţ'}

        for c in trans:
            if c in s: s = s.replace(c, trans[c])

    ## Characters with breve above. Note that the "\u" is problematic when "unicode_literals" is turned on via
    ## "from __future__ import unicode_literals". Thus, in the block below, rather than raw strings with single
    ## backslashes, we have to use double-backslashes.
    if ('\\u' in s):
        trans = {'\\u{A}':'Ă', '{\\u A}':'Ă', '\\u{a}':'ă',  '{\\u a}':'ă', '\\u{E}':'Ĕ', '{\\u E}':'Ĕ',
                 '\\u{e}':'ĕ', '{\\u e}':'ĕ', '\\u{G}':'Ğ',  '{\\u G}':'Ğ', '\\u{g}':'ğ', '{\\u g}':'ğ',
                 '\\u{I}':'Ĭ', '{\\u I}':'Ĭ', '\\u{\i}':'ĭ', '{\\u\i}':'ĭ', '\\u{O}':'Ŏ', '{\\u O}':'Ŏ',
                 '\\u{o}':'ŏ', '{\\u o}':'ŏ', '\\u{U}':'Ŭ',  '{\\u U}':'Ŭ', '\\u{u}':'ŭ', '{\\u u}':'ŭ'}

        for c in trans:
            if c in s: s = s.replace(c, trans[c])

    ## Characters with an ogonek.
    if (r'\k' in s):
        trans = {r'\k{A}':'Ą', r'{\k A}':'Ą', r'\k{a}':'ą', r'{\k a}':'ą', r'\k(E}':'Ę', r'{\k E}':'Ę',
                 r'\k{e}':'ę', r'{\k e}':'ę', r'\k{I}':'Į', r'{\k I}':'Į', r'\k{i}':'į', r'{\k i}':'į',
                 r'\k{O}':'Ǫ', r'{\k O}':'Ǫ', r'\k{o}':'ǫ', r'{\k o}':'ǫ', r'\k{U}':'Ų', r'{\k U}':'Ų',
                 r'\k{u}':'ų', r'{\k u}':'ų'}
        for c in trans:
            if c in s: s = s.replace(c, trans[c])

    ## Characters with hachek.
    if (r'\v' in s):
        trans = {r'\v{C}':'Č', r'{\v C}':'Č', r'\v{c}':'č', r'{\v c}':'č', r'\v{D}':'Ď', r'{\v D}':'Ď',
                 r'\v{d}':'ď', r'{\v d}':'ď', r'\v{E}':'Ě', r'{\v E}':'Ě', r'\v{e}':'ě', r'{\v e}':'ě',
                 r'\v{L}':'Ľ', r'{\v L}':'Ľ', r'\v{l}':'ľ', r'{\v l}':'ľ', r'\v{N}':'Ň', r'{\v N}':'Ň',
                 r'\v{n}':'ň', r'{\v n}':'ň', r'\v{R}':'Ř', r'{\v R}':'Ř', r'\v{r}':'ř', r'{\v r}':'ř',
                 r'\v{S}':'Š', r'{\v S}':'Š', r'\v{s}':'š', r'{\v s}':'š', r'\v{T}':'Ť', r'{\v T}':'Ť',
                 r'\v{t}':'ť', r'{\v t}':'ť', r'\v{Z}':'Ž', r'{\v Z}':'Ž', r'\v{z}':'ž', r'{\v z}':'ž',
                 r'\v{H}':'\u021E', r'{\v H}':'\u021E', r'\v{h}':'\u021F',  r'{\v h}':'\u021F',
                 r'\v{A}':'\u01CD', r'{\v A}':'\u01CD', r'\v{a}':'\u01CE',  r'{\v a}':'\u01CE',
                 r'\v{I}':'\u01CF', r'{\v I}':'\u01CF', r'\v{\i}':'\u01D0', r'{\v \i}':'\u01D0',
                 r'\v{O}':'\u01D1', r'{\v O}':'\u01D1', r'\v{o}':'\u01D2',  r'{\v o}':'\u01D2',
                 r'\v{U}':'\u01D3', r'{\v U}':'\u01D3', r'\v{u}':'\u01D4',  r'{\v u}':'\u01D4',
                 r'\v{G}':'\u01E6', r'{\v G}':'\u01E6', r'\v{g}':'\u01E7',  r'{\v g}':'\u01E7',
                 r'\v{K}':'\u01E8', r'{\v K}':'\u01E8', r'\v{k}':'\u01E9',  r'{\v k}':'\u01E9'}
        for c in trans:
            if c in s: s = s.replace(c, trans[c])

    if (r'\H' in s):
        trans = {r'\H{O}':u'Ő',  r'\H{o}':u'ő',  r'\H{U}':u'Ű',  r'\H{u}':u'ű', r'{\H O}':u'Ő', r'{\H o}':u'ő',
                 r'{\H U}':u'Ű', r'{\H u}':u'ű'}
        for c in trans:
            if c in s: s = s.replace(c, trans[c])

    ## Characters with a ring above.
    if (r'\r' in s):
        trans = {r'\r{U}':u'Ů', r'{\r U}':u'Ů', r'\r{u}':u'ů', r'{\r u}':u'ů'}
        for c in trans:
            if c in s: s = s.replace(c, trans[c])

    ## Now let's do the straightforward accent characters.
    trans = {r'\`A':u'\u00C1',  r'\`a':u'\u00E0',  r"\'A":u'\u00C1',  r"\'a":u'\u00E1',  r'\~A':u'\u00C3',
             r'\^a':u'\u00E2',  r'\"A':u'\u00C4',  r'\~a':u'\u00E3',  r'\"a':u'\u00E4',  r'\`E':u'\u00C8',
             r"\'E":u'\u00C9',  r'\`e':u'\u00E8',  r'\^E':u'\u00CA',  r"\'e":u'\u00E9',  r'\"E':u'\u00CB',
             r'\^e':u'\u00EA',  r'\`I':u'\u00CC',  r'\"e':u'\u00EB',  r"\'I":u'\u00CD',  r'\`\i':u'\u00EC',
             r'\^I':u'\u00CE',  r"\'\i":u'\u00ED', r'\"I':u'\u00CF',  r'\^\i':u'\u00EE', r'\~N':u'\u00D1',
             r'\"\i':u'\u00EF', r'\`O':u'\u00D2',  r'\~n':u'\u00F1',  r"\'O":u'\u00D3',  r'\`o':u'\u00F2',
             r'\^O':u'\u00D4',  r"\'o":u'\u00F3',  r'\~O':u'\u00D5',  r'\^o':u'\u00F4',  r'\"O':u'\u00D6',
             r'\~o':u'\u00F5',  r'\"o':u'\u00F6',  r'\`U':u'\u00D9',  r"\'U":u'\u00DA',  r'\`u':u'\u00F9',
             r'\^U':u'\u00DB',  r"\'u":u'\u00FA',  r'\"U':u'\u00DC',  r'\^u':u'\u00FB',  r"\'Y":u'\u00DD',
             r'\"u':u'\u00FC',  r"\'y":u'\u00FD',  r'\"y':u'\u00FF',  r'\=A':u'\u0100',  r'\=a':u'\u0101',
             r"\'C":u'\u0106',  r"\'c":u'\u0107',  r'\^C':u'\u0108',  r'\^c':u'\u0109',  r'\.C':u'\u010A',
             r'\.c':u'\u010B',  r'\=E':u'\u0112',  r'\=e':u'\u0113',  r'\.E':u'\u0116',  r'\.e':u'\u0117',
             r'\^G':u'\u011C',  r'\^g':u'\u011D',  r'\.G':u'\u0120',  r'\.g':u'\u0121',  r'\^H':u'\u0124',
             r'\^h':u'\u0125',  r'\~I':u'\u0128',  r'\~\i':u'\u0129', r'\=I':u'\u012A',  r'\=\i':u'\u012B',
             r'\.I':u'\u0130',  r'\^J':u'\u0134',  r'\^\j':u'\u0135', r"\'L":u'\u0139',  r"\'N":u'\u0143',
             r"\'n":u'\u0144',  r'\=O':u'\u014C',  r'\=o':u'\u014D',  r"\'R":u'\u0154',  r"\'r":u'\u0155',
             r"\'S":u'\u015A',  r"\'s":u'\u015B',  r'\~U':u'\u0168',  r'\~u':u'\u0169',  r'\=U':u'\u016A',
             r'\=u':u'\u016B',  r'\^W':u'\u0174',  r'\^w':u'\u0175',  r'\^Y':u'\u0176',  r'\^y':u'\u0177',
             r"\'Z":u'\u0179',  r"\'z":u'\u017A',  r'\.Z':u'\u017B',  r'\.z':u'\u017C',  r'\`Y':u'Ỳ',
             r'\`y':u'ỳ',       r"\'K":u'Ḱ',       r"\'k":u'ḱ',       r"\'l":u'ĺ',       r'\^A':u'Â',
             r'\^S':u'Ŝ',       r'\^s':u'ŝ',       r'\"Y':u'Ÿ',       r'\~E':u'Ẽ',       r'\~e':u'ẽ',
             r'\~Y':u'Ỹ',       r'\~y':u'ỹ'}

    for c in trans:
        if c in s: s = s.replace(c, trans[c])

    ## Do again for anyone using extra braces.
    trans = {r'\`{A}':u'\u00C1',  r'\`{a}':u'\u00E0',  r"\'{A}":u'\u00C1',  r"\'{a}":u'\u00E1',  r'\~{A}':u'\u00C3',
             r'\^{a}':u'\u00E2',  r'\"{A}':u'\u00C4',  r'\~{a}':u'\u00E3',  r'\"{a}':u'\u00E4',  r'\`{E}':u'\u00C8',
             r"\'{E}":u'\u00C9',  r'\`{e}':u'\u00E8',  r'\^{E}':u'\u00CA',  r"\'{e}":u'\u00E9',  r'\"{E}':u'\u00CB',
             r'\^{e}':u'\u00EA',  r'\`{I}':u'\u00CC',  r'\"{e}':u'\u00EB',  r"\'{I}":u'\u00CD',  r'\`{\i}':u'\u00EC',
             r'\^{I}':u'\u00CE',  r"\'{\i}":u'\u00ED', r'\"{I}':u'\u00CF',  r'\^{\i}':u'\u00EE', r'\~{N}':u'\u00D1',
             r'\"{\i}':u'\u00EF', r'\`{O}':u'\u00D2',  r'\~{n}':u'\u00F1',  r"\'{O}":u'\u00D3',  r'\`{o}':u'\u00F2',
             r'\^{O}':u'\u00D4',  r"\'{o}":u'\u00F3',  r'\~{O}':u'\u00D5',  r'\^{o}':u'\u00F4',  r'\"{O}':u'\u00D6',
             r'\~{o}':u'\u00F5',  r'\"{o}':u'\u00F6',  r'\`{U}':u'\u00D9',  r"\'{U}":u'\u00DA',  r'\`{u}':u'\u00F9',
             r'\^{U}':u'\u00DB',  r"\'{u}":u'\u00FA',  r'\"{U}':u'\u00DC',  r'\^{u}':u'\u00FB',  r"\'{Y}":u'\u00DD',
             r'\"{u}':u'\u00FC',  r"\'{y}":u'\u00FD',  r'\"{y}':u'\u00FF',  r'\={A}':u'\u0100',  r'\={a}':u'\u0101',
             r"\'{C}":u'\u0106',  r"\'{c}":u'\u0107',  r'\^{C}':u'\u0108',  r'\^{c}':u'\u0109',  r'\.{C}':u'\u010A',
             r'\.{c}':u'\u010B',  r'\={E}':u'\u0112',  r'\={e}':u'\u0113',  r'\.{E}':u'\u0116',  r'\.{e}':u'\u0117',
             r'\^{G}':u'\u011C',  r'\^{g}':u'\u011D',  r'\.{G}':u'\u0120',  r'\.{g}':u'\u0121',  r'\^{H}':u'\u0124',
             r'\^{h}':u'\u0125',  r'\~{I}':u'\u0128',  r'\~{\i}':u'\u0129', r'\={I}':u'\u012A',  r'\={\i}':u'\u012B',
             r'\.{I}':u'\u0130',  r'\^{J}':u'\u0134',  r'\^{\j}':u'\u0135', r"\'{L}":u'\u0139',  r"\'{N}":u'\u0143',
             r"\'{n}":u'\u0144',  r'\={O}':u'\u014C',  r'\={o}':u'\u014D',  r"\'{R}":u'\u0154',  r"\'{r}":u'\u0155',
             r"\'{S}":u'\u015A',  r"\'{s}":u'\u015B',  r'\~{U}':u'\u0168',  r'\~{u}':u'\u0169',  r'\={U}':u'\u016A',
             r'\={u}':u'\u016B',  r'\^{W}':u'\u0174',  r'\^{w}':u'\u0175',  r'\^{Y}':u'\u0176',  r'\^{y}':u'\u0177',
             r"\'{Z}":u'\u0179',  r"\'{z}":u'\u017A',  r'\.{Z}':u'\u017B',  r'\.{z}':u'\u017C',  r'\`{Y}':u'Ỳ',
             r'\`{y}':u'ỳ',       r"\'{K}":u'Ḱ',       r"\'{k}":u'ḱ',       r"\'{l}":u'ĺ',       r'\^{A}':u'Â',
             r'\^{S}':u'Ŝ',       r'\^{s}':u'ŝ',       r'\"{Y}':u'Ÿ',       r'\~{E}':u'Ẽ',       r'\~{e}':u'ẽ',
             r'\~{Y}':u'Ỹ',       r'\~{y}':u'ỹ'}

    for c in trans:
        if c in s: s = s.replace(c, trans[c])

    ## Those were easy. Next we look for single-char codes that must be followed by a non-alpha element, so that for
    ## example \orange will produce the "\orange" LaTeX command while "{\o}range" or "\o range" will produce "ørange".
    ## Since we're using regex and not Python's string objects, we need to replace all backslashes with double-
    ## backslashes. Thankfully, no other regex escape characters occur in this list of LaTeX markup for foreign letters.
    trans = {r'\AA':u'Å', r'\AE':u'Æ', r'\aa':u'å', r'\ae':u'æ', r'\O':u'Ø',  r'\o':u'ø',
             r'\ss':u'ß', r'\i':u'ı',  r'\L':u'Ł',  r'\l':u'ł',  r'\OE':u'Œ', r'\oe':u'œ',
             r'\j':u'ȷ',  r'\P':u'¶',  r'\S':u'§',  r'\DH':u'Ð', r'\dh':u'ð', r'\DJ':u'Đ',
             r'\dj':u'đ', r'\IJ':u'Ĳ', r'\ij':u'ĳ', r'\NG':u'Ŋ', r'\ng':u'ŋ', r'\SS':u'ẞ',
             r'\TH':u'Þ', r'\th':u'þ'}

    for c in trans:
        match = re.compile(c.replace('\\','\\\\')+r'(?!\w)', re.UNICODE)
        s = match.sub(trans[c], s, re.UNICODE)

    return(s)

## =============================
def utf8_to_latex(s):
    '''
    Translate Unicode to LaTeX-markup. DEVELOPMENTAL ONLY
    
    Translate _ to \_

    Parameters
    ----------
    s : str
        The string to translate.

    Returns
    -------
    s : str
        The translated version of the input.
    '''

    ## First, some easy replacements.
    trans = {'_' : r'\_',
             '$' : r'\$',
             '%' : r'\%',
             '&' : r'\&',
             '#' : r'\#'}
    
     
    for c in trans:
        if c in s: s = s.replace(c, trans[c])

    return (s)



if (__name__ == '__main__'):
    
    warning("Warning 009 ",[9])
    monthnames, monthabbrevs = generate_inverse_month_names()
    pprint (monthnames)
    pprint (monthabbrevs)