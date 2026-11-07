import numpy as np
import xml.etree.ElementTree as ET

NS = {'k':'http://www.opengis.net/kml/2.2'}
LON0, LAT0 = -3.5842469378204105, 40.617111297108821
R_T = 6378388.0

def read_kml_paths(path):
    '''Return {path_name: arra(N,2) with columns [lon,lat] in deg}'''
    root = ET.parse(path).getroot()
    paths = {}
    for pm in root.iter('{http://www.opengis.net/kml/2.2}Placemark'):
        name = pm.find('k:name', NS).text
        text = pm.find('.//k:coordinates', NS).text
        coords = np.array([[float(c) for c in l.split(',')[:2]] for l in text.split()])
        paths[name] = coords
    return paths

def lonlat_to_xy(lon, lat):
    '''Convert lon,lat in deg to x,y in m'''
    lon, lat = np.asarray(lon), np.asarray(lat)
    x = R_T * np.radians(lon - LON0) * np.cos(np.radians(LAT0))
    y = R_T * np.radians(lat - LAT0)
    return x, y