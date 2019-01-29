all: areas.xml contour-labels.xml contour-mask.xml contours.xml features_fills.xml features_labels.xml features_mask.xml features_outlines.xml features_top.xml hypsorelief.xml ocean.xml

areas.xml: carto/areas.mml carto/colors.mss carto/areas.mss carto/features_water.mss
	cd carto; carto areas.mml >../areas.xml

contour-labels.xml: carto/contour-labels.mml carto/colors.mss carto/fonts.mss carto/contour-labels.mss
	cd carto; carto contour-labels.mml >../contour-labels.xml

contour-mask.xml: carto/contour-mask.mml carto/halo-colors.mss carto/fonts.mss carto/contour-labels.mss
	cd carto; carto contour-mask.mml >../contour-mask.xml

contours.xml: carto/contours.mml carto/colors.mss carto/fonts.mss carto/contours.mss
	cd carto; carto contours.mml >../contours.xml

features_fills.xml: carto/features_fills.mml carto/colors.mss carto/sizes.mss carto/fonts.mss carto/features_fills.mss carto/features_highways.mss carto/features_railways.mss carto/features_aeroways.mss
	cd carto; carto features_fills.mml >../features_fills.xml

features_labels.xml: carto/features_labels.mml carto/colors.mss carto/fonts.mss carto/features_labels.mss
	cd carto; carto features_labels.mml >../features_labels.xml

features_mask.xml: carto/features_mask.mml carto/halo-colors.mss carto/fonts.mss carto/features_labels.mss
	cd carto; carto features_mask.mml >../features_mask.xml

features_outlines.xml: carto/features_outlines.mml carto/colors.mss carto/sizes.mss carto/fonts.mss carto/ocean.mss carto/features_outlines.mss carto/features_water.mss carto/features_pipelines.mss carto/features_borders.mss carto/features_highways.mss carto/features_railways.mss carto/features_aeroways.mss
	cd carto; carto features_outlines.mml >../features_outlines.xml

features_top.xml: carto/features_top.mml carto/colors.mss carto/sizes.mss carto/fonts.mss carto/features_top.mss carto/features_borders.mss
	cd carto; carto features_top.mml >../features_top.xml

hypsorelief.xml: carto/hypsorelief.mml carto/hypsorelief.mss
	cd carto; carto hypsorelief.mml >../hypsorelief.xml

ocean.xml: carto/ocean.mml carto/colors.mss carto/ocean.mss
	cd carto; carto ocean.mml >../ocean.xml


