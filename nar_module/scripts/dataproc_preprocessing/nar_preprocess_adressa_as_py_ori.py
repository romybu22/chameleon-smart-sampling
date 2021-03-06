import pyspark
import os
import json
import pandas as pd
#import spark
import pickle
import datetime
import hashlib
import math
import matplotlib
import pyspark
import pyspark.sql.functions as F
import pyspark.sql.types as T
from pyspark.shell import spark
from pyspark.sql.functions import pandas_udf
from pyspark.sql.functions import PandasUDFType
import time
#%matplotlib inline


# from pyspark import SparkConf, SparkContext
# sc = SparkContext(master="local",appName="Spark Demo")
# print(sc.textFile("C:\\deckofcards.txt").first())

#strptime = datetime.datetime.strptime('2017-01-05 09:42:15', '%Y-%m-%d %H:%M:%S')
#return int(datetime.datetime.strptime(value, '%Y-%m-%dT%H:%M:%S').timestamp())

#ROOT_PATH = 'gs://news_public_datasets4/adressa'
ROOT_PATH = 'C:\\Users\\operi157093\\Desktop\\Master\\First Year\\Semester B\\Recommendation Systems\\Assignments\\Project\\'
ROOT_PATH = 'C:\\Users\\operi157093\\Desktop\\Master\\RecSys_project\\'
#TODO: Upload this file (generated by the ACR module training) to GCS before calling spark script
#!gsutil cp {ROOT_PATH}/data_transformed/adressa_articles.csv .




articles_original_df = pd.read_csv('C:\\Users\\operi157093\\Desktop\\Master\\RecSys_project\\adressa_articles.csv')

print(articles_original_df.columns)

print(articles_original_df['url'].nunique())

valid_articles_urls_to_ids_dict = dict(articles_original_df[['url','id_encoded']].apply(lambda x: (x['url'], x['id_encoded']), axis=1).values)
print(len(valid_articles_urls_to_ids_dict))






#INTERACTIONS_PATH = 'gs://news_public_datasets4/adressa/one_week/*'
#INTERACTIONS_PATH = 'three_month/20170101'

DAYS_TO_LOAD_INTERACTIONS=8
#interaction_json_files = [os.path.join(ROOT_PATH, 'three_month/201701{:02d}'.format(day)) for day in range(1, DAYS_TO_LOAD_INTERACTIONS)]
interaction_json_files = [os.path.join(ROOT_PATH, 'three_weeks_data/201701{:02d}'.format(day)) for day in range(1, DAYS_TO_LOAD_INTERACTIONS)]
#interaction_json_files = [os.path.join(ROOT_PATH, 'one_week.tar/one_week/20170106')]
print('Loading interaction files: {}'.format(interaction_json_files))

start = time.time()

interactions_df = spark.read \
  .option("mode", "PERMISSIVE") \
  .json(interaction_json_files)
#interactions_df.to_csv(os.path.join(ROOT_PATH,"df_20170106"), sep='\t', index=False, encoding='utf-8')
end = time.time()
print(f"Reading 1 file took {end - start}")

interactions_df.printSchema()

print(interactions_df.count())

#Retrives article id from its cannonical URL (because sometimes article ids in interactions do no match with articles tables, but cannonical URL do)
def get_article_id_encoded_from_url(canonical_url):
    if canonical_url in valid_articles_urls_to_ids_dict:
        return valid_articles_urls_to_ids_dict[canonical_url]
    return None

get_article_id_encoded_from_url_udf = F.udf(get_article_id_encoded_from_url, pyspark.sql.types.IntegerType())

#Filtering only interactions whose url/id is available in the articles table
interactions_article_id_encoded_df = interactions_df.withColumn('article_id', get_article_id_encoded_from_url_udf(interactions_df['canonicalUrl']))
interactions_filtered_df = interactions_article_id_encoded_df.filter(interactions_article_id_encoded_df['article_id'].isNull() == False).cache()

#Valid interactions
print(interactions_filtered_df.count())

#Distinct items count
print(interactions_filtered_df.select('article_id').distinct().count())

first_timestamp_ts = interactions_filtered_df.select('time').agg(F.min('time')).collect()[0][0] * 1000
print(first_timestamp_ts)






def get_timestamp_from_date_str(value):
  if value is not None:
      value = str(value)
      #return int(datetime.datetime.strptime(value, '%Y-%m-%dT%H:%M:%S.%fZ').timestamp())
      return int(datetime.datetime.strptime(value, '%Y-%m-%d %H:%M:%S').timestamp())
  return None


get_timestamp_from_date_str_udf = F.udf(get_timestamp_from_date_str, pyspark.sql.types.IntegerType())

interactions_filtered_with_publish_ts_df = interactions_filtered_df.withColumn('publish_ts', get_timestamp_from_date_str_udf(interactions_filtered_df['publishtime']))
interactions_filtered_with_publish_ts_df = interactions_filtered_with_publish_ts_df.withColumn('elapsed_min_since_published', ((F.col('time') - F.col('publish_ts')) / 60).cast(pyspark.sql.types.IntegerType()))

#%%time
interactions_filtered_with_publish_ts_df.approxQuantile("elapsed_min_since_published", [0.10, 0.25, 0.50, 0.75, 0.90], 0.01)
#[49.0, 108.0, 334.0, 1020.0, 4611.0]

elapsed_min_since_published_df = interactions_filtered_with_publish_ts_df.select('elapsed_min_since_published').toPandas()
print(len(elapsed_min_since_published_df[pd.isnull(elapsed_min_since_published_df['elapsed_min_since_published'])]))
elapsed_min_since_published_df.describe()





def get_categ_features_counts_dataframe(interactions_spark_df,column_name):
    df_pandas = interactions_spark_df.groupBy(column_name).count().toPandas().sort_values('count', ascending=False)
    return df_pandas

PAD_TOKEN = '<PAD>'
UNFREQ_TOKEN = '<UNF>'

def get_encoder_for_values(values):
    encoder_values = [PAD_TOKEN, UNFREQ_TOKEN] + values
    encoder_ids = list(range(len(encoder_values)))
    encoder_dict = dict(zip(encoder_values, encoder_ids))
    return encoder_dict

def get_categ_features_encoder_dict(counts_df, min_freq=100):
    freq_values = counts_df[counts_df['count'] >= 100][counts_df.columns[0]].values.tolist()
    encoder_dict = get_encoder_for_values(freq_values)
    return encoder_dict

def encode_cat_feature(value, encoder_dict):
    if value in encoder_dict:
        return encoder_dict[value]
    else:
        return encoder_dict[UNFREQ_TOKEN]



countries_df = get_categ_features_counts_dataframe(interactions_filtered_df, 'country')
print(len(countries_df))

countries_encoder_dict = get_categ_features_encoder_dict(countries_df)
print(len(countries_encoder_dict))

cities_df = get_categ_features_counts_dataframe(interactions_filtered_df, 'city')
print(len(cities_df))

cities_encoder_dict = get_categ_features_encoder_dict(cities_df)
print(len(cities_encoder_dict))

regions_df = get_categ_features_counts_dataframe(interactions_filtered_df, 'region')
print(len(regions_df))

regions_encoder_dict = get_categ_features_encoder_dict(regions_df)
print(len(regions_encoder_dict))

devices_df = get_categ_features_counts_dataframe(interactions_filtered_df, 'deviceType')
print(len(devices_df))
print(devices_df)

devices_encoder_dict = get_categ_features_encoder_dict(devices_df)
print(len(devices_encoder_dict))

os_df = get_categ_features_counts_dataframe(interactions_filtered_df, 'os')
print(len(os_df))
print(os_df)

os_encoder_dict = get_categ_features_encoder_dict(os_df)
len(os_encoder_dict)

referrer_class_df = get_categ_features_counts_dataframe(interactions_filtered_df, 'referrerHostClass')
print(len(referrer_class_df))
print(referrer_class_df)

referrer_class_encoder_dict = get_categ_features_encoder_dict(referrer_class_df)
print(len(referrer_class_encoder_dict))

encoders_dict = {
    'city': cities_encoder_dict,
    'region': regions_encoder_dict,
    'country': countries_encoder_dict,
    'os': os_encoder_dict,
    'device': devices_encoder_dict,
    'referrer_class': referrer_class_encoder_dict
}










#%%time
active_time_quantiles = interactions_filtered_df.approxQuantile("activeTime", [0.10, 0.25, 0.50, 0.75, 0.90], 0.01)
print(active_time_quantiles)

active_time_stats_df = interactions_filtered_df.describe('activeTime').toPandas()
print(active_time_stats_df)

active_time_mean = float(active_time_stats_df[active_time_stats_df['summary'] == 'mean']['activeTime'].values[0])
active_time_stddev = float(active_time_stats_df[active_time_stats_df['summary'] == 'stddev']['activeTime'].values[0])








def hash_str_to_int(encoded_bytes_text, digits):
    return int(str(int(hashlib.md5(encoded_bytes_text).hexdigest()[:8], 16))[:digits])


MAX_SESSION_IDLE_TIME_MS = 30 * 60 * 1000  # 30 min


def close_session(session):
    size = len(session)

    # Creating and artificial session id based on the first click timestamp and a hash of user id
    first_click = session[0]
    session_id = (int(first_click['timestamp']) * 100) + hash_str_to_int(first_click['user_id'].encode(), 3)
    session_hour = int((first_click['timestamp'] - first_timestamp_ts) / (
                1000 * 60 * 60))  # Converting timestamp to hours since first timestamp

    # Converting to Spark DataFrame Rows, to convert RDD back to DataFrame
    clicks = list([T.Row(**click) for click in session])
    session_dict = {'session_id': session_id,
                    'session_hour': session_hour,
                    'session_size': size,
                    'session_start': first_click['timestamp'],
                    'user_id': first_click['user_id'],
                    'clicks': clicks
                    }
    session_row = T.Row(**session_dict)

    return session_row


def transform_interaction(interaction):
    return {
        'article_id': interaction['article_id'],
        'url': interaction['canonicalUrl'],
        'user_id': interaction['userId'],
        'timestamp': interaction['time'] * 1000,  # converting to timestamp
        'active_time_secs': interaction['activeTime'],
        'country': encode_cat_feature(interaction['country'], encoders_dict['country']),
        'region': encode_cat_feature(interaction['region'], encoders_dict['region']),
        'city': encode_cat_feature(interaction['city'], encoders_dict['city']),
        'os': encode_cat_feature(interaction['os'], encoders_dict['os']),
        'device': encode_cat_feature(interaction['deviceType'], encoders_dict['device']),
        'referrer_class': encode_cat_feature(interaction['referrerHostClass'], encoders_dict['referrer_class']),
    }


def split_sessions(group):
    user, interactions = group
    # Ensuring items are sorted by time
    interactions_sorted_by_time = sorted(interactions, key=lambda x: x['time'])
    # Transforming interactions
    interactions_transformed = list(map(transform_interaction, interactions_sorted_by_time))

    sessions = []
    session = []
    first_timestamp = interactions_transformed[0]['timestamp']
    last_timestamp = first_timestamp
    for interaction in interactions_transformed:

        delta_ms = (interaction['timestamp'] - last_timestamp)
        interaction['_elapsed_ms_since_last_click'] = delta_ms

        if delta_ms <= MAX_SESSION_IDLE_TIME_MS:
            # Ignoring repeated items in session
            if len(list(filter(lambda x: x['article_id'] == interaction['article_id'], session))) == 0:
                session.append(interaction)
        else:
            # If session have at least 2 clicks (minimum for next click predicition)
            if len(session) >= 2:
                session_row = close_session(session)
                sessions.append(session_row)
            session = [interaction]

        last_timestamp = interaction['timestamp']

    if len(session) >= 2:
        session_row = close_session(session)
        sessions.append(session_row)

    # if len(sessions) > 1:
    #    raise Exception('USER with more than one session: {}'.format(user))

    return list(zip(map(lambda x: x['session_id'], sessions),
                    sessions))


#%%time
sessions_rdd = interactions_filtered_df.rdd.map(lambda x: (x['userId'], x)).groupByKey() \
                            .flatMap(split_sessions) \
                            .sortByKey() \
                            .map(lambda x: x[1])




sessions_sdf = sessions_rdd.toDF()

#%%time
write = sessions_sdf.write
by = write.partitionBy("session_hour")
path_join = os.path.join(ROOT_PATH, "report_experiments\\1_first_two_weeks\\1_preprocess_dataproc_notebook\\outputs\\data_transformed\\sessions_processed_by_spark\\")
by.json(path_join)

print(sessions_sdf.count())

def serialize(filename, obj):
    with open(filename, 'wb') as handle:
        pickle.dump(obj, handle)#, protocol=pickle.HIGHEST_PROTOCOL)

NAR_ENCODERS_PATH = 'report_experiments\\1_first_two_weeks\\1_preprocess_dataproc_notebook\\outputs\\nar_encoders_adressa.pickle'
serialize(os.path.join(ROOT_PATH,NAR_ENCODERS_PATH), encoders_dict)

#!gsutil cp {NAR_ENCODERS_PATH} {ROOT_PATH}/data_transformed/pickles/