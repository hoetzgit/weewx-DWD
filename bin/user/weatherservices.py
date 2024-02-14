#!/usr/bin/python3
# Copyright (C) 2022, 2023, 2024 Johanna Roedenbeck

"""

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""

"""
    POI
    ===
    
    There are data of 47 DWD weather stations available. 
    
    Configuration in weewx.conf:
    
    [DeutscherWetterdienst]
        ...
        [[forecast]]
            icon_set = replace_me # 'belchertown', 'dwd' or 'aeris', optional
            ...
        [[POI]]
            [[[stations]]]
                [[[[station_id]]]]
                    prefix = observation_type_prefix_for_station
                    #icon_set = replace_me # optional, default from section [[forecast]]
                    #log_success = replace_me # True or False, optional
                    #log_failure = replace_me # True or False, optional
                [[[[another_station_id]]]]
                    ...
            ...
    
    station list:
    https://github.com/roe-dl/weewx-DWD/wiki/POI-Stationen-in-Deutschland
    https://www.dwd.de/DE/leistungen/klimadatendeutschland/stationsuebersicht.html
    
    example station ids:
    10578 - Fichtelberg
    10453 - Brocken
    10961 - Zugspitze
    
    Those are all WMO station ids.
    
    current readings:
    https://www.dwd.de/DE/leistungen/beobachtung/beobachtung.html
    
    ----------------
    
    CDC
    ===
    
    CDC includes a lot more of stations than POI.
    
    https://opendata.dwd.de/climate_environment/CDC/Liesmich_intro_CDC-FTP.pdf
    https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/

    station data are in subdirectiory "meta_data"
    
    Configuration in weewx.conf:
    
    [DeutscherWetterdienst]
        ...
        [[CDC]]
            [[[stations]]]
                [[[[station_nr]]]]
                    prefix = observation_type_prefix_for_station
                    # equipment of the weather station (optional)
                    observations = air,wind,gust,precipitation,solar
                    #log_success = replace_me # True or False, optional
                    #log_failure = replace_me # True or False, optional
                [[[[another_station_nr]]]]
                    ...
            ...
    
    station list:
    https://opendata.dwd.de/climate_environment/CDC/help/wetter_tageswerte_Beschreibung_Stationen.txt
    https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/10_minutes/air_temperature/now/zehn_now_tu_Beschreibung_Stationen.txt
    
    example station nrs:
    01358 - Fichtelberg
    00840 - Carlsfeld
    00722 - Brocken
    05792 - Zugspitze
    
    ZAMG
    ====
    
    Austrian weather service
    
    [ZAMG]
        ...
        [[current]]
            [[[stations]]]
                [[[[station_nr]]]]
                    prefix = observation_type_prefix_for_station
                    # equipment of the weather station (optional)
                    observations = air,wind,gust,precipitation,solar
                    #log_success = replace_me # True or False, optional
                    #log_failure = replace_me # True or False, optional
                [[[[another_station_nr]]]]
                    ...
    
    station list:
    https://dataset.api.hub.zamg.ac.at/v1/station/current/tawes-v1-10min/metadata
    
    API description:
    https://dataset.api.hub.geosphere.at/v1/docs/
    
    ----------------
    
    API Open-Meteo
    ==============
    
    Open-Meteo is an open-source weather API with free access for non-commercial use.
    No API key is required. You can use it immediately!
    https://open-meteo.com
    
    unsing here the "DWD ICON API" to get current weather observations
    https://open-meteo.com/en/docs/dwd-api
    
    Configuration weewx.conf:
    
    [DeutscherWetterdienst]
        ...
        [[forecast]]
            icon_set = replace_me # 'belchertown', 'dwd' or 'aeris', optional
            ...
        [[OPENMETEO]]
            #enabled = replace_me # True or False, enable or disable Open-Meteo Service, optional, default False
            #prefix = replace_me # Example: "om", optional, default ""
            #icon_set = replace_me # optional, default from section [[forecast]]
            #debug = 0 # Example: 0 = no debug infos, 1 = min debug infos, 2 = more debug infos, >=3 = max debug infos, optional, default 0
            #log_success = replace_me # True or False, optional
            #log_failure = replace_me # True or False, optional
        ...
    
    API URL Builder:
    https://open-meteo.com/en/docs/dwd-api

    API call example:
    https://api.open-meteo.com/v1/dwd-icon?latitude=49.63227&longitude=12.056186&elevation=394.0&timeformat=unixtime&start_date=2023-01-29&end_date=2023-01-30&temperature_unit=celsius&windspeed_unit=kmh&precipitation_unit=mm&current_weather=true&hourly=temperature_2m,apparent_temperature,dewpoint_2m,pressure_msl,relativehumidity_2m,winddirection_10m,windspeed_10m,windgusts_10m,cloudcover,evapotranspiration,rain,showers,snowfall,freezinglevel_height,snowfall_height,weathercode,snow_depth,direct_radiation_instant
    
    Open-Meteo GitHub:
    https://github.com/open-meteo/open-meteo
"""

VERSION = "0.x"

import threading
import configobj
import requests
import csv
import io
import zipfile
import time
import datetime
import json
import random
import math
import traceback
import os.path

# deal with differences between python 2 and python 3
try:
    # Python 3
    import queue
except ImportError:
    # Python 2
    # noinspection PyUnresolvedReferences
    import Queue as queue

if __name__ == '__main__':

    import sys
    sys.path.append('/usr/share/weewx')

    def logdbg(x):
        print('DEBUG',x)
    def loginf(x):
        print('INFO',x)
    def logerr(x):
        print('ERROR',x)

else:

    try:
        # Test for new-style weewx logging by trying to import weeutil.logger
        import weeutil.logger
        import logging
        log = logging.getLogger("user.DWD")

        def logdbg(msg):
            log.debug(msg)

        def loginf(msg):
            log.info(msg)

        def logerr(msg):
            log.error(msg)

    except ImportError:
        # Old-style weewx logging
        import syslog

        def logmsg(level, msg):
            syslog.syslog(level, 'user.DWD: %s' % msg)

        def logdbg(msg):
            logmsg(syslog.LOG_DEBUG, msg)

        def loginf(msg):
            logmsg(syslog.LOG_INFO, msg)

        def logerr(msg):
            logmsg(syslog.LOG_ERR, msg)

def gettraceback(e):
    return ' - '.join(traceback.format_tb(e.__traceback__)).replace('\n',' ')

import weewx
from weewx.engine import StdService
import weeutil.weeutil
import weewx.accum
import weewx.units
import weewx.wxformulas
from user.weatherservicesutil import wget, BaseThread

try:
    import user.weatherservicesradar
    has_radar = True
except ImportError:
    has_radar = False

try:
    import user.wildfire
    has_wildfire = True
except ImportError:
    has_wildfire = False

try:
    from user.weatherservicesdb import databasecreatethread, databaseput
    has_db = True
except ImportError:
    has_db = False

for group in weewx.units.std_groups:
    weewx.units.std_groups[group].setdefault('group_coordinate','degree_compass')

def saturation_vapor_pressure_DWD(temp_C):
    """ Calculate saturation vapor pressure according to the DWD rules
        
        This function uses the Magnus formula with coefficients given in VuB2.
        https://www.dwd.de/DE/leistungen/pbfb_verlag_vub/pdf_einzelbaende/vub_2_binaer_barrierefrei.pdf?__blob=publicationFile&v=4
        
        Args:
            temp_C (float): temperature in degree Celsius
        
        Returns:
            float: saturation vapor pressure in hPa
    """
    try:
        return 6.11213*math.exp(17.5043*temp_C/(241.2+temp_C))
    except (TypeError,ValueError,LookupError,ArithmeticError):
        return None
    
def barometer_DWD(p, temp_C, humidity, altitude_m):
    """ Calculate barometer out of pressure according to DWD rules
    
        Args:
            p (float): station pressure
            temp_C (float): outdoor temperature in degree Celsius
            humidity (float): outdoor humidity in percent
            altitude_m (float): station altitude in meters
            
        Returns:
            float: barometer (same unit as p)
    """
    try:
        # saturation vapor pressure
        svp = saturation_vapor_pressure_DWD(temp_C)
        # vapor pressure
        vp = svp*humidity/100.0
        # reduction factor
        r = math.exp(9.80665/287.05*altitude_m/(273.15+temp_C+vp*0.12+0.0065*altitude_m/2))
        # barometer
        return p*r
    except (TypeError,ValueError,LookupError,ArithmeticError):
        return None

# Cloud cover icons

N_ICON_LIST = [
    # Belchertown day, Belchertown night, DWD icon, Aeris code, Aeris icon
    ('clear-day.png','clear-night.png','0-8.png','CL','clear'),
    ('mostly-clear-day.png','mostly-clear-night.png','2-8.png','FW','fair'),
    ('partly-cloudy-day.png','partly-cloudy-night.png','5-8.png','SC','pcloudy'),
    ('mostly-cloudy-day.png','mostly-cloudy-night.png','5-8.png','BK','mcloudy'),
    ('cloudy.png','cloudy.png','8-8.png','OV','cloudy')]
    
def get_cloudcover(n):
    """ get icon for cloud cover percentage """
    if n<7:
        icon = N_ICON_LIST[0]
    elif n<32:
        icon = N_ICON_LIST[1]
    elif n<70:
        icon = N_ICON_LIST[2]
    elif n<95:
        icon = N_ICON_LIST[3]
    else:
        icon = N_ICON_LIST[4]
    return icon


class DWDXType(weewx.xtypes.XType):
    """ derived types according to formulae used by the DWD """
    
    def __init__(self, altitude_vt, rv_thread):
        self.altitude = weewx.units.convert(altitude_vt, 'meter')[0]
        self.outTemp = None
        self.outHumidity = None
        self.outTemp_last_seen = 0
        self.outHumidity_last_seen = 0
        self.loop_seen = False
        self.rv_thread = rv_thread
    
    
    def get_scalar(self, obstype, record, dbmanager, **opt_dict):
        if obstype=='barometerDWD':
            return self.barometer(record)
        elif obstype=='outSVPDWD':
            return self.saturationvaporpressure(record)
        else:
            raise weewx.UnknownType(obstype)
    
    
    def remember(self, record):
        """ Remember outTemp and outHumidity for later use
        
            Use LOOP packets only. 
        """
        # Check if data available
        if record is None: return
        """
        # Check if LOOP packet or ARCHIVE record
        if 'interval' in record: 
            # archive record
            return
        """
        ts = record.get('dateTime',time.time())
        # Check if temperature is in the record. If so, remember the reading.
        try:
            if 'outTemp' in record:
                self.outTemp = weewx.units.convert(weewx.units.as_value_tuple(record, 'outTemp'), 'degree_C')[0]
                self.outTemp_last_seen = ts
                logdbg('barometerDWD outTemp %s' % self.outTemp)
        except (LookupError,ValueError,TypeError,ArithmeticError):
            pass
        # Check if humidity is in the record. If so, remember the reading.
        try:
            if 'outHumidity' in record:
                self.outHumidity = weewx.units.convert(weewx.units.as_value_tuple(record, 'outHumidity'), 'percent')[0]
                self.outHumidity_last_seen = ts
                logdbg('barometerDWD outHumidity %s' % self.outHumidity)
        except (LookupError,ValueError,TypeError,ArithmeticError):
            pass
        # Check for outdated readings.
        if self.outTemp_last_seen<(ts-300):
            self.outTemp = None
            logdbg('barometerDWD outTemp outdated')
        if self.outHumidity_last_seen<(ts-300):
            self.outHumidity = None
            logdbg('barometerDWD outHumidity outdated')
    
    
    def barometer(self, record):
        """ barometer (relative air pressure) according to the DWD formula
        
            If `record` is an ARCHIVE record it should contain all the 
            observation types necessary to calculate barometer. If not,
            return `None`.
            
            If `record` is a LOOP packet, it may not contain all the 
            required observation types. So calculate the value if there
            is a `pressure` reading in the record and get temperature
            and humidity out of previous LOOP packets if necessary.
            if one of the required observation types is missing, raise
            an `weewx.NoCalculate` exception, which means, that no
            value is included in the LOOP packet. 
        """
        if record is None: 
            raise weewx.CannotCalculate('barometerDWD')
        try:
            if 'interval' in record:
                # archive record
                p_abs = weewx.units.convert(weewx.units.as_value_tuple(record, 'pressure'), 'hPa')[0]
                outTemp = weewx.units.convert(weewx.units.as_value_tuple(record, 'outTemp'), 'degree_C')[0]
                outHumidity = weewx.units.convert(weewx.units.as_value_tuple(record, 'outHumidity'), 'percent')[0]
                p_rel = barometer_DWD(p_abs,outTemp,outHumidity,self.altitude)
                logdbg('barometerDWD ARCHIVE %s' % p_rel)
            else:
                # loop packet
                if ('pressure' not in record or 
                    self.outTemp is None or 
                    self.outHumidity is None):
                    raise weewx.NoCalculate('barometerDWD')
                p_abs = weewx.units.convert(weewx.units.as_value_tuple(record, 'pressure'), 'hPa')[0]
                p_rel = barometer_DWD(p_abs,self.outTemp,self.outHumidity,self.altitude)
                logdbg('barometerDWD LOOP %s p_abs %s t %s rH %s alt %s' % (p_rel,p_abs,self.outTemp,self.outHumidity,self.altitude))
            return weewx.units.convertStd(weewx.units.ValueTuple(p_rel,'hPa','group_pressure'), record['usUnits'])
        except (LookupError,ValueError,TypeError,ArithmeticError):
            raise weewx.CannotCalculate('barometerDWD')
    
    def saturationvaporpressure(self, record):
        if record is None: 
            raise weewx.CannotCalculate('barometerDWD')
        if 'outTemp' not in record:
            raise weewx.NoCalculate('outSVPDWD')
        try:
            temp = weewx.units.convert(weewx.units.as_value_tuple(record, 'outTemp'), 'degree_C')[0]
            svp = saturation_vapor_pressure_DWD(temp)
            return weewx.units.convertStd(weewx.units.ValueTuple(svp,'hPa','group_pressure'), record['usUnits'])
        except (LookupError,ValueError,TypeError,ArithmeticError):
            raise weewx.CannotCalculate('barometerDWD')

    def get_aggregate(self, obs_type, timespan, aggregate_type, db_manager, **option_dict):
        """ aggregations out of precipitation forecast for the next 2 hours """
        if self.rv_thread:
            forecast = self.rv_thread.get_forecast()
            if obs_type in forecast:
                val = forecast[obs_type]
                x = [x for x in val[0] if x is not None]
                if aggregate_type=='max':
                    return weewx.units.ValueTuple(max(x,default=None),val[1],val[2])
                if aggregate_type=='min':
                    return weewx.units.ValueTuple(min(x,default=None),val[1],val[2])
                if aggregate_type=='avg':
                    return weewx.units.ValueTuple(avg(x,default=None),val[1],val[2])
                raise weewx.UnknownAggregation('%s.%s' % (obs_type,aggregate_type))
        raise weewx.UnknownType(obs_type)
    
    def get_series(self, obs_type, timespan, db_manager, aggregate_type=None,
                   aggregate_interval=None, **option_dict):
        """ precipitation forecast for the next 2 hours """
        if self.rv_thread:
            forecast = self.rv_thread.get_forecast()
            if (forecast and 
                obs_type in forecast and 
                'start' in forecast and 
                'stop' in forecast):
                return (forecast['start'],
                        forecast['stop'],
                        forecast[obs_type])
        raise weewx.UnknownType(obs_type)


class DWDPOIthread(BaseThread):

    OBS = {
        'cloud_cover_total':'cloudcover',
        'dew_point_temperature_at_2_meter_above_ground':'dewpoint',
        'diffuse_solar_radiation_last_hour':'solarRad',
        'dry_bulb_temperature_at_2_meter_above_ground':'outTemp',
        'global_radiation_last_hour':'radiation',
        'height_of_base_of_lowest_cloud_above_station':'cloudbase',
        'horizontal_visibility':'visibility',
        'mean_wind_direction_during_last_10 min_at_10_meters_above_ground':'windDir',
        'mean_wind_speed_during last_10_min_at_10_meters_above_ground':'windSpeed',
        'precipitation_amount_last_hour':'rain',
        'present_weather':'presentWeather',
        'pressure_reduced_to_mean_sea_level':'barometer',
        'relative_humidity':'outHumidity',
        'temperature_at_5_cm_above_ground':'extraTemp1',
        'total_snow_depth':'snowDepth'}
    
    UNIT = {
        'Grad C':'degree_C',
        'W/m2':'watt_per_meter_squared',
        'km/h':'kilometer_per_hour',
        'h':'hour',
        'min':'minute',
        '%':'percent'}
    
    WEATHER = (
        ('unbekannt','unknown.png','unknown.png'), # 0
        ('wolkenlos','clear-day.png','0-8.png'), # 1
        ('heiter','mostly-clear-day.png','2-8.png'), # 2
        ('bewölkt','mostly-cloudy-day.png','5-8.png'), # 3
        ('bedeckt','cloudy.png','8-8.png'), # 4
        ('Nebel','fog.png','40.png'), # 5
        ('gefrierender Nebel','fog.png','48.png'), # 6
        ('leichter Regen','rain.png','7.png'), # 7
        ('Regen','rain.png','8.png'), # 8
        ('kräftiger Regen','rain.png','9.png'), # 9
        ('gefrierender Regen','sleet.png','66.png'), # 10
        ('kräftiger gefrierender Regen','sleet.png','67.png'), # 11
        ('Schneeregen','sleet.png','12.png'), # 12
        ('kräftiger Schneeregen','sleet.png','13.png'), # 13
        ('leichter Schneefall','snow.png','14.png'), # 14
        ('Schneefall','snow.png','15.png'), # 15
        ('kräftiger Schneefall','snow.png','16.png'), # 16
        ('Eiskörner','snow.png','17.png'), # 17
        ('Regenschauer','rain.png','80.png'), # 18
        ('kräftiger Regenschauer','rain.png','82.png'), # 19
        ('Schneeregenschauer','sleet.png','83.png'), # 20
        ('kräftiger Schneeregenschauer','sleet.png','84.png'), # 21
        ('Schneeschauer','snow.png','85.png'), # 22
        ('kräftiger Schneeschauer','snow.png','86.png'), # 23
        ('Graupelschauer','snow.png','87.png'), # 24
        ('kräftiger Graupelschauer','snow.png','88.png'), # 25
        ('Gewitter ohne Niederschlag','thunderstorm.png','26.png'), # 26
        ('Gewitter','thunderstorm.png','27.png'), # 27
        ('kräftiges Gewitter','thunderstorm.png','28.png'), # 28
        ('Gewitter mit Hagel','thunderstorm.png','29.png'), # 29
        ('kräftiges Gewitter mit Hagel','thunderstrom.png','30.png'), # 30
        ('Böen','wind.png','18.png')) # 31
        
    
    def __init__(self, name, location, prefix, iconset=4, log_success=False, log_failure=True):
    
        super(DWDPOIthread,self).__init__(name='DWD-POI-'+name, log_success=log_success, log_failure=log_failure)
        self.location = location
        self.iconset = weeutil.weeutil.to_int(iconset)
        
        self.lock = threading.Lock()
        
        self.data = []
        self.last_get_ts = 0
        
        weewx.units.obs_group_dict.setdefault(prefix+'DateTime','group_time')
        for key in DWDPOIthread.OBS:
            obstype = DWDPOIthread.OBS[key]
            if obstype=='visibility':
                obsgroup = 'group_distance'
            else:
                obsgroup = weewx.units.obs_group_dict.get(obstype)
            if obsgroup:
                weewx.units.obs_group_dict.setdefault(prefix+obstype[0].upper()+obstype[1:],obsgroup)


    def get_data(self, ts):
        """ get buffered data """
        try:
            self.lock.acquire()
            """
            try:
                last_ts = self.data[-1]['time']
                interval = last_ts - self.last_get_ts
                self.last_get_ts = last_ts
            except (LookupError,TypeError,ValueError,ArithmeticError):
                interval = None
            """
            interval = 1
            data = self.data
            #print('POI',data)
        finally:
            self.lock.release()
        #loginf("get_data interval %s data %s" % (interval,data))
        return data,interval


    @staticmethod
    def to_float(x):
        """ convert value out of the CSV file to float """
        try:
            if x[0:1]=='--': raise ValueError('no number')
            if ',' in x:
                return float(x.replace(',','.'))
            if '.' in x:
                return float(x)
            return int(x)
        except Exception:
            pass
        return None
        
    
    @staticmethod
    def get_ww(present_weather, night):
        """ get weather description from value of 'present_weather' 
        
            ww is not required, so it is None.
            
            returns: (ww,german_text,english_text,severity,belchertown_icon,dwd_icon,aeris_icon)
        """
        try:
            x = DWDPOIthread.WEATHER[present_weather]
        except (LookupError,TypeError):
            x = ('Wetterzustand nicht gemeldet','unknown.png','','')
        if present_weather and present_weather<5:
            # clouds only, nothing more
            night = 1 if night else 0
            idx = (0,0,1,3,4)[present_weather]
            aeris = N_ICON_LIST[idx][4] + ('n' if night==1 else '') + '.png'
            return (None,x[0],'',26,N_ICON_LIST[idx][night],N_ICON_LIST[idx][2],aeris)
        return (None,x[0],'',0,x[1],x[2],'')
        
    
    def getRecord(self):
        """ download and process POI weather data """
        url = 'https://opendata.dwd.de/weather/weather_reports/poi/'+self.location+'-BEOB.csv'
        try:
            reply = wget(url,
                     log_success=self.log_success,
                     log_failure=self.log_failure)
            reply = reply.decode('utf-8')
        except Exception as e:
            logerr("thread '%s': wget %s - %s" % (self.name,e.__class__.__name__,e))
            return
        x = []
        ii = 0;
        for ln in csv.reader(reply.splitlines(),delimiter=';'):
            if ii==0:
                # column names
                names = ln
            elif ii==1:
                # units
                units = ln
            elif ii==2:
                # german column names
                gnames = ln
            else:
                # data lines
                dt = ln[0].split('.')
                ti = ln[1].split(':')
                d = datetime.datetime(int(dt[2])+2000,int(dt[1]),int(dt[0]),int(ti[0]),int(ti[1]),0,tzinfo=datetime.timezone(datetime.timedelta(),'UTC'))
                y = dict()
                y['dateTime'] = (int(d.timestamp()),'unix_epoch','group_time')
                y['interval'] = (60,'minute','group_interval')
                for idx,val in enumerate(ln):
                    if idx==0:
                        y['date'] = (val,None,None)
                    elif idx==1:
                        y['time'] = (val,None,None)
                    else:
                        col = DWDPOIthread.OBS.get(names[idx])
                        unit = DWDPOIthread.UNIT.get(units[idx],units[idx])
                        if unit=='degree_C':
                            grp = 'group_temperature'
                        elif unit=='percent':
                            grp = 'group_percent'
                        else:
                            grp = weewx.units.obs_group_dict.get(col)
                        if col and val is not None:
                            y[col] = (DWDPOIthread.to_float(val),
                                      unit,
                                      grp)
                wwcode = DWDPOIthread.get_ww(y['presentWeather'][0],0)
                if wwcode:
                    y['icon'] = (wwcode[self.iconset],None,None)
                    y['icontitle'] = (wwcode[1],None,None)
                x.append(y)
            ii += 1
        try:
            self.lock.acquire()
            self.data = x
        finally:
            self.lock.release()


class DWDCDCthread(BaseThread):

    BASE_URL = 'https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate'
    
    OBS = {
        'STATIONS_ID':('station_id',None,None),
        'MESS_DATUM_ENDE':('MESS_DATUM_ENDE',None,None),
        'QN':('quality_level',None,None),
        # wind
        'FF_10':('windSpeed','meter_per_second','group_speed'),
        'DD_10':('windDir','degree_compass','group_direction'),
        # wind gust
        'FX_10':('windGust','meter_per_second','group_speed'),
        'DX_10':('windGustDir','degree_compass','group_direction'),
        # air temperature
        'PP_10':('pressure','hPa','group_pressure'),
        'TT_10':('outTemp','degree_C','group_temperature'),
        'TM5_10':('extraTemp1','degree_C','group_temperature'),
        'RF_10':('outHumidity','percent','group_percent'),
        'TD_10':('dewpoint','degree_C','group_temperature'),
        # precipitation
        'RWS_DAU_10':('rainDur','minute','group_deltatime'),
        'RWS_10':('rain','mm','group_rain'),
        'RWS_IND_10':('rainIndex',None,None),
        # solar
        'DS_10':('solarRad','J/cm^2','group_radiation'),
        'GS_10':('radiation','J/cm^2','group_radiation'),
        'SD_10':('sunshineDur','hour','group_deltatime'),
        'LS_10':('LS_10','J/cm^2','group_radiation')}
        
    DIRS = {
        'air':('air_temperature','10minutenwerte_TU_','_now.zip','Meta_Daten_zehn_min_tu_'),
        'wind':('wind','10minutenwerte_wind_','_now.zip','Meta_Daten_zehn_min_ff_'),
        'gust':('extreme_wind','10minutenwerte_extrema_wind_','_now.zip','Meta_Daten_zehn_min_fx_'),
        'precipitation':('precipitation','10minutenwerte_nieder_','_now.zip','Meta_Daten_zehn_min_rr_'),
        'solar':('solar','10minutenwerte_SOLAR_','_now.zip','Meta_Daten_zehn_min_sd_')}

    def __init__(self, name, location, prefix, iconset=4, observations=None, log_success=False, log_failure=True):
    
        super(DWDCDCthread,self).__init__(name='DWD-CDC-'+name, log_success=log_success, log_failure=log_failure)
        self.location = location
        self.iconset = weeutil.weeutil.to_int(iconset)
        self.lat = None
        self.lon = None
        self.alt = None
        
        self.lock = threading.Lock()
        
        self.data = []
        self.maxtime = None
        self.last_get_ts = 0
        
        if not observations:
            observations = ('air','wind','gust','precipitation')
        url = DWDCDCthread.BASE_URL+'/10_minutes/'
        self.urls = []
        for obs in observations:
            jj = DWDCDCthread.DIRS.get(obs)
            if jj:
                self.urls.append(url+jj[0]+'/now/'+jj[1]+self.location+jj[2])
                self.get_meta_data(url+jj[0]+'/meta_data/'+jj[3]+self.location+'.zip')
            else:
                logerr("thread '%s': unknown observation group %s" % (self.name,obs))

        weewx.units.obs_group_dict.setdefault(prefix+'DateTime','group_time')
        for key in DWDCDCthread.OBS:
            obs = DWDCDCthread.OBS[key]
            obstype = obs[0]
            obsgroup = obs[2]
            if obsgroup:
                weewx.units.obs_group_dict.setdefault(prefix+obstype[0].upper()+obstype[1:],obsgroup)
        weewx.units.obs_group_dict.setdefault(prefix+'Barometer','group_pressure')
        weewx.units.obs_group_dict.setdefault(prefix+'Altimeter','group_pressure')
        weewx.units.obs_group_dict.setdefault(prefix+'Altitude','group_altitude')


    def get_data(self, ts):
        """ get buffered data  """
        try:
            self.lock.acquire()
            """
            try:
                last_ts = self.data[-1]['time']
                interval = last_ts - self.last_get_ts
                self.last_get_ts = last_ts
            except (LookupError,TypeError,ValueError,ArithmeticError):
                interval = None
            """
            interval = 10
            data = self.data
            maxtime = self.maxtime
            #print('CDC',data)
        finally:
            self.lock.release()
        #loginf("get_data interval %s data %s" % (interval,data))
        return data,interval,maxtime
        

    def decodezip(self, zipdata):
        zz = zipfile.ZipFile(io.BytesIO(zipdata),'r')
        for ii in zz.namelist():
            return zz.read(ii).decode(encoding='utf-8')
        return None

        
    def decodecsv(self, csvdata):
        x = []
        first = True
        for ln in csv.reader(csvdata.splitlines(),delimiter=';'):
            if first:
                first = False
                names = ln
            else:
                y = dict()
                for idx,val in enumerate(ln):
                    nm = names[idx].strip()
                    if idx==0:
                        # station id
                        val = val.strip()
                    elif idx==1:
                        # date and time (UTC)
                        d = datetime.datetime(int(val[0:4]),int(val[4:6]),int(val[6:8]),int(val[8:10]),int(val[10:12]),0,tzinfo=datetime.timezone(datetime.timedelta(),'UTC'))
                        y['dateTime'] = (int(d.timestamp()),'unix_epoch','group_time')
                    elif nm=='QN':
                        val = int(val)
                    else:
                        # data columns
                        try:
                            val = float(val)
                            if val==-999.0: val=None
                        except (ValueError,TypeError,ArithmeticError):
                            pass
                    if val!='eor':
                        col = DWDCDCthread.OBS.get(nm,(nm,None,None))
                        if col[1]=='J/cm^2' and col[2]=='group_radiation':
                            # energy during the last 10 minutes
                            # As WeeWX uses power rather than energy, the
                            # reading must be converted.
                            if val is not None:
                                val *= 16.6666666666666666666666666
                            col = (col[0],'watt_per_meter_squared',col[2])
                        y[col[0]] = (val,col[1],col[2])
                if 'windDir' in y:
                    y['windDir10'] = y['windDir']
                if 'windSpeed' in y:
                    y['windSpeed10'] = y['windSpeed']
                if 'pressure' in y and 'altimeter' not in y and self.alt is not None:
                    try:
                        y['altimeter'] = (weewx.wxformulas.altimeter_pressure_Metric(y['pressure'][0],self.alt),'hPa','group_pressure')
                    except Exception as e:
                        logerr("thread '%s': altimeter %s" % (self.name,e))
                if 'pressure' in y and 'outTemp' in y and 'barometer' not in y and self.alt is not None:
                    try:
                        y['barometer'] = (weewx.wxformulas.sealevel_pressure_Metric(y['pressure'][0],self.alt,y['outTemp'][0]),'hPa','group_pressure')
                    except Exception as e:
                        logerr("thread '%s': barometer %s" % (self.name,e))
                if 'pressure' in y and 'outTemp' in y and 'outHumidity' in y and self.alt is not None and 'barometerDWD' not in y:
                    try:
                        y['barometerDWD'] = (barometer_DWD(y['pressure'][0],y['outTemp'][0],y['outHumidity'][0],self.alt),'hPa','group_pressure')
                    except Exception as e:
                        logerr("thread '%s': barometerDWD %s" % (self.name,e))
                x.append(y)
        return x

    
    def get_meta_data(self, url):
        try:
            func = 'wget'
            reply = wget(url,log_success=self.log_success,log_failure=self.log_failure)
            func = 'decodezip'
            zz = zipfile.ZipFile(io.BytesIO(reply),'r')
            func = 'decodecsv'
            for ii in zz.namelist():
                if ii[0:20]=='Metadaten_Geographie':
                    txt = zz.read(ii).decode(encoding='utf-8')
                    x = []
                    for ln in csv.reader(txt.splitlines(),delimiter=';'):
                        x.append(ln)
                    if x:
                        self.alt = float(x[-1][1])
                        self.lat = float(x[-1][2])
                        self.lon = float(x[-1][3])
                        loginf("thread '%s': id %s, name '%s', lat %.4f°, lon %.4f°, alt %.1f m" % (
                                self.name,
                                x[-1][0],x[-1][6],
                                self.lat,self.lon,self.alt))

        except Exception as e:
            logerr("thread '%s': %s %s %s" % (self.name,func,e.__class__.__name__,e))
    
    
    def getRecord(self):
        x = None
        ti = None
        maxtime = None
        with requests.Session() as session:
          for url in self.urls:
            try:
                # download data in ZIP format from DWD's server
                func = 'wget'
                reply = wget(url,log_success=self.log_success,log_failure=self.log_failure,session=session)
                if not reply: raise TypeError('no data')
                # extract data file out of the downloaded ZIP file
                func = 'decodezip'
                txt = self.decodezip(reply)
                if not txt: raise FileNotFoundError('no file inside ZIP')
                # convert CSV data to Python array
                func = 'decodecsv'
                tab = self.decodecsv(txt)
                # process data
                if x:
                    func = 'other table'
                    tabti = []
                    errti = []
                    for ii in tab:
                        if ii['dateTime'] in ti:
                            # timestamp is already present
                            x[ti[ii['dateTime']]].update(ii)
                            tabti.append(ii['dateTime'])
                        elif ii['dateTime'][0]>x[-1]['dateTime'][0]:
                            # timestamp is after the last timestamp in list
                            ti[ii['dateTime']] = len(x)
                            x.append(ii)
                            tabti.append(ii['dateTime'])
                        else:
                            # timestamp is out of range
                            errti.append(ii['dateTime'][0])
                    # maximum timestamp for which there are all kinds
                    # of records available
                    # tabti may be empty if all the records in the file are
                    # out of date. Then the file is ignored entirely.
                    if tabti:
                        if tabti[-1][0]<maxtime[0] or tabti[0][0]>maxtime[0]:
                            maxtime = tabti[-1]
                    # timestamps that are not processed
                    if errti:
                        if len(errti)==1:
                            errti_str = ' %s (%s)' % (errti[0],time.strftime('%Y-%m-%dT%H:%M',time.localtime(errti[0])))
                        else:
                            errti_str = 's %s (%s) to %s (%s)' % (min(errti),time.strftime('%Y-%m-%dT%H:%M',time.localtime(min(errti))),max(errti),time.strftime('%Y-%m-%dT%H:%M',time.localtime(max(errti))))
                        logerr("thread '%s': missing timestamp%s in %s, required for %s" % (self.name,errti_str,self.urls[0],url))
                else:
                    func = 'first table'
                    x = tab
                    ti = {vv['dateTime']:ii for ii,vv in enumerate(tab)}
                    maxtime = tab[-1]['dateTime']
            except Exception as e:
                logerr("thread '%s': %s %s %s traceback %s" % (self.name,func,e.__class__.__name__,e,gettraceback(e)))
        if x:
            for idx,_ in enumerate(x):
                x[idx]['interval'] = (10,'minute','group_interval')
                if self.lat is not None:
                    x[idx]['latitude'] = (self.lat,'degree_compass','group_coordinate')
                if self.lon is not None:
                    x[idx]['longitude'] = (self.lon,'degree_compass','group_coordinate')
                if self.alt:
                    x[idx]['altitude'] = (self.alt,'meter','group_altitude')
        #print(x[ti[maxtime]])
        try:
            self.lock.acquire()
            self.data = x
            self.maxtime = ti[maxtime] if (ti and maxtime) else None
        finally:
            self.lock.release()


class ZAMGthread(BaseThread):

    # https://dataset.api.hub.zamg.ac.at/v1/station/historical/klima-v1-10min/metadata
    # https://dataset.api.hub.zamg.ac.at/v1/docs/quickstart.html
    # https://dataset.api.hub.zamg.ac.at/v1/docs/daten.html
    
    # Meßnetz:
    # https://www.zamg.ac.at/cms/de/dokumente/klima/dok_messnetze/Stationsliste_20230101.pdf
    
    BASE_URL = 'https://dataset.api.hub.zamg.ac.at'
    
    # /v1/{grid,timeseries,station}/{historical,current,forecast}/{resource_id}/
    #
    # Nicht alle Kombinationen funktionieren. Die Möglichkeiten können wie
    # folgt abgefragt werden:
    #
    # https://dataset.api.hub.zamg.ac.at/v1/datasets?type={grid,timeseries,station}&mode={historical,current,forecast}
    
    RESOURCE_ID = (
        "inca-v1-1h-1km", # INCA stündlich
        "klima-v1-1d",    # Meßstationen Tagesdaten
        "klima-v1-10min", # Meßstationen Zehnminutendaten
        "klima-v1-1m",    # Meßstationen Monatsdaten
        "tawes-v1-10min", # Tawes Meßstationen
        "synop-v1-1h"     # Synopdaten
    )
    
    OBS = {
        'DD':('windDir','degree_compass','group_direction'),
        'DDX':('windGustDir','degree_compass','group_direction'),
        'FFAM':('windSpeed','meter_per_second','group_speed'),
        'FFX':('windGust','meter_per_second','group_speed'),
        'GLOW':('radiation','watt_per_meter_squared','group_radiation'),
        'P':('pressure','hPa','group_pressure'),
        'PRED':('pred','hPa','group_pressure'), # altimeter or barometer?
        'RFAM':('humidity','percent','group_humidity'),
        'SCHNEE':('snowDepth','cm','group_distance'),
        'S0':('sunshineDur','second','group_deltatime'),
        'TL':('outTemp','degree_C','group_temperature'),
        'TP':('dewpoint','degree_C','group_temperature'),
        'TS':('extraTemp1','degree_C','group_temperature'),
        'RR':('rain','mm','group_rain')
    }
    
    UNIT = {
        '°':'degree_compass',
        '°C':'degree_C',
        'm/s':'meter_per_second',
        'mm':'mm',
        'cm':'cm',
        'W/m²':'watt_per_meter_squared',
        'hPa':'hPa',
        'min':'minute',
        'sec':'second',
    }
    
    DIRS = {
        'air':['TL','TS','P','PRED','RFAM'],
        'wind':['DD','FFAM'],
        'gust':['DDX','FFX'],
        'precipitation':['RR'],
        'solar':['GLOW']
    }
    
    def __init__(self, name, location, prefix, iconset=4, observations=None, user='', passwd='', log_success=False, log_failure=True):
    
        super(ZAMGthread,self).__init__(name='ZAMG-'+name, log_success=log_success, log_failure=log_failure)
        self.location = location
        self.iconset = weeutil.weeutil.to_int(iconset)
        self.lat = None
        self.lon = None
        self.alt = None
        
        self.lock = threading.Lock()
        
        self.data = dict()
        
        datasets = self.get_datasets('station','current')
        if datasets:
            self.current_url = datasets[0]['url']
        else:
            self.current_url = None
        self.get_meta_data()
        
        if not observations:
            observations = ('air','wind','gust','precipitation')
        self.observations = []
        for observation in observations:
            if observation in ZAMGthread.OBS:
                jj = [observation]
            else:
                jj = ZAMGthread.DIRS.get(observation)
            self.observations.extend(jj)
        
        weewx.units.obs_group_dict.setdefault(prefix+'DateTime','group_time')
        for key in ZAMGthread.OBS:
            obs = ZAMGthread.OBS[key]
            obstype = obs[0]
            obsgroup = obs[2]
            if obsgroup:
                weewx.units.obs_group_dict.setdefault(prefix+obstype[0].upper()+obstype[1:],obsgroup)
        weewx.units.obs_group_dict.setdefault(prefix+'Barometer','group_pressure')
        weewx.units.obs_group_dict.setdefault(prefix+'Altimeter','group_pressure')
        weewx.units.obs_group_dict.setdefault(prefix+'Altitude','group_altitude')


    def get_data(self, ts):
        try:
            self.lock.acquire()
            x = self.data
        finally:
            self.lock.release()
        return x,1


    def get_datasets(self, type, mode):
        """ get which datasets are available
        
            type: 'grid', 'timeseries', 'station'
            mode: 'historical', 'current', 'forecast'
        """
        url = ZAMGthread.BASE_URL+'/v1/datasets?type='+type+'&mode='+mode
        reply = wget(url,log_success=self.log_success,log_failure=self.log_failure)
        x = []
        if reply:
            reply = json.loads(reply)
            # Example:
            # {
            #   "/station/current/tawes-v1-10min": {    <-- resource_id
            #     "type": "station",
            #     "mode": "current",
            #     "response_formats": [
            #       "geojson",
            #       "csv"
            #     ],
            #     "url": "https://dataset.api.hub.zamg.ac.at/v1/station/current/tawes-v1-10min"
            #   }
            # }
            for resource_id in reply:
                x.append({
                    'resource_id': resource_id,
                    'url': reply[resource_id]['url']
                })
        return x

        
    def get_meta_data(self):
        url = self.current_url+'/metadata?station_ids=%s' % self.location
        reply = wget(url)
        if reply:
            reply = json.loads(reply)
            stations = reply['stations']
            for station in stations:
                if station['id']==self.location:
                    self.lat = float(station['lat'])
                    self.lon = float(station['lon'])
                    self.alt = float(station['altitude'])
                    self.locationName = station['name']
                    self.locationState = station['state']
                    loginf("thread '%s': id %s, name '%s', lat %.4f°, lon %.4f°, alt %.1f m" % (
                                self.name,
                                station['id'],station['name'],
                                self.lat,self.lon,self.alt))
                    break
    
    
    def getRecord(self):
        url = self.current_url+'?parameters=%s&station_ids=%s&output_format=geojson' % (','.join(self.observations),self.location)
        try:
            reply = wget(url, log_success=self.log_success, log_failure=self.log_failure)
            if reply:
                reply = json.loads(reply)
                x = dict()
                ts = reply['timestamps'][-1].split('T')
                dt = ts[0].split('-')
                ts = ts[1].split('+')
                ti = ts[0].split(':')
                d = datetime.datetime(int(dt[0]),int(dt[1]),int(dt[2]),int(ti[0]),int(ti[1]),0,tzinfo=datetime.timezone(datetime.timedelta(),'UTC'))
                x['dateTime'] = (int(d.timestamp()),'unix_epoch','group_time')
                observations = reply['features'][0]['properties']['parameters']
                for observation in observations:
                    try:
                        name = observations[observation]['name']
                        unit = observations[observation]['unit']
                        unit = ZAMGthread.UNIT.get(unit,unit)
                        val = float(observations[observation]['data'][-1])
                        obs = ZAMGthread.OBS.get(observation)
                        obstype = obs[0]
                        obsgroup = obs[2]
                        x[obstype] = (val,unit,obsgroup)
                    except Exception as e:
                        if self.log_failure:
                            logerr("thread '%s': %s %s" % (self.name,observation,e))
                if 'pressure' in x and 'altimeter' not in x and self.alt is not None:
                    try:
                        x['altimeter'] = (weewx.wxformulas.altimeter_pressure_Metric(x['pressure'][0],self.alt),'hPa','group_pressure')
                    except Exception as e:
                        logerr("thread '%s': altimeter %s" % (self.name,e))
                if 'pressure' in x and 'outTemp' in x and 'barometer' not in x and self.alt is not None:
                    try:
                        x['barometer'] = (weewx.wxformulas.sealevel_pressure_Metric(x['pressure'][0],self.alt,x['outTemp'][0]),'hPa','group_pressure')
                    except Exception as e:
                        logerr("thread '%s': barometer %s" % (self.name,e))
                if x:
                    x['interval'] = (10,'minute','group_interval')
                    if self.lat is not None:
                        x['latitude'] = (self.lat,'degree_compass','group_coordinate')
                    if self.lon is not None:
                        x['longitude'] = (self.lon,'degree_compass','group_coordinate')
                    if self.alt:
                        x['altitude'] = (self.alt,'meter','group_altitude')
                try:
                    self.lock.acquire()
                    self.data = x
                finally:
                    self.lock.release()
        except Exception as e:
            if self.log_failure:
                logerr("thread '%s': %s" % (self.name,e))





class DWDOPENMETEOthread(BaseThread):

    # Evapotranspiration/UV-Index: 
    # Attention, no capital letters for WeeWX fields. Otherwise the WeeWX field "ET"/"UV" will be formed if no prefix is used!
    # Mapping API field -> WeeWX field
    HOURLYOBS = {
        'temperature_2m':'outTemp'
        ,'apparent_temperature':'appTemp'
        ,'dewpoint_2m':'dewpoint'
        ,'pressure_msl':'barometer'
        ,'relativehumidity_2m':'outHumidity'
        ,'winddirection_10m':'windDir'
        ,'windspeed_10m':'windSpeed'
        ,'windgusts_10m':'windGust'
        ,'cloudcover':'cloudcover'
        ,'evapotranspiration':'et'
        ,'rain':'rain'
        ,'showers':'shower'
        ,'snowfall':'snow'
        ,'freezinglevel_height':'freezinglevelHeight'
        ,'weathercode':'weathercode'
        ,'snow_depth':'snowDepth'
        ,'direct_radiation_instant':'radiation'
        # Europe only
        ,'snowfall_height':'snowfallHeight'
    }

    # Mapping API field -> WeeWX field
    CURRENTOBS = {
        'temperature':'outTemp'
        ,'windspeed':'windSpeed'
        ,'winddirection':'windDir'
        ,'weathercode':'weathercode'
    }

    # API result contain no units for current_weather
    # Mapping API current_weather unit -> WeeWX unit
    CURRENTUNIT = {
        'temperature':'°C'
        ,'windspeed':'km/h'
        ,'winddirection':'°'
        ,'weathercode':'wmo code'
        ,'time':'unixtime'
    }

    # Mapping API hourly unit -> WeeWX unit
    UNIT = {
        '°':'degree_compass'
        ,'°C':'degree_C'
        ,'mm':'mm'
        ,'cm':'cm'
        ,'m':'meter'
        ,'hPa':'hPa'
        ,'kPa':'kPa'
        ,'W/m²':'watt_per_meter_squared'
        ,'km/h':'kilometer_per_hour'
        ,'%':'percent'
        ,'wmo code':'count'
        ,'unixtime':'unix_epoch'
    }

    # https://open-meteo.com/en/docs/dwd-api
    # WMO Weather interpretation codes (WW)
    # Code        Description
    # 0           Clear sky
    # 1, 2, 3     Mainly clear, partly cloudy, and overcast
    # 45, 48      Fog and depositing rime fog
    # 51, 53, 55  Drizzle: Light, moderate, and dense intensity
    # 56, 57      Freezing Drizzle: Light and dense intensity
    # 61, 63, 65  Rain: Slight, moderate and heavy intensity
    # 66, 67      Freezing Rain: Light and heavy intensity
    # 71, 73, 75  Snow fall: Slight, moderate, and heavy intensity
    # 77          Snow grains
    # 80, 81, 82  Rain showers: Slight, moderate, and violent
    # 85, 86      Snow showers slight and heavy
    # 95 *        Thunderstorm: Slight or moderate
    # 96, 99 *    Thunderstorm with slight and heavy hail
    # (*) Thunderstorm forecast with hail is only available in Central Europe

    # TODO Structure?
    #              0       1      2     3          4              5          6
    # WMO Key: [german, english, None, None, Belchertown Icon, DWD Icon, Aeris Icon]
    WEATHER = {
        -1:['unbekannte Wetterbedingungen', 'unknown conditions', '', '', 'unknown.png', 'unknown.png', 'na']
        # 0-3 using N_ICON_LIST, here only Documentation
        ,0:['wolkenlos', 'clear sky', '', '', 'clear-day.png', '0-8.png', 'clear']
        ,1:['heiter', 'mainly clear', '', '','mostly-clear-day.png', '2-8.png', 'fair']
        ,2:['bewölkt', 'partly cloudy', '', '','mostly-cloudy-day.png', '5-8.png', 'pcloudy']
        ,3:['bedeckt', 'overcast', '', '','cloudy.png', '8-8.png', 'cloudy']
        # from here on we evaluate
        ,45:['Nebel', 'fog', '', '','fog.png', '40.png', 'fog']
        ,48:['gefrierender Nebel', 'depositing rime fog', '', '','fog.png', '48.png', '']
        ,51:['leichter Nieselregen', 'light drizzle', '', '','rain.png', '7.png', 'drizzle']
        ,53:['Nieselregen', 'moderate drizzle', '', '','rain.png', '8.png', 'drizzle']
        ,55:['starker Nieselregen', 'dense drizzle', '', '','rain.png', '9.png', 'drizzle']
        ,56:['gefrierender Nieselregen', 'light freezing drizzle', '', '','sleet.png', '66.png', 'freezingrain']
        ,57:['kräftiger gefrierender Nieselregen', 'dense freezing drizzle', '', '','sleet.png', '67.png', 'freezingrain']
        ,61:['leichter Regen', 'slight rain', '', '','rain.png', '7.png', 'rain']
        ,63:['Regen', 'moderate rain', '', '','rain.png', '8.png', 'rain']
        ,65:['starker Regen', 'heavy rain', '', '','rain.png', '9.png', 'rain']
        ,66:['gefrierender Regen', 'light freezing rain', '', '','sleet.png', '66.png', 'freezingrain']
        ,67:['starker gefrierender Regen', 'heavy freezing rain', '', '','sleet.png', '67.png', 'freezingrain']
        ,71:['leichter Schneefall', 'slight snow fall', '', '','snow.png', '14.png', 'snow']
        ,73:['Schneefall', 'moderate snow fall', '', '','snow.png', '15.png', 'snow']
        ,75:['starker Schneefall', 'heavy snow fall', '', '','snow.png', '16.png', 'snow']
        ,77:['Eiskörner', 'snow grains' , '', '','snow.png', '17.png', 'sleet']
        ,80:['leichter Regenschauer', 'slight rain showers', '', '','rain.png', '80.png', 'showers']
        ,81:['Regenschauer', 'moderate rain showers', '', '','rain.png', '80.png', 'showers']
        ,82:['starker Regenschauer', 'heavy rain showers', '', '','rain.png', '82.png', 'showers']
        ,85:['Schneeregen', 'slight snow showers', '', '','sleet.png', '12.png', 'rainandsnow']
        ,86:['starker Schneeregen', 'heavy snow showers', '', '', 'sleet.png', '13.png', 'rainandsnow']
        ,95:['Gewitter', 'thunderstorm', '', '', 'thunderstorm.png', '27.png', 'tstorm']
        ,96:['Gewitter mit Hagel', 'thunderstorm with slight hail', '', '', 'thunderstorm.png', '29.png', 'tstorm']
        ,99:['starkes Gewitter mit Hagel', 'thunderstorm with slight hail', '', '', 'thunderstrom.png', '30.png', 'tstorm']
    }
    
    def __init__(self, name, openmeteo_dict, log_success=False, log_failure=True):
    
        super(DWDOPENMETEOthread,self).__init__(name='OPENMETEO-'+name)

        self.log_success = log_success
        self.log_failure = log_failure
        self.debug = weeutil.weeutil.to_int(openmeteo_dict.get('debug', 0))
        self.latitude = weeutil.weeutil.to_float(openmeteo_dict.get('latitude'))
        self.longitude = weeutil.weeutil.to_float(openmeteo_dict.get('longitude'))
        self.altitude = weeutil.weeutil.to_float(openmeteo_dict.get('altitude'))

        self.iconset = weeutil.weeutil.to_int(openmeteo_dict.get('iconset', 4))
        self.prefix = openmeteo_dict.get('prefix','')
        self.model = openmeteo_dict.get('model','dwd-icon')

        self.lock = threading.Lock()
        
        self.data = []
        self.last_get_ts = 0
        
        for opsapi, obsweewx in DWDOPENMETEOthread.CURRENTOBS.items():
            obsgroup = None
            if obsweewx=='weathercode':
                obsgroup = 'group_count'
            else:
                obsgroup = weewx.units.obs_group_dict.get(obsweewx)
            if obsgroup is not None:
                weewx.units.obs_group_dict.setdefault(self.prefix+obsweewx[0].upper()+obsweewx[1:],obsgroup)

        for opsapi, obsweewx in DWDOPENMETEOthread.HOURLYOBS.items():
            if obsweewx=='weathercode':
                # filled with CURRENTOBS
                continue
            obsgroup = None
            if obsweewx=='shower':
                obsgroup = 'group_rain'
            elif obsweewx=='freezinglevelHeight':
                obsgroup = 'group_altitude'
            elif obsweewx=='snowfallHeight':
                obsgroup = 'group_altitude'
            else:
                obsgroup = weewx.units.obs_group_dict.get(obsweewx)
            if obsgroup is not None:
                weewx.units.obs_group_dict.setdefault(self.prefix+obsweewx[0].upper()+obsweewx[1:],obsgroup)

    def shutDown(self):
        """ request thread shutdown """
        self.running = False
        self.evt.set()
        if self.debug > 0:
            logdbg("thread '%s': shutdown requested" % self.name)

    def get_data(self, ts):
        """ get buffered data """
        try:
            self.lock.acquire()
            """
            try:
                last_ts = self.data[-1]['time']
                interval = last_ts - self.last_get_ts
                self.last_get_ts = last_ts
            except (LookupError,TypeError,ValueError,ArithmeticError):
                interval = None
            """
            interval = 1
            data = self.data
            #print('POI',data)
        finally:
            self.lock.release()
        #loginf("get_data interval %s data %s" % (interval,data))
        return data,interval

    @staticmethod
    def get_ww(wwcode, night):
        """ get weather description from value of 'wwcode' 
            returns: (german_text,english_text,'','',belchertown_icon,dwd_icon,aeris_icon)
        """
        try:
            x = DWDOPENMETEOthread.WEATHER[wwcode]
        except (LookupError,TypeError):
            # fallback
            x = DWDOPENMETEOthread.WEATHER[-1]
        if wwcode < 4:
            # clouds only, nothing more
            night = 1 if night else 0
            idx = (0,1,2,4)[wwcode]
            aeris = N_ICON_LIST[idx][4] + ('n' if night==1 else '') + '.png'
            return (x[0],x[1],'','',N_ICON_LIST[idx][night],N_ICON_LIST[idx][2],aeris)
        return x

    def getRecord(self):
        """ download and process POI weather data """

        # DWD API endpoint "v1/dwd-icon"
        baseurl = 'https://api.open-meteo.com/v1/'+self.model

        # Geographical WGS84 coordinate of the location
        params = '?latitude=%s' % self.latitude
        params += '&longitude=%s' % self.longitude

        # The elevation used for statistical downscaling. Per default, a 90 meter digital elevation model is used.
        # You can manually set the elevation to correctly match mountain peaks. If &elevation=nan is specified,
        # downscaling will be disabled and the API uses the average grid-cell height.
        # If a valid height exists, it will be used
        if self.altitude is not None:
            params += '&elevation=%s' % self.altitude

        # timeformat iso8601 | unixtime
        params += '&timeformat=unixtime'

        # timezone
        # If timezone is set, all timestamps are returned as local-time and data is returned starting at 00:00 local-time.
        # Any time zone name from the time zone database is supported. If auto is set as a time zone, the coordinates will
        # be automatically resolved to the local time zone.
        # using API default
        #params += '&timezone=Europe%2FBerlin'

        # TODO config param?
        # cell_selection, land | sea | nearest
        # Set a preference how grid-cells are selected. The default land finds a suitable grid-cell on land with similar
        # elevation to the requested coordinates using a 90-meter digital elevation model. sea prefers grid-cells on sea.
        # nearest selects the nearest possible grid-cell.
        #params += '&cell_selection=land'

        # TODO use "past_days=1" instead of yesterday?
        # The time interval to get weather data. A day must be specified as an ISO8601 date (e.g. 2022-06-30).
        yesterday = datetime.datetime.now() - datetime.timedelta(1)
        yesterday = datetime.datetime.strftime(yesterday, '%Y-%m-%d')
        today = datetime.datetime.today().strftime('%Y-%m-%d')
        params += '&start_date=%s' % str(yesterday)
        params += '&end_date=%s' % str(today)

        # units
        # The API request is made in the metric system
        # Temperature in celsius
        params += '&temperature_unit=celsius'
        # Wind in km/h
        params += '&windspeed_unit=kmh'
        # Precipitation in mm
        params += '&precipitation_unit=mm'

        # Include current weather conditions in the JSON output.
        # currently contained values (28.01.2023): temperature, windspeed, winddirection, weathercode, time
        params += '&current_weather=true'

        # A list of weather variables which should be returned. Values can be comma separated,
        # or multiple &hourly= parameter in the URL can be used.
        # defined in HOURLYOBS
        params += '&hourly='+','.join([ii for ii in DWDOPENMETEOthread.HOURLYOBS])
        """
        first = True
        for obsapi in DWDOPENMETEOthread.HOURLYOBS:
            if first:
                params += obsapi
                first = False
            else:
                params += "," + obsapi
        """

        url = baseurl + params

        if self.debug > 0:
            logdbg("thread '%s': URL=%s" % (self.name, url))

        apidata = {}
        try:
            reply = wget(url,
                     log_success=(self.log_success or self.debug > 0),
                     log_failure=(self.log_failure or self.debug > 0))
            if reply is not None:
                apidata = json.loads(reply.decode('utf-8'))
            else:
                if self.log_failure or self.debug > 0:
                    logerr("thread '%s': Open-Meteo returns None data." % self.name)
                return
        except Exception as e:
            if self.log_failure or self.debug > 0:
                logerr("thread '%s': Open-Meteo %s - %s" % (self.name, e.__class__.__name__, e))
            return

        # check results
        if apidata.get('hourly') is None:
            if self.log_failure or self.debug > 0:
                logerr("thread '%s': Open-Meteo returns no hourly data." % self.name)
            return

        hourly_units = apidata.get('hourly_units')
        if hourly_units is None:
            if self.log_failure or self.debug > 0:
                logerr("thread '%s': Open-Meteo returns no hourly_units data." % self.name)
            return

        current_weather = apidata.get('current_weather')
        if current_weather is None:
            if self.log_failure or self.debug > 0:
                logerr("thread '%s': Open-Meteo returns no current_weather data." % self.name)
            return

        timelist = apidata['hourly'].get('time')
        if timelist is None:
            if self.log_failure or self.debug > 0:
                logerr("thread '%s': Open-Meteo returns no time periods data." % self.name)
            return

        if not isinstance(timelist, list):
            if self.log_failure or self.debug > 0:
                logerr("thread '%s': Open-Meteo returns time periods data not as list." % self.name)
            return

        if len(timelist) == 0:
            if self.log_failure or self.debug > 0:
                logerr("thread '%s': Open-Meteo returns time periods without data." % self.name)
            return
            
        latitude = apidata.get('latitude')
        longitude = apidata.get('longitude')
        altitude = apidata.get('elevation')

        # holds the return values
        x = []
        y = dict()

        # get the last hourly observation timestamp before the current time
        actts = weeutil.weeutil.to_int(time.time())
        obshts = None
        for ts in timelist:
            if ts > actts:
                break
            obshts = weeutil.weeutil.to_int(ts)
        if obshts is None:
            if self.log_failure or self.debug > 0:
                logerr("thread '%s': Open-Meteo returns timestamps only in the future." % self.name)
            return

        if self.debug >= 3:
            logdbg("thread '%s': API result: %s" % (self.name, str(apidata)))
            logdbg("thread '%s':    ts now=%s" % (self.name, str(actts)))
            logdbg("thread '%s':    ts now=%s" % (self.name, str( datetime.datetime.fromtimestamp(actts).strftime('%Y-%m-%d %H:%M:%S'))))
            logdbg("thread '%s': ts hourly=%s" % (self.name, str(obshts)))
            logdbg("thread '%s': ts hourly=%s" % (self.name, str( datetime.datetime.fromtimestamp(obshts).strftime('%Y-%m-%d %H:%M:%S'))))
            logdbg("thread '%s': lat %s lon %s alt %s" % (self.name,latitude,longitude,altitude))

        # timestamp current_weather
        obscts = int(current_weather.get('time', 0))

        # final timestamp
        obsts = weeutil.weeutil.to_int(max(obscts, obshts))

        y['dateTime'] = (obsts, 'unix_epoch', 'group_time')
        y['interval'] = (60, 'minute', 'group_interval')

        #get current weather data
        for obsapi, obsweewx in DWDOPENMETEOthread.CURRENTOBS.items():
            obsname = self.prefix+obsweewx[0].upper()+obsweewx[1:]
            if self.debug >= 2:
                logdbg("thread '%s': weewx=%s api=%s obs=%s" % (self.name, str(obsweewx), str(obsapi), str(obsname)))
            obsval = current_weather.get(obsapi)
            if obsval is None:
                if self.log_failure or self.debug > 0:
                    logerr("thread '%s': Open-Meteo returns no value for observation %s - %s on timestamp %s" % (self.name, str(obsapi), str(obsname), str(obscts)))
                continue
            # API json response contain no unit data for current_weather observations
            unitapi = DWDOPENMETEOthread.CURRENTUNIT.get(obsapi)
            if unitapi is None:
                if self.log_failure or self.debug > 0:
                    logerr("thread '%s': Open-Meteo returns no unit for observation %s - %s" % (self.name, str(obsapi), str(obsname)))
                continue
            unitweewx = DWDOPENMETEOthread.UNIT.get(unitapi)
            if unitweewx is None:
                if self.log_failure or self.debug > 0:
                    logerr("thread '%s': could not convert api unit '%s' to weewx unit" % (self.name, str(unitapi)))
                continue
            groupweewx = weewx.units.obs_group_dict.get(obsname)
            y[obsweewx] = (weeutil.weeutil.to_float(obsval), unitweewx, groupweewx)
            if self.debug >= 2:
                logdbg("thread '%s': weewx=%s result=%s" % (self.name, str(obsweewx), str(y[obsweewx])))

        if self.debug >= 2:
            logdbg("thread '%s': current weather data=%s" % (self.name, str(y)))

        # get hourly weather data
        for obsapi, obsweewx in DWDOPENMETEOthread.HOURLYOBS.items():
            obsname = self.prefix+obsweewx[0].upper()+obsweewx[1:]
            if y.get(obsweewx) is not None:
                # filled with current_weather data
                continue
            if self.debug >= 2:
                logdbg("thread '%s': weewx=%s api=%s obs=%s" % (self.name, str(obsweewx), str(obsapi), str(obsname)))
            obslist = apidata['hourly'].get(obsapi)
            if obslist is None:
                if self.log_failure or self.debug > 0:
                    logerr("thread '%s': Open-Meteo returns no value for observation '%s' - '%s'" % (self.name, str(obsapi), str(obsname)))
                continue
            # Build a dictionary with timestamps as key and the corresponding values
            obsvals = dict(zip(timelist, obslist))
            obsval = obsvals.get(obshts)
            if obsval is None:
                # snowfall_height could be None, value is not always available
                if obsapi == 'snowfall_height':
                    if self.debug > 0:
                        # what is better, loginf or logdbg?
                        logdbg("thread '%s': Open-Meteo returns no value for observation %s - %s on timestamp %s" % (self.name, str(obsapi), str(obsname), str(obshts)))
                elif self.log_failure or self.debug > 0:
                    logerr("thread '%s': Open-Meteo returns no value for observation %s - %s on timestamp %s" % (self.name, str(obsapi), str(obsname), str(obshts)))
                continue
            unitapi = hourly_units.get(obsapi)
            if unitapi is None:
                if self.log_failure or self.debug > 0:
                    logerr("thread '%s': Open-Meteo returns no unit for observation %s - %s" % (self.name, str(obsapi), str(obsname)))
                continue
            unitweewx = DWDOPENMETEOthread.UNIT.get(unitapi)
            if unitweewx is None:
                if self.log_failure or self.debug > 0:
                    logerr("thread '%s': could not convert api unit '%s' to weewx unit" % (self.name, str(unitapi)))
                continue
            groupweewx = weewx.units.obs_group_dict.get(obsname)
            # snowDepth from meter to mm, weewx snowDepth is weewx group_rain
            if obsweewx == 'snowDepth':
                obsval = (weeutil.weeutil.to_float(obsval) * 1000)
                unitweewx = 'mm'
            y[obsweewx] = (weeutil.weeutil.to_float(obsval), unitweewx, groupweewx)
            if self.debug >= 2:
                logdbg("thread '%s': weewx=%s result=%s" % (self.name, str(obsweewx), str(y[obsweewx])))

        wwcode = y.get('weathercode')
        if wwcode is not None:
            wwcode = int(wwcode[0])
        else:
            wwcode = -1
        logdbg("thread '%s': wwcode=%s" % (self.name, str(wwcode)))
        wwcode = DWDOPENMETEOthread.get_ww(wwcode, 0)
        logdbg("thread '%s': wwcode=%s" % (self.name, str(wwcode)))
        if wwcode:
            y['icon'] = (wwcode[self.iconset],None,None)
            y['icontitle'] = (wwcode[0],None,None)
        
        if latitude is not None and longitude is not None:
            y['latitude'] = (latitude,'degree_compass','group_coordinate')
            y['longitude'] = (longitude,'degree_compass','group_coordinate')
        if altitude is not None:
            y['altitude'] = (altitude,'meter','group_altitude')

        x.append(y)

        if self.debug >= 3:
            logdbg("thread '%s': result=%s" % (self.name, str(x)))

        try:
            self.lock.acquire()
            self.data = x
        finally:
            self.lock.release()


class DWDservice(StdService):

    def __init__(self, engine, conf_dict):
        super(DWDservice,self).__init__(engine, conf_dict)
        
        if 'WeatherServices' in conf_dict:
            if 'include' in conf_dict['WeatherServices']:
                dire = os.path.dirname(conf_dict.get('config_path','/'))
                include_dict = configobj.ConfigObj(os.path.join(dire,conf_dict['WeatherServices']['include']))
                config_dict = weeutil.config.deep_copy(conf_dict)
                weeutil.config.merge_config(config_dict['WeatherServices'],include_dict)
            else:
                config_dict = conf_dict
            site_dict = weeutil.config.accumulateLeaves(config_dict.get('WeatherServices',configobj.ConfigObj()))
        else:
            config_dict = conf_dict
            site_dict = weeutil.config.accumulateLeaves(config_dict.get('DeutscherWetterdienst',configobj.ConfigObj()))
        self.log_success = weeutil.weeutil.to_bool(site_dict.get('log_success',True))
        self.log_failure = weeutil.weeutil.to_bool(site_dict.get('log_failure',True))
        self.debug = weeutil.weeutil.to_int(site_dict.get('debug',0))
        if self.debug>0:
            self.log_success = True
            self.log_failure = True
        archive_interval = 300 # engine.archive_interval

        self.threads = dict()
        rv_thread = None
        
        try:
            iconset = config_dict['WeatherServices']['forecast']['icon_set']
        except LookupError:
            iconset = config_dict.get('DeutscherWetterdienst',site_dict).get('forecast',site_dict).get('icon_set','belchertown').lower()
        self.iconset = 4
        if iconset=='dwd': self.iconset = 5
        if iconset=='aeris': self.iconset = 6
        
        # deprecated, use section [WeatherServices][[forecast]]
        poi_dict = config_dict.get('DeutscherWetterdienst',config_dict).get('POI',site_dict)
        stations = poi_dict.get('stations',site_dict)
        for station in stations.sections:
            station_dict = weeutil.config.accumulateLeaves(stations[station])
            station_dict['iconset'] = self.iconset
            iconset = station_dict.get('icon_set')
            if iconset is not None:
                station_dict['iconset'] = self.iconset
                if iconset=='belchertown': station_dict['iconset'] = 4
                if iconset=='dwd': station_dict['iconset'] = 5
                if iconset=='aeris': station_dict['iconset'] = 6
            self._create_poi_thread(station, station, station_dict)
            
        # deprecated, use section [WeatherServices][[forecast]]
        # https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/
        cdc_dict = config_dict.get('DeutscherWetterdienst',config_dict).get('CDC',site_dict)
        stations = cdc_dict.get('stations',site_dict)
        for station in stations.sections:
            station_dict = weeutil.config.accumulateLeaves(stations[station])
            station_dict['iconset'] = self.iconset
            iconset = station_dict.get('icon_set')
            if iconset is not None:
                station_dict['iconset'] = self.iconset
                if iconset=='belchertown': station_dict['iconset'] = 4
                if iconset=='dwd': station_dict['iconset'] = 5
                if iconset=='aeris': station_dict['iconset'] = 6
            self._create_cdc_thread(station, station, station_dict)
        
        # deprecated, use section [WeatherServices][[forecast]]
        zamg_dict = config_dict.get('ZAMG',configobj.ConfigObj()).get('current',configobj.ConfigObj())
        stations = zamg_dict.get('stations',site_dict)
        for station in stations.sections:
            station_dict = weeutil.config.accumulateLeaves(stations[station])
            station_dict['iconset'] = self.iconset
            iconset = station_dict.get('icon_set')
            if iconset is not None:
                station_dict['iconset'] = self.iconset
                if iconset=='belchertown': station_dict['iconset'] = 4
                if iconset=='dwd': station_dict['iconset'] = 5
                if iconset=='aeris': station_dict['iconset'] = 6
            self._create_zamg_thread(station, station, station_dict, zamg_dict.get('user'), zamg_dict.get('password'))
        
        # General interface
        site_dict = config_dict.get('WeatherServices',configobj.ConfigObj()).get('current',configobj.ConfigObj())
        for location in site_dict.sections:
            location_dict = weeutil.config.accumulateLeaves(site_dict[location])
            # Icon set 
            iconset = location_dict.get('icon_set', iconset)
            if iconset is not None:
                location_dict['iconset'] = self.iconset
                if iconset=='belchertown': location_dict['iconset'] = 4
                if iconset=='dwd': location_dict['iconset'] = 5
                if iconset=='aeris': location_dict['iconset'] = 6
            # Station 
            # Note: Latitude and Longitude (if needed) are already in dict()
            station = location_dict.get('station',location)
            if station.lower() in ('here','thisstation'):
                location_dict['latitude'] = engine.stn_info.latitude_f
                location_dict['longitude'] = engine.stn_info.longitude_f
                location_dict['altitude'] = weewx.units.convert(engine.stn_info.altitude_vt, 'meter')[0]
            # Provider and data model
            provider = location_dict.get('provider')
            model = location_dict.get('model')
            if model: model = model.lower()
            # enabled?
            enable = weeutil.weeutil.to_bool(location_dict.get('enable',True))
            if enable and provider:
                provider = provider.lower()
                if provider=='dwd':
                    if model=='poi':
                        self._create_poi_thread(location, station, location_dict)
                    elif model=='cdc':
                        self._create_cdc_thread(location, station, location_dict)
                    else:
                        logerr("unkown model '%s' for provider '%s'" % (model,provider))
                elif provider=='zamg':
                    self._create_zamg_thread(
                        location, 
                        station, 
                        location_dict, 
                        location_dict.get('user'), zamg_dict.get('password'))
                elif provider=='open-meteo':
                    self._create_openmeteo_thread(location, location_dict)
                else:
                    logerr("unknown weather service provider '%s'" % provider)
        
        site_dict = config_dict.get('WeatherServices',configobj.ConfigObj()).get('forecast',configobj.ConfigObj())
        for location in site_dict.sections:
            location_dict = weeutil.config.accumulateLeaves(site_dict[location])
            provider = location_dict.get('provider')
            if has_wildfire:
                if provider in user.wildfire.providers_dict:
                    try:
                        thread = user.wildfire.create_thread(location,location_dict,archive_interval)
                        if thread:
                            self.threads[location] = thread
                    except (LookupError,ValueError,TypeError,ArithmeticError) as e:
                        logerr("error creating forecast thread '%s': %s %s" % (location,e.__class__.__name__,e))
                    continue
        
        if has_radar:
            radar_dict = configobj.ConfigObj()
            weewx_root = config_dict.get('WEEWX_ROOT','')
            skin_root = config_dict.get('StdReport',configobj.ConfigObj()).get('SKIN_ROOT','')
            if skin_root:
                font_root = os.path.join(weewx_root,skin_root,'Seasons','font')
            else:
                font_root = weewx_root
            site_dict = config_dict.get('WeatherServices',configobj.ConfigObj()).get('radar',configobj.ConfigObj())
            if 'places_de1200' in site_dict:
                user.weatherservicesradar.load_places(os.path.join(weewx_root,site_dict['places_de1200']),'DE1200')
            for location in site_dict.sections:
                location_dict = weeutil.config.accumulateLeaves(config_dict['WeatherServices']['radar'][location])
                if 'place_label_font_path' in location_dict:
                    location_dict['place_label_font_path'] = os.path.join(font_root, location_dict['place_label_font_path'])
                elif font_root:
                    location_dict['place_label_font_path'] = os.path.join(font_root, 'OpenSans-Regular.ttf')
                provider = location_dict.get('provider')
                models = location_dict.get('model')
                if models and provider:
                    if not isinstance(models,list): models = [models]
                    for model in models:
                        idx = str(provider)+'_!_'+str(model)
                        if idx not in radar_dict:
                            radar_dict[idx] = self._radar_entry(provider,model,location_dict)
                        radar_dict[idx][location] = configobj.ConfigObj()
                        weeutil.config.merge_config(radar_dict[idx][location],location_dict)
                        radar_dict[idx][location]['model'] = model
            if 'DWD_!_HGRV' in radar_dict:
                if 'DWD_!_HG' not in radar_dict:
                    radar_dict['DWD_!_HG'] = self._radar_entry('DWD','HG',configobj.ConfigObj())
                if 'DWD_!_RV' not in radar_dict:
                    radar_dict['DWD_!_RV'] = self._radar_entry('DWD','RV',configobj.ConfigObj())
                q = queue.Queue(4)
            else:
                q = None
            #loginf('radar %s' % radar_dict)
            for radar in radar_dict:
                try:
                    #loginf('radar %s' % radar)
                    #loginf('radar %s' % radar_dict[radar])
                    thread_name = radar_dict[radar]['provider']+'_'+radar_dict[radar]['model']
                    thread = user.weatherservicesradar.create_thread(
                        thread_name,
                        radar_dict[radar],
                        archive_interval
                    )
                    if thread:
                        self.threads[thread_name] = thread
                        if radar_dict[radar]['provider']=='DWD':
                            if radar_dict[radar]['model'] in ('HG','RV','HGRV'):
                                thread['thread'].hgrv_queue = q
                            if radar_dict[radar]['model']=='RV':
                                rv_thread = thread['thread']
                except (LookupError,ValueError,TypeError,ArithmeticError,NameError) as e:
                    logerr("error creating radar thread '%s': %s %s" % (thread_name,e.__class__.__name__,e))
        
        if has_db:
            self.database_q, self.database_thread = databasecreatethread('DWDsave',config_dict)
        
        self.next_loop_error_ts = 0
        
        if  __name__!='__main__':
            self.bind(weewx.NEW_LOOP_PACKET, self.new_loop_packet)
            self.bind(weewx.NEW_ARCHIVE_RECORD, self.new_archive_record)
        
        # Initialization for calculating barometer according to DWD formula
        self.station_altitude = weewx.units.convert(engine.stn_info.altitude_vt, 'meter')[0]
        self.dwdxtype = DWDXType(engine.stn_info.altitude_vt, rv_thread)
        if self.dwdxtype:
            weewx.xtypes.xtypes.append(self.dwdxtype)
        weewx.units.obs_group_dict.setdefault('barometerDWD','group_pressure')
        weewx.units.obs_group_dict.setdefault('outSVPDWD','group_pressure')


    def _radar_entry(self, provider, model, location_dict):
        radar_dict = configobj.ConfigObj()
        radar_dict['provider'] = provider
        radar_dict['model'] = model
        if 'path' in location_dict:
            radar_dict['path'] = location_dict['path']
        radar_dict['log_success'] = location_dict.get('log_success',False)
        radar_dict['log_failure'] = location_dict.get('log_failure',True)
        return radar_dict
    
    def _create_poi_thread(self, thread_name, location, station_dict):
        prefix = station_dict.get('prefix','id'+thread_name)
        self.threads[thread_name] = dict()
        self.threads[thread_name]['datasource'] = 'POI'
        self.threads[thread_name]['prefix'] = prefix
        self.threads[thread_name]['thread'] = DWDPOIthread(thread_name,
                    location,
                    prefix,
                    iconset=station_dict.get('iconset',4),
                    log_success=weeutil.weeutil.to_bool(station_dict.get('log_success',False)),
                    log_failure=weeutil.weeutil.to_bool(station_dict.get('log_failure',True)))
        self.threads[thread_name]['thread'].start()
    
    
    def _create_cdc_thread(self, thread_name, location, station_dict):
        prefix = station_dict.get('prefix','id'+thread_name)
        self.threads[thread_name] = dict()
        self.threads[thread_name]['datasource'] = 'CDC'
        self.threads[thread_name]['prefix'] = prefix
        self.threads[thread_name]['thread'] = DWDCDCthread(thread_name,
                    location,
                    prefix,
                    iconset=station_dict.get('iconset',4),
                    observations=station_dict.get('observations'),
                    log_success=weeutil.weeutil.to_bool(station_dict.get('log_success',False)),
                    log_failure=weeutil.weeutil.to_bool(station_dict.get('log_failure',True)))
        self.threads[thread_name]['thread'].start()
    
    
    def _create_zamg_thread(self, thread_name, location, station_dict, user, passwd):
        prefix = station_dict.get('prefix','id'+thread_name)
        self.threads[thread_name] = dict()
        self.threads[thread_name]['datasource'] = 'ZAMG'
        self.threads[thread_name]['prefix'] = prefix
        self.threads[thread_name]['thread'] = ZAMGthread(thread_name,
                    location,
                    prefix,
                    iconset=station_dict.get('iconset',4),
                    observations=station_dict.get('observations'),
                    user=user,passwd=passwd,
                    log_success=weeutil.weeutil.to_bool(station_dict.get('log_success',False)),
                    log_failure=weeutil.weeutil.to_bool(station_dict.get('log_failure',True)))
        self.threads[thread_name]['thread'].start()
    
    
    def _create_openmeteo_thread(self, thread_name, openmeteo_dict):
        prefix = openmeteo_dict.get('prefix','id'+thread_name)
        self.threads[thread_name] = dict()
        self.threads[thread_name]['datasource'] = 'OPENMETEO'
        self.threads[thread_name]['prefix'] = prefix
        self.threads[thread_name]['thread'] = DWDOPENMETEOthread(thread_name,
                    openmeteo_dict,
                    log_success=weeutil.weeutil.to_bool(openmeteo_dict.get('log_success',False)),
                    log_failure=weeutil.weeutil.to_bool(openmeteo_dict.get('log_failure',True)))
        self.threads[thread_name]['thread'].start()
    
    
    def shutDown(self):
        """ shutdown threads """
        if self.dwdxtype:
            weewx.xtypes.xtypes.remove(self.dwdxtype)
        if has_db:
            self.database_thread.shutDown()
        for ii in self.threads:
            try:
                self.threads[ii]['thread'].shutDown()
            except Exception:
                pass


    def new_loop_packet(self, event):
        #for thread_name in self.threads:
        #    pass
        # remember outTemp and outHumidty for later use
        try:
            if self.dwdxtype:
                self.dwdxtype.remember(event.packet)
        except (LookupError,TypeError,ValueError,ArithmeticError,OSError) as e:
            # reported once every 5 minutes only
            if self.next_loop_error_ts<time.time():
                logerr("dwdxtype.remember() %s %s" % (e.__class__.__name__))
                self.next_loop_error_ts = time.time()+300
    
    
    def new_archive_record(self, event):
        elapsed = list()
        ts = event.record.get('dateTime',time.time())
        for thread_name in self.threads:
            try:
                elapsed.append('%s:%.2fs' % (thread_name,self.threads[thread_name]['thread'].last_run_duration))
            except AttributeError:
                pass
            try:
                # get collected data
                datasource = self.threads[thread_name]['datasource']
                if datasource=='POI':
                    data,interval = self.threads[thread_name]['thread'].get_data(ts)
                    if data: data = data[0]
                elif datasource=='CDC':
                    data, interval, maxtime = self.threads[thread_name]['thread'].get_data(ts)
                    if data:
                        if has_db:
                            databaseput(self.database_q,datasource,self.threads[thread_name]['prefix'],data) 
                        try:
                            data = data[maxtime]
                        except (TypeError,LookupError) as e:
                            logerr("error processing data of thread '%s' for the new archive record: CDC data error. maxtime=%s %s %s" % (thread_name,maxtime,e.__class__.__name__,e))
                            data = None
                elif datasource=='ZAMG':
                    data,interval = self.threads[thread_name]['thread'].get_data(ts)
                elif datasource=='OPENMETEO':
                    data,interval = self.threads[thread_name]['thread'].get_data(ts)
                    if data: data = data[0]
                elif datasource=='WBS':
                    data,interval = self.threads[thread_name]['thread'].get_data(ts)
                elif datasource.startswith('Radolan'):
                    data,interval = self.threads[thread_name]['thread'].get_data(ts)
                    logdbg('user.DWD.radar %s' % data)
                    if data and has_db:
                        databaseput(self.database_q,datasource,self.threads[thread_name]['prefix'],[data]) 
                else:
                    data = None
                #print(thread_name,data,interval)
                if data:
                    x = data.get('dateTime',(ts,'unix_epoch','group_time'))[0]
                    if x is None or x<(ts-10800):
                        # no recent readings found
                        for key in data:
                            if key not in ('interval','latitude','longitude','altitude'):
                                data[key] = weewx.units.ValueTuple(None,data[key][1],data[key][2])
                    x = self._to_weewx(thread_name,data,event.record['usUnits'])
                    event.record.update(x)
            except (LookupError,TypeError,ValueError,ArithmeticError,OSError) as e:
                logerr("error processing data of thread '%s' for the new archive record: %s %s traceback %s" % (thread_name,e.__class__.__name__,e,gettraceback(e)))
        logdbg('elapsed CPU time %s' % ' '.join(elapsed))


    def _to_weewx(self, thread_name, reply, usUnits):
        prefix = self.threads[thread_name]['prefix']
        data = dict()
        for key in reply:
            #print('*',key)
            if key in ('interval','count','sysStatus') or (key=='dateTime' and not prefix):
                pass
            elif key in ('interval','count'):
                data[key] = reply[key]
            else:
                try:
                    val = reply[key]
                    val = weewx.units.convertStd(val, usUnits)[0]
                except (TypeError,ValueError,LookupError,ArithmeticError) as e:
                    try:
                        val = reply[key][0]
                    except LookupError:
                        val = None
                if prefix:
                    data[prefix+key[0].upper()+key[1:]] = val
                else:
                    data[key] = val
        return data


if __name__ == '__main__':

    conf_dict = configobj.ConfigObj("DWD.conf")

    class Engine(object):
        class stn_info(object): 
            latitude_f = conf_dict['Station']['latitude']
            longitude_f = conf_dict['Station']['longitude']
            altitude_vt = (100.0,'meter','group_altitude') 
            location = 'Testlocation'
    engine = Engine()
    
    if False:

        t = DWDPOIthread('POI',conf_dict,log_success=True,log_failure=True)
        t.start()

        try:
            while True:
                x = t.get_data(time.time())
                print(x)
                time.sleep(10)
        except (Exception,KeyboardInterrupt):
            pass

        print('xxxxxxxxxxxxx')
        t.shutDown()
        print('+++++++++++++')

    else:
    
        sv = DWDservice(engine,conf_dict)
        
        try:
            while True:
                #event = weewx.Event(weewx.NEW_LOOP_PACKET)
                #event.packet = {'usUnits':weewx.METRIC}
                #sv.new_loop_packet(event)
                #if len(event.packet)>1:
                #    print(event.packet)
                event = weewx.Event(weewx.NEW_ARCHIVE_RECORD)
                event.record = {'usUnits':weewx.METRIC}
                sv.new_archive_record(event)
                if len(event.record)>1:
                    print(event.record)
                time.sleep(10)
        except Exception as e:
            print('**MAIN**',e.__class__.__name__,e)
        except KeyboardInterrupt:
            print()
            print('**MAIN** CTRL-C pressed')

        sv.shutDown()

