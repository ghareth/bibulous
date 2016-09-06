#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from __future__ import unicode_literals, print_function, division
from builtins import str as unicode
from builtins import range
from builtins import input
from past.builtins import basestring

import re
import os

from pprint import pprint       # for debugging

import mysql.connector
import datetime
from dateutil.parser import parse as dateparse
from dateutil.tz import tzutc

from bibulous_bib import Bib
import bibulous_tools as bibtools


def clear(cur):
    
    cur.execute('delete from biblio')

def insert(cur1, data):

    global x1,y1,x2, y2
    
    for each in list(data): 
        print ("Citekey:   "+each)
        if each == 'preamble': continue
        try:
            
            a = data[each].get('date-modified',"")
            
            if a:
                cur1.execute("insert into biblio values('"+ each +"','"+ a +"','')")
            else:
                cur1.execute("insert into biblio values('"+ each +"','"+datetime.datetime.now(tzutc()).isoformat()+"','')")

        except mysql.connector.errors.IntegrityError as err:
            if (err.args[0] == 1062) and (err.args[2] == "23000"):
                #print ("From Bib: "+data[each].get('date-modified',""))
                if not(data[each].get('date-modified')):
                    print ('No date-modified, not replacing') 
                else:
                    cur1.execute("select date_modified from biblio where citekey = '"+ each +"'")
                    a = cur1.fetchall()
                    x = dateparse(a[0][0])
                    y = dateparse (data[each]['date-modified'])
                    if each =='nimkathana-data-mining':
                        print (x)
                        print (y)
                        x1= x
                        y1= y
                    else:
                        x2= x
                        y2= y                        
                    
                    if x >= y :
                        print ("Matching citekey, date-modified the same")
                        
                    else:
                        print ("Matching citekey, date-modified not the same, replacing")
                        cur1.execute("delete from biblio where citekey ='"+ each + "'")
                        abc = "insert into biblio values('" + each + "','"+ str(y) +"','')"
                        cur1.execute(abc)
    
if (__name__ == '__main__'):
    
    cnx = mysql.connector.connect(user='root', password='',host='127.0.0.1', database='MyDB')
    
    arg_bibfile = './test/thiruv.bib'
    
    data = Bib()
    
    data.parse_bibfile(arg_bibfile, culldata=False , searchkeys=None , 
                               parse_only_entrykeys=False , 
                               options=bibtools.default_options )
    

        
    cur = cnx.cursor()
    
    #clear(cur)
    
    insert(cur, data.data)
        
    cur.close()    
    cnx.commit()
    cnx.close()