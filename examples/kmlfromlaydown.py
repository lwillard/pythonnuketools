# used for interpolation for nuclear blast effects
import numpy as np

# used for interpolation for nuclear blast effects
from scipy import interpolate

# used for nuclear blast effects
from glasstone.overpressure import brode_overpressure

# used to read laydown files
import csv

# used for coordinate calculations
import math

# used for Polygon definition
from shapely.geometry import Polygon

# used to merge polygons
from shapely.ops import unary_union

# used for writing KML files
import simplekml

# used for command line reading
import sys

import pythonnuketools

from pythonnuketools import GeographyUtils
from pythonnuketools import OverpressureRingCalculator
from pythonnuketools import KmlWriter

#Main Loop
if len(sys.argv) != 3:
    raise ValueError('Please provide a nuclear laydown map filename and a output filename.')

laydown_file = sys.argv[1]
output_file = sys.argv[2]    

laydown = pythonnuketools.LaydownFileReader()
dgzs = laydown.ReadLaydownFile(laydown_file)

poly20 = pythonnuketools.GeoPolygons('ab0000ff', '00202020')
poly5 = pythonnuketools.GeoPolygons('65007fff', '00202020')
poly2 = pythonnuketools.GeoPolygons('6519e3ff', '00202020')
poly1 = pythonnuketools.GeoPolygons('45ababab', '00202020')

for target in dgzs:
    c = OverpressureRingCalculator()

    #20 psi
    radius = c.GetOverpressureRadii(target.explosion_yield, target.height_of_burst, 20)
    poly20.polys.append(GeographyUtils.CreateGeoCirclePoly(target.latitude, target.longitude, float(radius), 80))

    #5 psi
    radius = c.GetOverpressureRadii(target.explosion_yield, target.height_of_burst, 5)
    poly5.polys.append(GeographyUtils.CreateGeoCirclePoly(target.latitude, target.longitude, float(radius), 80))
    
    #2 psi
    radius = c.GetOverpressureRadii(target.explosion_yield, target.height_of_burst, 2)
    poly2.polys.append(GeographyUtils.CreateGeoCirclePoly(target.latitude, target.longitude, float(radius), 80))

    #1 psi
    radius = c.GetOverpressureRadii(target.explosion_yield, target.height_of_burst, 1)
    poly1.polys.append(GeographyUtils.CreateGeoCirclePoly(target.latitude, target.longitude, float(radius), 80))

# merge the blast rings for better aesthetics
poly20.merge()
poly5.merge()
poly2.merge()
poly1.merge()

kml = KmlWriter()
kml.CreatePolys(poly20.merged_polys, poly20.fill_color, poly20.outline_color)
kml.CreatePolys(poly5.merged_polys, poly5.fill_color, poly5.outline_color)
kml.CreatePolys(poly2.merged_polys, poly2.fill_color, poly2.outline_color)
kml.CreatePolys(poly1.merged_polys, poly1.fill_color, poly1.outline_color)

kml.WriteKmlFile(output_file)    