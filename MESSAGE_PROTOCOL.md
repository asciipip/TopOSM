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


Normal render request sequence:

requester -> queuemaster

    { "command": "render",
      "tile": "z/x/y" }

queuemaster -> requester

    { "command": "rendered" }


The queuemaster also understands:

    { "command": "stats" }
