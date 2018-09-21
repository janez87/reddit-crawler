from pymongo import MongoClient
import json
import sys
import gensim
from nltk import word_tokenize
import numpy as np
from scipy.spatial.distance import cdist
from sklearn.cluster import KMeans, AgglomerativeClustering, SpectralClustering
from sklearn.metrics import silhouette_samples, silhouette_score
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from sklearn.decomposition import PCA

sys.path.append("../")
from configuration import configuration

client = MongoClient(
    configuration.DB_HOST, configuration.DB_PORT)

db = client[configuration.DB_NAME]

#submission = db["submissions"].find()

#corpus = []

#print("Creating the corpus")

'''for s in submission:
    if s["type"] == "post":
        text = s["title"]+' '+s["selftext"]
    else:
        text = s["body"]
    
    cleaned_text = gensim.utils.simple_preprocess(text)

    corpus.append(cleaned_text)'''


#print("Training the model")
#model = gensim.models.Word2Vec(corpus,min_count=1)
#model.train(corpus, total_examples=len(corpus), epochs=10)

#print("Saving the model")
#model.save("neet_word_embedding.bin")

#print("Done")

model = gensim.models.Word2Vec.load('neet_word_embedding.bin')

def get_post_vector(doc,model):

    if doc["type"] == "post":
        text = doc["title"]+' '+doc["selftext"]
    else:
        text = doc["body"]

    cleaned_text = gensim.utils.simple_preprocess(text)

    vector = []

    for t in cleaned_text:
        t_vector = model.wv.word_vec(t)
        if(len(t_vector)>0):
            vector.append(t_vector)

    if len(vector)>0:
        return np.mean(vector,axis=0)
    else:
        return [np.nan]

def get_user_vector(user,model,db):
    submissions = db["submissions"].find({"author_name":user})

    vector = []

    for s in submissions:
        s_vector = get_post_vector(s,model)
        if ~np.isnan(s_vector).any():
            vector.append(s_vector)
    

    vector =  np.mean(vector,axis=0)

    return vector

authors = db["submissions"].distinct('author_name')

X = list(map(lambda x: get_user_vector(x,model,db),authors))

X = np.array(X)

pca = PCA(.9).fit(X)
X = pca.transform(X)

range_n_clusters = range(2,10,2)

distortions = []
for n_clusters in range_n_clusters:
    # Create a subplot with 1 row and 2 columns
    print('Number of clusters:',n_clusters)
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
