# EasyGermanDataset

The dataset is introduced in the scientific publication "Developing A German Document-Level Parallel Dataset For Automatic Text Simplification To Generate Easy Language".

This repository contains all the code required to scrape, download, and build the **EasyGerman Dataset**, a dataset that can be used for research on the automatic generation of German Easy-to-Read Language (Leichte Sprache). It was developed as part of the Masterthesis in Computer Science by Vivien Jiranek at the Technical University of Berlin.

#### SCRAPE AND BUILD #### 

The directory `scrape_and_build` contains all scripts and files required to download and build the dataset from gathered urls of MDR news article pairs in easy German and regular German. The script **scrapy.py** downloads the news articles and their metadata from one or several files containing urls referencing the news articles. The file, directory or parent directory of a set of nested directories must be given as an input parameter to the script. To download all files included in the **EasyGerman Dataset** give the directory `mdr_urls` as an input parameter. The news articles are then downloaded pairwise and written to a directory called `mdr_articles` into a series of separate directories based on their language characteristics and their publishing date.

Using the script **dataset_builder.py**, the dataset is built from the previously downloaded news articles. Duplicates or articles that were marked as missing are removed and automatic statistics on the entire dataset, the articles in Easy German/ Leichte Sprache and the articles in regular German are computed. The script takes four input parameters, first it takes the maximum token length, which is set to 1024 tokens by default. Then it takes three local file paths to a directory containing all articles to be included, a directory containing all the articles in Easy German/ Leichte Sprache and a directory containing all the articles in regular German to ensure the parallel structure of the dataset and compute the automatic language assessment of the dataset. 

#### DATASET PROPERTIES #### 

The `dataset_properties` directory contains all automatically generated `metadata` compiled for all news articles in the full Dataset as well as subsets of data grouped by their language or period of publishing. The `statistics` folder contains computed insights on the language of the Dataset, written into respective text files.
