#TODO: Download all Berlin @ once. Saveit as shapefile
#TODO: Integrate colors to trafos in graph

#crs = 'EPSG:3035' #Statistical mapping at all scales and other purposes where true area representation is required
import sys
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from shapely.ops import transform
import osmnx as ox
import pandas as pd
import geopandas as gpd
from osmnx.save_load import graph_to_gdfs,gdfs_to_graph
from shapely.geometry import Point,LineString,Polygon,MultiPolygon
from shapely.ops import nearest_points
from sklearn.cluster import KMeans
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.pyplot import figure
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from scipy import spatial
from egoio.db_tables import openstreetmap
from egoio.db_tables import grid
from egoio.tools import db
from sqlalchemy.orm import sessionmaker
import shapely
from shapely.wkb import dumps, loads
import matplotlib.pyplot as plt
from geopandas.tools import sjoin
from shapely.strtree import STRtree
from shapely.ops import split
from functools import partial
import pyproj
import ding0
from collections import Counter
import math
import contextily as ctx
import itertools
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import StrMethodFormatter
import seaborn as sns
import matplotlib as mpl


def import_footprints_area(polygon, to_crs = None, plot = False, save = False, shp_name = 'NoName'):
    """
    Downloads building footprints from OSM and Projects it according its UMT
    :return: Projected GeoPandas DataFrame
    """
    #Import and project footprint area
    if isinstance(place, (Polygon,MultiPolygon)):
        gdf = ox.footprints_from_polygon(polygon)
    else:
        gdf = ox.footprints_from_place(polygon)

    #gdf_proj = ox.project_gdf(gdf,to_crs=to_crs)
    if plot == True:
        fig, ax = ox.plot_shape(gdf_proj)

    if save == True:
        gdf_save = gdf.drop(labels='nodes', axis=1)
        ox.save_gdf_shapefile(gdf_save, shp_name+ '.shp')

    return gdf

def get_street_graph(polygon, plot = False,save = False, shp_name = 'NoName'):
    """
    Downloads Street graph from the Polygon area
    :returns: Networkx MultiDiGraph
    """
    #MultiDiGraph
    if isinstance(polygon,Polygon) or isinstance(polygon,MultiPolygon):
        street_graph = ox.graph_from_polygon(polygon)
    else:
        street_graph = ox.graph_from_place(polygon)
    if plot == True:
        fig, ax = ox.plot_graph(street_graph)
    if save == True:
        ox.save_graph_shapefile(street_graph,filename=shp_name)

    return street_graph

def merge_maps(gdf_build,graph_streets,tr_x,tr_y):
    #TODO:
    # convert trafos in nx nodes (dictionaries) -> add edge
    # connect builduings to streets
    # convert res_gdf into a graph,
    # save df to shp,
    # calc_geo_branches_in_buffer(node, mv_grid, radius, radius_inc, proj) in ding0/tools/geo
    # find_nearest_conn_objects(node_shp, branches, proj, conn_dist_weight, debug, branches_only=False):
    trafos_dict = dict(zip(np.arange(0,len(trafo_posx)),trafo_posx, trafo_posy))

    for i in range(0,len(tr_x)):
        pass

    gdf_street = graph_to_gdfs(graph_streets)
    interesections = gpd.GeoDataFrame(geometry=gdf_street[0]['geometry'])
    streets = gpd.GeoDataFrame(geometry=gdf_street[1]['geometry'])

    #Find nearest point between builidings and streets
    #1. unary union of the gdf_build geomtries
    #pts3 = gdf_build.geometry.unary_union
    ps3 = streets.geometry.unary_union
    build_0 = gdf_build.representative_point().iloc[0,]
    origin,dest = nearest_points(gdf_build.representative_point().iloc[0,], ps3)


    res_gdf = gdfs_to_graph(pd.concat([gdf_build,interesections]),streets)
    ox.plot_shape(res_gdf)
    return res_gdf

def find_mv_clusters_kmeans(gdf_build, plot=False, k =5):
    """
    Applys k-means clustering to the dataset containing
    the repr. points of each building
    k is the number of clusters

    :return: List of shapely points containing the MV/LV Trafo position
    Geodataframe containing building location and label from the kmeans
    """
    #TODO: Get the descition boundaries for the k-means
    #https://github.com/srafay/Machine_Learning_A-Z/blob/master/Part%204%20-%20Clustering/Section%2024%20-%20K-Means%20Clustering/kmeans.py
    #Convert series to numpy array
    x =(np.array(gdf_build.representative_point().x)).reshape(-1,1)
    y =(np.array(gdf_build.representative_point().y)).reshape(-1,1)
    X = np.concatenate((x, y), axis=1)
    X_train, X_test, y_train, y_test = train_test_split(X[:,0], X[:,1], test_size=0.2, random_state=0)

    # Feature Scaling
    sc_X = StandardScaler()
    X_train = sc_X.fit_transform(X_train.reshape(-1,1))
    X_test = sc_X.transform(X_test.reshape(-1,1))
    sc_y = StandardScaler()
    y_train = sc_y.fit_transform(y_train.reshape(-1,1))

    kmeans = KMeans(n_clusters=k, init='k-means++', random_state=42)
    y_kmeans = kmeans.fit_predict(X)

    # Visualising the clusters
    #TODO: Make plotting more general
    if plot == True:
        plt.scatter(X[y_kmeans == 0, 0], X[y_kmeans == 0, 1], s=100, c='red', label='Cluster 1')
        plt.scatter(X[y_kmeans == 1, 0], X[y_kmeans == 1, 1], s=100, c='blue', label='Cluster 2')
        plt.scatter(X[y_kmeans == 2, 0], X[y_kmeans == 2, 1], s=100, c='green', label='Cluster 3')
        plt.scatter(X[y_kmeans == 3, 0], X[y_kmeans == 3, 1], s=100, c='cyan', label='Cluster 4')
        plt.scatter(X[y_kmeans == 4, 0], X[y_kmeans == 4, 1], s=100, c='magenta', label='Cluster 5')
        plt.scatter(kmeans.cluster_centers_[:, 0], kmeans.cluster_centers_[:, 1], s=300, c='yellow', label='Centroids')
        plt.title('Clusters of customers')
        plt.legend()
        plt.show()
    trafo_pos = list(zip(kmeans.cluster_centers_[:, 0], kmeans.cluster_centers_[:, 1]))
    trafo_geo = [shapely.geometry.Point(x) for x in trafo_pos]

    gdf_build['trafo'] = kmeans.labels_

    return trafo_geo, gdf_build

def osm_lu_import():
    """
    Sectors
    1: Residential
    2: Retail
    3: Industrial
    4: Agricultural
    """
    engine = db.connection(readonly=True)
    session = sessionmaker(bind=engine)()
    table = openstreetmap.OsmDeuPolygonUrban
    query = session.query(table.gid, table.sector, table.geom,)
    #TODO: Properly import table.geom (Multipolygons in wkb)
    geom_data = pd.read_sql_query(query.statement, query.session.bind)
    #geom_data = geom_data[0:500]
    #This operation takes too long
    for i, rows in geom_data.iterrows():
        geom_data['geom'][i] = shapely.wkb.loads(str(geom_data['geom'][i]), hex=True)


    geom_data = gpd.GeoDataFrame(geom_data, geometry= geom_data['geom'])
    geom_data_test = geom_data.drop(columns='geom')
    geom_data_test.to_file("osm_landuse.geojson", driver='GeoJSON')
    return geom_data

def find_building_sector(gdf, osm_lu):
    """
    returns a GPD df with the centroids as geometries and the sector they belong to
    """

    buildings.geometry = buildings.buildings.apply(lambda x: x.representative_point())
    #buildings['centroid'] = buildings.representative_point()
    #buildings.geometry = buildings.buildings
    """ 
   if buildings.crs == None: #TODO: Change this superficial fix. Create a general example (Not needed for ding0)
        #buildings_proj = buildings.apply(lambda x: transform(proj1, x.geometry), axis=1)
        buildings_proj = pd.read_csv('./building_proj', header = None)
        buildings_proj.columns = ["index","geometry"]
        buildings_proj['geometry'] = buildings_proj.apply(lambda x: shapely.wkt.loads(x["geometry"]), axis=1)
        buildings.geometry = buildings_proj['geometry']

    """

    sector_table = sjoin(buildings, osm_lu, how='inner', op = 'contains')
    sector_table = sjoin(buildings, osm_lu, how='inner', op='intersects') #This worked

    return sector_table

def calculate_load_per_building(sector,area):
    """
    sector_table: Table containing the centroids and the sector of each building
    gdf_refined: df['building'] contains the shapes of each building

    return: A table containing the Load for every building

    idea: calculate area in gdf_refined, apply function W/m², append that column, do sjoin

    """

    #fixme: Last zu hoch

    if sector == 1:
      return 120 * area # 120W/m² x Area
    elif sector == 2:
        return 125 * area
    elif sector == 3:
        return 150 * area
    elif sector == 4:
        return 150 * area

def gdf_project_to(gdf, proj_to):

    #Pick Correct Projection
    if proj_to == 4326:
        # ETRS (equidistant) to WGS84 (conformal) projection
        proj = partial(
            pyproj.transform,
            pyproj.Proj(init='epsg:3035'),  # source coordinate system
            pyproj.Proj(init='epsg:4326'))  # destination coordinate system
    else:
        proj = partial(
            pyproj.transform,
            pyproj.Proj(init='epsg:4326'),  # source coordinate system
            pyproj.Proj(init='epsg:3035'))

    gdf.geometry = gdf.apply(lambda x: transform(proj, x.geometry), axis=1)

     #Set it
    if proj_to == 4326:
        gdf.crs = {'init' :'epsg:4326'}
    else:
        gdf.crs = {'init': 'epsg:3035'}

def project_to(polygon, proj_to):
    # Pick Correct Projection
    if proj_to == 4326:
        # ETRS (equidistant) to WGS84 (conformal) projection
        proj = partial(
            pyproj.transform,
            pyproj.Proj(init='epsg:3035'),  # source coordinate system
            pyproj.Proj(init='epsg:4326'))  # destination coordinate system
    else:
        proj = partial(
            pyproj.transform,
            pyproj.Proj(init='epsg:4326'),  # source coordinate system
            pyproj.Proj(init='epsg:3035'))

    polygon = transform(proj, polygon)

    # Set it
    if proj_to == 4326:
        polygon._crs = 4326
    else:
        polygon._crs = 3035

def project_nx_graph(nx_graph,crs):
    pass

def find_trafo_connection(trafo_geodata, street_graph, radius_init=0, radius_inc=1e-9, plot=False):
    """
    :param GDF trafo_geo_data: Trafo positions
    :param Nx-Graph street_graph:

    :return: street graph with added trafos
    """

    crossings, streets = ox.graph_to_gdfs(street_graph)
    tree = STRtree(list(streets.geometry))
    nodes = []
    node_connections = []
    street_types = nx.get_edge_attributes(street_graph, 'highway')
    trafo_geodata_new = []
    i = 0  # Id for new trafos

    for trafo in trafo_geodata.geometry:
        radius = radius_init
        branches = []
        while not branches:
            branches = tree.query(trafo.buffer(radius))
            radius += radius_inc
        trafo, trafo_conn = nearest_points(trafo, branches[0])

        c = LineString([trafo, trafo_conn])
        proj_line = shapely.affinity.scale(c, xfact=5.0, yfact=5.0)
        result = split(branches[0], proj_line) #2 Linestrings from split

        trafo_geodata_new.append(trafo_conn)
        #Get the 2 boundary nodes from overlapping Linestring.
        node_a = [n for n, data in street_graph.nodes(data=True) if
                  data['x'] == branches[0].boundary[0].x and data['y'] == branches[0].boundary[0].y][0]
        coord_na = street_graph.nodes[node_a]['geometry']
        node_b = [n for n, data in street_graph.nodes(data=True) if
                  data['x'] == branches[0].boundary[1].x and data['y'] == branches[0].boundary[1].y][0]
        coord_nb = street_graph.nodes[node_b]['geometry']


        #Instert highway data into trafo_conn node
        trafo_conn_street_type = street_graph.get_edge_data(node_a, node_b)[0]['highway'] #0 is default
        n_conn = street_graph.number_of_edges(node_a, node_b) #Can be useful

        #Add Node to Graph, create trafo identifier in every node
        street_graph.add_node(i, **{'y': trafo_conn.y, 'x': trafo_conn.x, 'osmid': i,
                                        'street_type': trafo_conn_street_type, 'trafo':True, 'mv_station':False})
        # Connect nodes with trafo_conn (Directed Graph)
        street_graph.add_edge(i, node_a,
                              **{'length':coord_na.distance(trafo_conn),'geometry':result[0], 'highway':trafo_conn_street_type})
        street_graph.add_edge(node_a, i,
                              **{'length':coord_na.distance(trafo_conn),'geometry':result[0], 'highway':trafo_conn_street_type})
        street_graph.add_edge(i, node_b,
                              **{'length':coord_nb.distance(trafo_conn),'geometry':result[1], 'highway':trafo_conn_street_type})
        street_graph.add_edge(node_b, i,
                              **{'length':coord_nb.distance(trafo_conn),'geometry':result[1], 'highway':trafo_conn_street_type})
        """"""
        #Erase old edges
        while street_graph.has_edge(node_a,node_b):
            street_graph.remove_edges_from([(node_a,node_b)])
        while street_graph.has_edge(node_b,node_a):
            street_graph.remove_edges_from(([(node_b,node_a)]))

        i += 1

    trafo_geodata_new = gpd.GeoDataFrame(geometry=trafo_geodata_new)
    trafo_geodata_new.crs = crossings.crs
    full_map_gdf_bef = streets.append(crossings)

    nodes = crossings.append(trafo_geodata_new) #Crossings + Trafos to enable graph ops
    nodes.gdf_name = 'cross_trafo_nodes'
    full_map_gdf_after = streets.append(nodes)

    if plot == True: #Plots trafos in red over old network
        ax = plot_gdf(full_map_gdf_bef)
        plot_gdf(trafo_geodata_new, color='red',ax=plt.gca())

    return street_graph, trafo_geodata_new

def find_stat_connection(station_geodata, street_graph,radius_init=0, radius_inc=1e-6, plot=False):
    """
    :param GDF trafo_geo_data: HV/MV Station geodata
    :param Nx-Graph street_graph:

    :return: street graph with added trafos
    """

    crossings, streets = ox.graph_to_gdfs(street_graph)
    tree = STRtree(list(streets.geometry))
    nodes = []
    node_connections = []
    street_types = nx.get_edge_attributes(street_graph, 'highway')
    i = mv_station_gdf['subst_id'].iloc[0]
    station_geodata_new = []


    for trafo in station_geodata.geometry:
        radius = radius_init
        branches = []
        while not branches:
            branches = tree.query(trafo.buffer(radius))
            radius += radius_inc
        trafo, trafo_conn = nearest_points(trafo, branches[0])
        station_geodata_new.append(trafo_conn)

        #Get the 2 boundary nodes from overlapping Linestring.
        node_a = [n for n, data in street_graph.nodes(data=True) if
                  data['x'] == branches[0].boundary[0].x and data['y'] == branches[0].boundary[0].y][0]
        coord_na = street_graph.nodes[node_a]['geometry']
        node_b = [n for n, data in street_graph.nodes(data=True) if
                  data['x'] == branches[0].boundary[1].x and data['y'] == branches[0].boundary[1].y][0]
        coord_nb = street_graph.nodes[node_b]['geometry']


        #Instert highway data into trafo_conn node
        trafo_conn_street_type = street_graph.get_edge_data(node_a, node_b)[0]['highway'] #0 is default
        n_conn = street_graph.number_of_edges(node_a, node_b) #Can be useful

        #Add Node to Graph, create trafo identifier in every node
        street_graph.add_node(i, **{'y':trafo_conn.y,'x':trafo_conn.x,'osmid':i,
                                    'street_type':trafo_conn_street_type, 'trafo':True, 'mv_station':True})

        # Connect nodes with trafo_conn (Directed Graph)
        street_graph.add_edge(i, node_a,
                              **{'length':coord_na.distance(trafo_conn),'geometry':LineString([trafo_conn,coord_na]), 'highway':trafo_conn_street_type})
        street_graph.add_edge(node_a, i,
                              **{'length':coord_na.distance(trafo_conn),'geometry':LineString([trafo_conn,coord_na]), 'highway':trafo_conn_street_type})
        street_graph.add_edge(i, node_b,
                              **{'length':coord_nb.distance(trafo_conn),'geometry':LineString([trafo_conn,coord_nb]), 'highway':trafo_conn_street_type})
        street_graph.add_edge(node_b, i,
                              **{'length':coord_nb.distance(trafo_conn),'geometry':LineString([trafo_conn,coord_nb]), 'highway':trafo_conn_street_type})
        """"""
        #Erase old edges
        while street_graph.has_edge(node_a,node_b):
            street_graph.remove_edges_from([(node_a,node_b)])
        while street_graph.has_edge(node_b,node_a):
            street_graph.remove_edges_from(([(node_b,node_a)]))

        i += 1

    station_geodata_new = gpd.GeoDataFrame(geometry=station_geodata_new)
    station_geodata_new.crs = crossings.crs
    full_map_gdf_bef = streets.append(crossings)

    nodes = crossings.append(station_geodata_new) #Crossings + Trafos to enable graph ops
    nodes.gdf_name = 'cross_trafo_nodes'
    full_map_gdf_after = streets.append(nodes)

    if plot == True: #Plots trafos in red over old network
        ax = plot_gdf(full_map_gdf_bef)
        plot_gdf(station_geodata_new, color='red',ax=plt.gca())

    return street_graph,station_geodata_new

def reduce_street_graph(street_graph, rf = 1, plot=False):
    """
    Converts graph to undirected weighted graph

    Reduces the street graph to only essential roads using one of the following 2 methods
    1) Progressively reduce the graph by removing streets uncommon streets for routing
        Repeat until the graph is not connected anymore. Problem: After the first filtering the graph is not complete anymore

    2) Reduce the graph by applying Dijsktra's shortest path between every node pair for the transformers
    (Only possible after positioning of the transformers)

    street_graph: Reduce Networkx graph

    :return: 1 or 2 Street graphs containing only certain street types (Depending on the filtering method)
    """

    street_graph_un = street_graph.to_undirected()
    #street_graph_un.remove_edges_from(list(nx.selfloop_edges(street_graph_un)))
    edges_weight = [(u, v, e['length']) for u, v, e in list(street_graph_un.edges(data=True))]

    # weight_tuples = [(u, v, d['weight']) for (u, v, d) in street_graph_un.edges(data=True) if d['weight'] > 0]
    # Apparently this does'nt work on MultiGraphs

    for elem in edges_weight:
        street_graph_un[elem[0]][elem[1]][0]["weight"] = elem[2]  # Insert Weights in the Basis-graph (Multigraph)

    pos_tuples = dict([(n[0], (n[1]['x'], n[1]['y'])) for n in street_graph_un.nodes(data=True)]) #Node nr: lat, long
    #street_graph_un.add_weighted_edges_from(edges_weight)

    if rf == 1:
    #Approach 1: Convert digraph to graph, filter self loops, insert lenghts as weight
        filters1 = ['trunk','primary','secondary','tertiary','residential','unclassified',
                    'trunk_link', 'primary_link','secondary_link','tertiary_link','living_street', 'service',
                    'road']

        i=0
        while nx.is_connected(street_graph_un):
            selected_edges = [(u, v) for u, v, e in street_graph_un.edges(data=True) if e['highway'] in filters1[-i-1]]
            nbunch = [u for u, v, e in street_graph_un.edges(data=True) if e['highway'] in filters1]
            street_graph_un = street_graph_un.subgraph(nbunch).copy()

    elif rf==2:
        #Dijsktra
        trafo_list = [node for node, data in street_graph_un.nodes(data=True) if data['trafo'] == True]
        trafo_pairs = []
        paths =[] #Vainilla Dijsktra
        length = []
        for tuple in list(itertools.combinations(trafo_list, 2)): #Combinations of Trafo-pairs
            trafo_pairs.append(tuple)
            paths.append(nx.dijkstra_path(street_graph_un,tuple[0],tuple[1]))
            length.append(nx.dijkstra_path_length(street_graph_un,tuple[0],tuple[1]))



        #Find set of nodes in shortest ways. Filter Graph
        shortest_ways = list(zip(list(itertools.combinations(trafo_list, 2)), paths, length)) #Pair, way, lenght
        list_of_lists = [e[1] for e in shortest_ways]  # List of paths and trafos
        flattened_list = list(set([y for x in list_of_lists for y in x])) #List of all nodes contained in the paths
        street_graph_dijsktra = street_graph_un.subgraph(flattened_list).copy()
        return street_graph_dijsktra

    elif rf==3:
        #Johnhson: Find all shortest paths between nodes
        pass

    # Plot
    if plot == True:
        plot_graph(street_graph_un)

    pass

def peak_load_per_trafo(building_loads,k):
    """
    :param building_loads: geopandas dataframe: Building load information and labels from kmeans
           k: int: Number of trafos/Clusters
    :return: list of sum of loads per trafo
    """
    trafo_leistung = []
    for i in range(0,k):
        try:
            trafo = building_loads['trafo'] == i
            trafo_loads = building_loads[trafo]
            trafo_leistung.append(trafo_loads['load'].sum(axis=0))
            print('Transformer '+str(i)+ ' has ' + '{:.2e}'.format(trafo_leistung[i]) + 'kVA of power')
        except:
            trafo = building_loads['trafo'] == i
            trafo_loads = building_loads[trafo]
            filter = trafo_loads['load'] != ''
            trafo_loads = trafo_loads[filter]
            trafo_leistung.append(trafo_loads['load'].sum(axis=0))
            print('There is no load for building Idx'+
                  str(int([building_loads[building_loads['load'] == '']['index_right']][0]))+
                  ' supplied by Transfomer'+str(i))

    return trafo_leistung

def find_n_trafos(gdf):
    """
    :param GeoDataFrame: Building load information
    :return: int: Number of stations for that MVGD
    """
    # ~10 Trafos
    total_load = gdf['load'].sum(axis=0)
    n_trafos = math.ceil(total_load/1000) #1000kVA per Trafo
    return n_trafos

def test_street_completeness():
    #https: // wiki.openstreetmap.org / wiki / Key: highway
    place = 'Tempelhof, Berlin, Germany'
    G = get_street_graph(place)
    lista = []
    filters = ['trunk','primary_link','secondary_link','tertiary_link','residential',
               'primary','secondary','tertiary','living_street', 'service',
               'road', 'unclassified']
    selected_edges = [(u, v) for u, v, e in G.edges(data=True) if e['highway'] in filters]
    FG = nx.Graph(selected_edges)
    H = G.subgraph(FG.nodes())
    #H = G.edge_subgraph(selected_edges)
    """
    fig,ax = ox.plot_graph(street_graph)
    for i in range(0, len(list(G.edges))):
        lista.append(list(G.edges(data=True))[i][2]['highway'])
    lista
    """

def plot(poly,c=False,fig=1):
    """
    Tool for plottin shapely polygons and Multipolygons
    c: str: color for plotting
    """
    if type(poly) == Polygon:
        x, y = poly.exterior.xy
        if c == True:
            ax = plt.gca()
            ax.fill(x,y,'b')
        plt.plot(x, y)

    else:
        for singlepoly in poly:
            x, y = singlepoly.exterior.xy
            if c == True:
                ax = plt.gca()
                ax.fill(x, y, 'b')
            fig = plt.figure(fig)
            plt.plot(x, y, c=c, lw=1, alpha=1)

def street_lenght(geodataframe):
    df_counter = pd.DataFrame()
    i = 0
    errors_at = []
    total_n_mvgd = geodataframe.shape[0]
    #30-35 secs per geoseries
    for index,mvgds in geodataframe.iterrows():
        try:
            if not mvgds.geometry.is_valid:
                mvgds.geometry = mvgds.geometry.buffer(0e-16) #Takes invalid overlapping lines of multipolygons away from one another by buffer

            G = get_street_graph(mvgds.geometry)
            selected_edges = [e['highway'] for u, v, e in G.edges(data=True)]

            tl = [(e['highway'], e['length']) for u, v, e in G.edges(data=True)] #[(tipo, long)]
            cat_set = set([i for i in [elem[0] for elem in tl] if not isinstance(i, list)]) #List of Categories in the set
            cat_dict = dict.fromkeys(cat_set) #Dictionary of way's catergories
            #Filling the dict.
            for i in tl:
                category = i[0]  # key
                if not isinstance(category, list):
                    cat_dict[category] = + i[1]  # add lenght value
                elif isinstance(category, list): #If more than one category
                    for elem in category:
                        cat_dict[elem] = + i[1]

            df_counter[str(index)] = pd.Series(cat_dict,name=index)
        except:
            errors_at.append(index)
            print("Unexpected error:", sys.exc_info()[0], " at MVGD ",str(index))
            err_ratio = (len(errors_at)/total_n_mvgd)*100
            print("The valid to invalid ratio is ", err_ratio)

    total_batch_err = (len(errors_at)/total_n_mvgd)*100
    df_counter = df_counter.fillna(0)
    total_sum = df_counter.sum(axis=1)

    #Create Bar Plot
    #https://scentellegher.github.io/visualization/2018/10/10/beautiful-bar-plots-matplotlib.html
    # set font
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = 'Helvetica'

    # set the style of the axes and the text color
    plt.rcParams['axes.edgecolor'] = '#333F4B'
    plt.rcParams['axes.linewidth'] = 0.8
    plt.rcParams['xtick.color'] = '#333F4B'
    plt.rcParams['ytick.color'] = '#333F4B'
    plt.rcParams['text.color'] = '#333F4B'

    df = total_sum.sort_values()

    # we first need a numeric placeholder for the y axis
    my_range = list(range(1, len(df.index) + 1))
    fig, ax = plt.subplots(figsize=(5, 3.5))

    # create for each expense type an horizontal line that starts at x = 0 with the length
    # represented by the specific expense percentage value.
    plt.hlines(y=my_range, xmin=0, xmax=df, color='#007ACC', alpha=0.2, linewidth=5)

    # create for each expense type a dot at the level of the expense percentage value
    plt.plot(df, my_range, "o", markersize=5, color='#007ACC', alpha=0.6)

    # set labels
    ax.set_xlabel('Lenght [km]', fontsize=15, fontweight='black', color='#333F4B')
    ax.set_ylabel('')

    # set axis
    ax.tick_params(axis='both', which='major', labelsize=12)
    plt.yticks(my_range, df.index)

    # add an horizonal label for the y axis
    fig.text(-0.23, 0.96, 'Ways lenghts', fontsize=15, fontweight='black', color='#333F4B')

    # change the style of the axis spines
    ax.spines['top'].set_color('none')
    ax.spines['right'].set_color('none')
    ax.spines['left'].set_smart_bounds(True)
    ax.spines['bottom'].set_smart_bounds(True)

    # set the spines position
    ax.spines['bottom'].set_position(('axes', -0.04))
    ax.spines['left'].set_position(('axes', 0.015))

    plt.savefig('Berlin_ways.png', dpi=300, bbox_inches='tight')
    df_counter.to_csv('./df_street_count')


    """
    df_counters = pd.DataFrame.from_dict(street_collection, orient='index')
    
    
    count_table_roads = pd.DataFrame(columns=["motorway","trunk","primary","secondary","tertiary","unclassified",
                                        "residential","total"])
    count_table_link_roads = pd.DataFrame(columns=["motorway_link", "trunk_link","primary_link","secondary_link",
                                        "tertiary_link","total"])
    count_table_special = pd.DataFrame(columns=["living_street","service","pedestrian","track","bus_guideway","escape",
                                                "raceway","road","total"])
    count_table_paths = pd.DataFrame(columns=["footway","bridleway","steps","corridor","path","total"])
    #for i in MVGD
    G = get_street_graph(place)
    #street type list
    stl = [e['highway'] for u, v, e in G.edges(data=True)]
    count_table_roads.iloc[-1] = [stl.]
    count_table_link_roads.iloc[-1]
    count_table_special.iloc[-1]
    count_table_paths.iloc[-1]
    """

def read_street_count(fil=False):
    df_sum1 = pd.read_csv('./df_street_count').sum(axis=0)
    total = df_sum1[1:].sum()
    if fil == True:
        df1 = pd.read_csv('./df_street_count').set_index('Unnamed: 0')
        df1 = df1.drop(['footway', 'cycleway', 'path', 'steps','unclassified'], axis=0)
        df_sum1 = df1.sum(axis=0)
        total = df_sum1[1:].sum()
    return total

def street_details_mvgd(boundaries):
    """
    boundaries: Shapely Polygon of a MVGD

    :returns: pandasdf with categories as columns and streets (edges) as entries
    """

    if not boundaries.is_valid:
        boundaries.geometry = boundaries.geometry.buffer(
            0e-16)  # Takes invalid overlapping lines of multipolygons away from one another by buffer

    if boundaries._crs == 3035:
        project_to(boundaries,4326)

    G = get_street_graph(boundaries.geometry)
    gdf_street = graph_to_gdfs(G)
    df_street_data = pd.DataFrame(gdf_street[1])
    full_df = pd.DataFrame(gdf_street[1])
    filtered = full_df.filter(items=['name', 'highway', 'geometry', 'lenght', 'osmid'])
    return filtered

def plot_gdf(df, trafos = False, color ='blue', ax=None):
    df2 = df.to_crs(epsg=3857)
    ax = df2.plot(figsize=(9, 9), alpha=0.5, edgecolor='k',color=color,ax=ax)
    ctx.add_basemap(ax)
    if trafos == True:
        ax2 = df2.plot(ax=ax, color='red')
    return ax

def plot_graph(nx_graph,color ='blue', ax=None):
    crossings, streets = ox.graph_to_gdfs(nx_graph)
    df = streets.append(crossings)
    df2 = df.to_crs(epsg=3857)
    df2['trafo'] = df2['trafo'].fillna(False)
    ax = df2.plot(figsize=(9, 9), alpha=0.5, edgecolor='k',ax=ax,column=df2['trafo'])
    ctx.add_basemap(ax)
    return ax

def plot_gdf_trafos(nx_graph, trafos_gdf, color ='blue', ax=None):
    """

    :param nx_street: street nx-graph
    :param trafos_gdf:gdf only with trafos
    :param color:
    :param ax:
    :return:
    """
    #Street
    crossings, streets = ox.graph_to_gdfs(nx_graph)
    df = streets.append(crossings)
    df2 = df.to_crs(epsg=3857)
    ax1 = df2.plot(figsize=(9, 9), alpha=0.5, edgecolor='k',color=color,ax=ax)
    ctx.add_basemap(ax1)
    #Trafos
    df3 = trafos_gdf.to_crs(epsg=3857)
    ax = df3.plot(figsize=(9, 9), alpha=0.5, edgecolor='k',color='red',ax=ax1)
    return ax

def load_per_sector(sector_table):
    sector_table['area'] = sector_table.area
    sector_table['load'] = ''
    for i in range(0,sector_table.shape[0]):
        if sector_table['sector'].iloc[i,] == 1:
            sector_table['load'].iloc[i,] = 120 * sector_table.iloc[i,]['area']
        elif sector_table['sector'].iloc[i,] == 2:
            sector_table['load'].iloc[i,]  = 125 * sector_table.iloc[i,]['area']
        elif sector_table['sector'].iloc[i,] == 3:
            sector_table['load'].iloc[i,]  = 150 * sector_table.iloc[i,]['area']
        elif sector_table['sector'].iloc[i,] == 4:
            sector_table['load'].iloc[i,]  = 150 * sector_table.iloc[i,]['area']

    return sector_table
'''
TESTS
test_street_completeness()
place = 'Tempelhof, Berlin, Germany'
'''

def remove_area_outliers(gdf):
    q = gdf['area'].quantile(0.99)
    gdf = gdf[gdf['area'] < q]
    gdf_outl = gdf[gdf['area'] > q]
    return gdf, gdf_outl

def plot_area_distr(gdf, ctx_plot=False): #ctx. Map with contextility (slow)
    fig, axs  = plt.subplots(2, 2)
    axs[0,0].set_xlim(gdf['area'].min(axis=0),gdf['area'].max(axis=0))
    axs[0,0].set_title('Area [m²]')
    axs[0,1].set_xlim(gdf['load'].min(axis=0), gdf['load'].max(axis=0))
    axs[0,1].set_title('Load [kW]')
    fig.suptitle('Area and load distributions')
    axs[0,0].hist(gdf['area'],bins=10)
    axs[0,1].hist(gdf['load'],bins=10)
    sns.boxplot(gdf['area'], ax=axs[1, 0])
    sns.boxplot(gdf['load'], ax=axs[1, 1])
    if ctx_plot == True:
        df2 = gdf.to_crs(epsg=3857)
        ax = df2.plot(gdf['area'],legend=True)
        ctx.add_basemap(ax)

def averages(berlin_mvgds,local_lu):
    """
    Caluculates Avg_area and average load
    :param berlin_mvgds:
    :param local_lu:
    :return:
    """
    avg_load = [] #kW
    avg_area = [] #m²
    for i in range(66,berlin_mvgds.shape[0]-1): #Needs to be done in parts. Otherwise it overloads the machine
        try:
            place = berlin_mvgds.iloc[i, :].geometry.buffer(0)
            gdf = import_footprints_area(place)
            gdf = gdf.reset_index().rename(columns={'index': 'osmidx'})
            gdf = gdf[~(gdf.geometry.isna())]  # Remove nan
            gdf.geometry = [list(x)[0] if isinstance(x, MultiPolygon) else x for x in
                            gdf.geometry]  # Extract first layer of Multipolygons
            # Remove unsuported layers for Multipolygons
            gdf_project_to(gdf, 3035)
            gdf_sector_table = sjoin(gdf, local_lu, how='inner', op='intersects') \
                .filter(['osmidx', 'building', 'geometry', 'subst_id', 'sector']).drop_duplicates(
                'osmidx')  # Contains sectors values for every building
            gdf_sector_table['centroids'] = gdf_sector_table.apply(lambda x: x.geometry.centroid, axis=1)
            gdf_sector_table['area'] = gdf_sector_table.apply(lambda x: x.geometry.area, axis=1)
            gdf_sector_table['load'] = gdf_sector_table.apply(
                lambda x: calculate_load_per_building(x['sector'], x['area']), axis=1) / 1000
            avg_area.append(gdf_sector_table['area'].mean())
            avg_load.append(gdf_sector_table['load'].mean())
        except:
            print("Unexpected error:", sys.exc_info()[0], ' at MVGD ', i)

    return avg_area,avg_load

def plot_averages_berlin():
    area_and_load = pd.read_csv('0_66MVGDS_Berlin.csv').T
    area_and_load = area_and_load.rename(columns={0:'avg_load',1:'avg_area'}).drop('Unnamed: 0')
    area_and_load2 = pd.read_csv('66_117MVGDS_Berlin.csv').T
    area_and_load2 = area_and_load2.rename(columns={0:'avg_load',1:'avg_area'}).drop('Unnamed: 0')
    gdf = area_and_load.append(area_and_load2)

    mpl.style.use('seaborn')
    fig, axs = plt.subplots(2, 2)
    axs[0, 0].hist(gdf['avg_area'], bins=10)
    axs[0, 0].set_xlim(gdf['avg_area'].min(axis=0), gdf['avg_area'].max(axis=0))
    axs[0, 0].set_title('Area distribution')
    axs[0, 0].set_xlabel('Area [m²]')
    axs[0, 0].set_ylabel('Frequency')

    axs[0, 1].hist(gdf['avg_load'], bins=10)
    axs[0, 1].set_xlim(gdf['avg_load'].min(axis=0), gdf['avg_load'].max(axis=0))
    axs[0, 1].set_title('Load distribution')
    axs[0, 1].set_xlabel('Load [kW]')
    axs[0, 1].set_ylabel('Frequency')

    fig.suptitle('Area and load distributions in Berlin')

    sns.boxplot(gdf['avg_area'], ax=axs[1, 0])
    axs[1, 0].set_xlabel('Area [m²]')

    sns.boxplot(gdf['avg_load'], ax=axs[1, 1])
    axs[1, 1].set_xlabel('Load [kW]')

def import_hv_mv():
    #Import 'v0.4.5'
    engine = db.connection(readonly=True)
    session = sessionmaker(bind=engine)()
    table = grid.EgoDpHvmvSubstation
    query = session.query(table.version, table.subst_id, table.lon, table.lat, table.point)
    #TODO: Properly import table.geom (Multipolygons in wkb)
    hv_mv_stations = pd.read_sql_query(query.statement, query.session.bind)
    hv_mv_stations = hv_mv_stations[hv_mv_stations['version'] == "v0.4.5"]
    #This operation takes too long
    for i, rows in hv_mv_stations.iterrows():
        hv_mv_stations['point'][i] = shapely.wkb.loads(str(hv_mv_stations['point'][i]), hex=True)

    geom_data = gpd.GeoDataFrame(hv_mv_stations, geometry= hv_mv_stations['point'])
    geom_data_test = geom_data.drop('point')
    geom_data_test.to_file("hv_mv_stations.geojson", driver='GeoJSON')

def remove_stubs (reduced_graph): #TODO: Remove lonely neighbors
    ons = [n[0] for n in reduced_graph.nodes(data=True) if n[1]['trafo'] == True and n[1]['mv_station'] == False]
    stiche = [n for n in ons if len(reduced_graph[n].keys()) == 1]
    graph_no_st = reduced_graph.copy()
    graph_no_st.remove_nodes_from(stiche)
    return graph_no_st



#-1) Importing the data
"""
Unused Importations used for testing and creating the datasets
 
#deutschland_mvgds = gpd.read_file("/home/local/RL-INSTITUT/santiago.infantino/Desktop/BA Bachelorarbeit/BA_git_repo/MVGD.geojson")[['subst_id','geometry']]
berlin_mvgds = gpd.read_file("/home/local/RL-INSTITUT/santiago.infantino/Desktop/BA Bachelorarbeit/BA_git_repo/MVGD_in_Berlin.geojson")[['subst_id','geometry']]
#test = berlin_mvgds.iloc[0:3]
gdf_project_to(berlin_mvgds,4326)
#count_street_types(berlin_mvgds)
#df_ber_street_data = street_details_mvgd(test.iloc[1].geometry)

berlin_mvgds.geometry = berlin_mvgds.geometry.buffer(0e-16)
polygon = berlin_mvgds.geometry.unary_union
big_berlin = gpd.GeoDataFrame(geometry=[polygon], crs=berlin_mvgds.crs)


gdf = import_footprints_area(place)
gdf = gdf.filter(['type','geometry'])
gdf['buildings'] = gdf.geometry #Used to store the Polygons. Needed after sjoin with
gdf_project_to(gdf,3035)
gdf.to_csv('./berlin_footprints_test1')
nx.read_gpickle('./street_graph_test1')
"""

#0) Compute sector_table (Computationally expensive)
berlin_mvgds = gpd.read_file("/home/local/RL-INSTITUT/santiago.infantino/Desktop/BA Bachelorarbeit/BA_git_repo/MVGD_in_Berlin.geojson")[['subst_id','geometry']]

"""
Unused Imports summed up in sector_table_berlin.shp and hv_mv_stations_berlin.shp

osm_lu = gpd.read_file("/home/local/RL-INSTITUT/santiago.infantino/Desktop/BA Bachelorarbeit/BA_git_repo/osm_landuse.geojson")
berlin_mvgds.geometry = berlin_mvgds.geometry.buffer(-0.5) #Tidy the polygon to avoid contact to other polygons on the borders
sector_table = sjoin(berlin_mvgds, osm_lu, how='inner', op='intersects')
sector_table.to_file("./sector_table_berlin.shp")
hv_mv_stations = gpd.read_file("/home/local/RL-INSTITUT/santiago.infantino/Desktop/BA Bachelorarbeit/BA_git_repo/hv_mv_stations.geojson")
gdf_project_to(hv_mv_stations,3035)
hv_mv_berlin = sjoin(hv_mv_stations, berlin_mvgds, op='within')
hv_mv_berlin = hv_mv_berlin.rename(columns={'subst_id_left':'subst_id'}).drop(['index_right','subst_id_right'],axis=1)
hv_mv_berlin.to_file('./hv_mv_stations_berlin.shp') #crs 3035
"""

#1) Import Geometries
hv_mv_berlin = gpd.read_file('./hv_mv_stations_berlin.shp')
local_lu= gpd.read_file("./sector_table_berlin.shp")
berlin_mvgds.geometry = berlin_mvgds.geometry.buffer(0e-16)
gdf_project_to(berlin_mvgds,4326)
place = berlin_mvgds.iloc[1,:].geometry.buffer(0)
gdf = import_footprints_area(place) #Works only with crs 4236 and previous buffer (Buildin Footprints)

#Clean the data
def clean_data(gdf):
    """
    Cleaning procedures of Data
    :param gdf: GeopandasDataframe containing builing footprints
    :return gdf_sector_table: Cleaned gdf containing builing footprints + sector labels
    """
    gdf = gdf.reset_index().rename(columns={'index': 'osmidx'})
    gdf = gdf[~(gdf.geometry.isna())]  # Remove nan
    gdf.geometry = [list(x)[0] if isinstance(x, MultiPolygon) else x for x in
                    gdf.geometry]  # Extract first layer of Multipolygons
    # Remove uns_validsuported layers for Multipolygons
    gdf_project_to(gdf, 3035)
    # gdf_sector_table contains buildings footprints + the corresponding sectors
    gdf_sector_table = sjoin(gdf, local_lu, how='inner', op='intersects') \
        .filter(['osmidx', 'building', 'geometry', 'subst_id', 'sector']).drop_duplicates(
        'osmidx')  # Contains sectors values for every building
    gdf_sector_table['centroids'] = gdf_sector_table.apply(lambda x: x.geometry.centroid, axis=1)
    gdf_sector_table['area'] = gdf_sector_table.apply(lambda x: x.geometry.area, axis=1)
    gdf_sector_table['load'] = gdf_sector_table.apply(lambda x: calculate_load_per_building(x['sector'], x['area']),
                                                      axis=1) / 1000  # Umstelle auf kW

    return gdf_sector_table

gdf_sector_table = clean_data(gdf)

#Load and area distributions. Search for outliers
def load_area_stats(gdf_sector_table):

    plot_area_distr(gdf_sector_table,ctx_plot=False)
    gdf_sector_table, gdf_outl = remove_area_outliers(gdf_sector_table)
    plot_area_distr(gdf_sector_table)

#Filter the correct hv_mv station out
def filter_hv_mv_station(place,hv_mv_berlin):
    """
    :param place: Shapely Polygon with the boundaries of the city's disctric
    :param hv_mv_berlin: GPD containing hv_mv_stat
    :return:
    """

    disctrict_gdf = gpd.GeoDataFrame(geometry=[place])
    gdf_project_to(disctrict_gdf,3035)
    hv_mv_stat = sjoin(hv_mv_berlin,disctrict_gdf,op='within')

    return hv_mv_stat

mv_station_gdf = filter_hv_mv_station(place,hv_mv_berlin)
gdf_project_to(mv_station_gdf,4326)

#Find trafo poistions and load
def trafo_pos_and_load(gdf_sector_table):

    n_trafos = find_n_trafos(gdf_sector_table) #Too many/Too few trafos. Why?
    trafo_pos, building_loads = find_mv_clusters_kmeans(gdf_sector_table,plot=False,k=10) #The Pd_dt gets column Trafo
    trafo_leistung = peak_load_per_trafo(building_loads,20)
    trafo_geodata = gpd.GeoDataFrame(geometry=trafo_pos)
    gdf_project_to(trafo_geodata,4326)

    return trafo_geodata

trafo_geodata = trafo_pos_and_load(gdf_sector_table)

#Append trafos to street graph
def append_trafos(place,trafo_geodata, mv_station):

    #map_plot_graph(street_graph)
    street_graph = get_street_graph(polygon=place.buffer(0e-16)) #Import nx graph
    street_gdf = ox.graph_to_gdfs(street_graph)[1][ox.graph_to_gdfs(street_graph)[1]['highway'] != 'footway'] #Filter away footways
    crossings_gdf = ox.graph_to_gdfs(street_graph)[0] #Convert crossings to Gdf for further manipulation
    street_graph = ox.gdfs_to_graph(crossings_gdf,street_gdf) #Recreate filtered Nx Graph

    street_graph.remove_nodes_from(list(nx.isolates(street_graph))) #Remove isolated nodes (i.e. crossings of pathways)
    nx.set_node_attributes(street_graph, False, 'trafo')
    street_graph_trafos, trafo_conn_gdf= find_trafo_connection(trafo_geodata,street_graph) #Finds positions of trafos. Returns nx and gdf

    return street_graph_trafos,trafo_conn_gdf

street_graph_trafos,trafo_conn_gdf = append_trafos(place,trafo_geodata,mv_station_gdf)

#Reduce the Graph, Include hv_mv_station, Route the Rings
street_graph_station, station_conn_gdf = find_stat_connection(mv_station_gdf,street_graph_trafos,radius_inc=1e-6)
reduced_graph = reduce_street_graph(street_graph_station, rf = 2, plot=False)
reduced_graph2 = remove_stubs(reduced_graph) #Removes stubs (Smaller Trafos that aren'nt included in the ring)
hola ='hello'



##############Trash
place = 'Tempelhof, Berlin, Germany'
#import_footprints_area(place)

#TODO: Implement OSM_LU in Ding0
#osm_lu_import()

#gdf_refined = gpd.GeoDataFrame(geometry=gdf.geometry)
#gdf_refined['buildings'] = gdf.geometry #Used to store the Polygons. Needed after sjoin with

#edges = gpd.read_file("data/streetgraphs/edges/edges.shp")
#nodes = gpd.read_file("data/streetgraphs/nodes/nodes.shp")
#G = nx.read_shp('test.shp')

def find_mv_clusters_kd_tree(gdf):
    # I create the Tree from my list of point
    """
    zipped = list(zip(gdf.geometry.representative_point().x, gdf.geometry.representative_point().y))
    kdtree = spatial.KDTree(zipped)   # I calculate the nearest neighbours and their distance
    neigh = kdtree.query(zipped, k=8) # tuple containing a matrix with neibors on same column
    neigh[1][i,1]
    kdtree.data[neigh[1][1, 1]]
    hola = 'papa'
"""
    centroids = gdf['geometry'].apply(lambda g:[g.centroid.x,g.centroid.y]).tolist()# I create the Tree from my list of point
    kdtree = spatial.KDTree(centroids)# I calculate the nearest neighbours and their distance
    neigh = kdtree.query(centroids, k=8)

