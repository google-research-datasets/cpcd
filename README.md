# Beyond Single Items: Exploring User Preferences in Item Sets with the Conversational Playlist Curation Dataset

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

Read the paper on [arXiv](https://arxiv.org/abs/2303.06791).

## [Data Card](https://github.com/google-research-datasets/cpcd/blob/main/cpcd_data_card.pdf)

## Data Splits

The dataset consists of 917 conversations split into a [development set](https://github.com/google-research-datasets/cpcd/blob/main/data/cpcd_v1.dialogs.dev.jsonl) (450
conversations) and [test set](https://github.com/google-research-datasets/cpcd/blob/main/data/cpcd_v1.dialogs.test.jsonl) (467 conversations). We also provide canonical
[train](https://github.com/google-research-datasets/cpcd/blob/main/data/cpcd_v1.dialogs.dev.train.jsonl) and [validation](https://github.com/google-research-datasets/cpcd/blob/main/data/cpcd_v1.dialogs.dev.val.jsonl) splits of the development set, but encourage using k-fold
cross validation given the relatively small size.

## Schema

Each line of the dataset represents a single conversation in JSON format consisting of the following fields:
* `id` (string): a unique identifier for this conversation.
* `turns` (list[Turn]): A list of turns in the conversation.
* tracks` (dict[string, Track]): The metadata associated with each track referenced in turns above.
* `goal_playlist` (list[string]): The list of track ids for the final target list of “liked” tracks in this conversation.

Each turn consists of:
* `user_query` (string): user query for this turn.
* `system_response` (string): wizard response for this turn.
* `search_queries` (list[string]): list of queries entered by the wizard this turn.
* `search_results` (list[string]): list of track ids retrieved for each query in “search_queries”.
* `liked_results` (list[string]): list of track ids shown to users and liked by them.
* `disliked_results` (list[string]): list of track ids shown to users and disliked by them.

Each track consists of:
* `track_ids` (string): identifier for the track. It corresponds to a YouTube video id.
* `track_titles` (string): title of the track.
* `track_artists` (list[string]): names of the artist on this track.
* `track_release_titles` (string): title of the release or album.

Here is an abbreviated example:
```
{
  "id": "00079c9c8dd7b55a",
  "turns": [
    {
      "user_query": "I'd like to create a playlist that is perfect for a dance party. I'd like to create a playlist that I can utilize for a dance party.",
      "system_response": "Hello! I can help with that! What kind of genre or artist would you like to add to your playlist?",
      "search_queries": [],
      "search_results": [],
      "liked_results": [],
      "disliked_results": []
    },
    {
      "user_query": "Any genre works as long as it is upbeat and something people can jump around and sing to!",
      "system_response": "Here is a selection of songs that match your preferences. Any other artist or genre?",
      "search_queries": [
        "Party Rock Anthem",
        "Don't Stop Believin"
      ],
      "search_results": [
        [
          "3JDHlCcn-UY",
          "9acyYo1JdRg"
        ],
        [
          "0cBShyKk-w0",
          "14d5a5pxiV8"
        ],
      ],
      "liked_results": [
        "Jx_O6PHdWww",
        "OIPmhkzN2ug"
      ],
      "disliked_results": [
        "tYvFa2ARD24"
      ]
    }
  ],
  "tracks": {
    "4z-bOdAdias": {
      "track_artists": [
        "Beyoncé"
      ],
      "track_release_titles": "I AM...SASHA FIERCE",
      "track_titles": "Single Ladies (Put a Ring on It)",
      "track_ids": "4z-bOdAdias"
    },
    "7YQESUr8Cxc": {
      "track_artists": [
        "Gwen Stefani"
      ],
      "track_release_titles": "Love Angel Music Baby (Deluxe Version)",
      "track_titles": "Hollaback Girl",
      "track_ids": "7YQESUr8Cxc"
    }
  },
  "goal_playlist": [
    "4z-bOdAdias",
    "7YQESUr8Cxc",
    "BciS5krYL80",
    "Jx_O6PHdWww"
  ]
}
```
