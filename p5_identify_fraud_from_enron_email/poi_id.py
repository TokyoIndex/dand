#!/usr/bin/python

import sys
import pickle
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
sys.path.append("../tools/")

from feature_format import featureFormat, targetFeatureSplit
from tester import dump_classifier_and_data

### Task 1: Select what features you'll use.
### features_list is a list of strings, each of which is a feature name.
### The first feature must be "poi".
features_list = [
    'poi',
    'salary',
    'to_messages',
    'deferral_payments',
    'total_payments',
    'exercised_stock_options',
    'bonus',
    'restricted_stock',
    'shared_receipt_with_poi',
    'restricted_stock_deferred',
    'total_stock_value',
    'expenses',
    'loan_advances',
    'from_messages',
    'other',
    'from_this_person_to_poi',
    'director_fees',
    'deferred_income',
    'long_term_incentive',
    #'email_address', causes featureFormat issues when trying to convert to float
    'from_poi_to_this_person'
] 

### Load the dictionary containing the dataset
with open("final_project_dataset.pkl", "r") as data_file:
    data_dict = pickle.load(data_file)

# Explore the Data
print 'Number of Records:', len(data_dict)
print 'Number of Features per Person:', len(data_dict.values()[0])
#print 'List of Features:', data_dict.values()[0]
print 'There are 14 financial features and 6 email features'
print 'The last feature is a label denoting a Person of Interest(POI)'

### Task 2: Remove outliers
# Inspect Data manually for outliers
data_dict = pickle.load(open("final_project_dataset.pkl", "r") )
###creating dataFrame from dictionary - pandas
df = pd.DataFrame.from_dict(data_dict, orient='index', dtype=np.float)
df = df.fillna(value=0)
print 'Details:'
print df.describe().loc[:,['salary','bonus']]
# Investigate the very high salary/bonus and very low salary/bonus

# print the names
print "\n"
print data_dict.keys()

# THE TRAVEL AGENCY IN THE PARK, TOTAL, LOCKHART, EUGENE E
def remove_outliers(data, outliers):
    for outlier in data:
        data.pop('outliers', 0)
    return data

outliers = ['TOTAL', 'THE TRAVEL AGENCY IN THE PARK', 'LOCKHART, EUGENE E']
remove_outliers(data_dict, outliers)
print "\n"
print "Removing Outliers: 'TOTAL', 'THE TRAVEL AGENCY IN THE PARK', 'LOCKHART, EUGENE E'"

### Use KBest to find the actual features we will use
# Use SelectKBest to find the most influencial features
from sklearn import feature_selection 

k_data = featureFormat(data_dict, features_list)
labels, features = targetFeatureSplit(k_data)

k_best = feature_selection.SelectKBest()
k_best.fit(features, labels)
scores = k_best.scores_
feature_scores = zip(features_list[1:], scores)
sorted_feature_scores = list(reversed(sorted(feature_scores, key = lambda x: x[1]))) # sort by scores, desc
print "\n"
print 'List of Features by Influence (desc):', sorted_feature_scores

# Top Five
top_five = sorted_feature_scores[:5]
print "\n"
print 'Top Five:', top_five

target = ['poi']

email_features_list = [
    #'from_messages',
    'from_poi_to_this_person',
    'from_this_person_to_poi',
    'shared_receipt_with_poi',
    'to_messages'
    ]

financial_features_list = [
    #'bonus',
    #'deferral_payments',
    #'deferred_income',
    'director_fees',
    #'exercised_stock_options',
    #'expenses',
    'loan_advances',
    #'long_term_incentive',
    #'other',
    #'restricted_stock',
    #'restricted_stock_deferred',
    #'salary',
    #'total_payments',
    #'total_stock_value'
    ]

## Visualize Feature Scores
x = [1, 2, 3,4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
y = sorted(scores, reverse=True)
plt.scatter( x, y  )

plt.xlabel("SelectKBest Feature Scores")
plt.ylabel("Feature")
#plt.show()

## Measure Precision and Recall for different arragements of Features

## Visualize Precision and Recall
precision = [0, 0.00339, 0, 0, 0, 0.19038, 0.14755, 0.15423, 0.14552, 0.14509, 0.14195, 0.14276, 0.14134, 0.14139, 0.14146, 0.14143, 0.14186, 0.15593, 0.15599]
recall = [0, 0.00200, 0, 0, 0, 0.76800, 0.82400, 0.81400, 0.82300, 0.82050, 0.81850, 0.82050, 0.81850, 0.81700, 0.81900, 0.81900, 0.82250, 0.83600, 0.83400]
num_of_features = x
plt.scatter( x, precision, c='b'   )
plt.scatter( x, recall, c='r'  )

plt.xlabel("K best Features")
plt.ylabel("Score")
#plt.show()

### Task 3: Create new feature(s)
### Store to my_dataset for easy export below., 0.15423, 0.14552
my_dataset = data_dict

# Calculate the Ratio of Messages
def ratio(poi_messages, all_messages):
	if poi_messages == 'NaN' or all_messages == 'NaN':
		return 0
	else:
		return poi_messages / all_messages

for employee in my_dataset:
	data_point = my_dataset[employee]
	to_messages = data_point["to_messages"]
	from_messages = data_point["from_messages"]
	from_this_person_to_poi = data_point["from_this_person_to_poi"]
	from_poi_to_this_person = data_point["from_poi_to_this_person"]
	fraction_from_poi = ratio(from_poi_to_this_person, to_messages)
	data_point["fraction_from_poi"] = fraction_from_poi
	fraction_to_poi = ratio(from_this_person_to_poi, from_messages)
	data_point["fraction_to_poi"] = fraction_to_poi

# Add new feature to my feature list
features_list = target + email_features_list + financial_features_list #+ ['fraction_to_poi', 'fraction_from_poi']


### Extract features and labels from dataset for local testing
data = featureFormat(my_dataset, features_list, sort_keys = True)
labels, features = targetFeatureSplit(data)


### Task 4: Try a varity of classifiers#
### Please name your classifier clf for easy export below.
### Note that if you want to do PCA or other multi-stage operations,
### you'll need to use Pipelines. For more info:
### http://scikit-learn.org/stable/modules/pipeline.html

# Provided to give you a starting point. Try a variety of classifiers.
from sklearn.naive_bayes import GaussianNB
#clf = GaussianNB()

from sklearn import neighbors
#clf = neighbors.KNeighborsClassifier(n_neighbors=2)

from sklearn import tree 
#clf = tree.DecisionTreeClassifier(random_state = 24, class_weight = "balanced")  # pretty good results # 

from sklearn.linear_model import LogisticRegression
clf = LogisticRegression(C = 10**20, random_state = 42, tol = 10**-10, class_weight='balanced') # much better results 


### Task 5: Tune your classifier to achieve better than .3 precision and recall 
### using our testing script. Check the tester.py script in the final project
### folder for details on the evaluation method, especially the test_classifier
### function. Because of the small size of the dataset, the script uses
### stratified shuffle split cross validation. For more info: 
### http://scikit-learn.org/stable/modules/generated/sklearn.cross_validation.StratifiedShuffleSplit.html

# Example starting point. Try investigating other evaluation techniques!
from sklearn.cross_validation import train_test_split
features_train, features_test, labels_train, labels_test = \
    train_test_split(features, labels, test_size=0.4, random_state=42)


clf.fit(features_train, labels_train)
pred = clf.predict(features_test)

# Call tester.py for Evaluation
#print "\n"
#from tester import test_classifier
#test_classifier(clf, my_dataset, features_list)

### Task 6: Dump your classifier, dataset, and features_list so anyone can
### check your results. You do not need to change anything below, but make sure
### that the version of poi_id.py that you submit can be run on its own and
### generates the necessary .pkl files for validating your results.

dump_classifier_and_data(clf, my_dataset, features_list)

### good job!  have some cake.