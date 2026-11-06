from sklearn.model_selection import train_test_split
from sklearn.feature_selection import SelectKBest, f_classif
Z=SelectKBest(f_classif,k=50).fit_transform(X,y)
a,b,c,d=train_test_split(Z,y,test_size=.25,random_state=7)
