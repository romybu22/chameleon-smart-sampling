# CHAMELEON - A Deep Learning Meta-Architecture for News Recommender Systems With Smart Sampling

In this project we try to improve the CHANELEON architecture [1].
To accomplish this task, we used the researches' published code, via this link: https://github.com/gabrielspmoreira/chameleon_recsys. 
Please look up at the original README to run our improvement.


## Implementation

This implementation uses **Python 3.7** (with Pandas, Scikit-learn and SciPy modules) and **TensorFlow 1.12**. CHAMELEON modules were implemented using TF [Estimators](https://www.tensorflow.org/guide/estimators) and [Datasets](https://www.tensorflow.org/guide/datasets).

The CHAMELEON smart sampling's modules training and evaluation can be performed locally (GPU highly recommended).

## Dataset for reproducibility
The experiment reported use the following dataset:

* [SmartMedia Adressa dataset](http://reclab.idi.ntnu.no/dataset) - This dataset contains approximately 20
million page visits from a Norwegian news portal [91]. In our experiments we used 16 days of the full dataset, which is available upon request, and includes article text and click events of about 2 million users and 13,000 articles.

In our expirement we use the first 7 days due to lack of resources.

You must download this dataset to be able to run the commands to pre-process, train, and evaluate the session-based algorithms for next-click recommendation within user sessions.

## Publication
[1] Gabriel de Souza Pereira Moreira, Felipe Ferreira, and Adilson Marques da Cunha. 2018. CHAMELEON: A Deep Learning Meta-Architecture for News Recommender Systems. In Proceedings of Doctoral Symposium of the 12th ACM RecSys'18, October 6, 2018, Vancouver, BC, Canada. ACM, New York, NY, USA, 9 pages. https://doi.org/10.1145/3240323.3240331
