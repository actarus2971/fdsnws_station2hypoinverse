### IMPORTING LIBRARIES
import os,argparse,subprocess,copy,pwd,socket,time
import sys
import math
import json
import decimal
import pandas
import configparser as cp
import numpy

from datetime import datetime
from xml.etree import ElementTree as ET
from six.moves import urllib

## the imports of Obspy are all for version 1.1 and greater
from obspy import read, UTCDateTime
from obspy.core.event import Catalog, Event, Magnitude, Origin, Arrival, Pick
from obspy.core.event import ResourceIdentifier, CreationInfo, WaveformStreamID
try:
    from obspy.core.event import read_events
except:
    from obspy.core.event import readEvents as read_events

class MyParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2)

def parseArguments():
        parser=MyParser()
        parser.add_argument('--station', help='network,station')
        parser.add_argument('--stations_file', help='list of network station lines')
        parser.add_argument('--conf', default='./ws_agency_route.conf', help="agency webservices routes list type (default: %(default)s)")
        parser.add_argument('--agency', default='ingv', help="different routes for different webservices (default: %(default)s)")
        parser.add_argument('--format', default='hi2', help="Allowed formats are Hypoellipse (he), Hypoinverse #1 (hi1), Hypoinverse #2 (hi2)")
        if len(sys.argv) <= 1:
            parser.print_help()
            sys.exit(1)
        args=parser.parse_args()
        return args



# Build a dictionary from config file section
def get_config_dictionary(cfg, section):
    dict1 = {}
    options = cfg.options(section)
    for option in options:
        try:
            dict1[option] = cfg.get(section, option)
            if dict1[option] == -1:
                print("skip: %s" % option)
        except:
            print("exception on %s!" % option)
            dict1[option] = None
    return dict1

def getxml(st,nt,lo,bu,op):
    if lo == "--":
        urltext=bu + "query?station=" + st + "&network=" + nt + op
    else:
        urltext=bu + "query?station=" + st + "&network=" + nt + "&location=" + lo + op
        print(urltext)
    try:
        req = urllib.request.Request(url=urltext)
        try:
            res = urllib.request.urlopen(req)
        except Exception as e:
            print("Query in urlopen (inner)\n",e)
            print(urltext)
            sys.exit(1)
    except Exception as e:
        print("Query in Request (outer)\n",e)
        print(urltext)
        sys.exit(1)
    return res.read(),urltext

#def to_hypoellipse(stl):
#    for s in stl:
        

def stations_format(sl,fmt):
    if fmt == "he":
       slo = to_hypoellipse(sl)
    elif fmt == "hi1":
       slo = to_hypoinverse1(sl)
    elif fmt == "hi2":
       slo = to_hypoinverse2(sl)
    return slo

def to_out(d,fn):
    s=''
    for index, row in d.iterrows():
        code = row['alias']
        ilat = int(float(row['lat']))
        flat = (float(row['lat']) - ilat) * 60.
        ilon = int(float(row['lon']))
        flon = (float(row['lon']) - ilon) * 60.
        elev = int(float(row['ele']) - float(row['dep']))
        if fn == 'he':
           s1 = "%4s%2iN%5.2f %3iE%5.2f %4i\n" % (code,ilat,flat,ilon,flon,elev)
           s2 = "%4s*     0     1.00\n" % (code)
        elif fn == 'hi1':
           s1 = "%4s %2i %5.2fN%3i %5.2fE%4i\n" % (code,ilat,flat,ilon,flon,elev)
           s2 = ""
        s=s+s1+s2
    return s

################## MAIN ####################
args=parseArguments()

if not args.stations_file:
       n,s,l = args.station.split(',')
       stations_list = [n + ' ' + s + ' ' + l]
else:
       if args.stations_file:
          try:
              f = open(args.stations_file)
              stations_list = f.read().splitlines() #f.readlines()
              f.close()
          except Exception as e:
              print(e)
              sys.exit()

if args.format:
   fmts = args.format.split(',')
   fmts = [x.lower() for x in fmts]

if os.path.exists(args.conf) and os.path.getsize(args.conf) > 0:
   paramfile=args.conf
else:
   print("Config file " + args.conf + " not existing or empty")
   sys.exit(2)

confObj = cp.ConfigParser()
confObj.read(paramfile)

# Configuration parameters loading
agency_name = args.agency.lower()
try:
    ws_route = get_config_dictionary(confObj, agency_name)
except Exception as e:
    print(e)
    sys.exit(1)

try:
    files_name = get_config_dictionary(confObj, 'files_name')
except Exception as e:
    print(e)
    sys.exit(1)

stations=[]
for ns in stations_list:
    net,sta,loc = ns.split()
    r,u = getxml(sta,net,loc,ws_route['base_url'],ws_route['in_options'])
    stations.append(list(r.decode('utf-8').split('\n'))[1].split('|')) 
    #print(list(r.decode('utf-8').split('\n'))[1])
#['IV','AQU', ''  ,'SHZ','42.35388','13.40193', '729', '0' , '0' , '-90', 'GEOTECH S-13', '582216000', '0.2', 'm/s', '50', '2003-03-01T00:00:00', '2008-10-15T00:00:00']
df = pandas.DataFrame(stations, columns =['net','sta','loc','cha','lat','lon','ele','dep','azi','dip','inst','const','per','unit','samp','start','stop'])

df['alias'] = df['sta']
df['increment'] = df['sta'].str.len().isin({5,7}).cumsum()
df['alias'] = numpy.where(    df['increment']-df['increment'].shift(1,fill_value=df['increment'][0]) > 0           , 'A'+df['increment'].map('{:03.0f}'.format).astype(str), df['alias'])
df['lenght'] = df['alias'].str.len()
df=df.sort_values(['lenght','alias'],ascending=[True,True])
for f in fmts:
   of = open(files_name[f],'w')
   outwrite = to_out(df,f)
   of.write(outwrite)
   of.close()
