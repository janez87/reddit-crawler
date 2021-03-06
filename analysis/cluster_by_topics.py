from pymongo import MongoClient, DESCENDING
import sys
from collections import Counter
from sklearn.cluster import KMeans, AgglomerativeClustering, SpectralClustering
from scipy.cluster.hierarchy import dendrogram, linkage
from sklearn.metrics import silhouette_samples, silhouette_score
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np
from scipy.spatial.distance import cdist
from sklearn.decomposition import PCA
from sklearn.preprocessing import normalize
import json
sys.path.append("../")
from configuration import configuration

client = MongoClient(
    configuration.DB_HOST, configuration.DB_PORT)


db = client[configuration.DB_NAME]

authors = list(db["author_demographic"].find(
    {}, {"submission_topics": 1,"name":1}))

submission_topics = list(
    map(lambda x: x["submission_topics"], authors))

topics = set()

for s in submission_topics:
    keys = s.keys()
    topics = topics.union(set(keys))

topic_df = dict.fromkeys(topics,0)

X = []
for a in authors:
    authors_topic = a["submission_topics"]
    author_vector = []

    at_least_one = False
    
    for t in topics:
        if t in authors_topic: 
            author_vector.append(authors_topic[t])
            topic_df[t]+=1
            at_least_one = True
        else:
            author_vector.append(0)

    if(at_least_one):
        X.append(author_vector)

for j, x in enumerate(X):
    for i,v in enumerate(x):
        x[i] = v / topic_df[list(topics)[i]]


X  = normalize(X,axis=1)

X = np.array(X)

pca = PCA(.9).fit(X)
X = pca.transform(X)

print(X.shape)
n_cluster = 5

clusterer = KMeans(n_clusters=n_cluster, random_state=10,
                   init='k-means++')

cluster_labels = clusterer.fit_predict(X)

print(cluster_labels)

clusters_population = [set() for i in range(0,n_cluster)]
i = 0
for c in cluster_labels:
    clusters_population[c] = clusters_population[c].union(set(authors[i]["submission_topics"]))
    i=i+1

i=0
for c in clusters_population:
    print("Cluster",i)
    print(c)
    i=i+1

'''range_n_clusters = range(2, 10, 1)

distortions = []
for n_clusters in range_n_clusters:
    # Create a subplot with 1 row and 2 columns
    print('Number of clusters:', n_clusters)
    fig, (ax1, ax2) = plt.subplots(1, 2)
    fig.set_size_inches(18, 7)

    # The 1st subplot is the silhouette plot
    # The silhouette coefficient can range from -1, 1 but in this example all
    # lie within [-0.1, 1]
    ax1.set_xlim([-1, 1])
    # The (n_clusters+1)*10 is for inserting blank space between silhouette
    # plots of individual clusters, to demarcate them clearly.
    ax1.set_ylim([0, len(X) + (n_clusters + 1) * 10])

    # Initialize the clusterer with n_clusters value and a random generator
    # seed of 10 for reproducibility.
    clusterer = KMeans(n_clusters=n_clusters, random_state=10,
                       init='k-means++', max_iter=100)
    cluster_labels = clusterer.fit_predict(X)

    distortions.append(sum(np.min(
        cdist(X, clusterer.cluster_centers_, 'euclidean'), axis=1)) / X.shape[0])

    # The silhouette_score gives the average value for all the samples.
    # This gives a perspective into the density and separation of the formed
    # clusters
    silhouette_avg = silhouette_score(X, cluster_labels)
    print("For n_clusters =", n_clusters,
          "The average silhouette_score is :", silhouette_avg)

    # Compute the silhouette scores for each sample
    sample_silhouette_values = silhouette_samples(X, cluster_labels)

    y_lower = 10
    for i in range(n_clusters):
        # Aggregate the silhouette scores for samples belonging to
        # cluster i, and sort them
        ith_cluster_silhouette_values = \
            sample_silhouette_values[cluster_labels == i]

        ith_cluster_silhouette_values.sort()

        size_cluster_i = ith_cluster_silhouette_values.shape[0]
        y_upper = y_lower + size_cluster_i

        color = cm.nipy_spectral(float(i) / n_clusters)
        ax1.fill_betweenx(np.arange(y_lower, y_upper),
                          0, ith_cluster_silhouette_values,
                          facecolor=color, edgecolor=color, alpha=0.7)

        # Label the silhouette plots with their cluster numbers at the middle
        ax1.text(-0.05, y_lower + 0.5 * size_cluster_i, str(i))

        # Compute the new y_lower for next plot
        y_lower = y_upper + 10  # 10 for the 0 samples

    ax1.set_title("The silhouette plot for the various clusters.")
    ax1.set_xlabel("The silhouette coefficient values")
    ax1.set_ylabel("Cluster label")

    # The vertical line for average silhouette score of all the values
    ax1.axvline(x=silhouette_avg, color="red", linestyle="--")

    ax1.set_yticks([])  # Clear the yaxis labels / ticks
    ax1.set_xticks([-0.1, 0, 0.2, 0.4, 0.6, 0.8, 1])

    # 2nd Plot showing the actual clusters formed
    colors = cm.nipy_spectral(cluster_labels.astype(float) / n_clusters)
    ax2.scatter(X[:, 0], X[:, 1], marker='.', s=30, lw=0, alpha=0.7,
                c=colors, edgecolor='k')

    # Labeling the clusters
    centers = clusterer.cluster_centers_
    # Draw white circles at cluster centers
    ax2.scatter(centers[:, 0], centers[:, 1], marker='o',
                c="white", alpha=1, s=200, edgecolor='k')

    for i, c in enumerate(centers):
        ax2.scatter(c[0], c[1], marker='$%d$' % i, alpha=1,
                    s=50, edgecolor='k')

    ax2.set_title("The visualization of the clustered data.")
    ax2.set_xlabel("Feature space for the 1st feature")
    ax2.set_ylabel("Feature space for the 2nd feature")

    plt.suptitle(("Silhouette analysis for KMeans clustering on sample data "
                  "with n_clusters = %d" % n_clusters),
                 fontsize=14, fontweight='bold')

plt.show()

plt.plot(range_n_clusters, distortions, 'bx-')
plt.xlabel('k')
plt.ylabel('Distortion')
plt.title('The Elbow Method showing the optimal k')

plt.show()
'''
