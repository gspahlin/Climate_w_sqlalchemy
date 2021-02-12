# Climate_w_sqlalchemy
A climate analysis using the sqlalchemy library of python

Files - 

Climate_sql_alchemy_5.ipynb - This is a jupyter notebook with some basic analysis of weather patterns in Hawaii. The data comes out of a sql database, 
which is queried using the sqlalchemy library of python. Analysis and plotting are done with Pandas and Matplotlib. 

Climate_app5.py - This app uses some of the same code to query the database, and then provide the data in JSON format through a python flask api. 
Two of the routes in the flask api will do custom queries based on the dates entered in the url. If you run the program the home route features directions
for obtaining any of the data. 

hawaii.sqlite - This is the database where all of the queried data comes from. 
