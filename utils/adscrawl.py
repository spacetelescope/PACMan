#!/usr/bin/env python
import os,sys,pdb,scipy,glob
from pylab import *

import urllib, urllib2
import xml.dom.minidom

import datetime

def ADS():
    thisMirror = 'http://adsabs.harvard.edu/'
    print 'Retrieving from ',thisMirror
    baseUrl = thisMirror + 'cgi-bin/nph-abs_connect?'
    return baseUrl

def get_text(node_list):
    text = []
    for node in node_list:
        if node.nodeType == node.TEXT_NODE:
            this_text = node.data
            this_text.strip()
            text.append(this_text)
        return "".join(text).strip()



def getXMLForAuthor(author,year0,year1,ref_stems=''):
         startMonth = 1
         endMonth = 12
         #year0 = 1981
         #year1 = 2009
         numberToGet = 500
         # deal with unicode???
         searchauthor = author# urllib.quote(author.encode('utf-8'))
         #print searchauthor
         values={
             'db_key':'AST','qform':'AST',
             'arxiv_sel':'astro-ph',
             ## 'arxiv_sel':'cond-mat', 'arxiv_sel':'cs','arxiv_sel':'gr-qc',
             ## 'arxiv_sel':'hep-ex', 'arxiv_sel':'q-bio',
             ## 'arxiv_sel':'hep-lat','arxiv_sel':'hep-ph',
             ## 'arxiv_sel':'hep-th', 'arxiv_sel':'math',
             ## 'arxiv_sel':'math-ph', 'arxiv_sel':'nlin',
             ## 'arxiv_sel':'nucl-ex', 'arxiv_sel':'nucl-th',
             ## 'arxiv_sel':'physics', 'arxiv_sel':'quant-ph',
             'sim_query':'YES', 'ned_query':'YES',
             'adsobj_query':'YES', 'aut_logic':'OR','aut_xct':'YES', 'obj_logic':'OR', # exact author
             'object':'',  'start_mon':startMonth,
             'start_year':year0, 'end_mon':endMonth, 'end_year':year1,
             'ttl_logic':'OR',  'title':'', 'txt_logic':'OR', 'text':'',
             'nr_to_return':numberToGet, 'start_nr':'1',
             'jou_pick':'NO', 'ref_stems':ref_stems, 'data_and':'ALL',
             'group_and':'ALL', 'start_entry_day':'',
             'start_entry_mon':'', 'start_entry_year':'',
             'end_entry_day':'', 'end_entry_mon':'', 'end_entry_year':'',
             'min_score':'',  'sort':'SCORE', 'data_type':'XML',
             'aut_syn':'YES', 'ttl_syn':'YES','txt_syn':'YES',
             'aut_wt':'1.0', 'obj_wt':'1.0', 'ttl_wt':'0.3',
             'txt_wt':'3.0', 'aut_wgt':'YES', 'obj_wgt':'YES',
             'ttl_wgt':'YES', 'txt_wgt':'YES', 'ttl_sco':'YES',
             'txt_sco':'YES', 'version':'1'
             }
         

         # jou_pick = 'NO' means only refereed papers

         data = urllib.urlencode(values)
         # this fixes the unicode author problem
         ## just first authors?
         ## data += '&author=' + urllib.quote('^'+author.encode('utf-8'))
         # any author
         data += '&author=' + urllib.quote(author.encode('utf-8'))
         #print ADS()+data
         err = 1
         while err == 1:
             try:
                 #baseUrl = RandomADSMirror()
                 baseUrl = ADS()
                 req = urllib2.Request(baseUrl, data)
                 response = urllib2.urlopen(req)
                 the_page = response.read()
                 err = 0
             except:
                 err = 1
         return the_page


def run_exact_authors(authors, nyears = 5):
    baseUrl = 'http://adsabs.harvard.edu/cgi-bin/nph-abs_connect?'
    
    
    uniqueAuthors = set(authors)

    this_year = int(datetime.datetime.now().strftime('%Y'))
    this_month = int(datetime.datetime.now().strftime('%M'))


    data = {}
    cites = {}
    for i,author in enumerate(uniqueAuthors):
        print '... running %s, %d of %d' %(author,i+1,len(uniqueAuthors))
        the_page = getXMLForAuthor(author,this_year-nyears,this_year)
        print 'Hi There'
        this_dom = xml.dom.minidom.parseString(the_page)
        for element in this_dom.getElementsByTagName('abstract'):
            text = get_text(element.childNodes)
            try:
                data[author.encode('ascii').lower().replace(' ','')]+=[text.encode('utf-8')+' ']
            except:
                data[author.encode('ascii').lower().replace(' ','')]=[text.encode('utf-8')+' ']
        for element in this_dom.getElementsByTagName('citations'):
            text = get_text(element.childNodes)
            try:
                cites[author.encode('ascii').lower().replace(' ','')]+=[int(text.encode('utf-8'))]
            except:
                cites[author.encode('ascii').lower().replace(' ','')]=[int(text.encode('utf-8'))]
    return(data,cites)

def run_authors(authors, nyears = 5, rs_exceptions=''):

    rs_exceptions.replace(' ','')
    rs_exceptions.replace(',','%2C')
    rs_exceptions.replace('+','%2B')
    rs_exceptions.replace('-','%2D')
    rs_exceptions.replace('&','%26')


    baseUrl = 'http://adsabs.harvard.edu/cgi-bin/nph-abs_connect?'
    
    
    uniqueAuthors = set(authors)

    this_year = int(datetime.datetime.now().strftime('%Y'))
    this_month = int(datetime.datetime.now().strftime('%M'))


    data = {}
    cites = {} 
    for i,author in enumerate(uniqueAuthors):
        print '... running %s, %d of %d' %(author,i+1,len(uniqueAuthors))

        ## first try exact author
        print author
        the_page = getXMLForAuthor(author,this_year-nyears,this_year,ref_stems=rs_exceptions)
        this_dom = xml.dom.minidom.parseString(the_page)
        for element in this_dom.getElementsByTagName('abstract'):
            text = get_text(element.childNodes)
            try:
                data[author.encode('ascii').lower().replace(' ','')]+=[text.encode('utf-8')+' ']
            except:
                data[author.encode('ascii').lower().replace(' ','')]=[text.encode('utf-8')+' ']
        for element in this_dom.getElementsByTagName('citations'):
            text = get_text(element.childNodes)
            try:
                cites[author.encode('ascii').lower().replace(' ','')]+=[int(text.encode('utf-8'))]
            except:
                cites[author.encode('ascii').lower().replace(' ','')]=[int(text.encode('utf-8'))]

        ## now try first and middle initial
        last, first_middle =author.split(',')
        first_middle_list = first_middle.strip().split()
        fm_initials=[]
        for item in first_middle_list:
            fm_initials.append(item[0]+'.')
        authorn = last+', '+' '.join(fm_initials)
        print authorn
        the_page = getXMLForAuthor(authorn,this_year-nyears,this_year,ref_stems=rs_exceptions)
        this_dom = xml.dom.minidom.parseString(the_page)
        for element in this_dom.getElementsByTagName('abstract'):
            text = get_text(element.childNodes)
            try:
                data[author.encode('ascii').lower().replace(' ','')]+=[text.encode('utf-8')+' ']
            except:
                data[author.encode('ascii').lower().replace(' ','')]=[text.encode('utf-8')+' ']
        for element in this_dom.getElementsByTagName('citations'):
            text = get_text(element.childNodes)
            try:
                cites[author.encode('ascii').lower().replace(' ','')]+=[int(text.encode('utf-8'))]
            except:
                cites[author.encode('ascii').lower().replace(' ','')]=[int(text.encode('utf-8'))]

        ## and just first if not already done
        if len(first_middle_list) > 1:
            authorn = last+','+' '+fm_initials[0]
            print authorn
            the_page = getXMLForAuthor(authorn,this_year-nyears,this_year,ref_stems=rs_exceptions)
            this_dom = xml.dom.minidom.parseString(the_page)
            for element in this_dom.getElementsByTagName('abstract'):
                text = get_text(element.childNodes)
                try:
                    data[author.encode('ascii').lower().replace(' ','')]+=[text.encode('utf-8')+' ']
                except:
                    data[author.encode('ascii').lower().replace(' ','')]=[text.encode('utf-8')+' ']
            for element in this_dom.getElementsByTagName('citations'):
                text = get_text(element.childNodes)
                try:
                    cites[author.encode('ascii').lower().replace(' ','')]+=[int(text.encode('utf-8'))]
                except:
                    cites[author.encode('ascii').lower().replace(' ','')]=[int(text.encode('utf-8'))]

        ## and, what if the name is hypenated?
        last, first_middle =author.split(',')
        first_middle_list = first_middle.strip().split('-')
        if len(first_middle_list) > 1:
            fm_initials=[]
            for item in first_middle_list:
                fm_initials.append(item[0]+'.')
            authorn = last+', '+'-'.join(fm_initials)
            print authorn
            the_page = getXMLForAuthor(authorn,this_year-nyears,this_year,ref_stems=rs_exceptions)
            this_dom = xml.dom.minidom.parseString(the_page)
            for element in this_dom.getElementsByTagName('abstract'):
                text = get_text(element.childNodes)
                try:
                    data[author.encode('ascii').lower().replace(' ','')]+=[text.encode('utf-8')+' ']
                except:
                    data[author.encode('ascii').lower().replace(' ','')]=[text.encode('utf-8')+' ']
            for element in this_dom.getElementsByTagName('citations'):
                text = get_text(element.childNodes)
                try:
                    cites[author.encode('ascii').lower().replace(' ','')]+=[int(text.encode('utf-8'))]
                except:
                    cites[author.encode('ascii').lower().replace(' ','')]=[int(text.encode('utf-8'))]
        try:
            data[author.encode('ascii').lower().replace(' ','')]=list(set(data[author.encode('ascii').lower().replace(' ','')]))
        except:
            continue
    return(data, cites)





if __name__=='__main__':

    
    journals=['+SPIE','+PASP','-APJ','-AJ','-NATUR','-SCI','-MNRAS','-A&A','-PhDT']
    ref_stem = ','.join(journals)
    print ref_stem
    
    data=run_authors(['strolger, louis-gregory'], nyears=20,rs_exceptions=ref_stem)
    pdb.set_trace()
    
