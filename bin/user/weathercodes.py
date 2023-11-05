#!/usr/bin/python3
# Weather Codes and Symbols
# Copyright (C) 2023 Johanna Roedenbeck
# licensed under the terms of the General Public License (GPL) v3

from __future__ import absolute_import
from __future__ import print_function
from __future__ import with_statement

"""
    This script is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This script is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
"""

"""
    Usage
    =====
    
    Standard use case is to set up a search list extension in skin.conf:
    
        search_list_extensions = ..., user.weathercodes.WeatherSearchList
        
    Then an additional tag is available:
    
        $presentweather(ww, n=None, night=False).ww
        $presentweather(ww, n=None, night=False).text
        $presentweather(ww, n=None, night=False).mosmix_priority
        $presentweather(ww, n=None, night=False).belchertown_icon
        $presentweather(ww, n=None, night=False).dwd_icon
        $presentweather(ww, n=None, night=False).aeris_icon
        $presentweather(ww, n=None, night=False).wmo_symbol
        $presentweather(ww, n=None, night=False).wmo_symbol(width)

    Use the icons with the <img> tag, for example:
    
        <img src="../images/$presentweather($ww,$n,$night).belchertown_icon" />

    "wmo_symbol" is a vector graphic that is displayed directly. The tag
    is enough. No <img> needed.
    
        $presentweather($ww,$n,$night).wmo_symbol($width)
    
    Standalone usage:
    
    python3 user/weathercodes.py --print-ww-list
    
        print an HTML table of all ww symbols and descriptions to stdout
        
    python3 user/weathercodes.py --print-ww-tab
    
        print an HTML table of all the ww symbols
        
    python3 user/weathercodes.py --write-ww-files
    
        write an SVG file for each of the ww symbols
        
    python3 user/weathercodes.py --test-searchlist
    
        for debugging only
    
    Present weather codes
    =====================
    
    Codes of present weather as defined by the WMO code table 4677
    ("present weather reported from a manned weather station")
    
    ww      | description
    --------|------------------------------------------------------------------
    00...49 | no precipitation at the station at the time of observation
            | but, may be, during the preceding hour
    50...99 | precipitation at the station at the time of observation
    --------|------------------------------------------------------------------
    00...19 | no precipitation, fog, storm
    20...29 | events not at the time of observation, but within the last hour
    30...39 | duststorm, sandstorm, drifting or blowing snow
    40...49 | fog, ice fog at the time of observation
    --------|------------------------------------------------------------------
    50...59 | drizzle at the time of observation
    60...69 | rain at the time of observation
    70...79 | solid precipitation not in showers
    80...99 | showery precipitation or pricipitation with current or recent 
            | thunderstorm
    
    Not all of the codes are used by the DWD-MOSMIX forecast.
    
    WMO 4680 w(a)w(a) present weather reported from an automatic weather station
    WMO 4687 W(1)W(1)

    yellow  #ffc83f
    red     #ed1c24
    blue    #1e3dfa
    green   #00d700
    magenta #ac00ff

    https://www.dwd.de/DE/leistungen/opendata/help/schluessel_datenformate/kml/mosmix_element_weather_xls.xlsx?__blob=publicationFile&v=6
    https://www.nodc.noaa.gov/archive/arc0021/0002199/1.1/data/0-data/HTML/WMO-CODE/WMO4677.HTM
    https://www.woellsdorf-wetter.de/info/presentweather.html
    https://library.wmo.int/doc_num.php?explnum_id=10235
    https://rmets.onlinelibrary.wiley.com/doi/pdf/10.1017/S1350482701004108
    https://www.meteopool.org/en/encyclopedia-wmo-ww-wx-code-id2
    https://www.meteopool.org/de/encyclopedia-wmo-ww-wx-code-id2
    
    Calculation of pressure tendency code according to DWD
    BUFR 0 10 063:
    
    dSP  = p(now) - p(-3h)
    dSP3 = p(now) - p(-1h)
    dSP1 = p(-2h) - p(-3h)
    
    dSP  |  dSP3-dSP1  |  dSP3  |  code
    -----|-------------|--------|------
    >0   |  >0         |  any   |  3
    >0   |  =0         |  any   |  2
    >0   |  <0         |  >0    |  1
    >0   |  <0         |  =0    |  1
    >0   |  <0         |  <0    |  0
    =0   |  >0         |  any   |  5
    =0   |  =0         |  any   |  4
    =0   |  <0         |  any   |  0
    <0   |  >0         |  >0    |  5
    <0   |  >0         |  =0    |  6
    <0   |  >0         |  <0    |  6
    <0   |  =0         |  any   |  7
    <0   |  <0         |  any   |  8
    
"""

import json
import copy
import configobj
import math
if __name__ == "__main__":
    import optparse
    import os.path
    import sys
    import time
    sys.path.append('/usr/share/weewx')
try:
    from weewx.cheetahgenerator import SearchList
    from weewx.units import ValueHelper, ValueTuple, kph_to_knot
    from weewx.tags import ObservationBinder, AggTypeBinder
    hasSearchList = True
except ImportError:
    hasSearchList = False

import weeutil.weeutil

SVG_ICON_START = '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" %s width="%s" height="%s" viewBox="-64 -50 128 100">%s<g stroke-width="3">'
SVG_ICON_END = '</g></svg>'
SVG_ICON_UNKNOWN = '<path stroke="#828487" fill="none" d="M -31,28 a 20,20 0 1 1 4.88026841,-39.3954371 a 24,24 0 0 1 43.20059379,-9.49083912 a 16.25,16.25 0 0 1 16.9191378,9.88627622 a 20,20 0 0 1 -6.244998,39z" /><text x="-18" y="18" fill="#828487" style="font-family:sans-serif;font-size:50px;font-weight:normal;text-align:center">?</text>'
SVG_ICON_CLOUDY = '<path stroke="#828487" stroke-width="1.8" fill="none" d="M 5,-30 a 14.4,14.4 0 0 1 25.8,-5.4 h 2 a 9.75,9.75 0 0 1 9,6 a 12,12 0 0 1 0.3,22.68" /><path stroke="#828487" fill="none" d="M -31,28 a 20,20 0 1 1 4.88026841,-39.3954371 a 24,24 0 0 1 43.20059379,-9.49083912 a 16.25,16.25 0 0 1 16.9191378,9.88627622 a 20,20 0 0 1 -6.244998,39z" />'
SVG_ICON_CLOUDY_WIND = '<path stroke="#828487" stroke-width="1.8" fill="none" d="M 5,-30 a 14.4,14.4 0 0 1 25.8,-5.4 h 2 a 9.75,9.75 0 0 1 9,6 a 12,12 0 0 1 0.3,22.68" /><path stroke="#828487" fill="none" d="M -31,28 m 4,0 h -4 a 20,20 0 1 1 4.88026841,-39.3954371 a 24,24 0 0 1 43.20059379,-9.49083912 a 16.25,16.25 0 0 1 16.9191378,9.88627622 a 20,20 0 0 1 -6.244998,39h -4" /><path stroke-width="3.0" stroke="#404040" fill="none" d="M-23,16.5 h20.0 a6.0,6.0 0 1 0 -6.0,-6.0 M-23,24 h37.5 a6.0,6.0 0 1 0 -6.0,-6.0 M-23,31.5 h28.75 a6.0,6.0 0 1 1 -6.0,6.0" />'
SVG_ICON_FOG = '<path stroke="rgba(111,155,164,90)" stroke-linecap="round" d="M -39,-15 h 78 M -39,-5 h 78 M -39,5 h 78 M -39,15 h 78 " />'
SVG_ICON_WIND = '<path stroke-width="6" stroke="#404040" fill="none" d="M-45,-15 h40 a12,12 0 1 0 -12,-12 M-45,0 h75 a12,12 0 1 0 -12,-12 M-45,15 h57.5 a12,12 0 1 1 -12,12" />'
SVG_ICON_RAIN = '<path stroke="#828487" fill="none" d="M -31,22 m 4,0 h -4 a 20,20 0 1 1 4.88026841,-39.3954371 a 24,24 0 0 1 43.20059379,-9.49083912 a 16.25,16.25 0 0 1 16.9191378,9.88627622 a 20,20 0 0 1 -6.244998,39h -4" /><path stroke="none" fill="#66a1ba" d="M -28,10 h 5 l 22.0,30 h -5 l -22.0,-30 z m 15,0 h 5 l 22.0,30 h -5 l -22.0,-30 z m 15,0 h 5 l 22.0,30 h -5 l -22.0,-30 z " />'
SVG_ICON_DRIZZLE = '<path stroke="#828487" fill="none" d="M -31,22 m 4,0 h -4 a 20,20 0 1 1 4.88026841,-39.3954371 a 24,24 0 0 1 43.20059379,-9.49083912 a 16.25,16.25 0 0 1 16.9191378,9.88627622 a 20,20 0 0 1 -6.244998,39h -4" /><path stroke="#66a1ba" fille="none" stroke-dasharray="4 9" stroke-width="2" d="M -4.5,40 l -22,-30 m 7.5,0 l 22,30 m 7.5,0 l -22,-30 m 7.5,0 l 22,30 m 7.5,0 l -22,-30 " />'
SVG_ICON_HAIL = '<path stroke="#828487" fill="none" d="M -31,22 m 4,0 h -4 a 20,20 0 1 1 4.88026841,-39.3954371 a 24,24 0 0 1 43.20059379,-9.49083912 a 16.25,16.25 0 0 1 16.9191378,9.88627622 a 20,20 0 0 1 -6.244998,39h -4" /><g stroke="none" fill="#66a1ba"><circle cx="-15" cy="37" r="4" /><circle cx="-6" cy="19" r="4" /><circle cx="11" cy="30" r="4" /></g>'
SVG_ICON_SLEET = '<path stroke="#828487" fill="none" d="M -31,22 m 4,0 h -4 a 20,20 0 1 1 4.88026841,-39.3954371 a 24,24 0 0 1 43.20059379,-9.49083912 a 16.25,16.25 0 0 1 16.9191378,9.88627622 a 20,20 0 0 1 -6.244998,39h -4" /><path stroke="#66a1ba" stroke-width="1.5" stroke-linecap="round" fill="none" d="M -13,23 l0.0,20.0 m-8.66025404,-15.0 l17.32050808,10.0 m-17.32050808,-0.0 l17.32050808,-10.0 m-8.66025404,-5.0 m2.88675135,1.66666667 l-2.88675135,1.66666667 l-2.88675135,-1.66666667 m2.88675135,-1.66666667 m-8.66025404,5.0 m2.88675135,-1.66666667 l-0.0,3.33333333 l-2.88675135,1.66666667 m0.0,-3.33333333 m-0.0,10.0 m0.0,-3.33333333 l2.88675135,1.66666667 l0.0,3.33333333 m-2.88675135,-1.66666667 m8.66025404,5.0 m-2.88675135,-1.66666667 l2.88675135,-1.66666667 l2.88675135,1.66666667 m-2.88675135,1.66666667 m8.66025404,-5.0 m-2.88675135,1.66666667 l0.0,-3.33333333 l2.88675135,-1.66666667 m-0.0,3.33333333 m0.0,-10.0 m-0.0,3.33333333 l-2.88675135,-1.66666667 l-0.0,-3.33333333 m2.88675135,1.66666667 m -8.66025404,0.0 m1.44337567,0.83333333 l-1.44337567,0.83333333 l-1.44337567,-0.83333333 m1.44337567,-0.83333333 m -4.33012702,2.5 m1.44337567,-0.83333333 l-0.0,1.66666667 l-1.44337567,0.83333333 m0.0,-1.66666667 m -0.0,5.0 m0.0,-1.66666667 l1.44337567,0.83333333 l0.0,1.66666667 m-1.44337567,-0.83333333 m 4.33012702,2.5 m-1.44337567,-0.83333333 l1.44337567,-0.83333333 l1.44337567,0.83333333 m-1.44337567,0.83333333 m 4.33012702,-2.5 m-1.44337567,0.83333333 l0.0,-1.66666667 l1.44337567,-0.83333333 m-0.0,1.66666667 m 0.0,-5.0 m-0.0,1.66666667 l-1.44337567,-0.83333333 l-0.0,-1.66666667 m1.44337567,0.83333333 " /><path stroke="#66a1ba" fille="none" stroke-dasharray="4 9" stroke-width="2" d="M 13.5,40 l -22,-30 m 7.5,0 l 22,30 m 7.5,0 l -22,-30 m 7.5,0 " />'
SVG_ICON_SNOW = '<path stroke="#828487" fill="none" d="M -31,22 m 4,0 h -4 a 20,20 0 1 1 4.88026841,-39.3954371 a 24,24 0 0 1 43.20059379,-9.49083912 a 16.25,16.25 0 0 1 16.9191378,9.88627622 a 20,20 0 0 1 -6.244998,39h -4" /><path stroke="#66a1ba" stroke-width="1.5" stroke-linecap="round" fill="none" d="M -13,7 l0.0,20.0 m-8.66025404,-15.0 l17.32050808,10.0 m-17.32050808,-0.0 l17.32050808,-10.0 m-8.66025404,-5.0 m2.88675135,1.66666667 l-2.88675135,1.66666667 l-2.88675135,-1.66666667 m2.88675135,-1.66666667 m-8.66025404,5.0 m2.88675135,-1.66666667 l-0.0,3.33333333 l-2.88675135,1.66666667 m0.0,-3.33333333 m-0.0,10.0 m0.0,-3.33333333 l2.88675135,1.66666667 l0.0,3.33333333 m-2.88675135,-1.66666667 m8.66025404,5.0 m-2.88675135,-1.66666667 l2.88675135,-1.66666667 l2.88675135,1.66666667 m-2.88675135,1.66666667 m8.66025404,-5.0 m-2.88675135,1.66666667 l0.0,-3.33333333 l2.88675135,-1.66666667 m-0.0,3.33333333 m0.0,-10.0 m-0.0,3.33333333 l-2.88675135,-1.66666667 l-0.0,-3.33333333 m2.88675135,1.66666667 m -8.66025404,0.0 m1.44337567,0.83333333 l-1.44337567,0.83333333 l-1.44337567,-0.83333333 m1.44337567,-0.83333333 m -4.33012702,2.5 m1.44337567,-0.83333333 l-0.0,1.66666667 l-1.44337567,0.83333333 m0.0,-1.66666667 m -0.0,5.0 m0.0,-1.66666667 l1.44337567,0.83333333 l0.0,1.66666667 m-1.44337567,-0.83333333 m 4.33012702,2.5 m-1.44337567,-0.83333333 l1.44337567,-0.83333333 l1.44337567,0.83333333 m-1.44337567,0.83333333 m 4.33012702,-2.5 m-1.44337567,0.83333333 l0.0,-1.66666667 l1.44337567,-0.83333333 m-0.0,1.66666667 m 0.0,-5.0 m-0.0,1.66666667 l-1.44337567,-0.83333333 l-0.0,-1.66666667 m1.44337567,0.83333333 " /><path stroke="#66a1ba" stroke-width="1.5" stroke-linecap="round" fill="none" d="M 12,0 l0.0,20.0 m-8.66025404,-15.0 l17.32050808,10.0 m-17.32050808,-0.0 l17.32050808,-10.0 m-8.66025404,-5.0 m2.88675135,1.66666667 l-2.88675135,1.66666667 l-2.88675135,-1.66666667 m2.88675135,-1.66666667 m-8.66025404,5.0 m2.88675135,-1.66666667 l-0.0,3.33333333 l-2.88675135,1.66666667 m0.0,-3.33333333 m-0.0,10.0 m0.0,-3.33333333 l2.88675135,1.66666667 l0.0,3.33333333 m-2.88675135,-1.66666667 m8.66025404,5.0 m-2.88675135,-1.66666667 l2.88675135,-1.66666667 l2.88675135,1.66666667 m-2.88675135,1.66666667 m8.66025404,-5.0 m-2.88675135,1.66666667 l0.0,-3.33333333 l2.88675135,-1.66666667 m-0.0,3.33333333 m0.0,-10.0 m-0.0,3.33333333 l-2.88675135,-1.66666667 l-0.0,-3.33333333 m2.88675135,1.66666667 m -8.66025404,0.0 m1.44337567,0.83333333 l-1.44337567,0.83333333 l-1.44337567,-0.83333333 m1.44337567,-0.83333333 m -4.33012702,2.5 m1.44337567,-0.83333333 l-0.0,1.66666667 l-1.44337567,0.83333333 m0.0,-1.66666667 m -0.0,5.0 m0.0,-1.66666667 l1.44337567,0.83333333 l0.0,1.66666667 m-1.44337567,-0.83333333 m 4.33012702,2.5 m-1.44337567,-0.83333333 l1.44337567,-0.83333333 l1.44337567,0.83333333 m-1.44337567,0.83333333 m 4.33012702,-2.5 m-1.44337567,0.83333333 l0.0,-1.66666667 l1.44337567,-0.83333333 m-0.0,1.66666667 m 0.0,-5.0 m-0.0,1.66666667 l-1.44337567,-0.83333333 l-0.0,-1.66666667 m1.44337567,0.83333333 " /><path stroke="#66a1ba" stroke-width="1.5" stroke-linecap="round" fill="none" d="M 5,23 l0.0,20.0 m-8.66025404,-15.0 l17.32050808,10.0 m-17.32050808,-0.0 l17.32050808,-10.0 m-8.66025404,-5.0 m2.88675135,1.66666667 l-2.88675135,1.66666667 l-2.88675135,-1.66666667 m2.88675135,-1.66666667 m-8.66025404,5.0 m2.88675135,-1.66666667 l-0.0,3.33333333 l-2.88675135,1.66666667 m0.0,-3.33333333 m-0.0,10.0 m0.0,-3.33333333 l2.88675135,1.66666667 l0.0,3.33333333 m-2.88675135,-1.66666667 m8.66025404,5.0 m-2.88675135,-1.66666667 l2.88675135,-1.66666667 l2.88675135,1.66666667 m-2.88675135,1.66666667 m8.66025404,-5.0 m-2.88675135,1.66666667 l0.0,-3.33333333 l2.88675135,-1.66666667 m-0.0,3.33333333 m0.0,-10.0 m-0.0,3.33333333 l-2.88675135,-1.66666667 l-0.0,-3.33333333 m2.88675135,1.66666667 m -8.66025404,0.0 m1.44337567,0.83333333 l-1.44337567,0.83333333 l-1.44337567,-0.83333333 m1.44337567,-0.83333333 m -4.33012702,2.5 m1.44337567,-0.83333333 l-0.0,1.66666667 l-1.44337567,0.83333333 m0.0,-1.66666667 m -0.0,5.0 m0.0,-1.66666667 l1.44337567,0.83333333 l0.0,1.66666667 m-1.44337567,-0.83333333 m 4.33012702,2.5 m-1.44337567,-0.83333333 l1.44337567,-0.83333333 l1.44337567,0.83333333 m-1.44337567,0.83333333 m 4.33012702,-2.5 m-1.44337567,0.83333333 l0.0,-1.66666667 l1.44337567,-0.83333333 m-0.0,1.66666667 m 0.0,-5.0 m-0.0,1.66666667 l-1.44337567,-0.83333333 l-0.0,-1.66666667 m1.44337567,0.83333333 " />'
SVG_ICON_FREEZINGRAIN = '<path stroke="#828487" fill="none" d="M -26.349999999999998,4 m 3.4,0 h -3.4 a17.0,17.0 0 1 1 4.1482281485,-33.486121535 a20.4,20.4 0 0 1 36.7205047215,-8.067213252 a13.8125,13.8125 0 0 1 14.381267130000001,8.403334786999999 a17.0,17.0 0 0 1 -5.3082483,33.15 h -3.4" /><path stroke="none" fill="#66a1ba" d="M -27,-7 h 5 l 18.7,25.5 h -5 l -18.7,-25.5 z m 15,0 h 5 l 18.7,25.5 h -5 l -18.7,-25.5 z m 15,0 h 5 l 18.7,25.5 h -5 l -18.7,-25.5 z " /><path stroke="none" fill="#000000" d="M-9.42235138,48 l8.54455967,-4.047423 a6.04100450,6.04100450 0 0 0 2.54603347,-8.64621208 l-3.23725145,-5.21347156 a2.74580363,2.74580363 0 0 1 0.78256116,-3.71485342 l4.93895246,-3.37803994 h-1.38888889 l-5.10795449,2.93585208 a4.68254091,4.68254091 0 0 0 -2.09563466,5.5796135 l2.27226862,6.62156404 a3.29583971,3.29583971 0 0 1 -1.84474537,4.10998876 l-13.74323385,5.75298161 z m33.33333333,0 l1.22771241,-1.22771241 a6.20359314,6.20359314 0 0 0 -1.28480621,-9.75907203 l-13.55967183,-7.82868018 a3.22628070,3.22628070 0 0 1 -1.41857181,-3.89749403 l0.83241498,-2.28704135 h-1.38888889 l-0.68119443,1.08342259 a4.68254091,4.68254091 0 0 0 1.30173924,6.30605466 l12.49300857,8.59055233 a2.68888799,2.68888799 0 0 1 0.13365758,4.33313596 l-5.98873292,4.68683446 z" /><path stroke="#66a1ba" stroke-width="1.2" stroke-linecap="round" fill="none" d="M -17,26 l0.0,16.0 m-6.92820323,-12.0 l13.85640646,8.0 m-13.85640646,-0.0 l13.85640646,-8.0 m-6.92820323,-4.0 m2.30940108,1.33333333 l-2.30940108,1.33333333 l-2.30940108,-1.33333333 m2.30940108,-1.33333333 m-6.92820323,4.0 m2.30940108,-1.33333333 l-0.0,2.66666667 l-2.30940108,1.33333333 m0.0,-2.66666667 m-0.0,8.0 m0.0,-2.66666667 l2.30940108,1.33333333 l0.0,2.66666667 m-2.30940108,-1.33333333 m6.92820323,4.0 m-2.30940108,-1.33333333 l2.30940108,-1.33333333 l2.30940108,1.33333333 m-2.30940108,1.33333333 m6.92820323,-4.0 m-2.30940108,1.33333333 l0.0,-2.66666667 l2.30940108,-1.33333333 m-0.0,2.66666667 m0.0,-8.0 m-0.0,2.66666667 l-2.30940108,-1.33333333 l-0.0,-2.66666667 m2.30940108,1.33333333 " />'
SVG_ICON_LIGHTNING = '<path stroke="#828487" fill="none" d="M -31,28 a 20,20 0 1 1 4.88026841,-39.3954371 a 24,24 0 0 1 43.20059379,-9.49083912 a 16.25,16.25 0 0 1 16.9191378,9.88627622 a 20,20 0 0 1 -6.244998,39z" /><path stroke="none" fill="#f6bc68" d="M -4,16 l 8.03418996,-20.9297804 l -12.4943457,3.34784984 l 6.68617042,-17.41806944 h -5.42818409 l -4.83202054,20.9297804 l 12.02652853,-3.22249861 z" />'
SVG_ICON_N = [
    ('<g stroke="#f6bc68"><circle cx="0" cy="0" r="18" fill="none" /><path d="M 24.0,0.0 L 38.0,0.0 M 16.97056274847714,16.97056274847714 L 26.87005768508881,26.8700576850888 M 0.0,24.0 L 0.0,38.0 M -16.97056274847714,16.97056274847714 L -26.8700576850888,26.87005768508881 M -24.0,0.0 L -38.0,0.0 M -16.97056274847714,-16.97056274847714 L -26.87005768508881,-26.8700576850888 M -0.0,-24.0 L -1e-14,-38.0 M 16.97056274847714,-16.97056274847714 L 26.8700576850888,-26.87005768508881 " /></g>',
     '<path stroke="#da4935" fill="none" d="M 0,-24 a 26,26 0 0 1 -22,39 a 24,24 0 1 0 22,-39 z" />'),
    ('<g stroke="#f6bc68"><path fill="none" d="M 17.4069956,-2.41780574 A 18,18 0 1 0 -5.26007294,10.21428571 M 24.0,-7.0 L 38.0,-7.0 M -16.97056274847714,9.970562748477139 L -26.8700576850888,19.87005768508881 M -24.0,-7.0 L -38.0,-7.0 M -16.97056274847714,-23.97056274847714 L -26.87005768508881,-33.870057685088796 M 0.0,-31.0 L -1e-14,-45.0 M 16.97056274847714,-23.97056274847714 L 26.8700576850888,-33.87005768508881 " /></g><path stroke="#828487" stroke-width="1.8" fill="none" d="M 0,33 a 12,12 0 1 1 2.92816105,-23.63726226 a 14.4,14.4 0 0 1 25.92035627,-5.69450347 a 9.75,9.75 0 0 1 10.15148268,5.93176573 a 12,12 0 0 1 -3.7469988,23.4 z " />',
     '<path stroke="#da4935" fill="none" d="M 19.97705974,-2.12865019 a 24,24 0 0 0 -19.97705974,-28.87134981 a 26,26 0 0 1 -22,39 a 24,24 0 0 0 11.27165715,7.62388061" /><path stroke="#828487" stroke-width="1.8" fill="none" d="M 0,33 a 12,12 0 1 1 2.92816105,-23.63726226 a 14.4,14.4 0 0 1 25.92035627,-5.69450347 a 9.75,9.75 0 0 1 10.15148268,5.93176573 a 12,12 0 0 1 -3.7469988,23.4 z " />'),
    ('<g stroke="#f6bc68"><path fill="none" d="M -18.00252351,-17.73419552 A 14,14 0 1 0 -39.25615559,-6.02718888 M -45.4350288425444,-4.5649711574556004 L -53.21320343559642,3.21320343559643 M -51.0,-18.0 L -62.0,-18.0 M -45.43502884254441,-31.435028842544398 L -53.21320343559643,-39.21320343559642 M -32.0,-37.0 L -32.00000000000001,-48.0 M -18.564971157455602,-31.435028842544412 L -10.78679656440358,-39.21320343559643 " /></g><path stroke="#828487" fill="none" d="M -25,28 a 20,20 0 1 1 4.88026841,-39.3954371 a 24,24 0 0 1 43.20059379,-9.49083912 a 16.25,16.25 0 0 1 16.9191378,9.88627622 a 20,20 0 0 1 -6.244998,39z" />',
     '<path stroke="#da4935" fill="none" d="M -13.88,-23.64 a 24,24 0 0 0 -20.12,-19.36 a 26,26 0 0 1 -22,39 a 24,24 0 0 0 11.44,7.68 m 30.68,-27.32 a 24,24 0 0 0 -20.12,-19.36 " /><path stroke="#828487" fill="none" d="M -25,28 a 20,20 0 1 1 4.88026841,-39.3954371 a 24,24 0 0 1 43.20059379,-9.49083912 a 16.25,16.25 0 0 1 16.9191378,9.88627622 a 20,20 0 0 1 -6.244998,39z" />'),
    ('<g stroke="#f6bc68"><path fill="none" d="M -19.99475974,-23.48547467 A 14,14 0 0 0 -41.65782625,-8.92367394 M -47.0,-12.0 L -58.0,-12.0 M -41.43502884254441,-25.435028842544398 L -49.21320343559643,-33.21320343559642 M -28.0,-31.0 L -28.00000000000001,-42.0 " /></g><path stroke="#828487" stroke-width="1.8" fill="none" d="M 5,-30 a 14.4,14.4 0 0 1 25.8,-5.4 h 2 a 9.75,9.75 0 0 1 9,6 a 12,12 0 0 1 0.3,22.68" /><path stroke="#828487" fill="none" d="M -31,28 a 20,20 0 1 1 4.88026841,-39.3954371 a 24,24 0 0 1 43.20059379,-9.49083912 a 16.25,16.25 0 0 1 16.9191378,9.88627622 a 20,20 0 0 1 -6.244998,39z" />',
     '<path stroke="#da4935" fill="none" d="M -13.88,-23.64 a 24,24 0 0 0 -20.12,-19.36 a 26,26 0 0 1 -22,39 a 24,24 0 0 0 11.44,7.68 m 30.68,-27.32 a 24,24 0 0 0 -20.12,-19.36 " /><path stroke="#828487" stroke-width="1.8" fill="none" d="M 11,-30 a 14.4,14.4 0 0 1 25.8,-5.4 h 2 a 9.75,9.75 0 0 1 9,6 a 12,12 0 0 1 0.3,22.68" /><path stroke="#828487" fill="none" d="M -25,28 a 20,20 0 1 1 4.88026841,-39.3954371 a 24,24 0 0 1 43.20059379,-9.49083912 a 16.25,16.25 0 0 1 16.9191378,9.88627622 a 20,20 0 0 1 -6.244998,39z" />'),
    (SVG_ICON_CLOUDY,SVG_ICON_CLOUDY),
    (SVG_ICON_FOG,SVG_ICON_FOG),
    (SVG_ICON_UNKNOWN,SVG_ICON_UNKNOWN)
]
SVG_ICON_N_WIND = [
    ('<g stroke="#f6bc68"><circle cx="-21" cy="-6" r="18" fill="none" /><path d="M 3.0,-6.0 L 17.0,-6.0 M -4.02943725152286,10.97056274847714 L 5.87005768508881,20.8700576850888 M -21.0,18.0 L -21.0,32.0 M -37.97056274847714,10.97056274847714 L -47.8700576850888,20.87005768508881 M -45.0,-6.0 L -59.0,-6.0 M -37.97056274847714,-22.97056274847714 L -47.87005768508881,-32.8700576850888 M -21.0,-30.0 L -21.00000000000001,-44.0 M -4.02943725152286,-22.97056274847714 L 5.8700576850888,-32.87005768508881 " /></g><path stroke-width="3.0" stroke="#404040" fill="none" d="M13,16.5 h20.0 a6.0,6.0 0 1 0 -6.0,-6.0 M13,24 h37.5 a6.0,6.0 0 1 0 -6.0,-6.0 M13,31.5 h28.75 a6.0,6.0 0 1 1 -6.0,6.0" />',
     '<path stroke="#da4935" fill="none" d="M -23,-35 a 26,26 0 0 1 -22,39 a 24,24 0 1 0 22,-39 z" /><path stroke-width="3.0" stroke="#404040" fill="none" d="M3,7.5 h20.0 a6.0,6.0 0 1 0 -6.0,-6.0 M3,15 h37.5 a6.0,6.0 0 1 0 -6.0,-6.0 M3,22.5 h28.75 a6.0,6.0 0 1 1 -6.0,6.0" />'),
    ('<g stroke="#f6bc68"><path fill="none" d="M -3.5930044000000017,4.58219426 A 18,18 0 1 0 -26.26007294,17.21428571 M 3.0,0.0 L 17.0,0.0 M -37.970562748477136,16.97056274847714 L -47.870057685088796,26.87005768508881 M -45.0,0.0 L -59.0,0.0 M -37.970562748477136,-16.97056274847714 L -47.87005768508881,-26.8700576850888 M -21.0,-24.0 L -21.00000000000001,-38.0 M -4.029437251522861,-16.97056274847714 L 5.870057685088799,-26.87005768508881 " /></g><path stroke="#828487" stroke-width="1.8" fill="none" d="M -21,40 a 12,12 0 1 1 2.92816105,-23.63726226 a 14.4,14.4 0 0 1 25.92035627,-5.69450347 a 9.75,9.75 0 0 1 10.15148268,5.93176573 a 12,12 0 0 1 -3.7469988,23.4 z " /><path stroke-width="3.0" stroke="#404040" fill="none" d="M14,-30.5 h20.0 a6.0,6.0 0 1 0 -6.0,-6.0 M14,-23 h37.5 a6.0,6.0 0 1 0 -6.0,-6.0 M14,-15.5 h28.75 a6.0,6.0 0 1 1 -6.0,6.0" />',
     '<path stroke="#da4935" fill="none" d="M-1.0229402599999986,4.87134981 a 24,24 0 0 0 -19.97705974,-28.87134981 a 26,26 0 0 1 -22,39 a 24,24 0 0 0 11.27165715,7.62388061" /><path stroke="#828487" stroke-width="1.8" fill="none" d="M -21,40 a 12,12 0 1 1 2.92816105,-23.63726226 a 14.4,14.4 0 0 1 25.92035627,-5.69450347 a 9.75,9.75 0 0 1 10.15148268,5.93176573 a 12,12 0 0 1 -3.7469988,23.4 z " /><path stroke-width="3.0" stroke="#404040" fill="none" d="M14,-30.5 h20.0 a6.0,6.0 0 1 0 -6.0,-6.0 M14,-23 h37.5 a6.0,6.0 0 1 0 -6.0,-6.0 M14,-15.5 h28.75 a6.0,6.0 0 1 1 -6.0,6.0" />'),
    ('<g stroke="#f6bc68"><path fill="none" d="M -18.00252351,-17.73419552 A 14,14 0 1 0 -39.25615559,-6.02718888 M -45.4350288425444,-4.5649711574556004 L -53.21320343559642,3.21320343559643 M -51.0,-18.0 L -62.0,-18.0 M -45.43502884254441,-31.435028842544398 L -53.21320343559643,-39.21320343559642 M -32.0,-37.0 L -32.00000000000001,-48.0 M -18.564971157455602,-31.435028842544412 L -10.78679656440358,-39.21320343559643 " /></g><path stroke="#828487" fill="none" d="M -25,28 m 4,0 h -4 a 20,20 0 1 1 4.88026841,-39.3954371 a 24,24 0 0 1 43.20059379,-9.49083912 a 16.25,16.25 0 0 1 16.9191378,9.88627622 a 20,20 0 0 1 -6.244998,39h -4" /><path stroke-width="3.0" stroke="#404040" fill="none" d="M-17,16.5 h20.0 a6.0,6.0 0 1 0 -6.0,-6.0 M-17,24 h37.5 a6.0,6.0 0 1 0 -6.0,-6.0 M-17,31.5 h28.75 a6.0,6.0 0 1 1 -6.0,6.0" />',
     '<path stroke="#da4935" fill="none" d="M -13.88,-23.64 a 24,24 0 0 0 -20.12,-19.36 a 26,26 0 0 1 -22,39 a 24,24 0 0 0 11.44,7.68 m 30.68,-27.32 a 24,24 0 0 0 -20.12,-19.36 " /><path stroke="#828487" fill="none" d="M -25,28 m 4,0 h -4 a 20,20 0 1 1 4.88026841,-39.3954371 a 24,24 0 0 1 43.20059379,-9.49083912 a 16.25,16.25 0 0 1 16.9191378,9.88627622 a 20,20 0 0 1 -6.244998,39h -4" /><path stroke-width="3.0" stroke="#404040" fill="none" d="M-17,16.5 h20.0 a6.0,6.0 0 1 0 -6.0,-6.0 M-17,24 h37.5 a6.0,6.0 0 1 0 -6.0,-6.0 M-17,31.5 h28.75 a6.0,6.0 0 1 1 -6.0,6.0" />'),
    ('<g stroke="#f6bc68"><path fill="none" d="M -19.99475974,-23.48547467 A 14,14 0 0 0 -41.65782625,-8.92367394 M -47.0,-12.0 L -58.0,-12.0 M -41.43502884254441,-25.435028842544398 L -49.21320343559643,-33.21320343559642 M -28.0,-31.0 L -28.00000000000001,-42.0 " /></g><path stroke="#828487" stroke-width="1.8" fill="none" d="M 5,-30 a 14.4,14.4 0 0 1 25.8,-5.4 h 2 a 9.75,9.75 0 0 1 9,6 a 12,12 0 0 1 0.3,22.68" /><path stroke="#828487" fill="none" d="M -31,28 m 4,0 h -4 a 20,20 0 1 1 4.88026841,-39.3954371 a 24,24 0 0 1 43.20059379,-9.49083912 a 16.25,16.25 0 0 1 16.9191378,9.88627622 a 20,20 0 0 1 -6.244998,39h -4" /><path stroke-width="3.0" stroke="#404040" fill="none" d="M-23,16.5 h20.0 a6.0,6.0 0 1 0 -6.0,-6.0 M-23,24 h37.5 a6.0,6.0 0 1 0 -6.0,-6.0 M-23,31.5 h28.75 a6.0,6.0 0 1 1 -6.0,6.0" />',
     '<path stroke="#da4935" fill="none" d="M -13.88,-23.64 a 24,24 0 0 0 -20.12,-19.36 a 26,26 0 0 1 -22,39 a 24,24 0 0 0 11.44,7.68 m 30.68,-27.32 a 24,24 0 0 0 -20.12,-19.36 " /><path stroke="#828487" stroke-width="1.8" fill="none" d="M 11,-30 a 14.4,14.4 0 0 1 25.8,-5.4 h 2 a 9.75,9.75 0 0 1 9,6 a 12,12 0 0 1 0.3,22.68" /><path stroke="#828487" fill="none" d="M -25,28 m 4,0 h -4 a 20,20 0 1 1 4.88026841,-39.3954371 a 24,24 0 0 1 43.20059379,-9.49083912 a 16.25,16.25 0 0 1 16.9191378,9.88627622 a 20,20 0 0 1 -6.244998,39h -4" /><path stroke-width="3.0" stroke="#404040" fill="none" d="M-17,16.5 h20.0 a6.0,6.0 0 1 0 -6.0,-6.0 M-17,24 h37.5 a6.0,6.0 0 1 0 -6.0,-6.0 M-17,31.5 h28.75 a6.0,6.0 0 1 1 -6.0,6.0" />'),
    (SVG_ICON_CLOUDY_WIND,SVG_ICON_CLOUDY_WIND),
    (SVG_ICON_FOG,SVG_ICON_FOG),
    (SVG_ICON_UNKNOWN,SVG_ICON_UNKNOWN)
]

def svg_icon_n(okta, night=False, width=128, text=None, x=None, y=None, wind=0):
    try:
        height = width * 0.78125
        night = 1 if night else 0
        idx = (0,1,1,2,2,2,3,3,4,5,6)[okta]
        text = ('<title>%s</title><rect x="-64" y="-50" width="100%%" height="100%%" stroke="none" fill="#000000" fill-opacity="0" />' % text) if text else ''
        coord = ('x="%s" y="%s"' % (x,y)) if x is not None and y is not None else ''
        icon = SVG_ICON_N_WIND if wind else SVG_ICON_N
        return ((SVG_ICON_START % (coord,width,height,text))+
            icon[idx][night]+
            SVG_ICON_END)
    except (ArithmeticError,LookupError,TypeError,ValueError):
        return ""

SVG_ICON_WW = [
    # 00
    None,
    # 01
    None,
    # 02
    None,
    # 03
    None,
    # 04
    None,
    # 05
    None,
    # 06
    None,
    # 07
    None,
    # 08
    None,
    # 09
    SVG_ICON_WIND,
    # 10
    None,
    # 11
    SVG_ICON_FOG,
    # 12
    SVG_ICON_FOG,
    # 13
    SVG_ICON_LIGHTNING,
    # 14
    None,
    # 15
    None,
    # 16
    None,
    # 17
    SVG_ICON_LIGHTNING,
    # 18
    SVG_ICON_WIND,
    # 19
    '',
    # 20
    None,
    # 21
    None,
    # 22
    None,
    # 23
    None,
    # 24
    None,
    # 25
    None,
    # 26
    None,
    # 27
    None,
    # 28
    None,
    # 29
    None,
    # 30
    SVG_ICON_WIND,
    # 31
    SVG_ICON_WIND,
    # 32
    SVG_ICON_WIND,
    # 33
    SVG_ICON_WIND,
    # 34
    SVG_ICON_WIND,
    # 35
    SVG_ICON_WIND,
    # 36
    SVG_ICON_WIND,
    # 37
    SVG_ICON_WIND,
    # 38
    SVG_ICON_WIND,
    # 39
    SVG_ICON_WIND,
    # 40
    SVG_ICON_FOG,
    # 41
    SVG_ICON_FOG,
    # 42
    SVG_ICON_FOG,
    # 43
    SVG_ICON_FOG,
    # 44
    SVG_ICON_FOG,
    # 45
    SVG_ICON_FOG,
    # 46
    SVG_ICON_FOG,
    # 47
    SVG_ICON_FOG,
    # 48
    SVG_ICON_FOG,
    # 49
    SVG_ICON_FOG,
    # 50
    SVG_ICON_DRIZZLE,
    # 51
    SVG_ICON_DRIZZLE,
    # 52
    SVG_ICON_DRIZZLE,
    # 53
    SVG_ICON_DRIZZLE,
    # 54
    SVG_ICON_DRIZZLE,
    # 55
    SVG_ICON_DRIZZLE,
    # 56
    SVG_ICON_FREEZINGRAIN,
    # 57
    SVG_ICON_FREEZINGRAIN,
    # 58
    SVG_ICON_RAIN,
    # 59
    SVG_ICON_RAIN,
    # 60
    SVG_ICON_RAIN,
    # 61
    SVG_ICON_RAIN,
    # 62
    SVG_ICON_RAIN,
    # 63
    SVG_ICON_RAIN,
    # 64
    SVG_ICON_RAIN,
    # 65
    SVG_ICON_RAIN,
    # 66
    SVG_ICON_FREEZINGRAIN,
    # 67
    SVG_ICON_FREEZINGRAIN,
    # 68
    SVG_ICON_SLEET,
    # 69
    SVG_ICON_SLEET,
    # 70
    SVG_ICON_SNOW,
    # 71
    SVG_ICON_SNOW,
    # 72
    SVG_ICON_SNOW,
    # 73
    SVG_ICON_SNOW,
    # 74
    SVG_ICON_SNOW,
    # 75
    SVG_ICON_SNOW,
    # 76
    None,
    # 77
    SVG_ICON_SNOW,
    # 78
    SVG_ICON_SNOW,
    # 79
    SVG_ICON_HAIL,
    # 80
    SVG_ICON_RAIN,
    # 81
    SVG_ICON_RAIN,
    # 82
    SVG_ICON_RAIN,
    # 83
    SVG_ICON_SLEET,
    # 84
    SVG_ICON_SLEET,
    # 85
    SVG_ICON_SNOW,
    # 86
    SVG_ICON_SNOW,
    # 87
    SVG_ICON_HAIL,
    # 88
    SVG_ICON_HAIL,
    # 89
    SVG_ICON_HAIL,
    # 90
    SVG_ICON_HAIL,
    # 91
    SVG_ICON_RAIN,
    # 92
    SVG_ICON_RAIN,
    # 93
    SVG_ICON_SNOW,
    # 94
    SVG_ICON_SNOW,
    # 95
    '<path stroke="#828487" fill="none" d="M -31,22 m 4,0 h -4 a 20,20 0 1 1 4.88026841,-39.3954371 a 24,24 0 0 1 43.20059379,-9.49083912 a 16.25,16.25 0 0 1 16.9191378,9.88627622 a 20,20 0 0 1 -6.244998,39h -4" /><path stroke="none" fill="#f6bc68" d="M -4,6 l 8.03418996,-20.9297804 l -12.4943457,3.34784984 l 6.68617042,-17.41806944 h -5.42818409 l -4.83202054,20.9297804 l 12.02652853,-3.22249861 z" /><path stroke="none" fill="#66a1ba" d="M -28,10 h 5 l 22.0,30 h -5 l -22.0,-30 z m 15,0 h 5 l 22.0,30 h -5 l -22.0,-30 z m 15,0 h 5 l 22.0,30 h -5 l -22.0,-30 z " />',
    # 96
    '<path stroke="#828487" fill="none" d="M -31,22 m 4,0 h -4 a 20,20 0 1 1 4.88026841,-39.3954371 a 24,24 0 0 1 43.20059379,-9.49083912 a 16.25,16.25 0 0 1 16.9191378,9.88627622 a 20,20 0 0 1 -6.244998,39h -4" /><path stroke="none" fill="#f6bc68" d="M -4,6 l 8.03418996,-20.9297804 l -12.4943457,3.34784984 l 6.68617042,-17.41806944 h -5.42818409 l -4.83202054,20.9297804 l 12.02652853,-3.22249861 z" /><g stroke="none" fill="#66a1ba"><circle cx="-15" cy="37" r="4" /><circle cx="-6" cy="19" r="4" /><circle cx="11" cy="30" r="4" /></g>',
    # 97
    '<path stroke="#828487" fill="none" d="M -31,22 m 4,0 h -4 a 20,20 0 1 1 4.88026841,-39.3954371 a 24,24 0 0 1 43.20059379,-9.49083912 a 16.25,16.25 0 0 1 16.9191378,9.88627622 a 20,20 0 0 1 -6.244998,39h -4" /><path stroke="none" fill="#f6bc68" d="M -4,6 l 8.03418996,-20.9297804 l -12.4943457,3.34784984 l 6.68617042,-17.41806944 h -5.42818409 l -4.83202054,20.9297804 l 12.02652853,-3.22249861 z" /><path stroke="none" fill="#66a1ba" d="M -28,10 h 5 l 22.0,30 h -5 l -22.0,-30 z m 15,0 h 5 l 22.0,30 h -5 l -22.0,-30 z m 15,0 h 5 l 22.0,30 h -5 l -22.0,-30 z " />',
    # 98
    SVG_ICON_LIGHTNING,
    # 99
    '<path stroke="#828487" fill="none" d="M -31,22 m 4,0 h -4 a 20,20 0 1 1 4.88026841,-39.3954371 a 24,24 0 0 1 43.20059379,-9.49083912 a 16.25,16.25 0 0 1 16.9191378,9.88627622 a 20,20 0 0 1 -6.244998,39h -4" /><path stroke="none" fill="#f6bc68" d="M -4,6 l 8.03418996,-20.9297804 l -12.4943457,3.34784984 l 6.68617042,-17.41806944 h -5.42818409 l -4.83202054,20.9297804 l 12.02652853,-3.22249861 z" /><g stroke="none" fill="#66a1ba"><circle cx="-15" cy="37" r="4" /><circle cx="-6" cy="19" r="4" /><circle cx="11" cy="30" r="4" /></g>',
]

def svg_icon_ww(ww, width=128, text=None, x=None, y=None):
    try:
        height = width * 0.78125
        text = ('<title>%s</title><rect x="-64" y="-50" width="100%%" height="100%%" stroke="none" fill="#000000" fill-opacity="0" />' % text) if text else ''
        coord = ('x="%s" y="%s"' % (x,y)) if x is not None and y is not None else ''
        return ((SVG_ICON_START % (coord,width,height,text))+
            SVG_ICON_WW[ww]+
            SVG_ICON_END)
    except (ArithmeticError,LookupError,TypeError,ValueError):
        return ""






# The list is sorted by severity.
# ww, german description, English description, severity, Belchertown icon, DWD icon, Aeris icon, Aeris coded weather
WW_LIST = [
    # ::FC ::TO
    (19,'Tornado (Windhose), Trichterwolke','funnel clouds (tornado)',None,'tornado.png','18.png','','::FC','wi-tornado'),
    # 95...99 thunderstorm at time of observation
    (99,'schweres Gewitter mit Hagel','heavy thunderstorm with hail',None,'thunderstorm.png','30.png','tstorm',':H:T','wi-thunderstorm'),
    (98,'Gewitter mit Staub- oder Standsturm','thunderstorm with duststorm or sandstorm',None,'thunderstorm.png','27.png','tstorm','::T','wi-thunderstorm'),
    (97,'schweres Gewitter mit Regen oder Schnee','heavy thunderstorm with rain or snow',None,'thunderstorm.png','28.png','tstorm',':H:T','wi-thunderstorm'),
    (96,'leichtes oder mäßiges Gewitter mit Hagel','slight or moderate thunderstorm with hail',None,'thunderstorm.png','29.png','tstorm',':L:T','wi-thunderstorm'),
    (95,'leichtes oder mäßiges Gewitter mit Regen oder Schnee','slight or moderate thunderstorm with rain or snow',1,'thunderstorm.png','27.png','tstorm',':L:T','wi-thunderstorm'),
    # 50...59 drizzle (here: freezing drizzle)
    (57,'mäßiger oder starker gefrierender Sprühregen','Drizzle, freezing, moderate or heavy (dence)',2,'sleet.png','67.png','freezingrain',':H:ZL','wi-sleet'),
    (56,'leichter gefrierender Sprühregen','Drizzle, freezing, slight',3,'sleet.png','66.png','freezingrain',':L:ZL','wi-sleet'),
    # 60...69 rain (here: freezing rain)
    (67,'mäßiger bis starker gefrierender Regen','Rain, freezing, moderate or heavy (dence)',4,'sleet.png','67.png','freezingrain',':H:ZR','wi-sleet'),
    (66,'leichter gefrierender Regen','Rain, freezing, slight',5,'sleet.png','66.png','freezingrain',':L:ZR','wi-sleet'),
    # 20...29 events during the preceding hour but not now
    # 24 freezing drizzle or freezing rain ::ZL ::ZR
    (24,'nach gefrierendem Regen','after freezing drizzle or freezing rain',None,None,'eis.png',None,'::ZR',''),
    # 80...90 shower(s) or precipitation with current or recent thunderstorm
    (90,'kräftige Hagelschauer','moderate or heavy shower(s) of hail',None,'hail.png','17.png','hail',':H:A','wi-hail'),
    (89,'leichte Hagelschauer','slight shower(s) of hail',None,'hail.png','17.png','hail',':L:A','wi-hail'),
    (88,'kräftige Graupelschauer','moderate or heavy shower(s) of snow pellets',None,'snow.png','86.png','snow',':H:A','wi-hail'),
    (87,'leichte Graupelschauer','slight shower(s) of snow pellets',None,'snow.png','85.png','snow',':L:A','wi-hail'),
    # 70...79
    # 79 Eiskörner
    (79,'Niederschlag in Form von Eiskörnern','ice pellets',None,'snow.png','85.png','snow',':L:A','wi-hail'),
    # 91...94 thunderstorm during the preceding hour but not at time of observation
    (94,'Schnee, Schneeregen oder Hagel nach einem Gewitter','snow, or rain and snow mixed or hail after thunderstorm',None,'snow.png','27.png','snow',':H:T','wi-snow'),
    (93,'leichter Schnee, Schneeregen oder Hagel nach einem Gewitter','slight snow, or rain and snow mixed or hail after thunderstorm',None,'snow.png','27.png','snow',':L:T','wi-snow'),
    (92,'kräftiger Regen nach Gewitter','moderate or heavy rain after thunderstorm',None,'rain.png','27.png','rain',':H:T','wi-rain'),
    (91,'leichter Regen nach Gewitter','slight rain after thunderstorm',None,'rain.png','27.png','rain',':L:T','wi-rain'),
    # 80...90 shower(s) or precipitation with current or recent thunderstorm
    (86,'mäßiger bis starker Schneeschauer','Snow shower(s), moderate or heavy',6,'snow.png','86.png','snowshowers',':H:SW','wi-snow'),
    (85,'leichter Schneeschauer','Snow shower(s), slight',7,'snow.png','85.png','snowshowers',':L:SW','wi-snow'),
    (84,'mäßiger oder starker Schneeregenschauer','Shower(s) of rain and snow mixed, moderate or heavy',8,'sleet.png','84.png','wintrymix',':H:RS','wi-sleet'),
    (83,'leichter Schneeregenschauer','Shower(s) of rain and snow mixed, slight',9,'sleet.png','83.png','wintrymix',':L:RS','wi-sleet'),
    (82,'äußerst heftiger Regenschauer','extremely heavy rain shower',10,'rain.png','82.png','showers',':VH:RW','wi-showers'),
    (81,'mäßiger oder starker Regenschauer','moderate or heavy rain showers',11,'rain.png','82.png','showers',':H:RW','wi-showers'),
    (80,'leichter Regenschauer','slight rain shower',12,'rain.png','80.png','showers',':L:RW','wi-showers'),
    # 70...79 solid precipitation not in showers
    (75,'durchgehend starker Schneefall','heavy snowfall, continuous',13,'snow.png','16.png','snow',':H:S','wi-snow'),
    (74,'intermittierend starker Schneefall','heavy snowfall, intermittent',None,'snow.png','16.png','snow','IN:H:S','wi-snow'),
    (73,'durchgehend mäßiger Schneefall','moderate snowfall, continuous',14,'snow.png','15.png','snow','::S','wi-snow'),
    (72,'intermittierend mäßiger Schneefall','moderate snowfall, intermittent',None,'snow.png','15.png','snow','IN::S','wi-snow'),
    (71,'durchgehend leichter Schneefall','slight snowfall, continuous',15,'snow.png','14.png','snow',':L:S','wi-snow'),
    (70,'intermittierend leichter Schneefall','slight snowfall, intermittent',None,'snow.png','14.png','snow','IN:L:S','wi-snow'),
    # 60...69 rain
    (69,'mäßger oder starker Schneeregen','moderate or heavy rain and snow',16,'sleet.png','13.png','rainandsnow',':H:RS','wi-sleet'),
    (68,'leichter Schneeregen','slight rain and snow',17,'sleet.png','12.png','rainandsnow',':L:RS','wi-sleet'),
    # 50...59 drizzle
    (59,'starker Sprühregen und Regen','moderate or heavy drizzle and rain',None,'rain.png','','rain','','wi-rain'),
    (58,'leichter Sprühregen und Regen','slight drizzle and rain',None,'rain.png','','rain','','wi-rain'),
    (55,'durchgehend starker Sprühregen','heavy drizzle, not freezing, continuous',18,'drizzle.png','9.png','drizzle',':H:L','wi-sprinkle'),
    (54,'intermittierend starker Sprühregen','heavy drizzle, not freezing, intermittent',None,'drizzle.png','9.png','drizzle','IN:H:L','wi-sprinkle'),
    (53,'durchgehend mäßiger Sprühregen','moderate drizzle, not freezing, continuous',19,'drizzle.png','8.png','drizzle','::L','wi-sprinkle'),
    (52,'intermittierend mäßiger Sprühregen','moderate drizzle, not freezing, intermittent',None,'drizzle.png','8.png','drizzle','IN::L','wi-sprinkle'),
    (51,'durchgehend leichter Sprühregen','slight drizzle, not freezing, continuous',20,'drizzle.png','7.png','drizzle',':L:L','wi-sprinkle'),
    (50,'intermittierend leichter Sprühregen','slight drizzle, not freezing, intermittent',None,'drizzle.png','7.png','drizzle','IN:L:L','wi-sprinkle'),
    # 60...69 rain
    (65,'durchgehend starker Regen','heavy rain, not freezing, continuous',21,'rain.png','9.png','rain',':H:R','wi-rain'),
    (64,'intermittierend starker Regen','heavy rain, not freezing, intermittent',None,'rain.png','9.png','rain','IN:H:R','wi-rain'),
    (63,'durchgehend mäßiger Regen','moderate rain, not freezing, continuous',22,'rain.png','8.png','rain','::R','wi-rain'),
    (62,'intermittierend mäßiger Regen','moderate rain, not freezing, intermittent',None,'rain.png','8.png','rain','IN::R','wi-rain'),
    (61,'durchgehend leichter Regen','slight rain, not freezing, continuous',23,'rain.png','7.png','rain',':L:R','wi-rain'),
    (60,'intermittierend leichter Regen','slight rain, not freezing, intermittent',None,'rain.png','7.png','rain','IN:L:R','wi-rain'),
    
    (78,'einzelne Schneeflocken, mit oder ohne Nebel','isolated star-like snow crystals with or without fog',None,'snow.png','14.png','snow',':L:S','wi-snow'),
    (77,'Schneegriesel, mit oder ohne Nebel','snow grains with or without fog',None,'snow.png','14.png','snow',':L:S','wi-snow'),
    (76,'Eisnadeln (auch Diamantstaub genannt), mit oder ohne Nebel','diamond dust with our without fog',None,'fog.png','','dust','','wi-fog'),

    # 49 in MOSMIX
    (49,'Nebel mit Reifansatz, Himmel nicht erkennbar, unverändert','Ice Fog, sky not recognizable',24,'fog.png','48.png','fog','::IF','wi-fog'),
    # 49 fog, despositing rime, sky invisible
    (48,'Nebel mit Reifansatz, Himmel erkennbar','fog depositing rime, sky visible',None,'fog.png','48.png','fog','::IF','wi-fog'),
    (47,'Nebel oder Eisnebel, Himmel nicht erkennbar, zunehmend','fog or ice fog, sky invisible, has become thicker',None,'fog.png','48.png','fog','::IF','wi-fog'),
    (46,'Nebel oder Eisnebel, Himmel erkennbar, zunehmend','fog or ice fog, sky visible, has become thicker',None,'fog.png','48.png','fog','::IF','wi-fog'),
    # 45 in MOSMIX
    (45,'Nebel, Himmel nicht erkennbar','Fog, sky not recognizable',25,'fog.png','40.png','fog','::F','wi-fog'),
    # 45 fog or ice fog, sky invisible, no appreciable change during the preceding hour
    (44,'Nebel oder Eisnebel, Himmel erkennbar, unverändert','fog or ice fog, sky visible, no change',None,'fog.png','40.png','fog','::F','wi-fog'), 
    (43,'Nebel oder Eisnebel, Himmel nicht erkennbar, abnehmend','fog or ice fog, sky invisible, has become thinner',None,'fog.png','40.png','fog','::F','wi-fog'),
    (42,'Nebel oder Eisnebel, Himmel erkennbar, abnehmend','fog or ice fog, sky visible, has become thinner',None,'fog.png','40.png','fog','::F','wi-fog'),
    (41,'stellenweise Nebel oder Eisnebel','fog or ice fog in patches',None,'fog.png','40.png','fog','PA::F','wi-fog'),
    (40,'Nebel oder Eisnebel in der Entfernung','fog or ice fog at a distance',None,'fog.png','40.png','fog','VC::F','wi-fog'),
    
    # duststorm, sandstorm, drifting or blowing snow
    # 39 heavy drifting snow, generally high (above eye level) :H:BS
    (39,'starkes Schneefegen, oberhalb Augenhöhe','heavy drifting snow, generally high (above eye level)',None,'wind.png','18.png','blowingsnow',':H:BS','wi-snow-wind'),
    # 38 slight or moderate blowing snow, generally high (above eye level) :L:BS
    (38,'Schneefegen, oberhalb Augenhöhe','slight or moderate blowing snow, generally high (above eye level)',None,'wind.png','18.png','blowingsnow',':L:BS','wi-snow-wind'),
    # 37 heavy drifting snow, generally low (below eye level) :H:BS
    (37,'starkes Schneefegen unterhalb Augenhöhe','heavy drifting snow, generally low (below eye level',None,'wind.png','18.png','blowingsnow',':H:BS','wi-snow-wind'),
    # 36 slight or moderate blowing snow, generally low (below eye level) :L:BS
    (36,'Schneefegen unterhalb Augenhöhe','slight or moderate blowing snow, generally low (below eye level)',None,'wind.png','18.png','blowingsnow',':L:BS','wi-snow-wind'),
    # 35 severe duststorm or sandstorm, increasing
    (35,'schwerer Staub- oder Sandsturm, zunehmend','severe duststorm or sandstorm, increasing',None,'wind.png','18.png','wind',':H:BD','wi-sandstorm'),
    # 34 severe duststorm or sandstorm, no change :H:BD :H:BN
    (34,'schwerer Staub- oder Sandsturm, unverändert','severe duststorm or sandstorm, no change',None,'wind.png','18.png','wind',':H:BD','wi-sandstorm'),
    # 33 severe duststorm or sandstorm, decreasing
    (33,'schwerer Staub- oder Sandsturm, abnehmend','severe duststorm or sandstorm, decreasing',None,'wind.png','18.png','wind',':H:BD','wi-sandstorm'),
    # 32 slight or moderate duststorm or sandstorm, increasing
    (32,'leichter oder mittlerer Staub- oder Sandsturm, zunehmend','slight or moderate duststorm or sandstorm, increasing',None,'wind.png','18.png','wind',':L:BD','wi-sandstorm'),
    # 31 slight or moderate duststorm or sandstorm, no change :L:BD :L:BN
    (31,'leichter oder mittlerer Staub- oder Sandsturm, unverändert','slight or moderate duststorm or sandstorm, no change',None,'wind.png','18.png','wind',':L:BD','wi-sandstorm'),
    # 30 slight or moderate duststorm or sandstorm, decreasing
    (30,'leichter oder mittlerer Staub- oder Sandsturm, abnehmend','slight or moderate duststorm or sandstorm, decreasing',None,'wind.png','18.png','wind',':L:BD','wi-sandstorm'),
    
    (18,'Böen','squalls',None,'wind.png','18.png','wind','','wi-strong-wind'),

    (17,'Gewitter ohne Niederschlag','thunderstorm, but no precipitation',None,'thunderstorm.png','26.png','tstorm','VC::T','wi-lightning'),
    (16,'Niederschläge in Sichtweite aber nicht an der Station, den Boden erreichend','Precipitation within sight, reaching the ground or the surface of the sea, near to, but not at the station',None,None,None,None,None,None),
    (15,'Niederschläge in Sichtweite, aber entfernt, den Boden erreichend','Precipitation within sight, reaching the ground or the surface of the sea, but distant, i.e.  estimated to be more than 5 km from the station',None,None,None,None,None,None),
    (14,'Niederschläge in Sichtweite, nicht den Boden erreichend','Precipitation within sight, not reaching the ground or the surface of the sea',None,None,None,None,None,None),
    (13,'Wetterleuchten','lightning visible, no thunder heard',None,None,'26.png',None,'VC::T','wi-lightning'),
    (12,'flacher Nebel','shallow fog or ice fog',None,'fog.png','40.png','fog','::BR',''),
    (11,'Nebelschwaden','patches of fog or ice fog',None,'fog.png','40.png','fog','PA::BR','wi-fog'),
    (10,'feuchter Dunst','mist',None,None,None,'fog','::BR','wi-fog'),
    (9,'Staub- oder Sandsturm in Sichtweite','duststorm or sandstorm in sight',None,'wind.png','18.png','wind','VC::BD','wi-sandstorm'),
    (8,'kleine Wirbel mit Staub oder Sand','well developed dust whirl(s) or sand whirls(s)',None,None,None,None,'VC::BD','wi-windy'),
    (7,'Staub oder Sand aufgewirbelt in der Luft','dust or sand raised by wind',None,None,None,'dust','::BD','wi-windy'),
    (6,'Staub in der Luft, kein Wind','widespread dust in suspension in the air, not raised by wind',None,None,None,'dust','::H','wi-dust'),
    (5,'trockener Dunst','haze',None,None,None,'hazy','::H','wi-dust'),
    (4,'durch Rauch oder Vulkanasche eingeschränkte Sicht','visbility reduced by smoke or volcanic ashes',None,'fog.png','40.png','smoke','::K','wi-smog'),
    
    # 20...29 events during the preceding hour but not now
    # 29 thunderstorm with or without precipitation ::T
    (29,'nach Gewitter','after thunderstorm',None,None,None,None,'::T',''),
    # 28 fog or ice fog ::F ::IF
    (28,'nach Nebel oder Eisnebel','after fog or ice fog',None,None,None,None,'::F',''),
    # 27 shower(s) of hail, or of rain and hail ::A
    (27,'nach Hagelschauer','after shower(s) of hail',None,None,None,None,'::A',''),
    # 26 shower(s) of snow, or of rain and snow ::SW
    (26,'nach Schneeschauer','after shower(s) of snow or rain and snow',None,None,None,None,'::SW',''),
    # 25 shower(s) of rain ::RW
    (25,'nach Regenschauer','after shower(s) of rain',None,None,None,None,'::RW',''),
    # 23 rain and snow or ice pellets, not falling as shower(s) ::SI
    (23,'nach Schneeregen','after rain and snow or ice pellets',None,None,None,None,'::SI',''),
    # 22 snow, not falling as shower(s) ::S
    (22,'nach Schneefall','after snow fall',None,None,None,None,'::S',''),
    # 21 rain (not freezing,''), not falling as shower(s) ::R
    (21,'nach Regen','after rain',None,None,None,None,'::R',''),
    # 20 drizzle (not freezing) or snow grains, not falling as shower(s) ::L
    (20,'nach Sprühregen','after drizzle',None,None,None,None,'::L',''),
    
    # clouds and cloud development
    (3,'Bewölkung zunehmend','Clouds generally forming or developing',26,None,None,None,None,None),
    (2,'Bewölkung unverändert','State of sky on the whole unchanged',27,None,None,None,None,None),
    (1,'Bewölkung abnehmend','Clouds generally dissolving or becoming less developed',28,None,None,None,None,None),
    (0,'keine Bewölkungsentwicklung','no cloud cover development',29,None,None,None,None,None)
]

N_ICON_LIST = [
    # Belchertown day, night, DWD, Aeris coded weather, Aeris, E. Flowers day, night
    # 0...7%     0/8
    ('clear-day.png','clear-night.png','0-8.png','::CL','clear','wi-day-sunny','wi-night-clear'),
    # 7...32%    1/8 2/8
    ('mostly-clear-day.png','mostly-clear-night.png','2-8.png','::FW','fair','wi-day-sunny-overcast','wi-night-alt-partly-cloudy'),
    # 32...70%   3/8 4/8 5/8
    ('partly-cloudy-day.png','partly-cloudy-night.png','5-8.png','::SC','pcloudy','wi-day-cloudy','wi-night-cloudy'),
    # 70...95%   6/8 7/8
    ('mostly-cloudy-day.png','mostly-cloudy-night.png','5-8.png','::BK','mcloudy','wi-day-cloudy','wi-night-cloudy'),
    # 95...100%  8/8
    ('cloudy.png','cloudy.png','8-8.png','::OV','cloudy','wi-cloudy','wi-cloudy')
]

WW_SECTIONS = {
    0:('Wolken und Bewölkungsentwicklung','clouds and cloud development'),
    4:('Dunst oder Staub','dust or haze'),
    13:('entfernte Wettererscheinungen','distant weather'),
    18:('besondere Windereignisse','remarkable wind events'),
    20:('Niederschlag in der letzten Stunde aber jetzt nicht mehr','events during the preceding hour but not now'),
    30:('Staubsturm, Sandsturm, Schneefegen','duststorm, sandstorm, drifting or blowing snow'),
    40:('Nebel oder Eisnebel in verschiedenen Ausführungen','fog or ice fog'),
    50:('Sprühregen','drizzle'),
    60:('Regen','rain'),
    70:('feste Niederschläge, nicht in Form von Schauern','solid precipitation not in showers'),
    80:('Schauer','shower(s)'),
    91:('Gewitter während der letzten Stunde, jetzt nur noch Niederschläge','thunderstorm during the preceding hour but not at the time of observation'),
    95:('Gewitter jetzt','thunderstorm at the time of observation')
}
WW_XML = '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">\n'
WW_SYMBOLS = [
    # 00 https://upload.wikimedia.org/wikipedia/commons/a/ab/Symbol_code_ww_00.svg
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 00-09 General Group: No precipitation, fog, duststorm, sandstorm, drifting or blowing snow at the station at the time of observation or, except for 09 during the preceeding hour. 	Code: 00 	Description: Cloud development NOT observed or NOT observable during past hour (not plotted) </desc> <g id="ww_00" fill="none" stroke-width="3" stroke="currentColor" > 	<circle r="17"/> </g> </svg> ',
    # 01 https://upload.wikimedia.org/wikipedia/commons/7/7d/Symbol_code_ww_01.svg
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 00-09 General Group: No precipitation, fog, duststorm, sandstorm, drifting or blowing snow at the station at the time of observation or, except for 09 during the preceeding hour. 	Code: 01 	Description: Clouds generally dissolving or becoming less developed during past hour (not plotted) </desc> <g id="ww_01" fill="none" stroke-width="3" stroke="currentColor" > 	<circle r="17"/> 	<path d="M 0,17 v 8"/> </g> </svg> ',
    # 02 https://upload.wikimedia.org/wikipedia/commons/f/f1/Symbol_code_ww_02.svg
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 00-09 General Group: No precipitation, fog, duststorm, sandstorm, drifting or blowing snow at the station at the time of observation or, except for 09 during the preceeding hour. 	Code: 02 	Description: State of sky on the whole unchanged during past hour (not plotted) </desc> <g id="ww_02" fill="none" stroke-width="3" stroke="currentColor" > 	<circle r="17"/> 	<path d="M 17,0 h 8"/> 	<path d="M -17,0 h -8"/> </g> </svg> ',
    # 03 https://upload.wikimedia.org/wikipedia/commons/9/99/Symbol_code_ww_03.svg
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 00-09 General Group: No precipitation, fog, duststorm, sandstorm, drifting or blowing snow at the station at the time of observation or, except for 09 during the preceeding hour. 	Code: 03 	Description: Clouds generally forming or developing during past hour (not plotted) </desc> <g id="ww_03" fill="none" stroke-width="3" stroke="currentColor" > 	<circle r="17"/> 	<path d="M 0,-17 v -8"/> </g> </svg> ',
    # 04 https://upload.wikimedia.org/wikipedia/commons/e/e3/Symbol_code_ww_04.svg
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 00-09 General Group: No precipitation, fog, duststorm, sandstorm, drifting or blowing snow at the station at the time of observation or, except for 09 during the preceeding hour. 	Code: 04 	Description: Visibility reduced by smoke </desc> <g id="ww_04" fill="none" stroke-width="3" stroke="currentColor" > 	<path d="M -19.5,22.5 v -39 a 4.5,4.5 0 0,1 9,0 a 4.5,4.5 0 0,0 9,0 a 4.5,4.5 0 0,1 9,0 a 4.5,4.5 0 0,0 9,0 a 4.5,4.5 0 0,1 4.5,-4.5"/> </g> </svg> ',
    # 05 Haze
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc>WMO 4677 ww 05</desc> <path fill="none" stroke-width="3" stroke="currentColor" d="M 0,0 a 17.705691893392046,34 0 0 1 -12,9 a 9,9 0 0 1 0,-18 a 17.705691893392046,34 0 0 1 12,9 a 17.705691893392046,34 0 0 0 12,9 a 9,9 0 0 0 0,-18 a 17.705691893392046,34 0 0 0 -12,9 z" /> </svg>',
    # 06 https://upload.wikimedia.org/wikipedia/commons/8/8d/Symbol_code_ww_06.svg
    ##'<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 00-09 General Group: No precipitation, fog, duststorm, sandstorm, drifting or blowing snow at the station at the time of observation or, except for 09 during the preceeding hour. 	Code: 06 	Description: Widespread dust in suspension in the air, not raised by wind at or near the station at the time of observation </desc> <g id="ww_06" fill="none" stroke-width="3" stroke="currentColor" > 	<path d="M 12,-12 a 12,12 0 0,0 -24,0 a 12,12 0 0,0 12,12 a 12,12 0 0,1 12,12 a 12,12 0 0,1 -24,0"/> </g> </svg> ',
    # 06 Widespread dust in suspension in the air, not raised by wind at or near the station at the time of observation
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc>WMO 4677 ww 06</desc> <path fill="none" stroke-width="3" stroke="currentColor" d="M 0,0 m 9,-12 a 9,9 0 0 0 -18,0 a 34,17.705691893392046 0 0 0 9,12 a 34,17.705691893392046 0 0 1 9,12 a 9,9 0 0 1 -18,0" /> </svg>',
    # 07 https://upload.wikimedia.org/wikipedia/commons/5/53/Symbol_code_ww_07.svg
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 00-09 General Group: No precipitation, fog, duststorm, sandstorm, drifting or blowing snow at the station at the time of observation or, except for 09 during the preceeding hour. 	Code: 07 	Description: Dust or sand raised by the wind at or near the station at the time of the observation, but no well-developed dust whirl(s), and no sandstorm seen: or, in the case of ships, blowing spray at the station </desc> <g id="ww_07" fill="none" stroke-width="3" stroke="currentColor" > 	<path d="M 9.5,-9.5 a 9.5,9.5 0 0,0 -19,0 a 9.5,9.5 0 0,0 9.5,9.5 a 9.5,9.5 0 0,1 9.5,9.5 a 9.5,9.5 0 0,1 -19,0"/> 	<path d="M 0,-24 v 48"/> </g> </svg> ',
    # 08 https://upload.wikimedia.org/wikipedia/commons/9/96/Symbol_code_ww_08.svg
    '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 00-09 General Group: No precipitation, fog, duststorm, sandstorm, drifting or blowing snow at the station at the time of observation or, except for 09 during the preceeding hour. 	Code: 08 	Description: Well developed dust whirl(s) or sand whirl(s) seen at or near the station during the preceding hour or at the time of observation, but no duststorm or sandstorm </desc> <g id="ww_08" fill="none" stroke-width="3" stroke="currentColor"> <path d="M 9,-18.75 C 7.5,-22 -10.5,-22 -10.5,-12.5 C -10.5,0 9,0 9,-6.25 C 9,-12.5 -10.5,-12.5 -10.5,0 C -10.5,12.5 9,12.5 9,6.25 C 9,0 -10.5,0 -10.5,12.5 C -10.5,22 6.5,22 9,18.75"/> </g> </svg> ',
    # 09 https://upload.wikimedia.org/wikipedia/commons/f/f2/Symbol_code_ww_09.svg
    '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 00-09 General Group: No precipitation, fog, duststorm, sandstorm, drifting or blowing snow at the station at the time of observation or, except for 09 during the preceeding hour. 	Code: 09 	Description: Duststorm or sandstorm within sight at the time of observation, or at the station during the preceding hour </desc> <g id="ww_o9" fill="none" stroke="currentColor" stroke-width="3"> 	<path d="M 9,-9 a 9,9 0 1,0 -9,9 a 9,9 0 1,1 -9,9" /> 	<path d="M 16,0 l -1.5,-1 v2 l 1.5,-1 z h -32.5" /> 	<path d="M 14,-19.5 a 25,25 0 0,1 0,39 M -14,19.5 a 25,25 0 0,1 0,-39"/> </g> </svg> ',
    # 10 https://upload.wikimedia.org/wikipedia/commons/2/29/Symbol_code_ww_10.svg
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 10-19 General Group: No precipitation at the station at the time of observation or, except 17, during the preceeding hour. 	Code: 10 	Description: Mist </desc> <g id="ww_10" fill="none" stroke-width="3" stroke="#ffc83f"> 	<path d="M -17.5,-4.5 h 35 M -17.5,4.5 h 35" /> </g> </svg> ',
    # 11 https://upload.wikimedia.org/wikipedia/commons/f/f7/Symbol_code_ww_11.svg
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 10-19 General Group: No precipitation at the station at the time of observation or, except 17, during the preceeding hour. 	Code: 11 	Description: Patches of shallow fog at station, NOT deeper than 6 feet on land </desc> <g id="ww_11" fill="none" stroke-width="3" stroke="#ffc83f" > 	<path d="M -17.5,-9.5 h 14.5 M 17.5,-9.5 h -14.5 M -17.5,0 h 14.5 M 17.5,0 h -14.5 M -17.5,9.5 h 14.5 M 17.5,9.5 h -14.5" /> </g> </svg> ',
    # 12 https://upload.wikimedia.org/wikipedia/commons/0/03/Symbol_code_ww_12.svg
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 10-19 General Group: No precipitation at the station at the time of observation or, except 17, during the preceeding hour. 	Code: 12 	Description: More or less continuous shallow fog at station, NOT deeper than 6 feet on land </desc> <g id="ww_12" fill="none" stroke-width="3" stroke="#ffc83f"> 	<path d="M -17.5,-9.5 h 14.5 M 17.5,-9.5 h -14.5 M -17.5,9.5 h 35 M -17.5,0 h 14.5 M 17.5,0 h -14.5" /> </g> </svg> ',
    # 13 https://upload.wikimedia.org/wikipedia/commons/8/82/Symbol_code_ww_13.svg
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 10-19 General Group: No precipitation at the station at the time of observation or, except 17, during the preceeding hour. 	Code: 13 	Description: Lighting visible, no thunder heard </desc> <g id="ww_13" fill="none" stroke-width="3" stroke="#ed1c24" > 	<path d="M -16.5,-17.5 m 24,0 l-14,19.5 l 14.5,14.5"/> 	<path d="M 7,16.5 h1 v-1 z"/> </g> </svg> ',
    # 14 https://upload.wikimedia.org/wikipedia/commons/8/8e/Symbol_code_ww_14.svg
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 10-19 General Group: No precipitation at the station at the time of observation or, except 17, during the preceeding hour. 	Code: 14 	Description: Precipitation within sight, but NOT reaching the ground </desc> <g id="ww_14"> <circle r="5.5" cy="-4.5" fill="#00d700" /> <path d="M 18.5,1 a 25,25 0 0,1 -37,0" fill="none" stroke-width="3" stroke="currentColor" /> </g> </svg> ',
    # 15 https://upload.wikimedia.org/wikipedia/commons/4/49/Symbol_code_ww_15.svg
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 10-19 General Group: No precipitation at the station at the time of observation or, except 17, during the preceeding hour. 	Code: 15 	Description: Precipitation within sight, reaching ground or the surface of the sea, but distant, i.e. estimated to be more than 3 miles from the station </desc> <g id="ww_15"> <circle r="5.5" fill="#00d700" /> <path d="M -18.5,-18.5 a 25,25 0 0,1 0,37 M 18.5,-18.5 a 25,25 0 0,0 0,37" fill="none" stroke-width="3" stroke="currentColor" /> </g> </svg> ',
    # 16 https://upload.wikimedia.org/wikipedia/commons/7/7b/Symbol_code_ww_16.svg
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 10-19 General Group: No precipitation at the station at the time of observation or, except 17, during the preceeding hour. 	Code: 16 	Description: Precipitation within sight, reaching the ground or the surface of the sea, near to (within 3 miles), but not at the station </desc> <g id="ww_16"> <circle r="5.5" fill="#00d700" /> <path d="M -5.5,-18.5 a 25,25 0 0,0 0,37 M 5.5,-18.5 a 25,25 0 0,1 0,37" fill="none" stroke-width="3" stroke="currentColor" /> </g> </svg> ',
    # 17 https://upload.wikimedia.org/wikipedia/commons/7/7b/Symbol_code_ww_17.svg
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 10-19 General Group: No precipitation at the station at the time of observation or, except 17, during the preceeding hour. 	Code: 17 	Description: Thunder heard, but no precipitation at the station </desc> <g id="ww_17" fill="none" stroke-width="3" stroke="#ed1c24" > 	<path d="M -14.5,-17.5 h 24 l-14,19.5 l 14.5,14.5"/> 	<path d="M -10.5,-17.5 v 37"/> 	<path d="M 9,16.5 h1 v-1 z"/> </g> </svg> ',
    # 18 https://upload.wikimedia.org/wikipedia/commons/7/74/Symbol_code_ww_18.svg
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 10-19 General Group: No precipitation at the station at the time of observation or, except 17, during the preceeding hour. 	Code: 18 	Description: Squall(s) within sight during past hour </desc> <g id="ww_18" fill="none" stroke-width="3" stroke="currentColor" stroke-miterlimit="2.5" > 	<path d="M 0,-11 l 16,-7.5 l -16,36 l -16,-36 l 16,7.5 z"/> </g> </svg> ',
    # 19 https://upload.wikimedia.org/wikipedia/commons/9/9c/Symbol_code_ww_19.svg
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 10-19 General Group: No precipitation at the station at the time of observation or, except 17, during the preceeding hour. 	Code: 19 	Description: Funnel cloud(s) / Tornado(s) during the preceding hour or at time of observation </desc> <g id="ww_19" fill="none" stroke-width="3" stroke="currentColor" > 	<path d="M -11.5,-20.5 l 8,7 v 27 l -8,7 M 11.5,-20.5 l -8,7 v 27 l 8,7"/> </g> </svg> ',
    # 20 https://upload.wikimedia.org/wikipedia/commons/d/da/Symbol_code_ww_20.svg
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 20-29 General Group: Precipitation, fog, ice fog, or thunderstorm at the station during the preceeding hour but not at the time of observation. 	Code: 20 	Description: Drizzle (not freezing) or snow grains not falling as shower(s) ended in the past hour </desc> <g id="ww_20"> <circle r="5.5" cx="-4" fill="#00d700" /> <path style="fill:none; stroke:#00d700; stroke-width:3; stroke-linecap:round;" d="M 0,0 C 0,3.7 -2.1,7.1 -5,9.2" /> <path d="M 1,-21 h 7 v42 h-7" fill="none" stroke-width="3" stroke="currentColor" /> </g> </svg> ',
    # 21 https://upload.wikimedia.org/wikipedia/commons/c/c3/Symbol_code_ww_21.svg
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 20-29 General Group: Precipitation, fog, ice fog, or thunderstorm at the station during the preceeding hour but not at the time of observation. 	Code: 21 	Description: Rain (not freezing) not falling as shower(s) ended in the past hour </desc> <g id="ww_21"> <circle r="5.5" cx="-4" fill="#00d700" /> <path d="M 1,-21 h 7 v42 h-7" fill="none" stroke-width="3" stroke="currentColor" /> </g> </svg> ',
    # 22 https://upload.wikimedia.org/wikipedia/commons/a/ae/Symbol_code_ww_22.svg
    '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 20-29 General Group: Precipitation, fog, ice fog, or thunderstorm at the station during the preceeding hour but not at the time of observation. 	Code: 22 	Description: Snow not falling as shower(s) ended in the past hour </desc> <g id="ww_22"> <g id="ww_22" transform="translate(-4,0)"> 	<path id="ww22arm" d="M -5.5,0 h11" stroke="#ac00ff" stroke-linecap="round" stroke-width="3" /> 	<use xlink:href="#ww22arm" transform="rotate(60)" /> 	<use xlink:href="#ww22arm" transform="rotate(120)" /> </g> <path d="M 1,-21 h 7 v42 h-7" fill="none" stroke-width="3" stroke="currentColor" /> </g> </svg> ',
    # 23 https://upload.wikimedia.org/wikipedia/commons/f/fc/Symbol_code_ww_23.svg
    '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 20-29 General Group: Precipitation, fog, ice fog, or thunderstorm at the station during the preceeding hour but not at the time of observation. 	Code: 23 	Description: Rain and snow or ice pellets not falling as shower(s) ended in the past hour </desc> <g> <g transform="translate(-4,7)"> 	<path id="ww23arm" d="M -5.5,0 h11" stroke="#ac00ff" stroke-linecap="round" stroke-width="3" /> 	<use xlink:href="#ww23arm" transform="rotate(60)" /> 	<use xlink:href="#ww23arm" transform="rotate(120)" /> </g> <circle r="5.5" cy="-7" cx="-4" fill="#00d700" /> <path d="M 1,-21 h 7 v42 h-7" fill="none" stroke-width="3" stroke="currentColor" /> </g> </svg> ',
    # 24 https://upload.wikimedia.org/wikipedia/commons/c/cc/Symbol_code_ww_24.svg
    '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 20-29 General Group: Precipitation, fog, ice fog, or thunderstorm at the station during the preceeding hour but not at the time of observation. 	Code: 24 	Description: Freezing drizzle or freezing rain not falling as shower(s) ended in the past hour </desc> <g id="ww_24"> <g fill="none" stroke="currentColor" stroke-linecap="round" stroke-width="3" transform="translate(-2,0)"> <path id="arc24" d="M 0,0 a7,7 0 0,0 14,0 v-1" fill="none" stroke="#ed1c24" stroke-linecap="round" stroke-width="3" /> <use xlink:href="#arc24" transform="scale(-1,-1)"/> </g> <path d="M 11.5,-23 h 7 v46 h-7" fill="none" stroke-width="3" stroke="currentColor" /> </g> </svg> ',
    # 25 https://upload.wikimedia.org/wikipedia/commons/6/69/Symbol_code_ww_25.svg
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 20-29 General Group: Precipitation, fog, ice fog, or thunderstorm at the station during the preceeding hour but not at the time of observation. 	Code: 25 	Description: Shower(s) of rain ended in the past hour </desc> <g id="ww_25"> <g id="ww_80" transform="translate(-4,3)"> 	<circle r="5.5" cy="-15.5" fill="#00d700" /> 	<path d="M 0,-5.5 h 8.5 l-8.5,20 l-8.5,-20 z" style="fill:none; stroke-width:3; stroke:#00d700" /> </g> <path d="M 6,-23 h 7 v46 h-7" fill="none" stroke-width="3" stroke="currentColor" /> </g> </svg> ',
    # 26 https://upload.wikimedia.org/wikipedia/commons/e/e8/Symbol_code_ww_26.svg
    '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 20-29 General Group: Precipitation, fog, ice fog, or thunderstorm at the station during the preceeding hour but not at the time of observation. 	Code: 26 	Description: Shower(s) of snow, or of rain and snow ended in the past hour </desc> <g id="ww_26"> <g id="ww_85" transform="translate(-4,3)"> 	<g transform="translate(0,-15.5)"> 	<path id="ww26arm" d="M -5.5,0 h11" stroke="#ac00ff" stroke-linecap="round" stroke-width="3" /> 	<use xlink:href="#ww26arm" transform="rotate(60)" /> 	<use xlink:href="#ww26arm" transform="rotate(120)" /> 	</g> 	<path d="M 0,-5.5 h 8.5 l-8.5,20 l-8.5,-20 z" style="fill:none; stroke-width:3; stroke:#ac00ff" /> </g> <path d="M 6,-23 h 7 v46 h-7" fill="none" stroke-width="3" stroke="currentColor" /> </g> </svg> ',
    # 27 https://upload.wikimedia.org/wikipedia/commons/f/f0/Symbol_code_ww_27.svg
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 20-29 General Group: Precipitation, fog, ice fog, or thunderstorm at the station during the preceeding hour but not at the time of observation. 	Code: 27 	Description: Shower(s) of hail, or of rain and hail ended in the past hour </desc> <g id="ww_27"> <g id="ww_87" transform="translate(-4,0)"> 	<path d="M -6,-8.5 h 12 l -6,-10.4 z" style="fill:none; stroke-width:3; stroke:#000000" /> 	<path d="M 0,-2.5 h 8.5 l-8.5,20 l-8.5,-20 z" style="fill:none; stroke-width:3; stroke:#00d700" /> </g> <path d="M 6,-23 h 7 v46 h-7" fill="none" stroke-width="3" stroke="currentColor" /> </g> </svg> ',
    # 28 https://upload.wikimedia.org/wikipedia/commons/5/5b/Symbol_code_ww_28.svg
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 20-29 General Group: Precipitation, fog, ice fog, or thunderstorm at the station during the preceeding hour but not at the time of observation. 	Code: 28 	Description: Fog or ice fog ended in the past hour </desc> <g id="ww_28"> 	<path d="M -19.5,-9.5 h 35 M -19.5,0 h 35 M -19.5,9.5 h 35" fill="none" stroke-width="3" stroke="#ffc83f" /> 	<path d="M 13.5,-23 h 7 v46 h-7" fill="none" stroke-width="3" stroke="currentColor" /> </g> </svg> ',
    # 29 https://upload.wikimedia.org/wikipedia/commons/d/da/Symbol_code_ww_29.svg
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 20-29 General Group: Precipitation, fog, ice fog, or thunderstorm at the station during the preceeding hour but not at the time of observation. 	Code: 29 	Description: Thunderstorm (with or without precipitation) ended in the past hour </desc> <g id="ww_29" fill="none" stroke-width="3" stroke="#ed1c24"><path d="M -14.5,-17.5 h 24 l-14,19.5 l 14.5,14.5"/><path d="M -10.5,-17.5 v 37"/><path d="M 9,16.5 h1 v-1 z"/></g> <g fill="none" stroke-width="3" stroke="currentColor"><path d="M 9.5,-23 h 7 v 46 h-7"/></g> </svg> ',
    # 30 https://upload.wikimedia.org/wikipedia/commons/9/9a/Symbol_code_ww_30.svg
    '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 30-39 General Group: Duststorm, sandstorm, drifting or blowing snow. 	Code: 30 	Description: Slight or moderate duststorm or sandstorm (has decreased during the preceding hour) </desc> <g fill="none" stroke="currentColor" stroke-width="3"> 	<path id="arc" d="M -2,0 a 9,9 0 1,1 9,-9" /> 	<path id="arc2" d="M -2,0 a 9,9 0 1,1 -9,9" /> </g> <path d="M 20,-20 v 40" fill="none" stroke="currentColor" stroke-width="3" /> <path d="M 14,0 l -1.5,-1 v2 l 1.5,-1 z h -32.5" fill="none" stroke="currentColor" stroke-width="3" /> </svg> ',
    # 31 https://upload.wikimedia.org/wikipedia/commons/1/15/Symbol_code_ww_31.svg
    '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 30-39 General Group: Duststorm, sandstorm, drifting or blowing snow. 	Code: 31 	Description: Slight or moderate duststorm or sandstorm (no appreciable change during the preceding hour) </desc> <g fill="none" stroke="currentColor" stroke-width="3"> 	<path id="arc" d="M 0,0 a 9,9 0 1,1 9,-9" /> 	<path id="arc2" d="M 0,0 a 9,9 0 1,1 -9,9" /> </g> <path d="M 16,0 l -1.5,-1 v2 l 1.5,-1 z h -32.5" fill="none" stroke="currentColor" stroke-width="3" /> </svg> ',
    # 32 https://upload.wikimedia.org/wikipedia/commons/1/12/Symbol_code_ww_32.svg
    '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 30-39 General Group: Duststorm, sandstorm, drifting or blowing snow. 	Code: 32 	Description: Slight or moderate duststorm or sandstorm (has begun or increased during the preceding hour) </desc> <g fill="none" stroke="currentColor" stroke-width="3"> 	<path id="arc" d="M 2,0 a 9,9 0 1,1 9,-9" /> 	<path id="arc2" d="M 2,0 a 9,9 0 1,1 -9,9" /> </g> <path d="M -20,-20 v 40" fill="none" stroke="currentColor" stroke-width="3" /> <path d="M 18,0 l -1.5,-1 v2 l 1.5,-1 z h -32.5" fill="none" stroke="currentColor" stroke-width="3" /> </svg> ',
    # 33 https://upload.wikimedia.org/wikipedia/commons/7/76/Symbol_code_ww_33.svg
    '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 30-39 General Group: Duststorm, sandstorm, drifting or blowing snow. 	Code: 33 	Description: Severe duststorm or sandstorm has decreased during the preceding hour </desc> <g fill="none" stroke="currentColor" stroke-width="3"> 	<path id="arc" d="M -2,0 a 9,9 0 1,1 9,-9" /> 	<path id="arc2" d="M -2,0 a 9,9 0 1,1 -9,9" /> </g> <path d="M 20,-20 v 40" fill="none" stroke="currentColor" stroke-width="3" /> <path d="M 13,2.8 h -32 M 13,-2.8 h -32 M 17,0 m -8,-6 l 8,6 l -8,6" fill="none" stroke="currentColor" stroke-width="1" /> </svg> ',
    # 34 https://upload.wikimedia.org/wikipedia/commons/6/64/Symbol_code_ww_34.svg
    '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 30-39 General Group: Duststorm, sandstorm, drifting or blowing snow. 	Code: 34 	Description: Severe duststorm or sandstorm has no appreciable change during the preceding hour </desc> <g fill="none" stroke="currentColor" stroke-width="3"> 	<path id="arc" d="M 0,0 a 9,9 0 1,1 9,-9" /> 	<path id="arc2" d="M 0,0 a 9,9 0 1,1 -9,9" /> </g> <path d="M 15,2.8 h -32 M 15,-2.8 h -32 M 19,0 m -8,-6 l 8,6 l -8,6" fill="none" stroke="currentColor" stroke-width="1" /> </svg> ',
    # 35 https://upload.wikimedia.org/wikipedia/commons/c/c8/Symbol_code_ww_35.svg
    '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 30-39 General Group: Duststorm, sandstorm, drifting or blowing snow. 	Code: 35 	Description: Severe duststorm or sandstorm has begun or increased during the preceding hour </desc> <g fill="none" stroke="currentColor" stroke-width="3"> 	<path id="arc" d="M 2,0 a 9,9 0 1,1 9,-9" /> 	<path id="arc2" d="M 2,0 a 9,9 0 1,1 -9,9" /> </g> <path fill="none" stroke="currentColor" stroke-width="3" d="M -20,-20 v 40" /> <path d="M 17,2.8 h -32 M 17,-2.8 h -32 M 21,0 m -8,-6 l 8,6 l -8,6" fill="none" stroke="currentColor" stroke-width="1"/> </svg> ',
    # 36 https://upload.wikimedia.org/wikipedia/commons/1/11/Symbol_code_ww_36.svg
    '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 30-39 General Group: Duststorm, sandstorm, drifting or blowing snow. 	Code: 36 	Description: Slight or moderate drifting snow (generally below eye level) </desc> <path d="M 16,0 l -1.5,-1 v2 l 1.5,-1 z h -32.5" fill="none" stroke="currentColor" stroke-width="3"/> <path d="M 0,16 l -1,-1.5 h2 l -1,1.5 z v -32.5" fill="none" stroke="currentColor" stroke-width="3"/> </svg> ',
    # 37 https://upload.wikimedia.org/wikipedia/commons/7/73/Symbol_code_ww_37.svg
    '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 30-39 General Group: Duststorm, sandstorm, drifting or blowing snow. 	Code: 37 	Description: Heavy drifting snow (generally below eye level) </desc> <path d="M 0,16 l -1,-1.5 h2 l -1,1.5 z v -32.5" fill="none" stroke="currentColor" stroke-width="3"/> <path d="M 15,2.8 h -32 M 15,-2.8 h -32 M 19,0 m -8,-6 l 8,6 l -8,6" fill="none" stroke="currentColor" stroke-width="1"/> </svg> ',
    # 38 https://upload.wikimedia.org/wikipedia/commons/1/16/Symbol_code_ww_38.svg
    '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 30-39 General Group: Duststorm, sandstorm, drifting or blowing snow. 	Code: 38 	Description: Slight or moderate blowing snow (generally above eye level) </desc> <path d="M 16,0 l -1.5,-1 v2 l 1.5,-1 z h -32.5" fill="none" stroke="currentColor" stroke-width="3"/> <path d="M 0,-16 l 1,1.5 h-2 l 1,-1.5 z v 32.5" fill="none" stroke="currentColor" stroke-width="3"/> </svg> ',
    # 39 https://upload.wikimedia.org/wikipedia/commons/1/1e/Symbol_code_ww_39.svg
    '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 30-39 General Group: Duststorm, sandstorm, drifting or blowing snow. 	Code: 39 	Description: Heavy drifting snow (generally above eye level) </desc> <path d="M 0,-16 l 1,1.5 h-2 l 1,-1.5 z v 32.5" fill="none" stroke="currentColor" stroke-width="3"/> <path d="M 15,2.8 h -32 M 15,-2.8 h -32 M 19,0 m -8,-6 l 8,6 l -8,6" fill="none" stroke="currentColor" stroke-width="1"/> </svg> ',
    # 40 https://upload.wikimedia.org/wikipedia/commons/b/ba/Symbol_code_ww_40.svg
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 40-49 General Group: Fog at the time of observation. 	Code: 40 	Description: Fog at a distance at the time of observation, but not at the station during the preceding hour, the fog or ice fog extending to a level above that of the observer </desc> <g id="ww_40"> 	<path d="M -17.5,-9.5 h 35 M -17.5,0 h 35 M -17.5,9.5 h 35" style="fill:none; stroke-width:3; stroke:#ffc83f" /><path d="M -15,-18.5 a 25,25 0 0,0 0,37 M 15,18.5 a 25,25 0 0,0 0,-37" stroke="currentColor" style="fill:none; stroke-width:3" /> </g> </svg> ',
    # 41 https://upload.wikimedia.org/wikipedia/commons/9/99/Symbol_code_ww_41.svg
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 40-49 General Group: Fog at the time of observation. 	Code: 41 	Description: Fog in patches </desc> <g id="ww_41"> 	<path d="M -17.5,-9.5 h 14.5 M 17.5,-9.5 h -14.5 M -17.5,0 h 35 M -17.5,9.5 h 14.5 M 17.5,9.5 h -14.5" fill="none" stroke-width="3" stroke="#ffc83f" /> </g> </svg> ',
    # 42 https://upload.wikimedia.org/wikipedia/commons/a/ab/Symbol_code_ww_42.svg
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 40-49 General Group: Fog at the time of observation. 	Code: 42 	Description: Fog sky visible (has become thinner during preceding hour) </desc> <g id="ww_42"> 	<path d="M -20,-9.5 h 14 M 14,-9.5 h -14 M -20,0 h 34 M -20,9.5 h 34" fill="none" stroke-width="3" stroke="#ffc83f" /> <path d="M 18.5,-11 v 22" fill="none" stroke-width="3" stroke="currentColor" /> </g> </svg> ',
    # 43 https://upload.wikimedia.org/wikipedia/commons/8/80/Symbol_code_ww_43.svg
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 40-49 General Group: Fog at the time of observation. 	Code: 43 	Description: Fog sky obscured (has become thinner during preceding hour) </desc> <g id="ww_43"> 	<path d="M -20,-9.5 h 34 M -20,0 h 34 M -20,9.5 h 34" fill="none" stroke-width="3" stroke="#ffc83f" /> <path d="M 18.5,-11 v 22" fill="none" stroke-width="3" stroke="currentColor" /> </g> </svg> ',
    # 44 https://upload.wikimedia.org/wikipedia/commons/3/38/Symbol_code_ww_44.svg
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 40-49 General Group: Fog at the time of observation. 	Code: 44 	Description: Fog sky visible (no appreciable change during the preceding hour) </desc> <g id="ww_44"> 	<path d="M -17.5,-9.5 h 14.5 M 17.5,-9.5 h -14.5 M -17.5,0 h 35 M -17.5,9.5 h 35" fill="none" stroke-width="3" stroke="#ffc83f" /> </g> </svg> ',
    # 45 https://upload.wikimedia.org/wikipedia/commons/5/5b/Symbol_code_ww_45.svg
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 40-49 General Group: Fog at the time of observation. 	Code: 45 	Description: Fog sky obscured (no appreciable change during the preceding hour) </desc> <g id="ww_45"> 	<path d="M -17.5,-9.5 h 35 M -17.5,0 h 35 M -17.5,9.5 h 35" fill="none" stroke-width="3" stroke="#ffc83f" /> </g> </svg> ',
    # 46 https://upload.wikimedia.org/wikipedia/commons/4/45/Symbol_code_ww_46.svg
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 40-49 General Group: Fog at the time of observation. 	Code: 46 	Description: Fog sky visible (has begun or has become thicker during the preceding hour) </desc> <g id="ww_46"> 	<path d="M -14,-9.5 h 14 M 20,-9.5 h -14 M -14,0 h 34 M -14,9.5 h 34" fill="none" stroke-width="3" stroke="#ffc83f" /> <path d="M -18.5,-11 v 22" fill="none" stroke-width="3" stroke="currentColor" /> </g> </svg> ',
    # 47 https://upload.wikimedia.org/wikipedia/commons/0/02/Symbol_code_ww_47.svg
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 40-49 General Group: Fog at the time of observation. 	Code: 47 	Description: Fog sky obscured (has begun or has become thicker during the preceding hour) </desc> <g id="ww_47"> 	<path d="M -14,-9.5 h 34 M -14,0 h 34 M -14,9.5 h 34" fill="none" stroke-width="3" stroke="#ffc83f" /> <path d="M -18.5,-11 v 22" fill="none" stroke-width="3" stroke="currentColor" /> </g> </svg> ',
    # 48 https://upload.wikimedia.org/wikipedia/commons/7/77/Symbol_code_ww_48.svg
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 40-49 General Group: Fog at the time of observation. 	Code: 48 	Description: Fog, depositing rime ice, sky visible </desc> <g id="ww_48"> 	<path d="M -2,0 L 0,4 L 2,0" fill="none" stroke-width="3" stroke="#ffc83f" stroke-linejoin="miter" /> 	<path d="M -17.5,-9.5 L -8.5,-9.5 L 0,7.5 L 8.5,-9.5 L 17.5,-9.5 M -17.5,0 h 35 M -17.5,9.5 h 35" fill="none" stroke-width="3" stroke="#ffc83f" stroke-linejoin="miter" /> </g> </svg> ',
    # 49 https://upload.wikimedia.org/wikipedia/commons/6/64/Symbol_code_ww_49.svg
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 40-49 General Group: Fog at the time of observation. 	Code: 49 	Description: Fog, depositing rime ice, or ice fog, sky obscured </desc> <g id="ww_49"> 	<path d="M -2,0 L 0,4 L 2,0 M -8.5,-9.5 L 8.5,-9.5" fill="none" stroke-width="3" stroke="#ffc83f" stroke-linejoin="miter" /> 	<path d="M -17.5,-9.5 L -8.5,-9.5 L 0,7.5 L 8.5,-9.5 L 17.5,-9.5 M -17.5,0 h 35 M -17.5,9.5 h 35" fill="none" stroke-width="3" stroke="#ffc83f" stroke-linejoin="miter" /> </g> </svg> ',
    # 50 https://upload.wikimedia.org/wikipedia/commons/8/81/Symbol_drizzle_50.svg
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 50-59 General Group: Drizzle. 	Code: 50 	Description: Drizzle, not freezing, intermittent (slight at time of observation) </desc> <circle r="5.5" fill="#00d700" /> <path style="fill:none; stroke:#00d700; stroke-width:3; stroke-linecap:round;" d="M 4,0 C 4,3.7 1.9,7.1 -1,9.2" /> </svg> ',
    # 51 https://upload.wikimedia.org/wikipedia/commons/d/db/Symbol_drizzle_51.svg
    '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 50-59 General Group: Drizzle. 	Code: 51 	Description: Drizzle, not freezing, continuous (slight at time of observation) </desc> <g id="ww_51" transform="translate(-9.5,0)"> 	<circle r="5.5" fill="#00d700" /> 	<path style="fill:none; stroke:#00d700; stroke-width:3; stroke-linecap:round;" d="M 4,0 C 4,3.7 1.9,7.1 -1,9.2" /> </g> <use xlink:href="#ww_51" transform="translate(19,0)" /> </svg> ',
    # 52 https://upload.wikimedia.org/wikipedia/commons/f/f9/Symbol_drizzle_52.svg
    '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 50-59 General Group: Drizzle. 	Code: 52 	Description: Drizzle, not freezing, intermittent (moderate at time of observation) </desc> <g transform="translate(0,-9.5)"> 	<g id="ww_52"> 		<circle r="5.5" fill="#00d700" /> 		<path style="fill:none; stroke:#00d700; stroke-width:3; stroke-linecap:round;" d="M 4,0 C 4,3.7 1.9,7.1 -1,9.2" /> 	</g> </g> <use xlink:href="#ww_52" transform="translate(0,9.5)" /> </svg> ',
    # 53 https://upload.wikimedia.org/wikipedia/commons/b/b7/Symbol_drizzle_53.svg
    '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 50-59 General Group: Drizzle. 	Code: 53 	Description: Drizzle, not freezing, continuous (moderate at time of observation) </desc> <g transform="translate(0,-11)"> 	<g id="ww_53"> 		<circle r="5.5" fill="#00d700" /> 		<path style="fill:none; stroke:#00d700; stroke-width:3; stroke-linecap:round;" d="M 4,0 C 4,3.7 1.9,7.1 -1,9.2" /> 	</g> </g> <use xlink:href="#ww_53" transform="rotate(120) translate(0,-11) rotate(-120)" /> <use xlink:href="#ww_53" transform="rotate(240) translate(0,-11) rotate(-240)" /> </svg> ',
    # 54 https://upload.wikimedia.org/wikipedia/commons/2/2f/Symbol_drizzle_54.svg
    '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="50" height="50" viewBox="-26 -26 52 52"> <desc id="en"> 	Codes 50-59 General Group: Drizzle. 	Code: 54 	Description: Drizzle, not freezing, intermittent (heavy at time of observation) </desc> <g transform="translate(0,-2)" id="ww_54"> 		<circle r="5.5" fill="#00d700" /> 		<path style="fill:none; stroke:#00d700; stroke-width:3; stroke-linecap:round;" d="M 4,0 C 4,3.7 1.9,7.1 -1,9.2" /> </g> <use xlink:href="#ww_54" y="-17" /> <use xlink:href="#ww_54" y="17" /> </svg> ',
    # 55 https://upload.wikimedia.org/wikipedia/commons/8/8f/Symbol_drizzle_55.svg
    '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 50-59 General Group: Drizzle. 	Code: 55 	Description: Drizzle, not freezing, continuous (heavy at time of observation) </desc> <g transform="translate(11,0)"> 	<g id="ww_55"> 			<circle r="5.5" fill="#00d700" /> 			<path style="fill:none; stroke:#00d700; stroke-width:3; stroke-linecap:round;" d="M 4,0 C 4,3.7 1.9,7.1 -1,9.2" /> 	</g> </g> <use xlink:href="#ww_55" x="-11" /> <use xlink:href="#ww_55" y="-11" /> <use xlink:href="#ww_55" y="11" /> </svg> ',
    # 56 https://upload.wikimedia.org/wikipedia/commons/c/ce/Symbol_drizzle_56.svg
    '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 50-59 General Group: Drizzle. 	Code: 56 	Description: Drizzle, freezing, slight </desc> <g transform="translate(-10,0) scale(0.7)"> 	<circle r="5.5" fill="#00d700" /> 	<path style="fill:none; stroke:#00d700; stroke-width:3; stroke-linecap:round;" d="M 4,0 C 4,3.7 1.9,7.1 -1,9.2" /> </g> <path id="arc56" d="M 0,0 a10,10 0 0,0 20,0 v-2" fill="none" stroke="#ed1c24" stroke-linecap="round" stroke-width="3" /> <use xlink:href="#arc56" transform="scale(-1,-1)"/> </svg> ',
    # 57 https://upload.wikimedia.org/wikipedia/commons/8/83/Symbol_drizzle_57.svg
    '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 50-59 General Group: Drizzle. 	Code: 57 	Description: Rain, freezing, moderate or heavy </desc> <g transform="translate(-10,0) scale(0.7)"> 	<circle r="5.5" fill="#00d700" /> 	<path style="fill:none; stroke:#00d700; stroke-width:3; stroke-linecap:round;" d="M 4,0 C 4,3.7 1.9,7.1 -1,9.2" /> </g> <g transform="translate(10,0) scale(0.7)"> 	<circle r="5.5" fill="#00d700" /> 	<path style="fill:none; stroke:#00d700; stroke-width:3; stroke-linecap:round;" d="M 4,0 C 4,3.7 1.9,7.1 -1,9.2" /> </g> <use xlink:href="#ww_50" transform="scale(-1,-1)"/> <path id="arc57" d="M 0,0 a10,10 0 0,0 20,0 v-2" fill="none" stroke="#ed1c24" stroke-linecap="round" stroke-width="3" /> <use xlink:href="#arc57" transform="scale(-1,-1)"/> </svg> ',
    # 58 https://upload.wikimedia.org/wikipedia/commons/f/ff/Symbol_drizzle_58.svg
    '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 50-59 General Group: Drizzle. 	Code: 58 	Description: Drizzle and rain, slight </desc> <circle r="5.5" cy="-7" fill="#00d700" /> <g transform="translate(0,7)"> 	<circle r="5.5" fill="#00d700" /> 	<path style="fill:none; stroke:#00d700; stroke-width:3; stroke-linecap:round;" d="M 4,0 C 4,3.7 1.9,7.1 -1,9.2" /> </g> </svg> ',
    # 59 https://upload.wikimedia.org/wikipedia/commons/7/78/Symbol_drizzle_59.svg
    '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 50-59 General Group: Drizzle. 	Code: 59 	Description: Drizzle and rain, moderate or heavy </desc> <g transform="translate(0,-19)"> 	<g id="ww_59"> 		<circle r="5.5" fill="#00d700" /> 		<path style="fill:none; stroke:#00d700; stroke-width:3; stroke-linecap:round;" d="M 4,0 C 4,3.7 1.9,7.1 -1,9.2" /> 	</g> </g> <circle r="5.5" cy="0" fill="#00d700" /> <use xlink:href="#ww_59" transform="translate(0,14)" /> </svg> ',
    # 60 https://upload.wikimedia.org/wikipedia/commons/1/19/Symbol_rain_60.svg
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 60-69 General Group: Rain. 	Code: 60 	Description: Rain, not freezing, intermittent (slight at time of observation) </desc> <circle r="5.5" fill="#00d700" /> </svg> ',
    # 61 https://upload.wikimedia.org/wikipedia/commons/b/bc/Symbol_rain_61.svg
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 60-69 General Group: Rain. 	Code: 61 	Description: Rain, not freezing, continuous (slight at time of observation) </desc> <circle r="5.5" cx="-9.5" fill="#00d700" /> <circle r="5.5" cx="9.5" fill="#00d700" /> </svg> ',
    # 62 https://upload.wikimedia.org/wikipedia/commons/a/a7/Symbol_rain_62.svg
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 60-69 General Group: Rain. 	Code: 62 	Description: Rain, not freezing, intermittent (moderate at time of observation) </desc> <circle r="5.5" cy="-9.5" fill="#00d700" /> <circle r="5.5" cy="9.5" fill="#00d700" /> </svg> ',
    # 63 https://upload.wikimedia.org/wikipedia/commons/d/d2/Symbol_rain_63.svg
    '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 60-69 General Group: Rain. 	Code: 63 	Description: Rain, not freezing, continuous (moderate at time of observation) </desc> <circle id="point63" r="5.5" cy="-9" fill="#00d700" /> <use xlink:href="#point63" transform="rotate(120)"/> <use xlink:href="#point63" transform="rotate(240)"/> </svg> ',
    # 64 https://upload.wikimedia.org/wikipedia/commons/8/8e/Symbol_rain_64.svg
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 60-69 General Group: Rain. 	Code: 64 	Description: Rain, not freezing, intermittent (heavy at time of observation) </desc> <circle r="5.5" fill="#00d700" /> <circle r="5.5" cy="-14" fill="#00d700" /> <circle r="5.5" cy="14" fill="#00d700" /> </svg> ',
    # 65 https://upload.wikimedia.org/wikipedia/commons/c/c5/Symbol_rain_65.svg
    '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 60-69 General Group: Rain. 	Code: 65 	Description: Rain, not freezing, continuous (heavy at time of observation) </desc> <circle id="point65" r="5.5" cy="-9.5" fill="#00d700" /> <use xlink:href="#point65" transform="rotate(90)"/> <use xlink:href="#point65" transform="rotate(180)"/> <use xlink:href="#point65" transform="rotate(270)"/> </svg> ',
    # 66 https://upload.wikimedia.org/wikipedia/commons/9/99/Symbol_rain_66.svg
    '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 60-69 General Group: Rain. 	Code: 66 	Description: Rain, freezing, slight </desc> <circle r="4.5" cx="-10" fill="#00d700" /> <path id="arc66" d="M 0,0 a10,10 0 0,0 20,0 v-2" fill="none" stroke="#ed1c24" stroke-linecap="round" stroke-width="3" /> <use xlink:href="#arc66" transform="scale(-1,-1)"/> </svg> ',
    # 67 https://upload.wikimedia.org/wikipedia/commons/4/4a/Symbol_rain_67.svg
    '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 60-69 General Group: Rain. 	Code: 67 	Description: Rain, freezing, moderate or heavy </desc> <g id="half67"> 	<circle r="4.5" cx="10" fill="#00d700" /> 	<path id="arc67" d="M 0,0 a10,10 0 0,0 20,0 v-2" fill="none" stroke="#ed1c24" stroke-linecap="round" stroke-width="3" /> </g> <use xlink:href="#half67" transform="scale(-1,-1)"/> </svg> ',
    # 68 https://upload.wikimedia.org/wikipedia/commons/d/dd/Symbol_rain_68.svg
    '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 60-69 General Group: Rain. 	Code: 68 	Description: Rain or drizzle and snow, slight </desc> <g id="ww_68" transform="translate(0,7)"> 	<path id="ww68arm" d="M -5.5,0 h11" stroke="#ac00ff" stroke-linecap="round" stroke-width="3" /> 	<use xlink:href="#ww68arm" transform="rotate(60)" /> 	<use xlink:href="#ww68arm" transform="rotate(120)" /> </g> <circle r="5.5" cy="-7" fill="#00d700" /> </svg> ',
    # 69 https://upload.wikimedia.org/wikipedia/commons/4/49/Symbol_rain_69.svg
    '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 60-69 General Group: Rain. 	Code: 69 	Description: Rain or drizzle and snow, moderate or heavy </desc> <g id="ww_69" transform="translate(0,14)"> 	<path id="ww69arm" d="M -5.5,0 h11" stroke="#ac00ff" stroke-linecap="round" stroke-width="3" /> 	<use xlink:href="#ww69arm" transform="rotate(60)" /> 	<use xlink:href="#ww69arm" transform="rotate(120)" /> </g> <use xlink:href="#ww_69" y="-28" /> <circle r="5.5" fill="#00d700" /> </svg> ',
    # 70 https://upload.wikimedia.org/wikipedia/commons/d/d7/Symbol_solid_precipitation_70.svg
    '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 70-79 General Group: Solid precipitation not in showers. 	Code: 70 	Description: Intermittent fall of snowflakes (slight at time of observation) </desc> <g id="ww_70"> 	<path id="ww70arm" d="M -5.5,0 h11" stroke="#ac00ff" stroke-linecap="round" stroke-width="3" /> 	<use xlink:href="#ww70arm" transform="rotate(60)" /> 	<use xlink:href="#ww70arm" transform="rotate(120)" /> </g> </svg> ',
    # 71 https://upload.wikimedia.org/wikipedia/commons/e/ee/Symbol_solid_precipitation_71.svg
    '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 70-79 General Group: Solid precipitation not in showers. 	Code: 71 	Description: Continuous fall of snowflakes (slight at time of observation) </desc> <g transform="translate(-9.5,0)"> 	<g id="ww_71"> 		<path id="ww71arm" d="M -5.5,0 h11" stroke="#ac00ff" stroke-linecap="round" stroke-width="3" /> 		<use xlink:href="#ww71arm" transform="rotate(60)" /> 		<use xlink:href="#ww71arm" transform="rotate(120)" /> 	</g> </g> <use xlink:href="#ww_71" x="9.5" /> </svg> ',
    # 72 https://upload.wikimedia.org/wikipedia/commons/f/fc/Symbol_solid_precipitation_72.svg
    '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 70-79 General Group: Solid precipitation not in showers. 	Code: 72 	Description: Intermittent fall of snowflakes (moderate at time of observation) </desc> <g transform="translate(0,-9.5)"> 	<g id="ww_72"> 		<path id="ww72arm" d="M -5.5,0 h11" stroke="#ac00ff" stroke-linecap="round" stroke-width="3" /> 		<use xlink:href="#ww72arm" transform="rotate(60)" /> 		<use xlink:href="#ww72arm" transform="rotate(120)" /> 	</g> </g> <use xlink:href="#ww_72" y="9.5" /> </svg> ',
    # 73 https://upload.wikimedia.org/wikipedia/commons/1/1f/Symbol_solid_precipitation_73.svg
    '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 70-79 General Group: Solid precipitation not in showers. 	Code: 73 	Description: Continuous fall of snowflakes (moderate at time of observation) </desc> <g transform="translate(0,-9.5) rotate(30)"> 	<g id="ww_73"> 		<path id="ww73arm" d="M -5.5,0 h11" stroke="#ac00ff" stroke-linecap="round" stroke-width="3" /> 		<use xlink:href="#ww73arm" transform="rotate(60)" /> 		<use xlink:href="#ww73arm" transform="rotate(120)" /> 	</g> </g> <use xlink:href="#ww_73" transform="rotate(120) translate(0,-9.5)" /> <use xlink:href="#ww_73" transform="rotate(240) translate(0,-9.5)" /> </svg> ',
    # 74 https://upload.wikimedia.org/wikipedia/commons/5/51/Symbol_solid_precipitation_74.svg
    '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 70-79 General Group: Solid precipitation not in showers. 	Code: 74 	Description: Intermittent fall of snowflakes (heavy at time of observation) </desc> <g id="ww_74"> 	<path id="ww74arm" d="M -5.5,0 h11" stroke="#ac00ff" stroke-linecap="round" stroke-width="3" /> 	<use xlink:href="#ww74arm" transform="rotate(60)" /> 	<use xlink:href="#ww74arm" transform="rotate(120)" /> </g> <use xlink:href="#ww_74" y="-15" /> <use xlink:href="#ww_74" y="15" /> </svg> ',
    # 75 https://upload.wikimedia.org/wikipedia/commons/7/73/Symbol_solid_precipitation_75.svg
    '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 70-79 General Group: Solid precipitation not in showers. 	Code: 75 	Description: Continuous fall of snowflakes (heavy at time of observation) </desc> <g transform="translate(-12,0)"> 	<g id="ww_75"> 		<path id="ww75arm" d="M -5.5,0 h11" stroke="#ac00ff" stroke-linecap="round" stroke-width="3" /> 		<use xlink:href="#ww75arm" transform="rotate(60)" /> 		<use xlink:href="#ww75arm" transform="rotate(120)" /> 		 	</g> </g> <use xlink:href="#ww_75" y="-12" /> <use xlink:href="#ww_75" y="12" /> <use xlink:href="#ww_75" x="12" /> </svg> ',
    # 76 https://upload.wikimedia.org/wikipedia/commons/e/ec/Symbol_solid_precipitation_76.svg
    '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 70-79 General Group: Solid precipitation not in showers. 	Code: 76 	Description: Ice needles (with or without fog) </desc> <g style="stroke-width:3; stroke:#ac00ff; fill:none; stroke-linejoin:miter"> 	<path id="ww_76_arrow" d="M -9,4.5 L -16,0 L -9,-4.5"  stroke-linecap="round" /> 	<use xlink:href="#ww_76_arrow" transform="scale(-1,1)" /> 	<path id="ww_76_line" d="M -15,0 h30" /> </g> </svg> ',
    # 77 https://upload.wikimedia.org/wikipedia/commons/2/23/Symbol_solid_precipitation_77.svg
    '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 70-79 General Group: Solid precipitation not in showers. 	Code: 77 	Description: Snow grains (with or without fog) </desc> <g style="stroke-width:3; stroke:#ac00ff; fill:none; stroke-linejoin:miter"> 	<path id="ww_77_triangle" d="M 0,-8 l 8.7,14.6 h-17.4 z" /> 	<path id="ww_77_line" d="M -18,0 h36" /> </g> </svg> ',
    # 78 https://upload.wikimedia.org/wikipedia/commons/b/bb/Symbol_solid_precipitation_78.svg
    '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 70-79 General Group: Solid precipitation not in showers. 	Code: 78 	Description: Isolated star-like snow crystals (with or without fog) </desc> <g style="stroke-width:3; stroke:#ac00ff; fill:none;"> 	<path id="ww_78_arm" d="M -5,-5 l 10,10" stroke-linecap="round" /> 	<use xlink:href="#ww_78_arm" transform="rotate(90)" /> 	<path id="ww_78_line" d="M -15,0 h30" /> </g> </svg> ',
    # 79 https://upload.wikimedia.org/wikipedia/commons/0/0e/Symbol_solid_precipitation_79.svg
    '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 70-79 General Group: Solid precipitation not in showers. 	Code: 79 	Description: Ice pellets (sleet) </desc> <g transform="translate(0,6)"> 	<circle r="4.2" fill="#ac00ff" /> 	<path d="M 0,-17.4 l 15.068842,26.1 h-30.137684 z" style="stroke-width:3; stroke:#ac00ff; fill:none" /> </g> </svg> ',
    # 80 https://upload.wikimedia.org/wikipedia/commons/5/57/Symbol_code_ww_80.svg
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 80-99 General Group: Showery precipitation, or precipitation with current or recent thunderstorm. 	Code: 80 	Description: Rain shower(s), slight </desc> <g id="ww_80"> 	<circle r="5.5" cy="-15.5" fill="#00d700" /> 	<path d="M 0,-5.5 h 8.5 l-8.5,20 l-8.5,-20 z" style="fill:none; stroke-width:3; stroke:#00d700" /> </g> </svg> ',
    # 81 https://upload.wikimedia.org/wikipedia/commons/7/71/Symbol_code_ww_81.svg
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 80-99 General Group: Showery precipitation, or precipitation with current or recent thunderstorm. 	Code: 81 	Description: Rain shower(s), moderate or heavy </desc> <g id="ww_81"> 	<circle r="5.5" cy="-15.5" fill="#00d700" /> 	<path d="M 0,-5.5 h 8.5 l-8.5,20 l-8.5,-20 z" style="fill:none; stroke-width:3; stroke:#00d700" /> 	<path d="M -6,0.5 h 12" style="fill:none; stroke-width:3; stroke:#00d700" /> </g> </svg> ',
    # 82 https://upload.wikimedia.org/wikipedia/commons/a/a7/Symbol_code_ww_82.svg
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-26 -26 52 52"> <desc id="en"> 	Codes 80-99 General Group: Showery precipitation, or precipitation with current or recent thunderstorm. 	Code: 82 	Description: Rain shower(s), violent </desc> <g id="ww_82"> 	<circle r="5.5" cy="-20.5" fill="#00d700" /> 	<circle r="5.5" cy="-8" fill="#00d700" /> 	<path d="M 0,0.5 h 8.5 l-8.5,20 l-8.5,-20 z" style="fill:none; stroke-width:3; stroke:#00d700" /> </g> </svg> ',
    # 83 https://upload.wikimedia.org/wikipedia/commons/6/6b/Symbol_code_ww_83.svg
    '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="50" height="50" viewBox="-26 -26 52 52"> <desc id="en"> 	Codes 80-99 General Group: Showery precipitation, or precipitation with current or recent thunderstorm. 	Code: 83 	Description: Shower(s) of rain and snow mixed, slight </desc> <g id="ww_83"> 	<circle r="5.5" cy="-20.5" fill="#00d700" /> 	<g transform="translate(0,-8)"> 	<path id="ww83arm" d="M -5.5,0 h11" stroke="#ac00ff" stroke-linecap="round" stroke-width="3" /> 	<use xlink:href="#ww83arm" transform="rotate(60)" /> 	<use xlink:href="#ww83arm" transform="rotate(120)" /> 	</g> 	<path d="M 0,0.5 h 8.5 l-8.5,20 l-8.5,-20 z" style="fill:none; stroke-width:3; stroke:#00d700" /> </g> </svg> ',
    # 84 https://upload.wikimedia.org/wikipedia/commons/d/d2/Symbol_code_ww_84.svg
    '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="50" height="50" viewBox="-26 -26 52 52"> <desc id="en"> 	Codes 80-99 General Group: Showery precipitation, or precipitation with current or recent thunderstorm. 	Code: 84 	Description: Shower(s) of rain and snow mixed, moderate or heavy </desc> <g id="ww_84"> 	<circle r="5.5" cy="-20.5" fill="#00d700" /> 	<g transform="translate(0,-8)"> 	<path id="ww84arm" d="M -5.5,0 h11" stroke="#ac00ff" stroke-linecap="round" stroke-width="3" /> 	<use xlink:href="#ww84arm" transform="rotate(60)" /> 	<use xlink:href="#ww84arm" transform="rotate(120)" /> 	</g> 	<path d="M 0,0.5 h 8.5 l-8.5,20 l-8.5,-20 z" style="fill:none; stroke-width:3; stroke:#00d700" /> 	<path d="M -6,6.5 h 12" style="fill:none; stroke-width:3; stroke:#00d700" /> </g> </svg> ',
    # 85 https://upload.wikimedia.org/wikipedia/commons/3/3f/Symbol_code_ww_85.svg
    '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 80-99 General Group: Showery precipitation, or precipitation with current or recent thunderstorm. 	Code: 85 	Description: Snow shower(s), slight </desc> <g id="ww_85"> 	<g transform="translate(0,-15.5)"> 	<path id="ww85arm" d="M -5.5,0 h11" stroke="#ac00ff" stroke-linecap="round" stroke-width="3" /> 	<use xlink:href="#ww85arm" transform="rotate(60)" /> 	<use xlink:href="#ww85arm" transform="rotate(120)" /> 	</g> 	<path d="M 0,-5.5 h 8.5 l-8.5,20 l-8.5,-20 z" style="fill:none; stroke-width:3; stroke:#ac00ff" /> </g> </svg> ',
    # 86 https://upload.wikimedia.org/wikipedia/commons/c/c4/Symbol_code_ww_86.svg
    '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 80-99 General Group: Showery precipitation, or precipitation with current or recent thunderstorm. 	Code: 86 	Description: Snow shower(s), moderate or heavy </desc> <g id="ww_86"> 	<g transform="translate(0,-15.5)"> 	<path id="ww86arm" d="M -5.5,0 h11" stroke="#ac00ff" stroke-linecap="round" stroke-width="3" /> 	<use xlink:href="#ww86arm" transform="rotate(60)" /> 	<use xlink:href="#ww86arm" transform="rotate(120)" /> 	</g> 	<path d="M 0,-5.5 h 8.5 l-8.5,20 l-8.5,-20 z" style="fill:none; stroke-width:3; stroke:#ac00ff" /> 	<path d="M -6,0.5 h 12" style="fill:none; stroke-width:3; stroke:#ac00ff" /> </g> </svg> ',
    # 87 https://upload.wikimedia.org/wikipedia/commons/f/f9/Symbol_code_ww_87.svg
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 80-99 General Group: Showery precipitation, or precipitation with current or recent thunderstorm. 	Code: 87 	Description: Shower(s) of snow pellets or small hail, slight with or without rain or rain and snow mixed </desc> <g id="ww_87"> 	<path d="M -6,-8.5 h 12 l -6,-10.4 z" style="fill:none; stroke-width:3; stroke:#000000" /> 	<path d="M 0,-2.5 h 8.5 l-8.5,20 l-8.5,-20 z" style="fill:none; stroke-width:3; stroke:#00d700" /> </g> </svg> ',
    # 88 https://upload.wikimedia.org/wikipedia/commons/7/7d/Symbol_code_ww_88.svg
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 80-99 General Group: Showery precipitation, or precipitation with current or recent thunderstorm. 	Code: 88 	Description: Shower(s) of snow pellets or small hail, moderate or heavy with or without rain or rain and snow mixed </desc> <g id="ww_88"> 	<path d="M -6,-8.5 h 12 l -6,-10.4 z" style="fill:none; stroke-width:3; stroke:#000000" /> 	<path d="M 0,-2.5 h 8.5 l-8.5,20 l-8.5,-20 z" style="fill:none; stroke-width:3; stroke:#00d700" /> 	<path d="M -6,3.5 h 12" style="fill:none; stroke-width:3; stroke:#00d700" /> </g> </svg> ',
    # 89 https://upload.wikimedia.org/wikipedia/commons/a/af/Symbol_code_ww_89.svg
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 80-99 General Group: Showery precipitation, or precipitation with current or recent thunderstorm. 	Code: 89 	Description: Shower(s) of hail, with or without rain or rain and snow mixed, not associated with thunder, slight </desc> <g id="ww_89"> 	<path d="M -6,-8.5 h 12 l -6,-10.4 z" style="fill:#000000; stroke-width:3; stroke:#000000" /> 	<path d="M 0,-2.5 h 8.5 l-8.5,20 l-8.5,-20 z" style="fill:none; stroke-width:3; stroke:#00d700" /> </g> </svg> ',
    # 90 https://upload.wikimedia.org/wikipedia/commons/d/d9/Symbol_code_ww_90.svg
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 80-99 General Group: Showery precipitation, or precipitation with current or recent thunderstorm. 	Code: 90 	Description: Shower(s) of hail, with or without rain or rain and snow mixed, not associated with thunder, moderate or heavy </desc> <g id="ww_90"> 	<path d="M -6,-8.5 h 12 l -6,-10.4 z" style="fill:#000000; stroke-width:3; stroke:#000000" /> 	<path d="M 0,-2.5 h 8.5 l-8.5,20 l-8.5,-20 z" style="fill:none; stroke-width:3; stroke:#00d700" /> 	<path d="M -6,3.5 h 12" style="fill:none; stroke-width:3; stroke:#00d700" /> </g> </svg> ',
    # 91 https://upload.wikimedia.org/wikipedia/commons/2/2c/Symbol_code_ww_91.svg
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 80-99 General Group: Showery precipitation, or precipitation with current or recent thunderstorm. 	Code: 91 	Description: Thunderstorm during the preceeding hour but not at time of observation with slight rain at time of observation </desc> <g id="ww_91"> 	<circle r="4.5" cx="17.5" cy="0" fill="#00d700" /> 	<path d="M -22.5,-17.5 h 24 l-14,19.5 l 14.5,14.5" style="fill:none; stroke-width:3; stroke:#ed1c24" /> 	<path d="M -18.5,-17.5 v 37" style="fill:none; stroke-width:3; stroke:#ed1c24" /> 	<path d="M 1.5,-23 h 7 v 46 h-7" style="fill:none; stroke-width:3; stroke:#000000" /> 	<path d="M 1,16.5 h1 v-1 z" style="fill:#ed1c24; stroke-width:3; stroke:#ed1c24" /> </g> </svg> ',
    # 92 https://upload.wikimedia.org/wikipedia/commons/4/49/Symbol_code_ww_92.svg
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 80-99 General Group: Showery precipitation, or precipitation with current or recent thunderstorm. 	Code: 92 	Description: Thunderstorm during the preceeding hour but not at time of observation with moderate or heavy rain at time of observation </desc> <g id="ww_92"> 	<circle r="4.5" cx="17.5" cy="-6" fill="#00d700" /> 	<circle r="4.5" cx="17.5" cy="6" fill="#00d700" /> 	<path d="M -22.5,-17.5 h 24 l-14,19.5 l 14.5,14.5" style="fill:none; stroke-width:3; stroke:#ed1c24" /> 	<path d="M -18.5,-17.5 v 37" style="fill:none; stroke-width:3; stroke:#ed1c24" /> 	<path d="M 1.5,-23 h 7 v 46 h-7" style="fill:none; stroke-width:3; stroke:#000000" /> 	<path d="M 1,16.5 h1 v-1 z" style="fill:#ed1c24; stroke-width:3; stroke:#ed1c24" /> </g> </svg> ',
    # 93 https://upload.wikimedia.org/wikipedia/commons/6/6b/Symbol_code_ww_93.svg
    '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 80-99 General Group: Showery precipitation, or precipitation with current or recent thunderstorm. 	Code: 93 	Description:  </desc> <g id="ww_93"> <g transform="translate(17.5,0)"> 	<path id="ww93arm" d="M -5.5,0 h 11" stroke="#ac00ff" stroke-linecap="round" stroke-width="3" /> 	<use xlink:href="#ww93arm" transform="rotate(60)" /> 	<use xlink:href="#ww93arm" transform="rotate(120)" /> </g> 	<path d="M -24.5,-17.5 h 24 l-14,19.5 l 14.5,14.5" style="fill:none; stroke-width:3; stroke:#ed1c24" /> 	<path d="M -20.5,-17.5 v 37" style="fill:none; stroke-width:3; stroke:#ed1c24" /> 	<path d="M -0.5,-23 h 7 v 46 h-7" style="fill:none; stroke-width:3; stroke:#000000" /> 	<path d="M -1,16.5 h1 v-1 z" style="fill:#ed1c24; stroke-width:3; stroke:#ed1c24" /> </g> </svg> ',
    # 94 https://upload.wikimedia.org/wikipedia/commons/0/05/Symbol_code_ww_94.svg
    '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 80-99 General Group: Showery precipitation, or precipitation with current or recent thunderstorm. 	Code: 94 	Description: Thunderstorm during the preceeding hour but not at time of observation with moderate or heavy snow, or rain and snow mixed, or hail at time of observation </desc> <g id="ww_94"> <g id="ww_70_in_94" transform="translate(17.5,7.5)"> 	<path id="ww94arm" d="M -5.5,0 h 11" stroke="#ac00ff" stroke-linecap="round" stroke-width="3" /> 	<use xlink:href="#ww94arm" transform="rotate(60)" /> 	<use xlink:href="#ww94arm" transform="rotate(120)" /> </g> 	<use xlink:href="#ww_70_in_94" transform="translate(0,-15)" /> 	<path d="M -24.5,-17.5 h 24 l-14,19.5 l 14.5,14.5" style="fill:none; stroke-width:3; stroke:#ed1c24" /> 	<path d="M -20.5,-17.5 v 37" style="fill:none; stroke-width:3; stroke:#ed1c24" /> 	<path d="M -0.5,-23 h 7 v 46 h-7" style="fill:none; stroke-width:3; stroke:#000000" /> 	<path d="M -1,16.5 h1 v-1 z" style="fill:#ed1c24; stroke-width:3; stroke:#ed1c24" /> </g> </svg> ',
    # 95 https://upload.wikimedia.org/wikipedia/commons/8/80/Symbol_code_ww_95.svg
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 80-99 General Group: Showery precipitation, or precipitation with current or recent thunderstorm. 	Code: 95 	Description: Thunderstorm, slight or moderate, without hail but with rain and or snow at time of observation </desc> <g id="ww_95"> 	<circle r="4.5" cx="0" cy="-19" fill="#00d700" /> 	<path d="M -10.5,-10 h 20 l-11.5,16.5 l 12,12" style="fill:none; stroke-width:3; stroke:#ed1c24" /> 	<path d="M -6.5,-10 v 31.5" style="fill:none; stroke-width:3; stroke:#ed1c24" /> 	<path d="M 9,18.5 h1 v-1 z" style="fill:#ed1c24; stroke-width:3; stroke:#ed1c24" /> </g> </svg> ',
    # 96 https://upload.wikimedia.org/wikipedia/commons/c/cd/Symbol_code_ww_96.svg
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 80-99 General Group: Showery precipitation, or precipitation with current or recent thunderstorm. 	Code: 96 	Description: Thunderstorm, slight or moderate, with hail at time of observation </desc> <g id="ww_96"> 	<path d="M -4,-14 h 8 l -4,-6.93 z" style="fill:none; stroke-width:2.5; stroke:#000000" /> 	<path d="M -10.5,-8 h 20 l-11.5,16.5 l 12,12" style="fill:none; stroke-width:3; stroke:#ed1c24" /> 	<path d="M -6.5,-8 v 31.5" style="fill:none; stroke-width:3; stroke:#ed1c24" /> 	<path d="M 9,20.5 h1 v-1 z" style="fill:#ed1c24; stroke-width:3; stroke:#ed1c24" /> </g> </svg> ',
    # 97 https://upload.wikimedia.org/wikipedia/commons/f/fb/Symbol_code_ww_97.svg
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 80-99 General Group: Showery precipitation, or precipitation with current or recent thunderstorm. 	Code: 97 	Description: Thunderstorm, heavy, without hail but with rain and or snow at time of observation </desc> <g id="ww_97"> 	<circle r="4.5" cx="0" cy="-19" fill="#00d700" /> 	<path d="M -10.5,-10 h 20 l-7.5,14.5 l 6.5,6.5 l-6.5,6.5" style="fill:none; stroke-width:3; stroke:#ed1c24" /> 	<path d="M -6.5,-10 v 31.5" style="fill:none; stroke-width:3; stroke:#ed1c24" /> 	<path d="M 2,18.5 h-1 v-1 z" style="fill:#ed1c24; stroke-width:3; stroke:#ed1c24" /> </g> </svg> ',
    # 98 https://upload.wikimedia.org/wikipedia/commons/b/b4/Symbol_code_ww_98.svg
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 80-99 General Group: Showery precipitation, or precipitation with current or recent thunderstorm. 	Code: 98 	Description: Thunderstorm combined with duststorm or sandstorm at time of observation </desc> <g id="ww_98"> 	<path d="M 3,-21 a3,3 0 0,0 -6,0 a3,3 0 0,0 3,3  	a3,3 0 0,1 3,3 a3,3 0 0,1 -6,0" style="fill:none; stroke-width:1.5; stroke:#000000" /> 	<path d="M -7,-18 h 14" style="fill:none; stroke-width:1.5; stroke:#000000" /> 	<path d="M 7,-18 v-0.5 l 0.5,0.5 l -0.5,0.5 z" style="fill:#000000; stroke-width:1.5; stroke:#000000" /> 	<path d="M -10.5,-8 h 20 l-11.5,16.5 l 12,12" style="fill:none; stroke-width:3; stroke:#ed1c24" /> 	<path d="M -6.5,-8 v 31.5" style="fill:none; stroke-width:3; stroke:#ed1c24" /> 	<path d="M 9,20.5 h1 v-1 z" style="fill:#ed1c24; stroke-width:3; stroke:#ed1c24" /> </g> </svg> ',
    # 99 https://upload.wikimedia.org/wikipedia/commons/8/89/Symbol_code_ww_99.svg
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc id="en"> 	Codes 80-99 General Group: Showery precipitation, or precipitation with current or recent thunderstorm. 	Code: 99 	Description: Thunderstorm, heavy, with hail at time of observation </desc> <g id="ww_99"> 	<path d="M -4,-14 h 8 l -4,-6.93 z" style="fill:none; stroke-width:2.5; stroke:#000000" /> 	<path d="M -10.5,-8 h 20 l-7.5,14.5 l 6.5,6.5 l-6.5,6.5" style="fill:none; stroke-width:3; stroke:#ed1c24" /> 	<path d="M -6.5,-8 v 31.5" style="fill:none; stroke-width:3; stroke:#ed1c24" /> 	<path d="M 2,20.5 h-1 v-1 z" style="fill:#ed1c24; stroke-width:3; stroke:#ed1c24" /> </g> </svg> '
]

WAWA_SYMBOLS = [
    # 00 No significant weather observed
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> </svg>',
    # 01 Clouds generally dissolving or becoming less developed during the past hour
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> </svg>',
    # 02 State of sky on the whole unchanged during the past hour
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> </svg>',
    # 03 Clouds generally forming or developing during the past hour
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> </svg>',
    # 04 Haze or smoke, or dust in suspension in the air, visibility equal to, or greater than, 1 km
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc>WMO 4680 wawa 04</desc> <path fill="none" stroke-width="3" stroke="currentColor" d="M 0,0 a 34,17.705691893392046 0 0 0 9,-12 a 9,9 0 0 0 -18,0 a 34,17.705691893392046 0 0 0 9,12 a 34,17.705691893392046 0 0 1 9,12 a 9,9 0 0 1 -18,0 a 34,17.705691893392046 0 0 1 9,-12 z" /> </svg>',
    # 05 Haze or smoke, or dust in suspension in the air, visibility less than 1 km
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc>WMO 4680 wawa 05</desc> <path fill="none" stroke-width="3" stroke="currentColor"  d="M 0,0 a 34,17.705691893392046 0 0 0 9,-12 a 9,9 0 0 0 -18,0 a 34,17.705691893392046 0 0 0 9,12 a 34,17.705691893392046 0 0 1 9,12 a 9,9 0 0 1 -18,0 a 34,17.705691893392046 0 0 1 9,-12 z" /> <path fill="currentColor" d="M 0,0 a 34,17.705691893392046 0 0 1 9,12 a 9,9 0 0 1 -18,0 a 34,17.705691893392046 0 0 1 9,-12 z" /> </svg>',
    # 06...09 reserved
    None,None,None,None,
    # 10 Mist
    WW_SYMBOLS[10],
    # 11 Diamond dust
    WW_SYMBOLS[76],
    # 12 Distant lightning
    WW_SYMBOLS[13],
    # 13...17 reserved
    None,None,None,None,None,
    # 18 Squalls
    WW_SYMBOLS[18],
    # 19 reserved
    None,
    # 20...29 events at the station during the preceding hour but not at the time of observation
    # 20 Fog
    WW_SYMBOLS[28],
    # 21 PRECIPITATION
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc>WMO 4680 wawa 21</desc> <g> <path d="M -13.5,0 A 9 9 0 0 1 4.5 0" fill="none" stroke="#00d700" stroke-linecap="round" stroke-width="3" /> <path d="M 6,-21 h 7 v42 h-7" fill="none" stroke-width="3" stroke="currentColor" /> </g> </svg> ',
    # 22 Drizzle (not freezing) or snow grains
    WW_SYMBOLS[20],
    # 23 Rain (not freezing)
    WW_SYMBOLS[21],
    # 24 Snow
    WW_SYMBOLS[22],
    # 25 Freezing drizzle or freezing rain
    WW_SYMBOLS[24],
    # 26 Thunderstorm (with or without precipitation)
    WW_SYMBOLS[29],
    # 27 BLOWING OR DRIFTING SNOW OR SAND
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc>WMO 4680 wawa 27</desc> <g stroke="currentColor" stroke-width="3" fill="none"> <path d="M -3.5,-10   a 7,7 0 0 0 -14,0   a 28,15.118578920369089 0 0 0 7,10   a 28,15.118578920369089 0 0 1 7,10   a 7,7 0 0 1 -14,0   M 6,-18.5 v 37" /> <path stroke-linecap="round" d="M -9,0 h 20.5" /> </g> <path fill="currentColor" d="M18.5,0 l -7,3 v -6 z" /> </svg>',
    # 28 Blowing or drifting snow or sand, visibility equal to, or greater than, 1 km
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc>WMO 4680 wawa 28</desc> <g stroke="currentColor" stroke-width="3" fill="none"> <path d="M -8.5,-18.5 v 37   M 6,-18.5 v 37   M -8.5,0 h 21" /> </g> <path fill="currentColor" d="M18.5,0 l -7,3 v -6 z" /> </svg>',
    # 29 Blowing or drifting snow or sand, visibility less than 1 km
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc>WMO 4680 wawa 29</desc> <g stroke="currentColor" stroke-width="3" fill="none"> <path d="M -20,-18.5 v 37   M -5.5,-18.5 v 37   M 9,-18.5 v 37   M -20,0 h 34.5" /> </g> <path fill="currentColor" d="M21.5,0 l -7,3 v -6 z" /> </svg>',
    # 30...39 FOG
    # 30 FOG
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <path d="M -17.5,14.25 h 35 M -17.5,-14.25 h 35 M -17.5,4.75 h 14 M -17.5,-4.75 h 14 M 17.5,-4.75 h -14 M 17.5,4.75 h -14" fill="none" stroke-width="3" stroke="#ffc83f" stroke-linejoin="miter" /> </svg>',
    # 31 Fog or ice fog in patches
    WW_SYMBOLS[41],
    # 32 Fog or ice fog, has become thinner during the past hour
    WW_SYMBOLS[43],
    # 33 Fog or ice fog, no appreciable change during the past hour
    WW_SYMBOLS[45],
    # 34 Fog or ice fog, has begun or become thicker during the past hour
    WW_SYMBOLS[47],
    # 35 Fog, depositing rime
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <g> <path d="M -8.5,-9.5 L 0,7.5 L 8.5,-9.5 M -17.5,0 h 35 M -17.5,9.5 h 35" fill="none" stroke-width="3" stroke="#ffc83f" stroke-linejoin="miter" /> </g> </svg> ',
    # 36...39 reserved
    None,None,None,None,
    # 40...49 PRECIPITATION
    # 40 PRECIPITATION
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"><g><path d="M -9,0 A 9 9 0 0 1 9 0" fill="none" stroke="#00d700" stroke-linecap="round" stroke-width="3" /></g></svg>',
    # 41 Precipitation, slight or moderate
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"><g><path d="M -14,0 A 5.5 5.5 0 0 1 -3 0 M 3,0 A 5.5 5.5 0 0 1 14,0" fill="none" stroke="#00d700" stroke-linecap="round" stroke-width="3" /></g></svg>',
    # 42 Precipitation, heavy
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"><g><path d="M -14,0 A 5.5 5.5 0 0 1 -3 0 M 3,0 A 5.5 5.5 0 0 1 14,0 M -5.5,11.5 A 5.5 5.5 0 0 1 5.5 11.5 M -5.5,-11.5 A 5.5 5.5 0 0 1 5.5 -11.5" fill="none" stroke="#00d700" stroke-linecap="round" stroke-width="3" /></g></svg>',
    # 43 Liquid precipitation, slight or moderate
    '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <g id="wawa_43" transform="translate(-9.5,0)"> <circle r="5.5" fill="#00d700" /> <path style="fill:none; stroke:#00d700; stroke-width:3; stroke-linecap:round;" d="M -4,0 C -4,-3.7 -1.9,-7.1 1,-9.2" /> </g> <use xlink:href="#wawa_43" transform="translate(19,0)" /> </svg> ',
    # 44 Liquid precipitation, heavy
    '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <g transform="translate(11,0)"> <g id="wawa_44"> <circle r="5.5" fill="#00d700" /> <path style="fill:none; stroke:#00d700; stroke-width:3; stroke-linecap:round;" d="M -4,0 C -4,-3.7 -1.9,-7.1 1,-9.2" /> 	</g> </g> <use xlink:href="#wawa_44" x="-11" /> <use xlink:href="#wawa_44" y="-11" /> <use xlink:href="#wawa_44" y="11" /> </svg> ',
    # 45 Solid precipitation, slight or moderate
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <g><path d="M -12.389087297,-3.889087297 l 7.778174593,7.778174593 M -12.389087297,3.889087297 l 7.778174593,-7.778174593 M 4.610912697,-3.889087297 l 7.778174593,7.778174593 M 4.610912697,3.889087297 l 7.778174593,-7.778174593" stroke="#ac00ff" stroke-linecap="round" stroke-width="3" /> </g> </svg> ',
    # 46 Solid precipitation, heavy
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <g><path d="M -12.389087297,-3.889087297 l 7.778174593,7.778174593 M -12.389087297,3.889087297 l 7.778174593,-7.778174593 M 4.610912697,-3.889087297 l 7.778174593,7.778174593 M 4.610912697,3.889087297 l 7.778174593,-7.778174593 M -3.889087297,-16.389087297 l 7.778174593,7.778174593 M -3.889087297,-8.610912703 l 7.778174593,-7.778174593 M -3.889087297,8.610912703 l 7.778174593,7.778174593 M -3.889087297,16.389087297 l 7.778174593,-7.778174593" stroke="#ac00ff" stroke-linecap="round" stroke-width="3" /> </g> </svg> ',
    # 47 Freezing precipitation, slight or moderate
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"><g transform="translate(-10,0) scale(0.7)"> <circle r="5.5" fill="#00d700" /> <path style="fill:none; stroke:#00d700; stroke-width:3; stroke-linecap:round;" d="M -4,0 C -4,-3.7 -1.9,-7.1 1,-9.2" /> </g> <path d="M 0,0 m -20,2 v -2 a 10,10 0 0 1 20,0 a10,10 0 0,0 20,0 v-2" fill="none" stroke="#ed1c24" stroke-linecap="round" stroke-width="3" /> </svg> ',
    # 48 Freezing precipitation, heavy
    '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <g transform="translate(-10,0) scale(0.7)"> <circle r="5.5" fill="#00d700" /> <path style="fill:none; stroke:#00d700; stroke-width:3; stroke-linecap:round;" d="M -4,0 C -4,-3.7 -1.9,-7.1 1,-9.2" /> </g> <g transform="translate(10,0) scale(0.7)"> <circle r="5.5" fill="#00d700" /> <path style="fill:none; stroke:#00d700; stroke-width:3; stroke-linecap:round;" d="M -4,0 C -4,-3.7 -1.9,-7.1 1,-9.2" /> </g>  <path d="M 0,0 m -20,2 v -2 a 10,10 0 0 1 20,0 a10,10 0 0,0 20,0 v-2" fill="none" stroke="#ed1c24" stroke-linecap="round" stroke-width="3" /> </svg> ',
    # 49 reserved
    None,
    # 50...59 DRIZZLE
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <circle r="5.5" stroke="#00d700" stroke-width="1.5" fill="none" /> <path style="fill:none; stroke:#00d700; stroke-width:1.5; stroke-linecap:round;" d="M 5.5,0 C 4,3.7 1.9,7.1 -1,9.2" /> </svg> ',
    WW_SYMBOLS[51],
    WW_SYMBOLS[53],
    WW_SYMBOLS[55],
    WW_SYMBOLS[56],
    WW_SYMBOLS[57],
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <g transform="translate(10,9),scale(0.7)"> <circle r="5.5" cx="0" cy="0" fill="#00d700" /> <path style="fill:none; stroke:#00d700; stroke-width:3; stroke-linecap:round;" d="M 4,0 C 4,3.7 1.9,7.1 -1,9.2" /></g> <g transform="translate(-10,9),scale(0.7)"> <circle r="5.5" cx="0" cy="0" fill="#00d700" /> <path style="fill:none; stroke:#00d700; stroke-width:3; stroke-linecap:round;" d="M 4,0 C 4,3.7 1.9,7.1 -1,9.2" /></g> <g transform="translate(0,-9),scale(0.7)"> <circle r="5.5" cx="0" cy="0" fill="#00d700" /> <path style="fill:none; stroke:#00d700; stroke-width:3; stroke-linecap:round;" d="M 4,0 C 4,3.7 1.9,7.1 -1,9.2" /></g> <g><path d="M 0,9 m -20,2 v -2 a 10,10 0 0 1 20,0 a10,10 0 0,0 20,0 v-2" fill="none" stroke="#ed1c24" stroke-linecap="round" stroke-width="3" /> </g></svg> ',
    WW_SYMBOLS[58],
    WW_SYMBOLS[59],
    None,
    # 60...69 RAIN
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <circle r="6.5" stroke="#00d700" stroke-width="1.5" fill="none"/> </svg> ',
    WW_SYMBOLS[61],
    WW_SYMBOLS[63],
    WW_SYMBOLS[65],
    WW_SYMBOLS[66],
    WW_SYMBOLS[67],
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <g> <circle r="4.5" cx="10" cy="9" fill="#00d700" /> <circle r="4.5" cx="-10" cy="9" fill="#00d700" /><path d="M 0,9 m -20,2 v -2 a 10,10 0 0 1 20,0 a10,10 0 0,0 20,0 v-2" fill="none" stroke="#ed1c24" stroke-linecap="round" stroke-width="3" /> </g> <circle cx="0" cy="-9" r="4.5" fill="#00d700" /></svg> ',
    WW_SYMBOLS[68],
    WW_SYMBOLS[69],
    None,
    # 70...79 SNOW
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <path d="M -17.5,0 h 35 L 8.75,-15.155 L -8.75,15.155 L 8.75,15.155 L -8.75,-15.155 z" fill="none" stroke="#ac00ff" stroke-width="1.5" /></svg>',
    WW_SYMBOLS[71],
    WW_SYMBOLS[73],
    WW_SYMBOLS[75],
    WW_SYMBOLS[79],
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc>WMO 4680 wawa 75</desc> <g transform="translate(-13,14.17283025),scale(0.67)"> <circle r="4.2" fill="#ac00ff" /> <path d="M 0,-17.4 l 15.068842,26.1 h-30.137684 z" style="stroke-width:3; stroke:#ac00ff; fill:none" /> </g> <g transform="translate(13,14.17283025),scale(0.67)"> <circle r="4.2" fill="#ac00ff" /> <path d="M 0,-17.4 l 15.068842,26.1 h-30.137684 z" style="stroke-width:3; stroke:#ac00ff; fill:none" /> </g> <g transform="translate(0,-8.34383025),scale(0.67)"> <circle r="4.2" fill="#ac00ff" /> <path d="M 0,-17.4 l 15.068842,26.1 h-30.137684 z" style="stroke-width:3; stroke:#ac00ff; fill:none" /> </g> </svg> ',
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc>WMO 4680 wawa 76</desc> <g transform="translate(-14,3),scale(0.5)"> <circle r="4.2" fill="#ac00ff" /> <path d="M 0,-17.4 l 15.068842,26.1 h-30.137684 z" style="stroke-width:3; stroke:#ac00ff; fill:none" /> </g> <g transform="translate(14,3),scale(0.5)"> <circle r="4.2" fill="#ac00ff" /> <path d="M 0,-17.4 l 15.068842,26.1 h-30.137684 z" style="stroke-width:3; stroke:#ac00ff; fill:none" /> </g> <g transform="translate(0,-14),scale(0.5)"> <circle r="4.2" fill="#ac00ff" /> <path d="M 0,-17.4 l 15.068842,26.1 h-30.137684 z" style="stroke-width:3; stroke:#ac00ff; fill:none" /> </g> <g transform="translate(0,19),scale(0.5)"> <circle r="4.2" fill="#ac00ff" /> <path d="M 0,-17.4 l 15.068842,26.1 h-30.137684 z" style="stroke-width:3; stroke:#ac00ff; fill:none" /> </g> </svg> ',
    WW_SYMBOLS[77],
    WW_SYMBOLS[78],
    None,
    # 80...89 SHOWER(S) or INTERMITTENT PRECIPITATION
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc>WMO 4680 wawa 80</desc> <g> <path d="M 0,-5.5 h 8.5 l-8.5,20 l-8.5,-20 z" style="fill:none; stroke-width:3; stroke:#00d700" /> </g> </svg> ',
    # 81 Rain shower(s) or intermittent rain, slight
    WW_SYMBOLS[80],
    # 82 Rain shower(s) or intermittent rain, moderate
    WW_SYMBOLS[81],
    # 83 Rain shower(s) or intermittent rain, heavy
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc>WMO 4680 wawa 83</desc> <circle r="5.5" cx="7" cy="-15.5" fill="#00d700" /> <circle r="5.5" cx="-7" cy="-15.5" fill="#00d700" /> <path d="M 0,-5.5 h 8.5 l-8.5,20 l-8.5,-20 z" style="fill:none; stroke-width:3; stroke:#00d700" /> </svg> ',
    # 84 Rain shower(s) or intermittent rain, violent
    WW_SYMBOLS[82],
    # 85 Snow shower(s) or intermittent snow, slight
    WW_SYMBOLS[85],
    # 86 Snow shower(s) or intermittent snow, moderate
    WW_SYMBOLS[86],
    # 87 Snow shower(s) or intermittent snow, heavy
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc>WMO 4680 wawa 87</desc> <g> <g transform="translate(0,-15.5)"> <path d="M -8.5,0 m -5.5,0 h 11 m -2.75,-4.763139720814413 l -5.5,9.526279441628825 m 5.5,0 l -5.5,-9.526279441628825" stroke="#ac00ff" stroke-linecap="round" stroke-width="3" /><path d="M 8.5,0 m -5.5,0 h 11 m -2.75,-4.763139720814413 l -5.5,9.526279441628825 m 5.5,0 l -5.5,-9.526279441628825" stroke="#ac00ff" stroke-linecap="round" stroke-width="3" /> </g> <path d="M 0,-5.5 h 8.5 l-8.5,20 l-8.5,-20 z" style="fill:none; stroke-width:3; stroke:#ac00ff" /> 	<path d="M -6,0.5 h 12" style="fill:none; stroke-width:3; stroke:#ac00ff" /> </g> </svg> ',
    # 88 reserved
    None,
    # 89 Hail
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc>WMO 4680 wawa 89</desc> <g stroke="currentColor" fill="currentColor" style="stroke-width:3; stroke-linejoin:miter"> <path d="M 0,-8 l 8.7,14.6 h-17.4 z" /> </g> </svg> ',
    # 90 THUNDERSTORM
    WW_SYMBOLS[17],
    # 91 Thunderstorm, slight or moderate, with no precipitation
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc>WMO 4680 wawa 91</desc> <g fill="none" stroke-width="3" stroke="#ed1c24" > <path d="M -16.5,-17.5 h 12 m 7,0 h 12" /><path d="M 9.5,-17.5 l-14,19.5 l 14.5,14.5"/> <path d="M -10.5,-17.5 v 37"/> <path d="M 9,16.5 h1 v-1 z"/> </g> </svg> ',
    # 92 Thunderstorm, slight or moderate, with rain showers and/or snow showers
    WW_SYMBOLS[95],
    # 93 Thunderstorm, slight or moderate, with hail
    WW_SYMBOLS[96],
    # 94 Thunderstorm, heavy, with no precipitation
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc>WMO 4680 wawa 94</desc> <g fill="none" stroke-width="3" stroke="#ed1c24"> <path d="M -13.635,-17.5 h 12 m 6,0 h 12" /><path d="M 11.159,-17.5 l-8.810,17.032 l 7.635,7.635 l-7.635,7.635" /> <path d="M -7.635,-17.5 v 37" /> <path d="M 2.349,15.976 h-1 v-1 z" fill="#ed1c24"  /> </g> </svg> ',
    # 95 Thunderstorm, heavy, with rain showers and/or snow showers
    WW_SYMBOLS[97],
    # 96 Thunderstorm, heavy, with hail
    WW_SYMBOLS[99],
    # 97...98 reserved
    None,None,
    # 99 Tornado
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50"> <desc>WMO 4680 wawa 99</desc> <path fill="none" stroke-width="3" stroke="currentColor" d="M -7.5,18.5 v -28.5 l -6,-8.5 M 7.5,18.5 v -28.5 l 6,-8.5 M 15,-1.9749371855331 A 18,9 0 1 0 15,7.9749371855331" /> <g transform="translate(12,9.708203933),rotate(-30)" > <path fill="currentColor" d="M 15,0 l -15,4.5 v -9 z" />  </g> </svg>'
]

# code table 4561 W W1 W2
W_SYMBOLS = [
    # 0 Cloud covering 1/2 or less of the sky throughout the appropriate period
    None,
    # 1 Cloud covering more than 1/2 of the sky during part of the appropriate period and covering 1/2 or less
    None,
    # 2 Cloud covering more than 1/2 of the sky throughout the appropriate period
    None,
    # 3 Sandstorm, duststorm or blowing snow
    # or WAWA_SYMBOLS[27]
    WW_SYMBOLS[38],
    # 4 Fog or ice fog or thick haze
    WW_SYMBOLS[45],
    # 5 Drizzle
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-20 -20 40 40"> <desc>WMO 4561 W 5</desc> <circle r="5.5" fill="#00d700" /> <path style="fill:none; stroke:#00d700; stroke-width:3; stroke-linecap:round;" d="M 4,0 C 4,3.7 1.9,7.1 -1,9.2" /> </svg> ',
    # 6 Rain
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-20 -20 40 40"> <desc>WMO 4561 W 6</desc> <circle r="5.5" fill="#00d700" /> </svg> ',
    # 7 Snow, or rain and snow mixed
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-20 -20 40 40"> <desc>WMO 4561 W 7</desc> <path d="M 0,0 m -5.5,0 h 11 m -2.75,-4.763139720814413 l -5.5,9.526279441628825 m 5.5,0 l -5.5,-9.526279441628825" stroke="#ac00ff" stroke-linecap="round" stroke-width="3" /></svg> ',
    # 8 Shower(s)
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-20 -20 40 40"> <desc>WMO 4680 W 8</desc> <g> <path d="M 0,-5.5 h 8.5 l-8.5,20 l-8.5,-20 z" style="fill:none; stroke-width:3; stroke:#00d700" /> </g> </svg> ',
    # 9 Thunderstorm(s) with or without precipitation
    WW_SYMBOLS[17]
]

# code table 4531 Wa Wa1 Wa2
WA_SYMBOLS = [
    # 0 No significant weather observed
    WAWA_SYMBOLS[0],
    # 1 VISIBILITY REDUCED
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-20 -20 40 40"> <desc>WMO 4531 Wa 1</desc> <path d="M-9.5,-14v28 M0,-14v28 M9.5,-14v28" fill="none" stroke-width="3" stroke="#ffc83f" /> </svg>',
    # 2 Blowing phenomena, visibility reduced
    W_SYMBOLS[3],
    # 3 FOG
    W_SYMBOLS[4],
    # 4 PRECIPITATION
    WAWA_SYMBOLS[40],
    # 5 Drizzle
    W_SYMBOLS[5],
    # 6 Rain
    W_SYMBOLS[6],
    # 7 Snow or ice pellets
    W_SYMBOLS[7],
    # 8 Snow shower(s) or intermittent precipitation
    W_SYMBOLS[8],
    # 9 Thunderstorm
    WW_SYMBOLS[17]
]

# code table 2700 n
OKTA_SYMBOLS = [
    # 0/8
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="0 0 100 100"> <desc>WMO 2700 N 0/8</desc> <circle cx="50" cy="50" r="45" stroke-width="8" stroke="currentColor" fill="none"/> </svg>',
    # 1/8
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="0 0 100 100"> <desc>WMO 2700 N 1/8</desc> <circle cx="50" cy="50" r="45" stroke-width="8" stroke="currentColor" fill="none"/> <line x1="50" y1="5" x2="50" y2="95" stroke-width="8" stroke="currentColor" /> </svg>',
    # 2/8
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="0 0 100 100"> <desc>WMO 2700 N 2/8</desc> <circle cx="50" cy="50" r="45" stroke-width="8" stroke="currentColor" fill="none"/> <path d="M 95,50 L 50,50 L 50,5 A 45 45 0 0 1 95,50 Z" stroke="none" fill="currentColor" /> </svg>',
    # 3/8
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="0 0 100 100"> <desc>WMO 2700 N 3/8</desc> <circle cx="50" cy="50" r="45" stroke-width="8" stroke="currentColor" fill="none"/> <path d="M 95,50 L 50,50 L 50,5 A 45 45 0 0 1 95,50 Z" stroke="none" fill="currentColor" /> <line x1="50" y1="5" x2="50" y2="95" stroke-width="8" stroke="currentColor" /> </svg>',
    # 4/8
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="0 0 100 100"> <desc>WMO 2700 N 4/8</desc> <circle cx="50" cy="50" r="45" stroke-width="8" stroke="currentColor" fill="none"/> <path d="M 50,95 L 50,5 A 45 45 0 0 1 50,95 Z" stroke="none" fill="currentColor" /> </svg>',
    # 5/8
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="0 0 100 100"> <desc>WMO 2700 N 5/8</desc> <circle cx="50" cy="50" r="45" stroke-width="8" stroke="currentColor" fill="none"/> <line x1="5" y1="50" x2="95" y2="50" stroke-width="8" stroke="currentColor" /> <path d="M 50,95 L 50,5 A 45 45 0 0 1 50,95 Z" stroke="none" fill="currentColor" /> </svg>',
    # 6/8
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="0 0 100 100"> <desc>WMO 2700 N 6/8</desc> <circle cx="50" cy="50" r="45" stroke-width="8" stroke="currentColor" fill="none"/> <path d="M 5,50 L 50,50 L 50,5 A 45 45 0 1 1 5,50 Z" stroke="none" fill="currentColor" /> </svg>',
    # 7/8
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="0 0 100 100"> <desc>WMO 2700 N 7/8</desc> <circle cx="50" cy="50" r="45" stroke-width="8" stroke="currentColor" fill="none"/> <path d="M 60,93.87482193696061 L 60,6.12517806303939 A 45 45 0 0 1 60,93.87482193696061 Z M 40,6.12517806303939 L 40,93.87482193696061 A 45 45 0 0 1 40,6.12517806303939 Z" stroke-width="8" stroke="currentColor" fill="currentColor" /> </svg>',
    # 8/8
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="0 0 100 100"> <desc>WMO 2700 N 8/8</desc> <circle cx="50" cy="50" r="45" stroke-width="8" stroke="currentColor" fill="currentColor" /> </svg>',
    # 9/8
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="0 0 100 100"> <desc>WMO 2700 N 9/8</desc> <circle cx="50" cy="50" r="45" stroke-width="8" stroke="currentColor" fill="none" /> <line x1="18.180194846605361" y1="18.180194846605361" x2="81.819805153394639" y2="81.819805153394639" stroke-width="8" stroke="currentColor" /> <line x1="18.180194846605361" y1="81.819805153394639" x2="81.819805153394639" y2="18.180194846605361" stroke-width="8" stroke="currentColor" /> </svg>',
    # no data
    '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="0 0 100 100"> <desc>WMO 2700 N no data</desc> <circle cx="50" cy="50" r="45" stroke-width="8" stroke="currentColor" fill="none" /> <line x1="5" y1="50" x2="95" y2="50" stroke-width="8" stroke="currentColor" /> <line x1="50" y1="5" x2="50" y2="95" stroke-width="8" stroke="currentColor" /> </svg>'
]

OKTA_TEXTS = {
    'de':[
        ('wolkenlos','klar'),        # 0/8
        ('sonnig','fast klar'),      # 1/8
        ('heiter','leicht bewölkt'), # 2/8
        'leicht bewölkt',            # 3/8
        'wolkig',                    # 4/8
        'bewölkt',                   # 5/8
        'stark bewölkt',             # 6/8
        'fast bedeckt',              # 7/8
        'bedeckt',                   # 8/8
        'nicht sichtbar',            # 9/8
        'keine Daten'                # no data
    ],
    'en':[
        'clear',           # 0/8 fine
        'fair',            # 1/8 fine
        'mostly sunny',    # 2/8 fine
        'partly cloudy',   # 3/8 partly cloudy
        'partly cloudy',   # 4/8 partly cloudy
        'partly cloudy',   # 5/8 partly cloudy
        'mostly cloudy',   # 6/8 cloudy
        'cloudy',          # 7/8 cloudy
        'overcast',        # 8/8 overcast
        'sky not visible', # 9/8 sky not visible due to meteorological conditions
        'no data'          # no data received or no observation made
    ]
}

WMO_TABLES = {
  2700: OKTA_SYMBOLS,
  4561: W_SYMBOLS,
  4531: WA_SYMBOLS,
  4677: WW_SYMBOLS,
  4680: WAWA_SYMBOLS
}


def get_ww(ww,n,night):
    """ get icon and description for the current weather 
    
        Args:
            ww (iterable)   : list of present weather codes
                              The most important one is used.
            n (int)         : cloud cover percentage
            night (boolean) : use night icon
        
        Returns:
            tuple: icons and description of the current weather
    """
    # If weather code ww is within the list of WW_LIST (which means
    # it is important over cloud coverage), get the data from that
    # list.
    for ii in WW_LIST:
        if ii[0] in ww:
            wwcode = ii+(WW_SYMBOLS[ii[0]],)
            break
    else:
        wwcode = (0,'','',30,'unknown.png','unknown.png','na.png','','wi_na',WW_SYMBOLS[0])
    # Otherwise use cloud coverage
    # see aerisweather for percentage values
    # https://www.aerisweather.com/support/docs/api/reference/weather-codes/
    if wwcode[0]<=3 or (wwcode[0]>=20 and wwcode[0]<30) or wwcode[0] in (14,15,16):
        night = 1 if night else 0
        cover = get_cloudcover(n)
        if cover is not None:
            # Belchertown icons
            icon = cover[night]
            # Aeris icons
            aeicon = cover[4]
            aecode = '::'+cover[3]
            # DWD icons
            if n<12.5:
                dwd = N_ICON_LIST[0][2]
            elif n<50:
                dwd = N_ICON_LIST[1][2]
            elif n<87.5:
                dwd = N_ICON_LIST[2][2]
            else:
                dwd = N_ICON_LIST[4][2]
            try:
                n_str = '%.0f%%' % float(n)
            except Exception:
                n_str = str(n)
            wi = cover[night+5]
            wwcode = (wwcode[0],wwcode[1]+' '+n_str,wwcode[2]+' '+str(n),wwcode[3],icon,dwd,aeicon,aecode,wi,WW_SYMBOLS[wwcode[0]])
    return wwcode

def get_cloudcover(n):
    """ get cloud cover symbols
    
        Args:
            n (int): cloud cover in percent
        
        Returns: 
            tuple: set of icons
    """
    if n is None: return None
    if n<7:
        icon = N_ICON_LIST[0]
    elif n<32:
        icon = N_ICON_LIST[1]
    elif n<70:
        icon = N_ICON_LIST[2]
    elif n<95:
        icon = N_ICON_LIST[3]
    elif n<106.25:
        icon = N_ICON_LIST[4]
    elif n<118.75:
        icon = ('fog.png','fog.png','40.png','::BR','fog','wi-fog','wi-fog')
    else:
        icon = ('unknown.png','unknown.png','','::','na','wi-na','wi-na')
    return icon

def visibility_code(visibility):
    """ visibility code according to WMO table 4377 
    
        Args:
            visibility (float): visibility in meters
            
        Returns:
            str: visibility code
    """
    vv = int(round(visibility*0.01,0))
    if vv<=50:
        return '%02d' % vv
    if vv<=55:
        return '50'
    vv = round(visibility,0)
    if vv<=30:
        return '%02d' % vv+50
    vv = round(visibility/5 ,0)
    if vv<=14:
        return '%02d' % vv+74
    return '89'

def pressure_tendency(p_list):
    """ calculate pressure tendency code according to WMO code table 0200
    
        I guess, when the pressure tendency code was defined, 
        meteorologists read the pressure gauge once an hour. So they
        had 3 readings available to determine the code. And the
        symbol reflects that situation.
        
        Args:
            p_list (list): list of time-pressure tuples of the last 3 hours
            
        Returns:
            int: pressure tendendy code
    """
    # extract values from the list
    p0h = p_list[-1][1]
    p3h = p_list[0][1]
    p0htime = p_list[-1][0]
    p3htime = p_list[0][0]
    p_list.sort(key=lambda x:x[1])
    pmax = p_list[-1][1]
    pmin = p_list[0][1]
    pmaxtime = (p_list[-1][0]-p3htime)/(p0htime-p3htime)
    pmintime = (p_list[0][0]-p3htime)/(p0htime-p3htime)
    if p3h is not None and p0h is not None:
        p3h = round(p3h,1)
        p0h = round(p0h,1)
        if p3h==p0h:
            # no matter what pressure was in between
            return 4
        if pmin is not None and pmax is not None:
            pmin = round(pmin,1)
            pmax = round(pmax,1)
            if pmin==p3h and pmax==p0h:
                return 2
            if pmin==p0h and pmax==p3h:
                return 7
            if p0h>p3h and pmin<=p0h:
                return 3
            if p0h<=p3h and pmin<p0h:
                return 5
            if p0h<p3h and pmax>=p3h:
                return 8
            if p0h<p3h and pmin==p0h:
                return 6
            if p0h>p3h and pmax==p0h:
                return 1
    return None

def pressure_tendency_bufr(p3, p2, p1, p0):
    """ pressure tendency according to the algorithm defined in BUFR
    
        Args:
            p3 (float): barometer 3 hours ago
            p2 (float): barometer 2 hours ago
            p1 (float): barometer 1 hour ago
            p0 (float): barometer now
            
        Returns:
            int: pressure tendency code a according to table 0200
    """
    A = {
        ( 1, 1, 1):3,
        ( 1, 1, 0):3,
        ( 1, 1,-1):3,
        ( 1, 0, 1):2,
        ( 1, 0, 0):2,
        ( 1, 0,-1):2,
        ( 1,-1, 1):1,
        ( 1,-1, 0):1,
        ( 1,-1,-1):0,
        ( 0, 1, 1):5,
        ( 0, 1, 0):5,
        ( 0, 1,-1):5,
        ( 0, 0, 1):4,
        ( 0, 0, 0):4,
        ( 0, 0,-1):4,
        ( 0,-1, 1):0,
        ( 0,-1, 0):0,
        ( 0,-1,-1):0,
        (-1, 1, 1):5,
        (-1, 1, 0):6,
        (-1, 1,-1):6,
        (-1, 0, 1):7,
        (-1, 0, 0):7,
        (-1, 0,-1):7,
        (-1,-1, 1):8,
        (-1,-1, 0):8,
        (-1,-1,-1):8
    }
    def sign(x):
        if x>0: return 1
        if x<0: return -1
        return 0
    try:
        # barometer difference
        diff_all   = p0-p3 # over all
        diff_third = p0-p1 # of the 3rd hour
        diff_first = p2-p3 # of the 1st hour
        # table lookup
        return A.get((sign(diff_all),
                      sign(diff_third-diff_first),
                      sign(diff_third)))
    except TypeError:
        return None
    
    
def pressure_tendency_svg_path(x, y, width, a):
    hl = width*0.75
    hk = hl*0.3
    bl = hl*0.577350269189626
    bk = hk*0.577350269189626
    if a==0:
        d = 'M %f,%f l %f,%f l %f,%f' % (x-bk/2-bl/2,y+hl/2,bl,-hl,bk,hk)
    elif a==1:
        d = 'M %f,%f l %f,%f h %f' % (x-hk/2-bl/2,y+hl/2,bl,-hl,hk)
    elif a==2:
        d = 'M %f,%f l %f,%f' % (x-bl/2,y+hl/2,bl,-hl)
    elif a==3:
        d = 'M %f,%f l %f,%f l %f,%f' % (x-bk/2-bl/2,y+hl/2-hk,bk,hk,bl,-hl)
    elif a==4:
        b = bl+bk
        d = 'M %f,%f h %f' % (x-b/2,y,b)
    elif a==5:
        d = 'M %f,%f l %f,%f l %f,%f' % (x-bl/2-bk/2,y-hl/2,bl,hl,bk,-hk)
    elif a==6:
        d = 'M %f,%f l %f,%f h %f' % (x-bl/2-hk/2,y-hl/2,bl,hl,hk)
    elif a==7:
        d = 'M %f,%f l %f,%f' % (x-bl/2,y-hl/2,bl,hl)
    elif a==8:
        d = 'M %f,%f l %f,%f l %f,%f' % (x-bl/2-bk/2,y-hl/2+hk,bk,-hk,bl,hl)
    else:
        return ''
    return '<path stroke="currentColor" stroke-width="%.1f" fill="none" d="%s" />' % (width*0.05,d)

def decolor_ww(ww_symbol, color):
    """ convert colored symbols to black or white 
    
        Args:
            ww_symbol (str): SVG of the symbol to remove color
            color (str): target color, normally #000000 or #ffffff
        
        Returns:
            str: SVG with changed colors
    """
    if color is None: return ww_symbol
    return ww_symbol.replace('#ffc83f',color).replace('#ed1c24',color).replace('#00d700',color).replace('#ac00ff',color).replace('#000000',color).replace('black',color).replace('currentColor',color)

def print_ww_list(image_path='.'):
    """ create a HTML table of present weather symbols and descriptions
    
        Args:
            image_path (str): path to the symbols
            
        Returns:
            str: table in HTML
    """
    x = copy.copy(WW_LIST)
    x.sort(key=lambda x:x[0])
    s = '<table>\n'
    s += '  <tr>\n'
    s += '    <th>WW</th>\n'
    s += '    <th>WMO-Symbol</th>\n'
    s += '    <th></th>\n'
    s += '    <th>Bedeutung</th>\n'
    s += '  </tr>\n'
    for ww in x:
        s += '  <tr>\n'
        s += '    <td>%02d</td>\n' % ww[0]
        s += '    <td>'+WW_SYMBOLS[ww[0]]+'</td>\n'
        s += '    <td>'
        if ww[4]:
            s += '<img src="%s" width="50" alt="%s" />' % (ww[4],ww[1])
        s += '</td>\n'
        s += '    <td>'+ww[1]+'</td>\n'
        s += '  </tr>\n'
    s += '</table>\n'
    return s
    
def print_ww_tab(image_path='.', color=None):
    """ create the wellknown table of present weather codes for manned stations
    
        Args:
            image_path (str): path to the symbols
            color (str): use this color instead of the original colors
            
        Returns:
            str: table in HTML
    """
    s = '<table cellspacing="0">\n'
    s += '<tr>\n  <th style="margin:0px;border:1px solid black;padding:5px;background-color:#E0E0E0">ww</th>\n'
    for i in range(10):
        s += '  <th style="margin:0px;border-top:1px solid black;border-right:1px solid black;border-bottom:1px solid black;padding:5px;background-color:#E0E0E0">%1d</th>\n' % i
    s += '</tr>\n'
    for ww,sym in enumerate(WW_SYMBOLS):
        if (ww%10)==0:
            s += '<tr>\n  <th style="margin:0px;border-left:1px solid black;border-right:1px solid black;border-bottom:1px solid black;padding:5px;background-color:#E0E0E0">%1d0</th>\n' % (ww//10)
        s += '  <td style="margin:0px;border-right:1px solid black;border-bottom:1px solid black;padding:5px">'+decolor_ww(sym,color).replace('width="50"','width="40"').replace('height="50"','height="40"')+'</td>\n'
        if (ww%10)==9:
            s += '</tr>\n'
    s += '</table>\n'
    return s

def print_wawa_tab(image_path='.', color=None):
    """ create the wellknown table of present weather codes for unmanned stations
    
        Args:
            image_path (str): path to the symbols
            color (str): use this color instead of the original colors
            
        Returns:
            str: table in HTML
    """
    s = '<table cellspacing="0">\n'
    s += '<tr>\n  <th style="margin:0px;border:1px solid black;padding:5px;background-color:#E0E0E0">w<sub>a</sub>w<sub>a</sub></th>\n'
    for i in range(10):
        s += '  <th style="margin:0px;border-top:1px solid black;border-right:1px solid black;border-bottom:1px solid black;padding:5px;background-color:#E0E0E0">%1d</th>\n' % i
    s += '</tr>\n'
    for ww,sym in enumerate(WAWA_SYMBOLS):
        if (ww%10)==0:
            s += '<tr>\n  <th style="margin:0px;border-left:1px solid black;border-right:1px solid black;border-bottom:1px solid black;padding:5px;background-color:#E0E0E0">%1d0</th>\n' % (ww//10)
        s += '  <td style="margin:0px;border-right:1px solid black;border-bottom:1px solid black;padding:5px;text-align:center">'
        if sym is not None:
            s += decolor_ww(sym,color).replace('width="50"','width="40"').replace('height="50"','height="40"')
        else:
            s += 'res.'
        s += '</td>\n'
        if (ww%10)==9:
            s += '</tr>\n'
    s += '</table>\n'
    return s

def print_n_tab(image_path='.', color=None):
    """ create a table of cloud cover symbols """
    s = '<table cellspacing="0">\n'
    s += '<tr>\n  <th style="margin:0px;border:1px solid black;padding:5px;background-color:#E0E0E0">&nbsp;N&nbsp;</th>\n'
    for i in range(10):
        s += '  <th style="margin:0px;border-top:1px solid black;border-right:1px solid black;border-bottom:1px solid black;padding:5px;background-color:#E0E0E0">%1d</th>\n' % i
    s += '  <th style="margin:0px;border-top:1px solid black;border-right:1px solid black;border-bottom:1px solid black;padding:5px;background-color:#E0E0E0">/</th>\n' 
    s += '</tr>\n'
    s += '<tr>\n  <th style="margin:0px;border-left:1px solid black;border-right:1px solid black;border-bottom:1px solid black;padding:5px;background-color:#E0E0E0"></th>\n' 
    for n,sym in enumerate(OKTA_SYMBOLS):
        s += '  <td style="margin:0px;border-right:1px solid black;border-bottom:1px solid black;padding:5px;text-align:center">'
        if sym is not None:
            s += decolor_ww(sym,color).replace('width="50"','width="40"').replace('height="50"','height="40"')
        else:
            s += 'res.'
        s += '</td>\n'
    s += '</tr>\n'
    s += '</table>\n'
    return s

def print_W1W2_tab(image_path='.', color=None):
    """ create a table of cloud cover symbols """
    s = '<table cellspacing="0">\n'
    s += '<tr>\n  <th style="margin:0px;border:1px solid black;padding:5px;background-color:#E0E0E0">&nbsp;W&nbsp;</th>\n'
    for i in range(10):
        s += '  <th style="margin:0px;border-top:1px solid black;border-right:1px solid black;border-bottom:1px solid black;padding:5px;background-color:#E0E0E0">%1d</th>\n' % i
    s += '</tr>\n'
    s += '<tr>\n  <th style="margin:0px;border-left:1px solid black;border-right:1px solid black;border-bottom:1px solid black;padding:5px;background-color:#E0E0E0"></th>\n' 
    for n,sym in enumerate(W_SYMBOLS):
        s += '  <td style="margin:0px;border-right:1px solid black;border-bottom:1px solid black;padding:5px;text-align:center">'
        if sym is not None:
            s += decolor_ww(sym,color).replace('width="50"','width="40"').replace('height="50"','height="40"')
        else:
            s += WAWA_SYMBOLS[0].replace('width="50"','width="40"').replace('height="50"','height="40"')
        s += '</td>\n'
    s += '</tr>\n'
    s += '</table>\n'
    return s

def write_svg_files_ww(image_path='.'):
    for ww,sym in enumerate(WW_SYMBOLS):
        fn = os.path.join(image_path,'wmo4677_ww%02d.svg' % ww)
        with open(fn,'w') as file:
            file.write(WW_XML)
            file.write(sym)

def write_svg_files_wawa(image_path='.'):
    for wawa,sym in enumerate(WAWA_SYMBOLS):
        fn = os.path.join(image_path,'wmo4680_wawa%02d.svg' % wawa)
        if sym:
            with open(fn,'w') as file:
                file.write(WW_XML)
                file.write(sym)

def write_svg_files_W(image_path='.'):
    for w,sym in enumerate(W_SYMBOLS):
        fn = os.path.join(image_path,'wmo4561_W%01d.svg' % w)
        if sym:
            with open(fn,'w') as file:
                file.write(WW_XML)
                file.write(sym)

def write_svg_files_n(image_path='.'):
    for n,sym in enumerate(OKTA_SYMBOLS):
        fn = os.path.join(image_path,'wmo2700_n%02d.svg' % n)
        if sym:
            with open(fn,'w') as file:
                file.write(WW_XML)
                file.write(sym)

def write_svg_files_a(image_path='.'):
    for a in range(9):
        fn = os.path.join(image_path,'wmo0200_a%01d.svg' % a)
        with open(fn,'w') as file:
            file.write(WW_XML+'\n')
            file.write('<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="50" height="50" viewBox="-25 -25 50 50">\n')
            file.write('<desc>WMO 0200 a %01d</desc>\n' % a)
            file.write(pressure_tendency_svg_path(0,0,50,a)+'\n')
            file.write('</svg>\n')

if hasSearchList:

    class PresentWeatherBinder(object):
        """ class for $presentweather """
    
        def __init__(self, wwl=None, n=None, night=False, lang='en', ww_texts=None, wawal=None, **kwargs):
            # We need the raw values.
            if isinstance(wwl,ValueHelper) or isinstance(wwl,AggTypeBinder):
                if isinstance(wwl.value_t,ValueTuple) and wwl.value_t[2]=='group_wmo_wawa':
                    wawal = wwl.raw
                    wwl = None
                else:
                    wwl = wwl.raw
            if isinstance(n,ValueHelper) or isinstance(n,AggTypeBinder):
                n = n.raw
            if isinstance(wawal,ValueHelper) or isinstance(wawal,AggTypeBinder):
                if isinstance(wawal.value_t,ValueTuple) and wawal.value_t[2]=='group_wmo_ww':
                    wwl = wawal.raw
                    wawal = None
                else:
                    wawal = wawal.raw
            # convert to list if it is not
            if (wwl is None) or isinstance(wwl,list):
                self.ww_list = wwl
            else:
                self.ww_list = [weeutil.weeutil.to_int(wwl)]
            self.nn = weeutil.weeutil.to_int(n)
            self.night = weeutil.weeutil.to_bool(night)
            self.lang = lang
            self.ww_texts = ww_texts
            # convert to list if it is not
            if (wawal is None) or isinstance(wawal,list):
                self.wawa_list = wawal
            else:
                self.wawa_list = [weeutil.weeutil.to_int(wawal)]
            # remember kwargs
            self.kwargs = kwargs
        
        def _get_ww_text(self, wwcode):
            ww_str = '%02d' % wwcode[0]
            if self.ww_texts and ww_str in self.ww_texts:
                return self.ww_texts[ww_str]
            elif self.lang=='de':
                return wwcode[1]
            else:
                return wwcode[2]
        
        def __getattr__(self, attr):
            if self.ww_list is not None:
                wwcode = get_ww(self.ww_list,self.nn,self.night)
                if wwcode:
                    if attr=='ww':
                        return wwcode[0]
                    if attr=='text':
                        return self._get_ww_text(wwcode)
                    if attr=='mosmix_priority':
                        return wwcode[3]
                    if attr=='belchertown_icon':
                        return wwcode[4]
                    if attr=='dwd_icon':
                        return wwcode[5]
                    if attr=='aeris_icon':
                        icon = wwcode[6]
                        if icon:
                            if self.night: icon += 'n'
                            icon += '.png'
                        else:
                            icon = 'na.png'
                        return icon
                    if attr=='wi_icon':
                        icon = wwcode[8]
                        if not icon: icon = 'wi-na'
                        return '<i class="wi %s"></i>' % icon
                    if attr=='svg_icon_filename':
                        if wwcode[0]==18 and self.nn is not None:
                            # squall
                            return get_ww([0,],self.nn,self.night)[4].replace('.png','-wind.svg')
                        if wwcode[0]==96:
                            return 'thunderstorm-hail.svg'
                        if wwcode[0] in (13,17):
                            return 'lightning.svg'
                        if wwcode[0] in (56,57,66,67):
                            return 'freezingrain.svg'
                        return wwcode[4].replace('.png','.svg')
                    if attr=='svg_icon':
                        try:
                            return SVGIconBinder(wwcode[0],n=self.nn,night=self.night,text=self._get_ww_text(wwcode))
                        except (LookupError,ArithmeticError,TypeError,ValueError):
                            return ""
                    if attr=='wmo_symbol':
                        return WMOSymbolBinder(wwcode[0],4677)
                    if attr=='station':
                        return StationBinder(ww=wwcode[0],n=self.nn,**self.kwargs)
            elif self.wawa_list is not None:
                if attr=='wi_icon':
                    return '<i class="wi wi-wmo4680-%02d"></i>' % max(self.wawa_list)
                if attr=='wmo_symbol':
                    return WMOSymbolBinder(max(self.wawa_list),4680)
                if attr=='station':
                    return StationBinder(wawa=max(self.wawa_list),n=self.nn,**self.kwargs)
            elif self.nn is not None:
                if attr=='n':
                    if self.nn>106.25:
                        if self.nn>118.75:
                            return '/'
                        return '-'
                    if self.lang=='de':
                        return ('%s%%' % self.nn).replace('.',',')
                    return '%s%%' % self.nn
                if attr=='okta':
                    if self.nn>118.75:
                        return '/'
                    return '%.0f/8' % (self.nn/100*8)
                if attr=='svg_icon':
                    try:
                        return SVGIconBinder(None,n=self.nn,night=self.night,text=None)
                        #return svg_icon_n(int(round(self.nn/100*8,0)))
                    except (LookupError,ArithmeticError,TypeError,ValueError):
                        return ""
                if attr=='wmo_symbol':
                    try:
                        return WMOSymbolBinder(int(round(self.nn/100*8,0)),2700)
                    except (LookupError,TypeError,ValueError):
                        return WMOSymbolBinder(None,2700)
                if attr=='station':
                    return StationBinder(n=self.nn,**self.kwargs)
                if attr=='text':
                    try:
                        if self.lang in OKTA_TEXTS:
                            txt = OKTA_TEXTS[self.lang][int(round(self.nn/100*8,0))]
                            if isinstance(txt,tuple):
                                txt = txt[1] if self.night else txt[0]
                            return txt
                        return '%s%%' % self.nn
                    except (LookupError,TypeError,ValueError):
                        return str(self.nn)
                n = get_cloudcover(self.nn)
                if attr=='belchertown_icon':
                    night = 1 if self.night else 0
                    return n[night]
                if attr=='dwd_icon':
                    return n[2]
                if attr=='aeris_icon':
                    night = 'n' if self.night and n[4]!='na' else ''
                    return n[4]+night+'.png'
                if attr=='wi_icon':
                    night = 6 if self.night else 5
                    return '<i class="wi %s"></i>' % n[night]
                if attr=='svg_icon_filename':
                    night = 1 if self.night else 0
                    return n[night].replace('.png','.svg')
            return super(PresentWeatherBinder,self).__getattr__(attr)

    class SVGIconBinder(object):
        """ Helper class for $presentweather(...).svg_icon """
        
        def __init__(self, ww, n=None, night=None, text=None):
            self.ww = ww
            self.nn = n
            self.night = night
            self.text = text
        
        def __str__(self):
            try:
                if self.nn is not None:
                    if self.ww is None or self.ww<=3 or (self.ww>=20 and self.ww<30) or self.ww in (14,15,16,18):
                        return svg_icon_n(int(round(float(self.nn)/100.0*8.0,0)),night=self.night,text=self.text,wind=3 if self.ww==18 else 0)
                return svg_icon_ww(self.ww,text=self.text)
            except (LookupError,ArithmeticError,TypeError,ValueError):
                return ""
        
        def __call__(self, width=128, x=None, y=None, with_tooltip=True):
            try:
                if self.nn is not None:
                    if self.ww is None or self.ww<=3 or (self.ww>=20 and self.ww<30) or self.ww in (14,15,16,18):
                        return svg_icon_n(
                                   int(round(float(self.nn)/100.0*8.0,0)),
                                   night=self.night,
                                   width=width,
                                   text=self.text if with_tooltip else None,
                                   x=x,y=y,
                                   wind=3 if self.ww==18 else 0)
                return svg_icon_ww(self.ww,
                                   width=width,
                                   text=self.text if with_tooltip else None,
                                   x=x,y=y)
            except (LookupError,ArithmeticError,TypeError,ValueError):
                return ""

    class WMOSymbolBinder(object):
        """ Helper class for $presentweather(...).wmo_symbol """
    
        def __init__(self, code, code_table):
            self.ww = code
            self.code_table = code_table
            try:
                self.wmosymbol = WMO_TABLES[code_table][code]
            except (LookupError,TypeError,ValueError,ArithmeticError):
                self.wmosymbol = str(code_table)+':'+str(code)
            
        def __str__(self):
            return self.wmosymbol
            
        def __call__(self, width=40, color=None):
            sym = self.wmosymbol
            if sym is None:
                sym = "N/A"
            else:
                if width:
                    sym = sym.replace('width="50"','width="%s"' % width).replace('height="50"','height="%s"' % width)
                if color is not None:
                    sym = decolor_ww(sym,color)
            return sym
    
    class StationBinder(object):
        """ Helper class for station model """
    
        # relative position of the weather elements within the station
        # model
        # x0,y0,x1,y1 --> surrounding rectangle
        # x,y         --> position of the symbol or text
        # size        --> size factor 
        # all values in respect to the parameter "width" 
        FORMAT = {
            'WMO': {
                #        x0 y0 x1 y1 x    y    size
                'n':    ( 0, 0, 1, 1, 0.0, 0.0,1.0),
                'ww':   (-1, 0, 0, 1,-1.0, 0.0,1.0),
                'TTT':  (-1,-1, 0, 0,-0.5,-0.5,0.4),
                'Td':   (-1, 1, 0, 2,-0.5, 1.5,0.4),
                'Tw':   (-1, 2, 0, 3,-0.5, 2.5,0.4),
                'PPPP': ( 1,-1, 2, 0, 1.5,-0.5,0.4),
                'ppp':  ( 0, 1, 2, 1, 1.5, 0.5,0.4),
                'a':    ( 2, 0, 3, 1, 2.5, 0.5,1.0),
                'VV':   (-2, 0,-1, 1,-1.5, 0.5,0.4),
                'W1':   ( 1, 1, 2, 2, 1.00, 1.25,0.5),
                'W2':   ( 1, 1, 2, 2, 1.50, 1.25,0.5),
                'RRR':  ( 1, 2, 2, 3, 1.50, 2.25,0.4),
            },
            'DWD': {
                #        x0 y0 x1 y1 x     y     size
                'n':    ( 0, 0, 1, 1, 0.00, 0.00,1.0),
                'ww':   (-1, 0, 0, 1,-1.00, 0.00,1.0),
                'TTT':  (-1,-1, 0, 0,-0.50,-0.75,0.4),
                'Td':   (-1, 1, 0, 2,-0.50, 1.25,0.4),
                'Tw':   (-1, 1, 0, 2,-0.50, 1.75,0.4),
                'PPPP': ( 1,-1, 2, 0, 1.50,-0.75,0.4),
                'ppp':  ( 1,-1, 2, 0, 1.50,-0.25,0.4),
                'a':    ( 1, 0, 2, 1, 1.50, 0.50,1.0),
                'VV':   (-1, 0,-1, 1,-0.50,-0.25,0.4),
                'W1':   ( 1, 1, 2, 2, 1.00, 1.00,0.5),
                'W2':   ( 1, 1, 2, 2, 1.50, 1.00,0.5),
                'RRR':  ( 1, 1, 2, 2, 1.50, 1.75,0.4),
            }
        }

        def __init__(self, ww=None, wawa=None, n=None, **kwargs):
            self.ww = ww
            self.wawa = wawa
            self.nn = n
            self.kwargs = kwargs
            
        def to_celsius(self, x, round=None):
            """ convert temperature value to text 
            
                Args:
                    x (any type): value to convert
                    round (boolean): round to integer
                    
                Returns:
                    str: value in degrees Celsius
            """
            if x is None:
                return ''
            if isinstance(x,ValueHelper) or isinstance(x,AggTypeBinder):
                t = x.degree_C.raw
            elif isinstance(x,ValueTuple):
                t = weewx.units.convert(x,'degree_C')[0]
            else:
                t = weeutil.weeutil.to_float(x)
            if round: return '%.0f' % t
            return '%.1f' % t
        
        def to_mbar(self, x):
            """ convert barometer to millibar 
            
                Args:
                    x (any type): value to convert
                    
                Returns:
                    float: value in millibar
            """
            if x is None:
                return None
            if isinstance(x,ValueHelper) or isinstance(x,AggTypeBinder):
                p = x.mbar.raw
            elif isinstance(x,ValueTuple):
                p = weewx.units.convert(x,'mbar')[0]
            else:
                p = weeutil.weeutil.to_float(x)
            return p
            
        def to_coded_mbar(self, x):
            """ convert barometer to the encrypted text used in weather maps
            
                If x represents a single value, this value is converted
                and returned as coded barometer. If x represents a timespan
                of barometer values, both the coded barometer and the
                coded pressure tendency are returned.
                
                By convention the pressure tendency is the difference 
                between the first and the last value of the timespan.
                No regression analysis is done.
                
                Args:
                    x (any type): value to convert
                    
                Returns:
                    tuple: coded barometer value and coded pressure tendency
            """
            # get the raw values
            if isinstance(x,ObservationBinder):
                # something like $span(hour_delta=3).barometer
                p = x.last.mbar.raw
                pdiff = x.diff.mbar.raw
            else:
                # all other possible data types
                p = self.to_mbar(x)
                pdiff = None
            # do coding of the barometer value
            if p is None: 
                p = ''
            else:
                p = int(round(p*10.0,0))
                if p>=10000: p -= 10000
                p = '%s' % p
            # do coding of the pressure tendency value
            if pdiff is None:
                pdiff = ''
            else:
                pdiff = '%02d' % (pdiff*10)
            # return results
            return p, pdiff
            
        def pressure_tendency_symbol(self, x, y, width, a):
            """ SVG path element of pressure tendency symbol
            
                according to WMO code table 0200
                
                Args:
                    x: x coordinate of the center of the symbol
                    y: y coordinate of the center of the symbol
                    width: size of the symbol
                    a: characteristic of the pressure tendency code
                    
                Returns:
                    SVG path
                
            """
            if isinstance(a,ObservationBinder):
                # something like $span(hour_delta=3).barometer
                try:
                    if -0.1<a.diff.mbar.raw<0.1:
                        # no matter what is in between
                        a = 4
                    else:
                        # calculate pressure tendency code
                        p_list = []
                        p0 = None
                        t0 = None
                        for start, stop, data in a.series():
                            p1 = self.to_mbar(data)
                            if p0:
                                p_list.append((
                                    (t0+stop.unix_epoch.raw)/2.0,
                                    (p0+p1)/2.0))
                            p0 = p1
                            t0 = start.unix_epoch.raw
                        a = pressure_tendency(p_list)
                except (LookupError,ValueError,TypeError,ArithmeticError,AttributeError) as e:
                    return '<text x="%s" y="%s">%s %s</text>' % (x,y,e.__class__.__name__,e)
            elif isinstance(a,ValueHelper):
                # something like $current.pressureTrend
                a = a.raw
            elif isinstance(a,ValueTuple):
                a = a[0]
            else:
                a = weeutil.weeutil.to_int(a)
            return '<g id="station_a">'+pressure_tendency_svg_path(x, y, width, a)+'<title>a</title></g>'
            
        def wind(self, windspeed, winddir, width, id):
            if isinstance(windspeed,ValueHelper):
                windspeed = windspeed.km_per_hour.raw
            elif isinstance(windspeed,ValueTuple):
                windspeed = weewx.units.convert(windspeed,'km_per_hour')[0]
            else:
                windspeed = weeutil.weeutil.to_float(windspeed)
            if windspeed is None:
                # no wind speed data available
                return ''
            kn = int(round(kph_to_knot(windspeed)/5,0))
            if kn==0:
                # no wind
                return ''
            if isinstance(winddir,ValueHelper):
                winddir = winddir.raw
            elif isinstance(winddir,ValueTuple):
                winddir = winddir.value
            else:
                winddir = weeutil.weeutil.to_float(winddir)
            if winddir is None:
                # no wind direction available
                return ''
            winddir_rad = -winddir/180.0*math.pi 
            x = 0.5*width*math.cos(winddir_rad)+width/2
            y = -0.5*width*math.sin(winddir_rad)+width/2
            b = width*math.sin(winddir_rad)
            h = width*math.cos(winddir_rad)
            bb = 0.1*width*math.cos(winddir_rad+0.286)
            hh = -0.1*width*math.sin(winddir_rad+0.286)
            #s = '<circle fill="red" cx="%f" cy="%f" r="3" />' % (x-b/2,y-h/2)
            s = '<g id="%s">' % id
            d = 'M%f,%f l%f,%f ' % (x-b/2,y-h/2,b,h)
            if kn>=10:
                s += '<path stroke="currentColor" stroke-width="%.1f" fill="currentColor" d="M%f,%f l%f,%f l%f,%f z" />' % (width*0.05,x-b/2,y-h/2,0.13*width*math.cos(winddir_rad-0.286),-0.13*width*math.sin(winddir_rad-0.286),-1.3*bb,-1.3*hh)
                kn2 = (kn-9)//2
                ii0 = 1.8
            else:
                kn2 = (kn+1)//2
                ii0 = 0
            for ii in range(kn2):
                if ii==(kn2-1) and (kn%2)!=0:
                    bbi = bb
                    hhi = hh
                else:
                    bbi = 2*bb
                    hhi = 2*hh
                if kn==1:
                    jj = 1
                else:
                    jj = ii+ii0
                d += 'M%f,%f l%f,%f ' % (x-b/2+b*0.1*jj,y-h/2+h*0.1*jj,bbi,hhi)
            s += '<path stroke="currentColor" stroke-width="%.2f" fill="none" d="%s" />' % (width*0.05,d)
            #s += self.svg_text(x-b/2,y-h/2,width*0.5,'wind','%s' % kn)
            s += '</g>'
            return s

        def svg_text(self, x, y, size, id, text, title=None):
            """ SVG text element """
            if title:
                title = '<title>%s</title>' % title
            else:
                title = ''
            return '<g><text id="%s" dominant-baseline="middle" text-anchor="middle" x="%.2f" y="%.2f" fill="currentColor" stroke="none" font-family="sans-serif" font-size="%d" font-weight="normal">%s</text>%s</g>' % (id,x,y,size,text,title)
            
        def station(self, format='WMO', width=None, color=None, round_temp=None, id_prefix='station'):
            """ SVG of station model
            
                Args:
                    format:     'WMO', 'DWD'
                    width:      width of the cloud cover symbol
                    color:
                    round_temp: round temperature to whole degrees
                    id_prefix (str): SVG element id prefix
                
                Returns:
                    str: SVG of the station model
            """
            if not width: width = 50
            format = format.upper()
            if format=='DWD' and round_temp is None:
                round_temp = True
            format = StationBinder.FORMAT.get(format,StationBinder.FORMAT['WMO'])
            els = []
            # cloud cover symbol (mandatory)
            obsfmt = format['n']
            x0, y0 = obsfmt[0]*width, obsfmt[1]*width
            x1, y1 = obsfmt[2]*width, obsfmt[3]*width
            try:
                st = WMO_TABLES[2700][int(round(self.nn/100*8,0))]
            except (LookupError,TypeError,ValueError,ArithmeticError):
                st = WMO_TABLES[2700][10]
            if width:
                st = st.replace('width="50"','width="%d"' % width).replace('height="50"','height="%d"' % width)
            if color:
                st = decolor_ww(st,color)
            st = st.replace('<svg ','<svg x="%.2f" y="%.2f" ' % (obsfmt[4]*width,obsfmt[5]*width))
            els.append(st)
            # present weather symbol
            try:
                if self.ww is not None:
                    ww = WMO_TABLES[4677][self.ww]
                elif self.wawa is not None:
                    ww = WMO_TABLES[4680][self.wawa]
                else: 
                    ww = None
                if ww:
                    if width:
                        ww = ww.replace('width="50"','width="%d"' % (format['ww'][6]*width)).replace('height="50"','height="%d"' % (format['ww'][6]*width))
                    if color:
                        ww = decolor_ww(ww,color)
                    ww = ww.replace('<svg ','<svg x="%.2f" y="%.2f" ' % (format['ww'][4]*width,format['ww'][5]*width))
                    x0 = min(x0,format['ww'][0]*width)
                    y0 = min(y0,format['ww'][1]*width)
                    x1 = max(x1,format['ww'][2]*width)
                    y1 = max(y1,format['ww'][3]*width)
                    els.append(ww)
            except (LookupError,TypeError,ValueError,ArithmeticError):
                pass
            # wind
            if 'windDir' in self.kwargs and 'windSpeed' in self.kwargs:
                x = self.wind(self.kwargs['windSpeed'],self.kwargs['windDir'],width,id_prefix+'_'+'wind')
                if x:
                    els.append(x)
                    x0 = min(x0,-15)
                    y0 = min(y0,-15)
                    x1 = max(x1,width+15)
                    y1 = max(y1,width+15)
            # barometer
            if 'a' in self.kwargs:
                obsfmt = format['a']
                if self.kwargs['a'] is not None:
                    x0 = min(x0,obsfmt[0]*width)
                    y0 = min(y0,obsfmt[1]*width)
                    x1 = max(x1,obsfmt[2]*width)
                    y1 = max(y1,obsfmt[3]*width)
                    els.append(self.pressure_tendency_symbol(obsfmt[4]*width,obsfmt[5]*width,obsfmt[6]*width,self.kwargs['a']))
            # text 
            for obs,val in self.kwargs.items():
                if obs in ('outTemp','TTT','TT'):
                    obsfmt = format['TTT']
                    t = self.to_celsius(val,round_temp)
                    els.append(self.svg_text(obsfmt[4]*width,obsfmt[5]*width,width*0.4,id_prefix+'_'+obs,t,title='TTT'))
                    #els.append('<circle cx="%d" cy="%d" r="3" fill="red" />' % (-width/2,-width/2))
                elif obs in ('dewpoint','TdTdTd','Td'):
                    obsfmt = format['Td']
                    td = self.to_celsius(val,round_temp)
                    els.append(self.svg_text(obsfmt[4]*width,obsfmt[5]*width,width*0.4,id_prefix+'_'+obs,td,title='Td'))
                    #els.append('<circle cx="%d" cy="%d" r="3" fill="red" />' % (-width/2,width*1.5))
                elif obs in ('barometer','PPPP'):
                    # barometer, barometer trend, pressure tendency symbol
                    # Note: If val is of type ObservationBinder like in
                    #       $span.barometer the barometer trend is derived
                    #       from the timespan supplied, and the barometer
                    #       readings within that timespan are used to
                    #       determine the pressure tendency symbol. The
                    #       barometer reading displayed is the last 
                    #       reading within the timespan. If val is of
                    #       another type, the barometer value is displayed
                    #       only.
                    p, pdiff = self.to_coded_mbar(val)
                    if p:
                        obsfmt = format['PPPP']
                        x0 = min(x0,obsfmt[0]*width)
                        y0 = min(y0,obsfmt[1]*width)
                        x1 = max(x1,obsfmt[2]*width)
                        y1 = max(y1,obsfmt[3]*width)
                        els.append(self.svg_text(obsfmt[4]*width,obsfmt[5]*width,width*0.4,id_prefix+'_'+'PPPP',p,title='PPPP'))
                    if pdiff:
                        obsfmt = format['ppp']
                        x0 = min(x0,obsfmt[0]*width)
                        y0 = min(y0,obsfmt[1]*width)
                        x1 = max(x1,obsfmt[2]*width)
                        y1 = max(y1,obsfmt[3]*width)
                        els.append(self.svg_text(obsfmt[4]*width,obsfmt[5]*width,width*0.4,id_prefix+'_'+'ppp',pdiff,title='ppp'))
                    if (isinstance(val,ObservationBinder) and 
                        'a' not in self.kwargs):
                        obsfmt = format['a']
                        x0 = min(x0,obsfmt[0]*width)
                        y0 = min(y0,obsfmt[1]*width)
                        x1 = max(x1,obsfmt[2]*width)
                        y1 = max(y1,obsfmt[3]*width)
                        els.append(self.pressure_tendency_symbol(obsfmt[4]*width,obsfmt[5]*width,obsfmt[6]*width,val))
                elif obs=='visibility':
                    obsfmt = format['VV']
                    if isinstance(val,ValueHelper):
                        vv = val.meter.raw
                    else:
                        vv = weeutil.weeutil.to_float(val)
                    els.append(self.svg_text(obsfmt[4]*width,obsfmt[5]*width,width*0.4,id_prefix+'_'+'VV',visibility_code(vv),title='VV'))
                elif obs in ('W1','W2','W1W2'):
                    obsfmt = format[obs]
                    if isinstance(val,ObservationBinder):
                        ww = val.max.value_t
                    elif isinstance(val,AggTypeBinder):
                        ww = val.value_t
                    elif isinstance(val,ValueTuple):
                        ww = val
                    else:
                        ww = ValueTuple(weeutil.weeutil.to_int(val),None,None)
                    if ww[2]=='group_wmo_ww':
                        if 30<=ww[0]<36:
                            ww = WAWA_SYMBOLS[27]
                        elif 36<=ww[0]<40:
                            ww = WW_SYMBOLS[38]
                        elif ww[0]==90:
                            ww = W_SYMBOLS[8]
                        elif ww[0]>=40:
                            ww = W_SYMBOLS[int(ww[0])//10]
                        else:
                            ww = None
                    elif ww[2]=='group_wmo_wawa':
                        if 27<=ww[0]<30:
                            ww = WAWA_SYMBOLS[27]
                        elif 30<=ww[0]<=35:
                            ww = WAWA_SYMBOLS[33]
                        elif 40<=ww[0]<50:
                            ww = WAWA_SYMBOLS[40]
                        elif ww[0]>=50:
                            ww = W_SYMBOLS[int(ww[0])//10]
                        else:
                            ww = None
                    else:
                        ww = W_SYMBOLS[int(ww[0])]
                    if ww:
                        if width:
                            ww = ww.replace('width="50"','width="%d"' % (obsfmt[6]*width)).replace('height="50"','height="%d"' % (obsfmt[6]*width))
                        if color:
                            ww = decolor_ww(ww,color)
                        ww = ww.replace('<svg ','<svg x="%d" y="%d" ' % (obsfmt[4]*width,obsfmt[5]*width))
                        els.append(ww)
                else:
                    obsfmt = None
                if obsfmt:
                    x0 = min(x0,obsfmt[0]*width)
                    y0 = min(y0,obsfmt[1]*width)
                    x1 = max(x1,obsfmt[2]*width)
                    y1 = max(y1,obsfmt[3]*width)
            b = x1-x0
            h = y1-y0
            s = '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="%d" height="%d" viewBox="%d %d %d %d">\n' % (b,h,x0,y0,b,h)
            for el in els:
                s += el+'\n'
            s += '</svg>\n'
            return s
            
        def __str__(self):
            return self.station()
            
        def __call__(self, format='WMO', width=40, color=None, round_temp=None,id_prefix='station'):
            return self.station(format,width,color,round_temp,id_prefix)
            
    class WeatherSearchList(SearchList):
        """ Search list extension to provide $presentweather """
    
        def __init__(self, generator):
            """Create an instance of the class"""
            super(WeatherSearchList,self).__init__(generator)
            # get language
            self.lang = self.generator.skin_dict.get('lang','en')
            self.ww_texts = self.generator.skin_dict.get('Texts',configobj.ConfigObj()).get('ww',None)
            
        def get_extension_list(self, timespan, db_lookup):
        
            def presentweather(ww=None, n=None, night=False, wawa=None, **kwargs):
                for ii in ('wwl','n','night','lang','texts','wawal'):
                    if ii in kwargs:
                        kwargs.pop(ii)
                return PresentWeatherBinder(wwl=ww, n=n, night=night, lang=self.lang, ww_texts=self.ww_texts, wawal=wawa, **kwargs)
                
            return [{'presentweather':presentweather}]
            
            
if __name__ == "__main__":

    usage = """Usage: %prog [options]

Direct call is for testing only."""
    epilog = None

    # Create a command line parser:
    parser = optparse.OptionParser(usage=usage, epilog=epilog)

    parser.add_option("--print-ww-list", dest="printwwlist", action="store_true",
                      help="Print ww list")
    parser.add_option("--print-ww-tab", dest="printwwtab", action="store_true",
                      help="Print ww table")
    parser.add_option("--print-wawa-tab", dest="printwawatab", action="store_true",
                      help="Print wawa table")
    parser.add_option("--print-n-tab", dest="printntab", action="store_true",
                      help="Print cloud cover table (N)")
    parser.add_option("--print-W1W2-tab", dest="printW1W2tab", action="store_true",
                      help="Print past weather table (W1W2)")
    parser.add_option("--write-svg", dest="writesvg", action="store_true",
                      help="Create a set of SVG files")
    parser.add_option("--test-searchlist", dest="searchlist", action="store_true",
                      help="Test search list extension")
    parser.add_option("--station", dest="station", action="store_true",
                      help="Station symbol")

    (options, args) = parser.parse_args()

    # options
    #x = copy.copy(WW_LIST)
    #x.sort(key=lambda x:x[0])
    #for i in x:
    #    print("%02d %-60s %-62s %4s %-16s %-8s %-14s %8s" % i)
    if options.printwwlist:
        print(print_ww_list())
    elif options.printwwtab:
        print(print_ww_tab(color=None))
    elif options.printwawatab:
        print(print_wawa_tab(color=None))
    elif options.printntab:
        print(print_n_tab(color=None))
    elif options.printW1W2tab:
        print(print_W1W2_tab(color=None))
    elif options.writesvg:
        if len(args)>0:
            pth = args[0]
        else:
            pth = '.'
        write_svg_files_ww(pth)
        write_svg_files_wawa(pth)
        write_svg_files_W(pth)
        write_svg_files_n(pth)
        write_svg_files_a(pth)
    elif options.station:
        # --station
        kwargs = dict()
        for ii in args:
            x = ii.split('=')
            kwargs[x[0]] = x[1]
        if 'n' in kwargs:
            n = kwargs.pop('n')
        else:
            n = None
        if 'ww' in kwargs:
            ww = kwargs.pop('ww')
        else:
            ww = None
        if 'wawa' in kwargs:
            wawa = kwargs.pop('wawa')
        else:
            wawa = None
        if 'format' in kwargs:
            format = kwargs.pop('format')
        else:
            format = 'WMO'
        if 'width' in kwargs:
            width = kwargs.pop('width')
        else:
            width = 50
        print(PresentWeatherBinder(wwl=ww,wawal=wawa,n=n,**kwargs).station(format=format,width=width))
        #print(StationBinder(ww=ww,wawa=wawa,n=n,**kwargs))
    elif options.searchlist:
        class Generator(object):
            skin_dict = configobj.ConfigObj()
        print('SearchList class loaded: %s' % hasSearchList)
        ti = time.time()
        wsl = WeatherSearchList(Generator())
        print('Language code: %s' % wsl.lang)
        sli = wsl.get_extension_list((ti-86400,ti),None)
        print('Extension list: %s' % sli)
        func = sli[0]['presentweather']
        print('Function: %s' % func)
        print('ww22',func(22).ww,type(func(22).ww))
        print('text',func(5).text)
        print('mosmix_priority',func(20).mosmix_priority)
        print('belchertown_icon',func(45).belchertown_icon)
        print('dwd_icon',func(67).dwd_icon)
        print('aeris_icon',func(92).aeris_icon)
        wmosym = func(71).wmo_symbol
        print('wmo_symbol',wmosym)
        print('wmo_symbol',func(83).wmo_symbol(30))
        print('50% bewölkt Tag',func(0,50,False).belchertown_icon)
        print('25% bewölkt Nacht',func(0,25,True).belchertown_icon)
        print('wawa44 wmo_symbol',func(wawa=44).wmo_symbol)
        print('wi',func(ww=19).wi_icon)
        print('wi',func(n=50).wi_icon)
        print('okta',func(n=87.5).wmo_symbol)
        print('svg ww',func(ww=53).svg_icon)
        print('svg n',func(n=50).svg_icon)
    else:
        print('nothing to do')
