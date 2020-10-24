#!/usr/bin/env python 

# convert csv into geoJSON   # i will just call it gson
# some customization may be needed to pick right column etc

# this one is for the ZWEDC data, ZWEDC_Biofilter_10X_2016_LongLat_25m_cbind.csv
# this version create gson with polygon around the data
# the new csv it uses has 4 vertices of (essentially) a square
# Test gson output at http://geojson.io/#map=15/37.4045/-121.9810

import argparse
import os
import sys
import re
#import json # don't print things with good indent, hinder development, don't find it useful
#import pandas # https://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.from_csv.html



INPUT="ZWEDC_Biofilter_10X_2016_LongLat_25m_cbind.csv"
# OUTPUT to std out, redirect to file :)

# dbgLevel 1 (ie -d  ) is good for telling when input fails to pass parser
# dbgLevel 3 (ie -ddd) is expected by user troubleshooting problem parsing input file
# currently most detailed output is at level 5 (ie -ddddd) and it is eye blurry even for programmer
dbgLevel = 0  

def process_cli() :
	parser = argparse.ArgumentParser( description='generate geoJSON from CSV, after customization' )
	parser.add_argument('-d', '--debuglevel', help="Debug mode. Up to -ddd useful for troubleshooting input file parsing. -ddddd intended for coder. ", action="count", default=0)
	args = parser.parse_args()
	global dbgLevel  # ie, tell fn to set the global var, not one created locally in this fn
	dbgLevel = args.debuglevel      # unable to change global here...   this has no effect :(
	return args
# process_cli()-end



def dbg( level, strg ):
    if( dbgLevel >= level ) : 
        print( "//--dbg%s: %s--" % (level, strg) )

gprintWithComment = 0 # dbg print geojson with comment for my own debug, bug geojson dont suports coment, so need way to turn it off easily for final production run.
def gprint( str1, str2="#" ):
    if( gprintWithComment >= 1 ) : 
        print( str1 + "\t\t //" + str2 )
    else :
        print( str1 )
# gprint()-end

# generate a single line of geojson  from a given input arg of 
# need to be sure points are 4 vertices in seq, something like TL, TR, BR, BL.  will name them seq in case polygon becomes more than just square
# gson need 5 poionts to close off a square, this fn will print first point last again for that purpose
def print_gsonLine( value, lon1,lat1, lon2,lat2, lon3,lat3, lon4,lat4) :
	gprint( '    { "type":       "Feature", ', '1' ) 	## 1
	gprint( '      "properties":            ', '2' ) 	## 2
	gprint( '           {"max": %s}' % value , "3" )        ## 3
	gprint( '      ,' , '2')
	gprint( '      "geometry": { "type": "Polygon", "coordinates": [[ [ %s,%s ], [ %s,%s], [%s,%s], [%s,%s], [%s,%s]  ]]}' % (lon1,lat1, lon2,lat2, lon3,lat3, lon4,lat4, lon1,lat1), '2b') 
	gprint( '    }', '1' )
# print_gsonLine()-end 


def print_opener() :
	gprint( '{ "type": "FeatureCollection", "features": [', 'top' )	## top
#print_operner() end

def print_closer() : 
	gprint( '] }', 'top' )		## top
#print_closer() end

# check input has format that fit req of lon/lat point
# eg one of: -121.985002139616 or  37.4079452829464
def chkPtFormat( pt, wholeLine ) :
    if( re.search( '^[-]{0,1}[0-9]+\.[0-9]+$', pt ) ) :     
        # re is the regular expression match.  
        dbg( 2, "Extract ok for lon or lat [%14s] from input line '%s' " % (pt, wholeLine) )
        return( pt )  
    else :
        dbg( 1, "Fail - unexptect pattern.  pt read as --%s--, input line was --%s--" % (pt, wholeLine) )
        return( "NaN" )  # used to return "" maybe NaN is better...
#end chkPtFormat()


"""
example input lines (didn't start with 0-index, so parser will -1)
1   2     3     4   5   6      7      8      9    10   11     12     13   14   15     16     17   18   19     20     21   22
"","lon","lat","x","y","Conc","lon1","lat1","x1","y1","lon2","lat2","x2","y2","lon3","lat3","x3","y3","lon4","lat4","x4","y4"
"1",-121.985002139616,37.4079452829464,589827,4140612,0.18577,-121.985287624997,37.4077223978109,589802,4140587,-121.984722734052,37.4077175479308,589852,4140587,-121.984716652544,37.4081681673591,589852,4140637,-121.985281546871,37.4081730173178,589802,4140637
"2",-121.984437247048,37.4079404316778,589877,4140612,0.18817,-121.984722734052,37.4077175479308,589852,4140587,-121.984157843243,37.4077126953524,589902,4140587,-121.984151758353,37.4081633147021,589902,4140637,-121.984716652544,37.4081681673591,589852,4140637

"""

val_idx  = 6-1  # value of the feature at the lon, lat (in this case, wants to aveconc)
lon1_idx = 7-1  # column index containing longitude, -1 cuz 0-indexed
lat1_idx = 8-1
lon2_idx = 11-1 # 
lat2_idx = 12-1
lon3_idx = 15-1 # 
lat3_idx = 16-1
lon4_idx = 19-1 # 
lat4_idx = 20-1
min_col = 22    # min number of columns in file
# this takes one input line, 
# return a triplet (lon, lat, val)
# which are the exact same params  the geojson print fn need
def parse1line( line ) :
    val = 0
    (lon1,lat1, lon2,lat2, lon3,lat3, lon4,lat4) = ( 0,0 , 0,0 , 0,0 , 0,0 ) # struct may have been nice...
    ifs = ","
    # comment line, blank lines, nothing to process, just return
    if( re.search( '^#', line ) ) :     
        return ("", "","" , "","" , "","" , "",""  )  # 9-tuple of blank, easier for caller to handle, struct may have been prettier syntatically
    if( re.search( '^$', line ) ) :     
        return ("", "","" , "","" , "","" , "",""  )  # 9-tuple of blank, easier for caller to handle, struct may have been prettier syntatically
    line = line.rstrip("\n\r") 
    lineList = line.split( ifs )

    if( len(lineList) < min_col ) :
        dbg( 1, "Not enough columns.  cannot extract features" )
        dbg( 3, "Line split into %s words" % len (lineList) )
        #dbg4( "col idx %s not found in this line, returning empty string." % colidx )
        return ("", "","" , "","" , "","" , "",""  )  # 9-tuple of blank, easier for caller to handle, struct may have been prettier syntatically
    val = lineList[val_idx].strip()
    lon1 = lineList[lon1_idx].strip()       # strip() removes white space on left and right ends only, not middle
    lat1 = lineList[lat1_idx].strip() 
    lon2 = lineList[lon2_idx].strip()       # vertices #2
    lat2 = lineList[lat2_idx].strip() 
    lon3 = lineList[lon3_idx].strip()       # vertices #3
    lat3 = lineList[lat3_idx].strip() 
    lon4 = lineList[lon4_idx].strip()       # vertices #4
    lat4 = lineList[lat4_idx].strip() 

    if( re.search( '^[-]{0,1}[0-9]+\.[0-9]+$', val ) ) :     
        dbg( 2, "Extract ok for val [%14s] from input line '%s' " % (val, line) )
    else :
        dbg( 1, "Fail - val_idex %s had %s , unexpected pattern (input line was '%s')" % (val_idx, val, line) )
        return ("", "","" , "","" , "","" , "",""  )  # 9-tuple of blank, easier for caller to handle, struct may have been prettier syntatically

    # ++ loop to test all 8 coordinates...
    pt = chkPtFormat( lon1, line )
    if( pt == "NaN" ) :
        return ( "", "","" , "","" , "","" , "",""  )  # 9-tuple of blank, easier for caller to handle, struct may have been prettier syntatically
    # lazy, they should be okay as csv created by R... run with -d and chkPtFormat would spill error message :)
    pt = chkPtFormat( lat1, line )
    pt = chkPtFormat( lon2, line )
    pt = chkPtFormat( lat2, line )
    pt = chkPtFormat( lon3, line )
    pt = chkPtFormat( lat3, line )
    pt = chkPtFormat( lon4, line )
    pt = chkPtFormat( lat4, line )

    return( val, lon1,lat1, lon2,lat2, lon3,lat3, lon4,lat4 )
#end



## this is like main() 
def run_conversion( args ) :
	dbg( 5, "converting csv to gson...")
	print_opener()  # some geojson header 
	(val, lon1,lat1, lon2,lat2, lon3,lat3, lon4,lat4)  = ( 0, "","" , "","" , "","" , "",""  )  # 9-tuple initialized to blank

	# loop to parse file
	filename = INPUT
	f = open( filename, 'r' )
	lineNum = 0
	for line in f:
		#print line
		#lineList = line.split( ',' )
		(val, lon1,lat1, lon2,lat2, lon3,lat3, lon4,lat4) = ( parse1line( line ) )
		if ( lon1 == "" )  :
			continue		# returned nothing, skipping the line
		if( lineNum > 0 ) :
			gprint( ",", "//next feature//" )	# print separator iff not first line
		print_gsonLine( val, lon1,lat1, lon2,lat2, lon3,lat3, lon4,lat4 )
		lineNum += 1		
	f.close()

	print_closer() # close out parenthesis...
# run_conversion()-end




# glance over data, find avg, std dev, min, max, missing value, etc # use pandas
# mostly to get idea to change opacity in mapbox studio using a custom range.
#https://pandas.pydata.org/pandas-docs/stable/generated/pandas.read_csv.html#pandas.read_csv
def sniff_data(args) :
    print("did the data analysis interactively in jupyther hub")
    #pandas.read_csv( INPUT )
#end sniff_data()


def main():
    args = process_cli()
    run_conversion(args)
# main()-end


##### program beign 
main()

################################################################################
################################################################################


"""
example output for 2 record:

{ "type": "FeatureCollection", "features": [
    { "type":       "Feature", 
      "properties":            
           {"max": 0.18577}
      ,
      "geometry": { "type": "Polygon", "coordinates": [[ [ -121.985287624997,37.4077223978109 ], [ -121.984722734052,37.4077175479308], [-121.984716652544,37.4081681673591], [-121.985281546871,37.4081730173178], [-121.985287624997,37.4077223978109]  ]]}
    }
,
    { "type":       "Feature", 
      "properties":            
           {"max": 0.18817}
      ,
      "geometry": { "type": "Polygon", "coordinates": [[ [ -121.984722734052,37.4077175479308 ], [ -121.984157843243,37.4077126953524], [-121.984151758353,37.4081633147021], [-121.984716652544,37.4081681673591], [-121.984722734052,37.4077175479308]  ]]}
    }
] }

"""

