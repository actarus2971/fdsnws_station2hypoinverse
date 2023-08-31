### IMPORTING LIBRARIES
import os,argparse,subprocess,copy,pwd,socket,time
import sys
import pandas

class MyParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2)

def parseArguments():
        parser=MyParser()
        parser.add_argument('--aliases', help='aliases file output of fdsnws_station2hypoinverse')
        parser.add_argument('--hypo71phs', help='hypo71 phase file of event(s)')
        if len(sys.argv) <= 1:
            parser.print_help()
            sys.exit(1)
        args=parser.parse_args()
        return args

################## MAIN ####################
args=parseArguments()

if os.path.isfile(args.aliases):
   df_aliases = pandas.read_csv(args.aliases)

if os.path.isfile(args.hypo71phs):
   file_phs = open(args.hypo71phs,'r')

hypo71phs = file_phs.readlines()

for l in hypo71phs:
    if len(l) > 1:
       if l[77] == " ":
          print(l[:76])
       else:
          sta=l[:4]+l[77]
          net=l[81:83]
          loc=l[83:85]
          alias=df_aliases.loc[(df_aliases['sta']==sta) & (df_aliases['net']==net)]['alias'].values[0]
          print(alias+l[4:76])
    else:
       print(l.rstrip())

file_phs.close()
