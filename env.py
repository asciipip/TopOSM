#!/usr/bin/python

"""env.py: Initializes the TopOSM render environment."""

import os
import sys

__author__      = "Lars Ahlzen"
__copyright__   = "(c) Lars Ahlzen 2008-2011"
__license__     = "GPLv2"


##### Import environment variables

# Check that the environment is set and import configuration
if not 'TOPOSM_ENV_SET' in os.environ:
    print("Error: TopOSM environment not set.")
    sys.exit(1)

BASE_TILE_DIR = os.environ['BASE_TILE_DIR']
TEMPDIR = os.environ['TEMP_DIR']
TILE_SIZE = int(os.environ['TILE_SIZE'])
BORDER_WIDTH = int(os.environ['BORDER_WIDTH'])
ERRORLOG = os.environ['ERROR_LOG']
TOPOSM_DEBUG = os.environ['TOPOSM_DEBUG']
MINUTELY_STATE_FILE = os.environ['MINUTELY_STATE_FILE']
EXTRA_FONTS_DIR = os.environ['EXTRA_FONTS_DIR']
CACHE_LAYERS = frozenset(os.environ['CACHE_LAYERS'].split(','))
DB_HOST = os.environ['DB_HOST']
INFLUX_SSL = os.environ['INFLUX_SSL'].upper() in ('1', 'YES', 'TRUE')
INFLUX_HOST = os.environ['INFLUX_HOST']
INFLUX_PORT = int(os.environ['INFLUX_PORT'])
INFLUX_USER = os.environ['INFLUX_USER']
INFLUX_PASS = os.environ['INFLUX_PASS']
INFLUX_DB = os.environ['INFLUX_DB']
AWS_ACCESS = os.environ['AWS_ACCESS']
AWS_SECRET = os.environ['AWS_SECRET']
AWS_BUCKET = os.environ['AWS_BUCKET']

##### Common constants

#CONTOUR_INTERVAL = 15.24 # 50 ft in meters
#CONTOUR_INTERVAL = 7.62 # 25 ft in meters
#CONTOUR_INTERVAL = 12.192 # 40 ft in meters
CONTOUR_INTERVAL = 5

AGG_LAYERS = frozenset(['hypsorelief', 'areas', 'ocean'])
CAIRO_LAYERS = frozenset(['contour-labels', 'contour-mask', 'contours',
                          'features_fills', 'features_labels', 'features_mask',
                          'features_outlines', 'features_top'])
MAPNIK_LAYERS = AGG_LAYERS | CAIRO_LAYERS

# Optimal metatile size (N x N subtiles) by zoom level.
# A too low number is inefficient. A too high number uses
# large amounts of memory and sometimes breaks the gdal tools.
NTILES = {
    0:1, 1:1, 2:1, 3:1, 4:1, 5:1, 6:1, 7:1, 8:1, 9:1, 10:1,
    11:2, 12:4, 13:6, 14:8, 15:10, 16:12, 17:12, 18:12,
    19:12, 20:12 }

# Which of the various TopOSM-generated tilesets should be the one to carry
# the "needs rendering" markers.
REFERENCE_TILESET = 'composite_h'

LATLONG_PROJECTION_DEF = "+proj=longlat +datum=WGS84 +no_defs"
MERCATOR_PROJECTION_DEF = "+proj=merc +a=6378137 +b=6378137 +lat_ts=0 +lon_0=0 +x_0=0 +y_0=0 +k=1 +units=m +nadgrids=@null +wktext +no_defs +type=crs"
NAD83_PROJECTION_DEF = "+proj=latlong +datum=NAD83 +ellps=GRS80 +no_defs"

