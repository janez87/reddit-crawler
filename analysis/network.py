from pymongo import MongoClient
import json
import numpy as np
import textrazor
import datetime
import pytz
import sys
import networkx as nx 
import matplotlib.pyplot as plt
from sklearn.cluster import SpectralClustering
from sklearn import metrics

sys.path.append("../")
from configuration import configuration

client = MongoClient(
    configuration.DB_HOST, configuration.DB_PORT)

db = client[configuration.DB_NAME]

submissions = list(db["submissions"].aggregate([
    {
        "$match":{
            "type":"post",
            "subreddit_name_prefixed":{
                "$ne":"r/NEET"
            }
        }
    },{
        "$project":{
            "subreddit_name_prefixed":1,
            "author_name":1
        }

    },{

        "$group":{
            "_id":"$author_name",
            "subreddits":{
                "$addToSet": "$subreddit_name_prefixed"
            }
        }
    }
]))

G = nx.Graph()

authors = list(map(lambda x: x["_id"],submissions))

#G.add_nodes_from(authors)
#to_remove = []
for i in range(0,len(submissions)):
    i_subreddits = submissions[i]["subreddits"]
    #connected = False
    for k in range(i+1,len(submissions)):
        k_subreddits = submissions[k]["subreddits"]
        if set(i_subreddits) & set(k_subreddits):
            #connected = True
            G.add_edge(submissions[i]["_id"], submissions[k]["_id"], subreddits=(
                set(i_subreddits) & set(k_subreddits)), weight=len(set(i_subreddits) & set(k_subreddits)))
    #if not connected:
        #to_remove.append(submissions[i]["_id"])

#for d in to_remove:
 #   G.remove_node(d)

#pos = nx.spring_layout(G)
#nx.draw(G, pos, node_size=10, with_labels=True)
#plt.show()

# Conveniently, networkx has a method for finding the Laplacian
#laplacian = nx.laplacian_matrix(G)

# Use numpy to compute the Fiedler vector, which corresponds to the
# second smallest eigenvalue of the Laplacian
#w, v = np.linalg.eig(laplacian.todense())
#algebraic_connectivity = w[1]  # Neat measure of how tight the graph is
#fiedler_vector = v[:, 1].T

# NOTE: Apparently nx also does this now
# fiedler_vector = [nx.fiedler_vector(G)]

laplacian = nx.laplacian_matrix(G)

v = np.sort(np.linalg.eigvals(laplacian.todense()))[::-1]
x = range(0,len(v))

#print(v)
plt.plot(x,v)
plt.show()

adj_mat = nx.to_numpy_matrix(G)

# Cluster
sc = SpectralClustering(20, affinity='precomputed', n_init=100)
sc.fit(adj_mat)


'''color_array = ['blue', 'red', 'green',
               'orange', 'black', 'navy', 'teal', 'lime', 'aqua', 'maroon', 'purple', 'olive', 'gray', 'silver', 'fuchsia','yellow']

color_map = list(map(lambda x: color_array[x], sc.labels_))

pos = nx.spring_layout(G,scale=2)
nx.draw(G, pos, node_size=50, node_color=color_map)
plt.show()'''

import functools
for i in range(0,20):
    print("Cluster",i)
    indexes = [c for c, x in enumerate(sc.labels_) if x == i]

    all_nodes = list(G.nodes())
    nodes = [all_nodes[k] for k in indexes]

    sub_graph = G.subgraph(nodes)

    edge_labels = nx.get_edge_attributes(sub_graph, 'subreddits')

    subreddits = list(edge_labels.values())

    subreddits = functools.reduce(lambda x,y: x.union(y) if x else y ,subreddits,set())
    print(subreddits)

    #w_labels = nx.get_edge_attributes(sub_graph, 'weight')
    #pos = nx.spring_layout(sub_graph, scale=2)
    #nx.draw(sub_graph, pos, node_size=50)
    #nx.draw_networkx_edge_labels(sub_graph, pos, labels=w_labels)
    #plt.show()
