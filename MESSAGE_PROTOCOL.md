## Medium

All communications are via AMQP, on the `osm` exchange.

Tile expirations should be sent to the `expire_toposm` topic.

All running programs listen for commands on the `toposm` topic.

The queuemaster listens for commands on the `toposm.queuemaster` topic.

Rendering threads may be addressed via a hierarchy.  An individual thread
will be addressable at the `toposm.render.<hostname>.<pid>.<id>` topic.
E.g. thread number 3 launched by the process with PID 55823 running on
host "vader" would be addressed as `toposm.render.vader.55823.3`.  All
rendering threads listen to all levels of the hierarchy, so a message sent
to `toposm.render` would be received by all rendering threads, and one
sent to `toposm.render.vader` would be received by all reads running on
host "vader".


## Messages

### Tile Expirations

Tile expirations are very simple.  They should be the tile address in
"z/x/y" format, with multiple tiles separated by semicolons.
e.g. `14/5672/3452;14/5673/3452;14/5672/3453`.


### Commands and Responses

All other communications between the queuemaster and other programs follow
the format described below.

Messages are all JSON.

Command:

    { "command": <command-name>, <parameters> ... }


Normal rendering sequence:

queuemaster -> all renderers

    { "command": "queuemaster online" }

renderer -> queuemaster

    { "command": "register",
      "hostname": <hostname>,
      "pid": <pid>,
      "threadid: <threadid>,
      "strategy": <strategy> }

"strategy" one of:
 * missing - Only render tiles that have been requested because they've
   never been rendered.
 * important - Only render tiles that have been queued as "important".
   Also render missing tiles.
 * by_work_available - Distributes work based on current queue length at
   various zoom levels.  This is the preferred "workhorse" strategy; it
   spends rendering effort where it's most needed.
 * by_zoom - Distributes work based on total number of tiles at each zoom
   level.  This is a good strategy for high-zoom cleanup.  Once a zoom
   level gets down to only a few tiles needing rendering, the
   "by_work_available" strategy will basically abandon them in favor of
   zoom levels with greater numbers of outstanding tiles.  The "by_zoom"
   strategy will always favor higher zoom levels because they have more
   tiles.

queuemaster -> renderer

    { "command": "render",
      "metatile": <metatile e.g. "15/950/1235"> }

renderer -> queuemaster

    { "command": "rendered",
      "metatile": <metatile> }

renderer -> queuemaster

    { "command": "unregister" }

All renderer -> queuemaster communication should have the renderer's queue
as the "reply_to" property.


## Rendering Example

Normal render request sequence:

requester -> queuemaster

    { "command": "render",
      "tile": "z/x/y" }

queuemaster -> requester

    { "command": "rendered" }


The queuemaster also understands:

    { "command": "stats" }
