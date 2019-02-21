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
import math

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
                "$nin":["r/NEET"]
            }
        }
    },{
        "$project":{
            "subreddit_name_prefixed":1,
            "author_name":1
        }

    },{

        "$group":{
            "_id": "$subreddit_name_prefixed",
            "authors":{
                "$addToSet": "$author_name"
            },
            "count":{
                "$sum":1
            }
        }
    },{
        "$match":{
            "count":{
                "$gte":35

            }
        }
    }
]))

G = nx.Graph()
submission_number = []
subreddit = list(map(lambda x: x["_id"],submissions))

#G.add_nodes_from(authors)
#to_remove = []
for i in range(0,len(submissions)):
    i_authors = submissions[i]["authors"]
    submission_number.append(submissions[i]["count"])
    #connected = False
    for k in range(i+1,len(submissions)):
        k_authors = submissions[k]["authors"]
        if set(i_authors) & set(k_authors):
            #connected = True
            G.add_edge(submissions[i]["_id"], submissions[k]["_id"], weight=math.log(len(
                set(i_authors) & set(k_authors))))
    #if not connected:
        #to_remove.append(submissions[i]["_id"])

#nx.draw_networkx_edges(G, pos, alpha=0.5)


'''n, bins, patches = plt.hist(x=submission_number, bins='auto', color='#0504aa',
                            alpha=0.7, rwidth=0.85)
plt.grid(axis='y', alpha=0.75)
plt.xlabel('Value')
plt.ylabel('Frequency')
plt.title('My Very Own Histogram')
plt.text(23, 45, r'$\mu=15, b=3$')
maxfreq = n.max()
# Set a clean upper y-axis limit.
plt.show()
#for d in to_remove:
 #   G.remove_node(d)
'''

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

#centrality = nx.algorithms.degree_centrality(G)
#print(centrality)

density = nx.density(G)
print(density)

#avg_shortest_path = nx.average_shortest_path_length(G)
#print(avg_shortest_path)

laplacian = nx.laplacian_matrix(G)

v = np.sort(np.linalg.eigvals(laplacian.todense()))[::-1]
x = range(0,len(v))

print(v)
plt.plot(x,v)
plt.show()

adj_mat = nx.to_numpy_matrix(G)

# Cluster
sc = SpectralClustering(18, affinity='precomputed', n_init=100)
sc.fit(adj_mat)


color_array = ['blue', 'red', 'green',
              'orange', 'black', 'navy', 'teal', 'lime', 'aqua', 'maroon', 'purple', 'olive', 'gray', 'silver', 'fuchsia','yellow']

'''color_map = list(map(lambda x: color_array[x], sc.labels_))

pos = nx.spring_layout(G,scale=2)
nx.draw(G, pos, node_size=50, node_color=color_map)
plt.show()'''

import functools
for i in range(0,17):
    print("Cluster",i)
    indexes = [c for c, x in enumerate(sc.labels_) if x == i]

    all_nodes = list(G.nodes())
    nodes = [all_nodes[k] for k in indexes]

    sub_graph = G.subgraph(nodes)

    if not nx.is_connected(sub_graph):
        print("WTF")
    #edge_labels = nx.get_edge_attributes(sub_graph, 'subreddits')

    #subreddits = list(edge_labels.values())

    #subreddits = functools.reduce(lambda x,y: x.union(y) if x else y ,subreddits,set())
    #print(subreddits)

    #w_labels = nx.get_edge_attributes(sub_graph, 'weight')
    pos = nx.spring_layout(sub_graph, scale=2)
    nx.draw(sub_graph, pos, node_size=50, with_labels=True)
    #nx.draw_networkx_edge_labels(sub_graph, pos, labels=w_labels)
    plt.show()
