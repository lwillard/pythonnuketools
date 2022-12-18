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

# use this class to calulate the altitude to detonate a nuke in order
# to optimize the area under a particular PSI footprint radius
class YieldAltitudeOptimizer:
    def __init__(self, max_radius=25000, max_height=5000, radius_interval=100, height_interval=10):
        self.max_radius = max_radius
        self.max_height = max_height
        self.radius_interval = radius_interval
        self.height_interval = height_interval

        # distance/radius intervals
        self.t = np.arange(0.01, self.max_radius, radius_interval)

        # height of detonation intervals
        self.u = np.arange(0, self.max_height, height_interval)

    # for a given bomb yield and desired over-pressure, calculates and returns the optimal detonation height to maximize the radius of the given overpressure
    def optimize_for_overpressure(self, bomb_yield, overpressure):
        arrs = []

        for height_of_burst in self.u:
            ovps = brode_overpressure(bomb_yield, self.t, height_of_burst, 'kT', dunits='m', opunits='psi')   

            # this defines a function that calculates/interpolates the extent of the radius where an overpressure is found for a given yield and height of burst 
            f = interpolate.interp1d(ovps, self.t, bounds_error=False, fill_value=0.0)

            # append to the array
            arrs.append(f(overpressure))

        # find the max radius of the overpressure across all of the heights
        max_radius = max(arrs)

        # find the index of the max radius
        max_index = arrs.index(max_radius)

        # return the value for the index of the height array used to generate the max radius
        return self.u[max_index]

# use this class to calculate overpressure ring radii given a yield (in kt) and altitude of 
# detontation (in meters)
class OverpressureRingCalculator:
    def __init__(self, max_radius=25000, max_height=5000, radius_interval=100, height_interval=10):
        self.max_radius = max_radius
        self.max_height = max_height
        self.radius_interval = radius_interval
        self.height_interval = height_interval

        # distance/radius intervals
        self.t = np.arange(0.01, self.max_radius, radius_interval)

        # height of detonation intervals
        self.u = np.arange(0, self.max_height, height_interval)

    def GetOverpressureRadii(self, bomb_yield, height_of_burst, overpressures):
        ovps = brode_overpressure(bomb_yield, self.t, height_of_burst, 'kT', dunits='m', opunits='psi')     

        f = interpolate.interp1d(ovps, self.t, bounds_error=False, fill_value=0.0)

        return f(overpressures)

class DesignatedGroundZero:
    def __init__(self, latitude, longitude, name, description, target_class, explosion_yield, height_of_burst, unit, launch_vehicle, warhead):
        self.latitude = latitude
        self.longitude = longitude
        self.name = name
        self.description = description
        self.target_class = target_class
        self.explosion_yield = explosion_yield
        self.height_of_burst = height_of_burst
        self.unit = unit
        self.launch_vehicle = launch_vehicle
        self.warhead = warhead

class LaydownFileReader:
    def ReadLaydownFile(self, filename):
        dgzs = []

        with open(filename) as csvDataFile:
            csvReader = csv.reader(csvDataFile)     
           
            n = 0

            for row in csvReader:
                #skip label row
                if n > 0:
                    dgz = DesignatedGroundZero(float(row[0]), float(row[1]), row[2], row[3], row[4], float(row[5]), float(row[6]), row[7], row[8], row[9])
                    dgzs.append(dgz)            

                n = n + 1
        return dgzs

class GeoPolygons:
    # initializes the object with fill color and outline color
    def __init__(self, fill_color, outline_color):            
        self.polys = []
        self.merged_polys = []
        self.fill_color = fill_color
        self.outline_color = outline_color

    # merges overlapping polys into a single poly
    def merge(self):
        self.merged_polys = unary_union(self.polys)

class GeographyUtils: 
    # calculates a point on a great circle given lat & lon, azimuth/bearing (in degrees), and radius (in meters)
    def GetPointOnCircle(lat, lon, azimuth, radius):
        R = 6378100
        d = radius

        lat1=math.radians(lat)
        lon1=math.radians(lon)

        lat2 = math.asin(math.sin(lat1)*math.cos(d/R) + math.cos(lat1)*math.sin(d/R)*math.cos(azimuth))
        lon2 = lon1 + math.atan2(math.sin(azimuth)*math.sin(d/R)*math.cos(lat1), math.cos(d/R)-math.sin(lat1)*math.sin(lat2))

        lat2 = math.degrees(lat2)
        lon2 = math.degrees(lon2)

        return (lat2, lon2)

    # returns a Circle Polygon centered on lat,lon with a radius of x composed of num_of_points on the outer ring of polygon
    def CreateGeoCirclePoly(lat, lon, radius, num_of_points):
        list = []

        for x in range(num_of_points):
            azimuth = ((360.0/num_of_points)*x)*(0.01745329)
            pt = GeographyUtils.GetPointOnCircle(lat, lon, azimuth, radius)

            # key point here - order for shapely/gis objects is LON/LAT not LAT/LON, hence the reversal of the array
            list.append([pt[1], pt[0]])
        
        p = Polygon(list)
        return p    

class KmlWriter:        
    def __init__(self):       
        self.kml = simplekml.Kml()

    def CreatePolys(self, geo_polys, fill_color, outline_color):
        # this test is necessary because sometimes merging the polys will result in a single polygon, and so the the loop iteration will fail as a consequence
        # there is probably a more elegant way to do this, but this hack works for now
        if hasattr(geo_polys, '__iter__'):
            for item in geo_polys:
                poly = self.kml.newpolygon()
                poly.style.polystyle.color = fill_color
                poly.style.polystyle.outline = outline_color

                poly.outerboundaryis.coords = item.exterior.coords
        else:
            poly = self.kml.newpolygon()
            poly.style.polystyle.color = fill_color
            poly.style.polystyle.outline = outline_color

            poly.outerboundaryis.coords = geo_polys.exterior.coords          

    def WriteKmlFile(self, filename):
        self.kml.save(filename)


### Main Loop
#if len(sys.argv) != 3:
#    raise ValueError('Please provide a nuclear laydown map filename and a output filename.')

#laydown_file = sys.argv[1]
#output_file = sys.argv[2]    

laydown_file = "D:/data/dev/PythonNukeTools/test_laydown_file.csv"
output_file = "D:/data/dev/PythonNukeTools/output.kml"

laydown = LaydownFileReader()
dgzs = laydown.ReadLaydownFile(laydown_file)

poly20 = GeoPolygons('ab0000ff', '00202020')
poly5 = GeoPolygons('65007fff', '00202020')
poly2 = GeoPolygons('6519e3ff', '00202020')
poly1 = GeoPolygons('45ababab', '00202020')

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
