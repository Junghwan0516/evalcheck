from sklearn.model_selection import train_test_split
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LogisticRegression
a,b,c,d=train_test_split(X,y,test_size=.25,random_state=7)
m=make_pipeline(SelectKBest(f_classif,k=50),LogisticRegression())
m.fit(a,c)
pred=m.predict(b)
