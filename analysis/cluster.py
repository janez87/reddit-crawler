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

print("Getting all the entities")

outliers = []

all_entities = list(db["submissions"].aggregate([{
    "$match": {
        "dbpedia_entities": {
            "$exists": True
        },
            "author_name":{
                "$nin":outliers
            }
        
    }

}, {

    "$project": {"dbpedia_entities": 1}

}, {
    "$unwind": "$dbpedia_entities"
}, {
	"$group": {
		"_id": "$dbpedia_entities.URI"
	}
}]))

print("Getting all the topics")

all_topics = list(db["submissions"].aggregate([{
    "$match": {
        "topics": {
            "$exists": True
        }, "author_name": {
                "$nin": outliers
            }
    }

}, {

    "$project": {"topics": 1}

}, {
    "$unwind": "$topics"
}, {
	"$group": {
		"_id": "$topics.label"
	}
}]))

print("Getting all the posted subreddit")

all_post_subreddit = list(db["submissions"].distinct("subreddit_name_prefixed",{"type":"post","subreddit_name_prefixed":{"$ne":"r/NEET"}}))

all_entities = list(map(lambda x: x["_id"], all_entities))
all_topics = list(map(lambda x: x["_id"], all_topics))

#all_features = all_entities + all_topics+ all_post_subreddit
all_features = all_post_subreddit

print("Getting user entities")

user_entities = list(db["submissions"].aggregate([{
	"$match": {
		"dbpedia_entities": {
			"$exists": True
		}, 
        "author_name": {
                    "$nin": outliers
                }
	}
}, {
	"$project": {
		"dbpedia_entities": 1,
		"author_name": 1
	}

}, {

	"$unwind": "$dbpedia_entities"

}, {

	"$project": {
		"uri": "$dbpedia_entities.URI",
		"author_name": 1
	}

}, {
	"$group": {
	  	"_id": "$author_name",
	  	"entities": {
	  		"$push": "$uri"
	  	}
	}
}]))

print("Getting all user topics")


user_topics = list(db["submissions"].aggregate([{
	"$match": {
		"topics": {
			"$exists": True
        },"author_name": {
                    "$nin": outliers
        }
	}
}, {
	"$project": {
		"topics": 1,
		"author_name": 1
	}

}, {

	"$unwind": "$topics"

}, {

	"$project": {
		"label": "$topics.label",
		"author_name": 1
	}

}, {
	"$group": {
	  	"_id": "$author_name",
	  	"topics": {
	  		"$push": "$label"
	  	}
	}
}]))

print("Getting user posted subreddit")

user_post_subreddit = list(db["submissions"].aggregate([{"$match": {"subreddit_name_prefixed":{"$ne":"r/NEET"},"type": "post", "author_name": {
    "$nin": outliers
}}}, {

    "$project": {"author_name": 1, "subreddit_name_prefixed": 1}

}, {
	"$group": {
		"_id": "$author_name",
		"subreddit": {"$push": "$subreddit_name_prefixed"}
	}
},{
    "$match":{
        "subreddit.10":{"$exists":True}
    }
}]))


all_users = list(db["submissions"].distinct("author_name",{"author_name":{"$nin":outliers},"subreddit_name_prefixed":"r/NEET","type":"comment"}))
users_features = []
considered_users = [] 

for u in all_users:
    #u_topics = list(filter(lambda x: x["_id"]==u,user_topics))

    u_post_subreddit = list(
        filter(lambda x: x["_id"] == u, user_post_subreddit))

    #u_entities = list(
    #    filter(lambda x: x["_id"] == u, user_entities))

    features = []

    #if len(u_entities)>0:
    #    u_entities = u_entities[0]
    #    features+= u_entities["entities"]

    #if len(u_topics)>0:
    #    u_topics = u_topics[0]
    #    features += u_topics["topics"]
   
    if len(u_post_subreddit)>0:
        u_post_subreddit = u_post_subreddit[0]
        features += u_post_subreddit["subreddit"]
    
    if len(features)>0:    
        users_features.append(features)
        considered_users.append(u)

#X = np.empty(len(all_features))

X = []

for u in users_features:
    count = Counter(u)
    mentioned_features = []
    for e in all_features:
       c = 1 if count[e]>0 else 0
       mentioned_features.append(c)

    #X = np.vstack((X,mentioned_features))
    #X = np.vstack((X, normalize([mentioned_features],axis=1)))
    #mentioned_features = normalize([mentioned_features],axis=1)
    X.append(mentioned_features)


#X = np.delete(X,0,0) #Delete the first empty row?

X = np.array(X)

pca = PCA(.9).fit(X)
X = pca.transform(X)

#pca.fit(X)
#plt.plot(np.cumsum(pca.explained_variance_ratio_))
#plt.xlabel('number of components')
#plt.ylabel('cumulative explained variance')

print(X.shape)

Z = linkage(X, 'ward',"euclidean")

plt.figure(figsize=(25, 10))
plt.title('Hierarchical Clustering Dendrogram')
plt.xlabel('sample index')
plt.ylabel('distance')
dendrogram(
    Z,
    leaf_rotation=90.,  # rotates the x axis labels
    leaf_font_size=8.,  # font size for the x axis labels
    labels=all_users
)
plt.show()


""" range_n_clusters = range(10, 20, 2)

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
 """