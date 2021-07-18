/* -*- css -*- */
#highway-lowzoom {
    [zoom >= 5][zoom < 9][highway = 'motorway'] {
        line-color: @interstatecolorlowzoom;
        line-join: round;
        line-cap: round;
        [zoom >= 5][zoom < 6] { line-width: 0.8; }
        [zoom >= 6][zoom < 7] { line-width: 1.0; }
        [zoom >= 7][zoom < 8] { line-width: 1.3; }
        [zoom >= 8][zoom < 9] { line-width: 1.8; }
    }
    [zoom >= 5][zoom < 9][highway = 'trunk'] {
        line-color: @trunkcolorlowzoom;
        line-join: round;
        line-cap: round;
        [zoom >= 5][zoom < 6] { line-width: 0.5; }
        [zoom >= 6][zoom < 7] { line-width: 0.7; }
        [zoom >= 7][zoom < 8] { line-width: 1.0; }
        [zoom >= 8][zoom < 9] { line-width: 1.5; }
    }
    [zoom >= 6][zoom < 9][highway = 'primary'] {
        line-color: @primarycolorlowzoom;
        line-join: round;
        line-cap: round;
        [zoom >= 6][zoom < 7] { line-width: 0.3; }
        [zoom >= 7][zoom < 8] { line-width: 0.5; }
        [zoom >= 8][zoom < 9] { line-width: 0.7; }
    }
}

#trail-colors {
    [zoom >= 15] {
        [highway = 'path'],
        [highway = 'trail'],
        [highway = 'footway'],
        [highway = 'steps'],
        [highway = 'pedestrian'],
        [route = 'hiking'] {
            [zoom >= 15][zoom < 16] { line-width: 4.5; }
            [zoom >= 16]            { line-width: 6.0; }
            line-color: [colour];
            line-join: round;
        }
    }
}

#highway-outlines {
    [zoom >= 9][highway = 'motorway'],
    [zoom >= 9][highway = 'trunk'] {
        [tunnel != 'yes'] {
            line-color: black;
            line-join: round;
            line-cap: round;
        }
        [tunnel = 'yes'] {
            line-color: @tunneloutlinecolor;
        }
        [zoom >=  9][zoom < 12] {
            line-width: 2 * @road-outline-z9-tier1 + @road-fill-z9-tier1; [tunnel = 'yes'] { line-dasharray:  4,2; }
        }
        [zoom >= 12][zoom < 14] {
            line-width: 2 * @road-outline-z12-tier1 + @road-fill-z12-tier1; [tunnel = 'yes'] { line-dasharray:  6,3; }
        }
        [zoom >= 14][zoom < 16] {
            line-width: 2 * @road-outline-z12-tier1 + @road-fill-z14-tier1; [tunnel = 'yes'] { line-dasharray:  6,3; }
        }
        [zoom >= 16] {
            line-width: 2 * @road-outline-z12-tier1 + @road-fill-z16-tier1; [tunnel = 'yes'] { line-dasharray: 10,5; }
        }
    }

    [zoom >= 9][zoom < 10][highway = 'primary'] {
        line-color: @primarycolorlowzoom;
        line-join: round;
        line-cap: round;
        line-width: @road-fill-z9-tier2;
    }
    [zoom >= 10][highway = 'primary'] {
        [tunnel != 'yes'] {
            line-color: black;
            line-join: round;
            line-cap: round;
        }
        [tunnel = 'yes'] {
            line-color: @tunneloutlinecolor;
        }
        [zoom >= 10][zoom < 12] {
            line-width: 2 * @road-outline-z9-tier2 + @road-fill-z10-tier2; [tunnel = 'yes'] { line-dasharray:  4,2; }
        }
        [zoom >= 12][zoom < 14] {
            line-width: 2 * @road-outline-z12-tier2 + @road-fill-z12-tier2; [tunnel = 'yes'] { line-dasharray:  6,3; }
        }
        [zoom >= 14][zoom < 16] {
            line-width: 2 * @road-outline-z12-tier1 + @road-fill-z14-tier1; [tunnel = 'yes'] { line-dasharray:  6,3; }
        }
        [zoom >= 16] {
            line-width: 2 * @road-outline-z12-tier1 + @road-fill-z16-tier1; [tunnel = 'yes'] { line-dasharray: 10,5; }
        }
    }
    
    [zoom >= 9][zoom < 10][highway = 'secondary'] {
        line-color: @secondarycolorlowzoom;
        line-join: round;
        line-cap: round;
        line-width: @road-fill-z9-tier3;
    }
    [zoom >= 9][zoom < 10][highway = 'tertiary'] {
        line-color: @smallroadcolorlowzoom;
        line-join: round;
        line-cap: round;
        line-width: @road-fill-z9-tier3;
    }
    [zoom >= 10][highway = 'secondary'],
    [zoom >= 10][highway = 'tertiary'] {
        [tunnel != 'yes'] {
            line-color: black;
            line-join: round;
            line-cap: round;
        }
        [tunnel = 'yes'] {
            line-color: @tunneloutlinecolor;
        }
        [zoom >= 10][zoom < 12] {
            line-width: 2 * @road-outline-z9-tier3 + @road-fill-z10-tier3; [tunnel = 'yes'] { line-dasharray:  4,2; }
        }
        [zoom >= 12][zoom < 14] {
            line-width: 2 * @road-outline-z12-tier3 + @road-fill-z12-tier3; [tunnel = 'yes'] { line-dasharray:  6,3; }
        }
        [zoom >= 14][zoom < 16] {
            line-width: 2 * @road-outline-z12-tier3 + @road-fill-z14-tier2; [tunnel = 'yes'] { line-dasharray:  6,3; }
        }
        [zoom >= 16] {
            line-width: 2 * @road-outline-z12-tier3 + @road-fill-z16-tier2; [tunnel = 'yes'] { line-dasharray: 10,5; }
        }
    }

    [zoom >= 10][zoom < 12][highway = 'unclassified'],
    [zoom >= 10][zoom < 12][highway = 'residential'] {
        line-color: #444;
        line-join: round;
        line-cap: round;
        [zoom >= 10][zoom < 11] { line-width: 0.5; }
        [zoom >= 11][zoom < 12] { line-width: 0.6; }
    }
    [zoom >= 12][zoom < 14][highway = 'unclassified'],
    [zoom >= 12][zoom < 14][highway = 'residential'] {
        line-width: 1.2;
        [tunnel = 'yes'] {
            line-color: @tunneloutlinecolor;
            line-dasharray: 6,3;
        }
        [tunnel != 'yes'] {
            line-color: #444;
            line-join: round;
            line-cap: round;
        }
    }
    [zoom >= 14][highway = 'unclassified'],
    [zoom >= 14][highway = 'residential'] {
        [tunnel != 'yes'] {
            line-color: black;
            line-join: round;
            line-cap: round;
        }
        [tunnel = 'yes'] {
            line-color: @tunneloutlinecolor;
        }
        [zoom >= 14][zoom < 16] {
            line-width: 2 * @road-outline-z12-tier3 + @road-fill-z14-tier3; [tunnel = 'yes'] { line-dasharray:  6,3; }
        }
        [zoom >= 16] {
            line-width: 2 * @road-outline-z12-tier3 + @road-fill-z16-tier3; [tunnel = 'yes'] { line-dasharray: 10,5; }
        }
    }

    [zoom >= 10][highway = 'motorway_link'],
    [zoom >= 10][highway = 'trunk_link'],
    [zoom >= 10][highway = 'primary_link'],
    [zoom >= 10][highway = 'secondary_link'],
    [zoom >= 10][highway = 'tertiary_link'] {
        [tunnel = 'yes'] {
            line-color: @tunneloutlinecolor;
        }
        [tunnel != 'yes'] {
            line-color: black;
            line-join: round;
            line-cap: round;
        }
        [zoom >= 10][zoom < 11] {
            line-width:  0.5;
        }
        [zoom >= 11][zoom < 12] {
            line-width:  0.6;
        }
        [zoom >= 12][zoom < 14] {
            line-width: 2 * @road-outline-z12-link + @road-fill-z12-link; [tunnel = 'yes'] { line-dasharray:  6,3; }
        }
        [zoom >= 14][zoom < 16] {
            line-width: 2 * @road-outline-z12-link + @road-fill-z14-link; [tunnel = 'yes'] { line-dasharray:  6,3; }
        }
        [zoom >= 16] {
            line-width: 2 * @road-outline-z12-link + @road-fill-z16-link; [tunnel = 'yes'] { line-dasharray:  6,3; }
        }
    }

    [zoom >= 12][zoom < 14][highway = 'service'] {
        line-color: #444;
        line-join: round;
        line-cap: round;
        line-width: 0.8;
    }
    [zoom >= 14][highway = 'service'] {
        [tunnel = 'yes'] {
            line-color: @tunneloutlinecolor;
        }
        [tunnel != 'yes'] {
            line-color: black;
            line-join: round;
            line-cap: round;
        }
        [zoom >= 14][zoom < 16] {
            line-width: 2 * @road-outline-z12-tier4 + @road-fill-z14-tier4; [tunnel = 'yes'] { line-dasharray:  6,3; }
        }
        [zoom >= 16] {
            line-width: 2 * @road-outline-z12-tier4 + @road-fill-z16-tier4; [tunnel = 'yes'] { line-dasharray: 10,5; }
        }
    }

    [zoom >= 12][highway = 'unsurfaced'],
    [zoom >= 12][highway = 'unimproved'],
    [zoom >= 12][highway = 'track'][bicycle != 'designated'] {
        [zoom >= 12][zoom < 14] {
            line-color: #444;
            line-width: 1.2;
            line-dasharray: 4,2;
        }
        [zoom >= 14] {
            line-color: black;
            line-dasharray: 5,2;
            [zoom >= 14][zoom < 16] { line-width: 2 * @road-outline-z12-tier4 + @road-fill-z14-tier4; }
            [zoom >= 16]            { line-width: 2 * @road-outline-z12-tier4 + @road-fill-z16-tier4; }
        }
    }

    [zoom >= 13][highway = 'cycleway'],
    [zoom >= 13][highway = 'bikeway'],
    [zoom >= 13][highway = 'bridleway'],
    [zoom >= 13][highway = 'track'][bicycle = 'designated'] {
        line-color: black;
        [zoom >= 13][zoom < 15] {
            line-width: 1.0;
            [tunnel =  'yes'] { line-dasharray: 0,6,5,1; }
            [tunnel != 'yes'] { line-dasharray: 5,1; }
        }
        [zoom >= 15] {
            line-width: 2.0;
            [tunnel =  'yes'] { line-dasharray: 0,7,6,1; }
            [tunnel != 'yes'] { line-dasharray: 6,1; }
        }
    }

    [zoom >= 13][highway = 'path'],
    [zoom >= 13][highway = 'trail'],
    [zoom >= 13][highway = 'footway'],
    [zoom >= 13][highway = 'steps'],
    [zoom >= 13][highway = 'pedestrian'] {
        line-color: black;
        [zoom >= 13][zoom < 15] {
            line-width: 0.8;
            [tunnel =  'yes'] { line-dasharray: 0,5,3,2; }
            [tunnel != 'yes'] { line-dasharray: 3,2; }
        }
        [zoom >= 15] {
            /* Invert color if we know it's going onto a dark background. */
            [colour = 'black'],
            [colour = '#000000'] {
                line-color: white;
            }
            line-width: 1.5;
            [tunnel =  'yes'] { line-dasharray: 0,7,4,3; }
            [tunnel != 'yes'] { line-dasharray: 4,3; }
        }
    }
}

#highway-fills {
    [zoom >= 9][highway = 'motorway'] {
        line-join: round;
        line-cap: round;
        line-color: @interstatecolor;
        [tunnel = 'yes'] { line-color: @interstatecolortunnel; }
        [zoom >=  9][zoom < 12] { line-width: @road-fill-z9-tier1; }
        [zoom >= 12][zoom < 14] { line-width: @road-fill-z12-tier1; }
        [zoom >= 14][zoom < 16] { line-width: @road-fill-z14-tier1; }
        [zoom >= 16]            { line-width: @road-fill-z16-tier1; }
    }
    
    [zoom >= 9][highway = 'trunk'] {
        line-join: round;
        line-cap: round;
        line-color: @trunkcolor;
        [tunnel = 'yes'] { line-color: @trunkcolortunnel; }
        [zoom >=  9][zoom < 12] { line-width: @road-fill-z9-tier1; }
        [zoom >= 12][zoom < 14] { line-width: @road-fill-z12-tier1; }
        [zoom >= 14][zoom < 16] { line-width: @road-fill-z14-tier1; }
        [zoom >= 16]            { line-width: @road-fill-z16-tier1; }
    }

    [zoom >= 10][highway = 'primary'] {
        line-join: round;
        line-cap: round;
        line-color: @primarycolor;
        [tunnel = 'yes'] { line-color: @primarycolortunnel; }
        [zoom >= 10][zoom < 12] { line-width: @road-fill-z10-tier2; }
        [zoom >= 12][zoom < 14] { line-width: @road-fill-z12-tier2; }
        [zoom >= 14][zoom < 16] { line-width: @road-fill-z14-tier1; }
        [zoom >= 16]            { line-width: @road-fill-z16-tier1; }
    }

    [zoom >= 10][highway = 'secondary'] {
        line-join: round;
        line-cap: round;
        line-color: @secondarycolor;
        [tunnel = 'yes'] { line-color: @secondarycolortunnel; }
        [zoom >= 10][zoom < 12] { line-width: @road-fill-z10-tier3; }
        [zoom >= 12][zoom < 14] { line-width: @road-fill-z12-tier3; }
        [zoom >= 14][zoom < 16] { line-width: @road-fill-z14-tier2; }
        [zoom >= 16]            { line-width: @road-fill-z16-tier2; }
    }

    [zoom >= 10][highway = 'tertiary'] {
        line-join: round;
        line-cap: round;
        line-color: @smallroadcolor;
        [tunnel = 'yes'] { line-color: @smallroadcolortunnel; }
        [zoom >= 10][zoom < 12] { line-width: @road-fill-z10-tier3; }
        [zoom >= 12][zoom < 14] { line-width: @road-fill-z12-tier3; }
        [zoom >= 14][zoom < 16] { line-width: @road-fill-z14-tier2; }
        [zoom >= 16]            { line-width: @road-fill-z16-tier2; }
    }

    [zoom >= 14][highway = 'unclassified'],
    [zoom >= 14][highway = 'residential'],
    [zoom >= 14][highway = 'unsurfaced'],
    [zoom >= 14][highway = 'unimproved'] {
        line-join: round;
        line-cap: round;
        line-color: @smallroadcolor;
        [tunnel = 'yes'] { line-color: @smallroadcolortunnel; }
        [zoom >= 14][zoom < 16] { line-width: @road-fill-z14-tier3; }
        [zoom >= 16]            { line-width: @road-fill-z16-tier3; }
    }

    [zoom >= 14][highway = 'service'],
    [zoom >= 14][highway = 'track'][bicycle != 'designated'] {
        line-join: round;
        line-cap: round;
        line-color: @smallroadcolor;
        [tunnel = 'yes'] { line-color: @smallroadcolortunnel; }
        [zoom >= 14][zoom < 16] { line-width: @road-fill-z14-tier4; }
        [zoom >= 16]            { line-width: @road-fill-z16-tier4; }
    }

    [zoom >= 12][highway = 'motorway_link'],
    [zoom >= 12][highway = 'trunk_link'],
    [zoom >= 12][highway = 'primary_link'],
    [zoom >= 12][highway = 'secondary_link'],
    [zoom >= 12][highway = 'tertiary_link'] {
        line-join: round;
        line-cap: round;
        [highway = 'motorway_link'] {
            line-color: @interstatecolor;
            [tunnel = 'yes'] { line-color: @interstatecolortunnel; }
        }
        [highway = 'trunk_link'] {
            line-color: @trunkcolor;
            [tunnel = 'yes'] { line-color: @trunkcolortunnel; }
        }
        [highway = 'primary_link'] {
            line-color: @primarycolor;
            [tunnel = 'yes'] { line-color: @primarycolortunnel; }
        }
        [highway = 'secondary_link'] {
            line-color: @secondarycolor;
            [tunnel = 'yes'] { line-color: @secondarycolortunnel; }
        }
        [highway = 'tertiary_link'] {
            line-color: @smallroadcolor;
            [tunnel = 'yes'] { line-color: @smallroadcolortunnel; }
        }
        line-color: @smallroadcolor;
        [zoom >= 12][zoom < 14] { line-width: @road-fill-z12-link; }
        [zoom >= 14][zoom < 16] { line-width: @road-fill-z14-link; }
        [zoom >= 16]            { line-width: @road-fill-z16-link; }
    }
}

#turning-circles-outlines {
    [int_tc_type = 'tertiary'] {
        [zoom >= 15][zoom < 16] {
            marker-line-width: 0;
            marker-width:  2 * @road-outline-z12-tier2 + 3 * @road-fill-z14-tier2;
            marker-height: 2 * @road-outline-z12-tier2 + 3 * @road-fill-z14-tier2;
            marker-fill: black;
            marker-allow-overlap: true;
        }
        [zoom >= 16] {
            marker-line-width: 0;
            marker-width:  2 * @road-outline-z12-tier2 + 3 * @road-fill-z16-tier2;
            marker-height: 2 * @road-outline-z12-tier2 + 3 * @road-fill-z16-tier2;
            marker-fill: black;
            marker-allow-overlap: true;
        }
    }
    [int_tc_type = 'unclassified'],
    [int_tc_type = 'residential'] {
        [zoom >= 15][zoom < 16] {
            marker-line-width: 0;
            marker-width:  2 * @road-outline-z12-tier3 + 3 * @road-fill-z14-tier3;
            marker-height: 2 * @road-outline-z12-tier3 + 3 * @road-fill-z14-tier3;
            marker-fill: black;
            marker-allow-overlap: true;
        }
        [zoom >= 16] {
            marker-line-width: 0;
            marker-width:  2 * @road-outline-z12-tier3 + 3 * @road-fill-z16-tier3;
            marker-height: 2 * @road-outline-z12-tier3 + 3 * @road-fill-z16-tier3;
            marker-fill: black;
            marker-allow-overlap: true;
        }
    }
    [int_tc_type = 'service'] {
        [zoom >= 15][zoom < 16] {
            marker-line-width: 0;
            marker-width:  2 * @road-outline-z12-tier4 + 3 * @road-fill-z14-tier4;
            marker-height: 2 * @road-outline-z12-tier4 + 3 * @road-fill-z14-tier4;
            marker-fill: black;
            marker-allow-overlap: true;
        }
        [zoom >= 16] {
            marker-line-width: 0;
            marker-width:  2 * @road-outline-z12-tier4 + 3 * @road-fill-z16-tier4;
            marker-height: 2 * @road-outline-z12-tier4 + 3 * @road-fill-z16-tier4;
            marker-fill: black;
            marker-allow-overlap: true;
        }
    }
}

#turning-circles-fills {
    [int_tc_type = 'tertiary'] {
        [zoom >= 15][zoom < 16] {
            marker-line-width: 0;
            marker-width:  3 * @road-fill-z14-tier2;
            marker-height: 3 * @road-fill-z14-tier2;
            marker-fill: @smallroadcolor;
            marker-allow-overlap: true;
        }
        [zoom >= 16] {
            marker-line-width: 0;
            marker-width:  3 * @road-fill-z16-tier2;
            marker-height: 3 * @road-fill-z16-tier2;
            marker-fill: @smallroadcolor;
            marker-allow-overlap: true;
        }
    }
    [int_tc_type = 'unclassified'],
    [int_tc_type = 'residential'] {
        [zoom >= 15][zoom < 16] {
            marker-line-width: 0;
            marker-width:  3 * @road-fill-z14-tier3;
            marker-height: 3 * @road-fill-z14-tier3;
            marker-fill: @smallroadcolor;
            marker-allow-overlap: true;
        }
        [zoom >= 16] {
            marker-line-width: 0;
            marker-width:  3 * @road-fill-z16-tier3;
            marker-height: 3 * @road-fill-z16-tier3;
            marker-fill: @smallroadcolor;
            marker-allow-overlap: true;
        }
    }
    [int_tc_type = 'service'] {
        [zoom >= 15][zoom < 16] {
            marker-line-width: 0;
            marker-width:  3 * @road-fill-z14-tier4;
            marker-height: 3 * @road-fill-z14-tier4;
            marker-fill: @smallroadcolor;
            marker-allow-overlap: true;
        }
        [zoom >= 16] {
            marker-line-width: 0;
            marker-width:  3 * @road-fill-z16-tier4;
            marker-height: 3 * @road-fill-z16-tier4;
            marker-fill: @smallroadcolor;
            marker-allow-overlap: true;
        }
    }
}

#parking-outlines {
    [zoom >= 14][amenity = 'parking'] {
        line-color: black;
        line-join: round;
        line-cap: round;
        [zoom >= 14][zoom < 16] {
            line-width: 2;
        }
        [zoom >= 16] {
            line-width: 3.5;
        }
    }
}

#parking-fills {
    [zoom >= 14][amenity = 'parking'] {
        polygon-fill: @smallroadcolor;
    }
}
