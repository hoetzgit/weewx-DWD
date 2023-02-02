# weewx-DWD

download weather and warning data and use them in WeeWX and skins.

<p align="center"><img src="Wettervorhersage-Warnungen-Fichtelberg.png" width="600px" /></p>

With this extension you can receive and process the following data:
* from Deutscher Wetterdienst (DWD)
  * pre-calculated weather forecasts based on hours, three-hours, and days
    for the next 10 days for about 6000 places around the world (`dwd-mosmix`)
  * weather alerts for counties and places in Germany (`dwd-warnings` and
    `dwd-capwarnings`)
  * weather maps of Europe (`wget-dwd`)
  * actual readings of the DWD weather stations
* from Zentralanstalt für Meteorologie und Geodynamik (ZAMG)
  * actual readings of the ZAMG weather stations
* by using the Open-Meteo weather API
  * pre-calculated weather forecasts based on different weather models for
    all over the world (`dwd-mosmix`)

Data will be processed to:
* HTML files (`*.inc`) to include in skins with `#include`
* JSON files (`*.json`) to automatically process 
* `forecast.json` for direct use with Belchertown skin

## Trouble shooting

If you need help, please make sure to provide:

* the complete command line used to invoke the program
* the complete output
* the sections `[WeatherServices]` and `[DeutscherWetterdienst]` if any
* Try to use the `--verbose` option to get more information

## Prerequisites

You may install GeoPy:

```
sudo apt-get install python3-geopy
```

## Installation

Download the extension from Github:

```
wget -O weewx-snmp.zip https://github.com/roe-dl/weewx-DWD/archive/master.zip
```

Unpack the file

Copy `bin/user/weatherservices.py` and `bin/user/capwarnings.py`
into the extension directory of WeeWX. That is often
`/usr/share/weewx/user`.

Copy `usr/local/bin/dwd-mosmix`, `usr/local/bin/dwd-warnings`,
`usr/local/bin/html2ent.ansi`, and `usr/local/bin/wget-dwd` to
`/usr/local/bin` and make it executable by `chmod +x file_name`.

Create the following links:
```
sudo ln -s /usr/share/weewx/user/capwarnings.py /usr/local/bin/bbk-warnings
sudo ln -s /usr/share/weewx/user/capwarnings.py /usr/local/bin/dwd-cap-warnings
```

If you installed WeeWX into another directory than `/usr/share/weewx`
then you have to adapt the path in the above commands.

## Programs

### dwd-mosmix

You can use `dwd-mosmix` to create weather forecasts in HTML to include
them in your website, JSON files of the forecast data for further processing
by Javascript, and the `forecast.json` file of the Belchertown skin to
replace the Aeris forecast by the forecast of another weather service
provider.

To use `dwd-mosmix` you need:
* weather icons of the [Belchertown Skin](https://obrienlabs.net/belchertownweather-com-website-theme-for-weewx/)
  or the [DWD](https://www.dwd.de/DE/wetter/warnungen_aktuell/objekt_einbindung/piktogramm_node.html)
* weather icons of [Erik Flowers](https://erikflowers.github.io/weather-icons/)
* additional CSS entries (see below)

You can invoke `dwd-mosmix` using the following options:

```
Usage: dwd-mosmix [options] [station]

Options:
  -h, --help            show this help message and exit
  --config=CONFIG_FILE  Use configuration file CONFIG_FILE.
  --weewx               Read config from weewx.conf.
  --orientation=H,V     HTML table orientation horizontal, vertial, or both
  --icon-set=SET        icon set to use, default is 'belchertown', possible
                        values are 'dwd', 'belchertown', and 'aeris'
  --lang=ISO639         Forecast language. Default 'de'
  --aqi-source=PROVIDER Provider for Belchertown AQI section
  --hide-placemark      No placemark caption over forecast table
  --open-meteo=MODEL    use Open-Meteo API instead of DWD MOSMIX

  Output and logging options:
    --dry-run           Print what would happen but do not do it. Default is
                        False.
    --log-tags          Log tags while parsing the KML file.
    -v, --verbose       Verbose output

  Commands:
    --print-icons-ww    Print which icons are connected to which ww weather
                        code
    --html              Write HTML .inc file
    --json              Write JSON file
    --belchertown       Write Belchertown style forecast file
    --database          Write database file
    --print-uba=CMD     download data from UBA

  Intervals:
    --all               Output all details in HTML
    --hourly            output hourly forecast
    --daily             output daily forecast (the default)
```

You can use several options of section "Commands" at the same time.

To specifiy the location you need a station code or a set of geographic
coordinates. Geographic coordinates are to be used together with the
option `--open-meteo`, station codes otherwise. See
[Wiki](https://github.com/roe-dl/weewx-DWD/wiki) for lists of
station codes.

If you do not specify otherwise the HTML file contains two tables,
one for PC usage in horizontal orientation and one for phone
usage in vertical orientation. By the CSS class `hidden-xs` 
one of them is visible at the same time only. You can restrict
the creation to one of the tables by using the `--orientation`
option. Possible values are `h` and `v`.

The option `--icon-set` specifies the weather icon set to be used.

The language option influences the weekday names only, for English
and german the tool tips, too. `de`, `en`, `fr`, `it`, and `cz`
are available.

The get data by the Open-Meteo API instead of the DWD, use the 
option `--open-meteo` and specify a weather model:

--open-meteo=   | Country | Weather service          | Model
----------------|---------|--------------------------|---------------
dwd-icon        | DE      | DWD                      | ICON
gfs             | US      | NOAA                     | GFS
meteofrance     | FR      | MeteoFrance              | Arpege+Arome
ecmwf           | EU      | ECMWF                    | open IFS
jma             | JP      | JMA                      | GSM+MSM
metno           | NO      | MET Norway               | Nordic
gem             | CA      | Canadian Weather Service | GEM+HRDPS
ecmwf_ifs04     | EU      | ECMWF                    | IFS
metno_nordic    | NO      | MET Norway               | Nordic
icon_seamless   | DE      | DWD                      | ICON Seamless
icon_global     | DE      | DWD                      | ICON Global
icon_eu         | DE      | DWD                      | ICON EU
icon_d2         | DE      | DWD                      | ICON D2
gfs_seamless    | US      | NOAA                     | GFS Seamless
gfs_global      | US      | NOAA                     | GFS Global
gfs_hrrr        | US      | NOAA                     | GFS HRRR
gem_seamless    | CA      | Canadian Weather Service | GEM
gem_global      | CA      | Canadian Weather Service | GEM
gem_regional    | CA      | Canadian Weather Service | GEM
gem_hrdps_continental | CA      | Canadian Weather Service | GEM-HRDPS

Don't forget to observe the terms and conditions of Open-Meteo and the respective
weather service when using their data.

## Configuration

### Create directory

You need to create a sub-directory within the directory of the skin
you are using. 

Example:
```
cd /etc/weewx/skins/Belchertown
mkdir dwd
```

The word `Belchertown` is to be replaced by the name of your skin.

All the programs and services of this extension save their files to
that directory.

Example:
```
[DeutscherWetterdienst]
    [[warning]]
        icons='../dwd/warn_icons_50x50'
        states='Sachsen','Thüringen'
        [[[counties]]]
              'Kreis Mittelsachsen - Tiefland'='DL'
              'Stadt Leipzig'='L'
              'Stadt Jena'='J'
              'Stadt Dresden'='DD'
        [[[cities]]]
              'Stadt Döbeln'='DL'
              'Stadt Waldheim'='DL'
              'Leipzig-Mitte'='L'
              'Stadt Jena'='J'
              'Dresden-Altstadt'='DD'
    [[forecast]]
        icons='../images'
        orientation=h,v
        #show_obs_symbols = True # optional
        #show_obs_description = False # optional
        #show_placemark = True # optional
    [[BBK]]
        #icons=...
        #logos=...
        [[[counties]]]
            145220000000 = DL
            147130000000 = L
     [[Belchertown]]
        section = Belchertown
        warnings = DL
        forecast = P0291
[WeatherServices]
    path='/etc/weewx/skins/Belchertown/dwd'
    [[current]]
        # Examples follow.
        [[[station_nr]]]
            provider = ZAMG  # DWD, ZAMG or Open-Meteo
            prefix = observation_type_prefix_for_station
            # equipment of the weather station (optional)
            observations = air,wind,gust,precipitation,solar
        [[[station_code]]]
            provider = DWD
            model = POI
            prefix = observation_type_prefix_for_station
        [[[station_id]]]
            provider = DWD
            model = CDC
            prefix = observation_type_prefix_for_station
            # equipment of the weather station (optional)
            observations = air,wind,gust,precipitation,solar
        [[[ThisStation]]]
            # actual readings out of the forecast for the location of this station
            provider = Open-Meteo
            model = dwd-icon
            prefix = observation_type_prefix
```

The key `path` has to point to the directory created before.

The paths, states, and counties are to replaced by the appropriate names.

**Note:** The key `icons` refers to the web servers. The value must not
start with `/`.
