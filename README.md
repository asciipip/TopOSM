# Phil's TopOSM Variant

This is my ([Phil Gold's](mailto:phil_g@pobox.com)) repository for
rendering [OpenStreetMap](https://www.openstreetmap.org/) data.  It's
based on Lars Ahlzen's [TopOSM](http://toposm.ahlzen.com/), but I've
modified it significantly according to what I want to see in a map.

This repository contains the map stylesheets as well as the core programs
for rendering and continuously rerendering a minutely-updated OSM
database.


## Requirements ##

I use a pretty standard OSM rendering stack:

 * PostgreSQL and PostGIS to store the data
 * osm2pgsql to import the data
 * osmosis to extract data for North America, plus follow minutely updates
 * GDAL and ImageMagick to process elevation data
 * Mapnik to render the maps
 * OSM "external data", principally the ocean shapefiles

In addition, I use some less common things:

 * [osm-shields][] for specialized route shield images
 * RabbitMQ (any AMQP server would do) to coordinate the rendering queues
 * InfluxDB to record rendering statistics

  [osm-shields]: https://gitlab.com/asciiphil/osm-shields

And my full rendering stack needs stuff from two other repositories:

 * Mapnik minutely updates (not yet uploaded anywhere)
 * Elevation data and processing pipeline (not yet uploaded anywhere)

Pretty much everything is written in Python.  The following modules are used:

 * PyPDF2
 * amqplib
 * boto
 * cairo
 * dateutil
 * filelock
 * influxdb
 * mapnik
 * pika
 * xattr


## Installation ##

TBD


## File Structure ##

### Configuration ###

`set-toposm-env.templ` should be copied to `set-toposm-env` and edited
with appropriate local configuration values.

Before using any of the programs here, either source `set-toposm-env`, e.g.:

    . ./set-toposm-env

Or use the `with-toposm-env` wrapper:

    ./with-toposm-env queue_stats.py


### Map Stylesheets ###

The stylesheets are in the `carto` directory and use CartoCSS.  They use
images in the `symbols` and `custom-symbols` directories.

There's a Makefile for updating the Mapnik stylesheets, so you can just
run `make` after editing any of the CartoCSS files.


### Rendering Programs ###

The heart of the tile rendering is `queuemaster.py`.  It listens for tile
requests and expirations (more on those shortly) and issues commands to
the rendering daemons to direct rendering of particular tiles.

Tiles are requested by `tp.py`.  It's intended to run as a CGI program on
a web server (via the tp.cgi wrapper, which sets the TopOSM environment
for it).  As it's called for each tile, it check to see if the tile exists
and is up to date.  If it is, it serves the tile image.  If not (it
doesn't exist or it's out of date), `tp.py` sends a rendering request via
AMQP to the queuemaster and waits for a response.  It has some logic for
waiting different amounts of time in different cases and optionally
uploading the tiles to Amazon S3 before serving.  (Some of that logic is
currently hardcoded and really ought to be more configurable.)

When minutely updates are processed, a program (not part of this
repository) sends the expired tile list from osmosis to the queuemaster
via AMQP.  The queuemaster checks to see which existing tile files are
affected by the expiration and: (1) marks them as dirty in the filesystem
using extended file attributes; and (2) adds them to its rendering queues.

`renderd.py` manages the rendering processes.  A single `renderd.py`
invocation can create multiple rendering threads, with different dequeuing
strategies.  I use the following command line on my 24-core, 128GB RAM
system:

    renderd.py missing:2 by_work_available:6 by_zoom:2 important:4

`queue_stats.py` requests some statistics from the queuemaster and then
prints them out.

`expire_tiles.py` is theoretically for expiring tiles ad hoc.  I don't use
it much, though, and it hasn't yet been updated to work on Python 3.

`toposm.py` contains the meat of the actual map rendering.  It can also be
run from the command line to render arbitrary images.  It uses `areas.py`,
`common.py`, `coords.py`, and `env.py`.  Most of the other programs import
toposm.  (`stats.py` and `tileexpire.py` are modules used by various of
the above programs.)

Check out the `MESSAGE_PROTOCOL.md` file for more information about the
communications between programs.


## Credits ##

TopOSM was originally created by Lars Ahlzen (lars@ahlzen.com), with
contributions from Ian Dees, Phil Gold, Kevin Kenny, Yves Cainaud, Richard
Weait, and others.

License: GPLv2
