### IMPORTING LIBRARIES
import os,argparse,subprocess,copy,pwd,socket,time
import sys
import math
import json
import decimal
import pandas
import configparser as cp

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
            print("Query in urlopen\n",e)
            sys.exit(1)
    except Exception as e:
        print("Query in Request\n",e)
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

if os.path.exists(args.conf) and os.path.getsize(args.conf) > 0:
   paramfile=args.conf
else:
   print("Config file " + args.conf + " not existing or empty")
   sys.exit(2)

confObj = cp.ConfigParser()
confObj.read(paramfile)

# Metadata configuration
agency_name = args.agency.lower()
try:
    ws_route = get_config_dictionary(confObj, agency_name)
except Exception as e:
    print(e)
    sys.exit(1)

stations=[]
for ns in stations_list:
    net,sta,loc = ns.split(' ')
    r,u = getxml(sta,net,loc,ws_route['base_url'],ws_route['in_options'])
    stations.append(list(r.decode('utf-8').split('\n'))[1].split('|')) 
    #print(list(r.decode('utf-8').split('\n'))[1])
#['IV','AQU', ''  ,'SHZ','42.35388','13.40193', '729', '0' , '0' , '-90', 'GEOTECH S-13', '582216000', '0.2', 'm/s', '50', '2003-03-01T00:00:00', '2008-10-15T00:00:00']
df = pandas.DataFrame(stations, columns =['net','sta','loc','cha','lat','lon','ele','dep','azi','dip','inst','const','per','unit','samp','start','stop'])
print(df)

