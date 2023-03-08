#!/usr/bin/env python

from argparse import ArgumentParser, FileType
from configparser import ConfigParser
from confluent_kafka import Producer
import praw
import os
from typing import Union
from collections import defaultdict
import json
import re
from pprint import pprint
import time
import callbacks


def clean_post(text):
    # remove [deleted] posts
    text = re.sub(r"\[deleted]", "", text)
    if not text:
        return None

    # embded hyperlinks (text)[link]
    text = re.sub(r"\[(.*?)\]\(http\S+\)", r"\1", text)

    # normal hyperlinks
    text = re.sub(r"http\S+", "", text)

    # remove newline/tabs characters
    text = text.replace("\n", "")
    text = text.replace("\t", "")

    # misc
    text = text.replace("'", "'")
    # double spaces
    text = text.replace("  ", " ")
    # tabs
    text = text.replace("   ", " ")
    return text


if __name__ == "__main__":
    # Parse the command line.
    parser = ArgumentParser()
    parser.add_argument("-t", "--topic", default="thoughts")
    parser.add_argument("--subreddit", default="showerthoughts")
    parser.add_argument("config_file", type=FileType("r"))
    args = parser.parse_args()

    # Parse the configuration.
    config_parser = ConfigParser()
    config_parser.read_file(args.config_file)
    config = dict(config_parser["default"])

    # Create Producer instance
    producer = Producer(config)

    # * Reddit init
    reddit = praw.Reddit(
        client_id=os.getenv("praw_client_id"),
        client_secret=os.getenv("praw_client_secret"),
        user_agent=os.getenv("praw_user_agent"),
    )

    # Create generator to subreddit
    subreddit = reddit.subreddit(args.subreddit)

    submission_stream = subreddit.stream.submissions(skip_existing=False)
    try:
        while True:
            for post in submission_stream:
                # skip innappropiate submissions
                # if post.over_18:
                # continue
                # clean artefacts
                title_clean = clean_post(post.title)
                key = post.id
                value = {
                    "subreddit": post.subreddit.display_name,
                    "title": title_clean,
                }
                value = json.dumps(value, indent=2).encode("utf-8")
                producer.produce(
                    args.topic,
                    key=key,
                    value=value,
                    callback=callbacks.delivery_callback,
                )

                # Wait 30 seconds before sending events
                producer.poll(30)
                producer.flush()

    except KeyboardInterrupt:
        print("Ending Stream")
        # Flush any leftover events before sending events
        producer.poll(1)
        producer.flush()
