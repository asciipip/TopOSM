all: areas.xml contour-labels.xml contour-mask.xml contours.xml features_fills.xml features_labels.xml features_mask.xml features_outlines.xml features_top.xml hypsorelief.xml ocean.xml

.SECONDEXPANSION:
%.xml: carto/%.mml $$(shell ./carto-deps carto/%.mml)
	carto -q -f $@ $<
