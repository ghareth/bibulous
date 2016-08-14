#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# pylint: disable-msg=C0321
# pylint: max-line-length=120
# pylint: max-module-lines=10000
# See the LICENSE.rst file for licensing information.


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


if (__name__ == '__main__'):
    
    warning("Warning 009 ",[9])
    monthnames, monthabbrevs = generate_inverse_month_names()
    pprint (monthnames)
    pprint (monthabbrevs)