# CPCD: Conversational Playlist Curation Dataset
---

## Copyright Notice

This is the work of Arun Tejasvi Chaganty, Megan Leszczynski, Shu Zhang, Ravi
Ganti, Krisztian Balog and Filip Radlinski from Google LLC, made available
under the Creative Commons Attribution 4.0 License. A full copy of the license
can be found at https://creativecommons.org/licenses/by/4.0/

## Abstract

Users in consumption domains, like music, are often able to more efficiently
provide preferences over a set of items (e.g. a playlist or radio) than over
single items (e.g. songs). Unfortunately, this is an underexplored area of
research, with most existing recommendation systems limited to understanding
preferences over single items. Curating an item set exponentiates the search
space that recommender systems must consider (all subsets of items!): this
motivates conversational approaches---where users explicitly state or refine
their preferences and systems elicit preferences in natural language---as an
efficient way to understand user needs. We call this task conversational item
set curation and present a novel data collection methodology that efficiently
collects realistic preferences about item sets in a conversational setting by
observing both item-level and set-level feedback. We apply this methodology to
music recommendation to build the Conversational Playlist Curation Dataset
(CPCD), where we show that it leads raters to express preferences that would
not be otherwise expressed. Finally, we propose a wide range of conversational
retrieval models as baselines for this task and evaluate them on the dataset.

## Data Splits

The dataset consists of 917 conversations split into a development set (450
conversations) and test set (467 conversations). We also provide canonical
train and validation splits of the development set, but encourage using k-fold
cross validation given the relatively small size.

