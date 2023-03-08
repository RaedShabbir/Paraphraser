import re
import praw

# * for KSQLDB
SUBMISSION_SCHEMA_STR = """{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Reddit Submission",
  "description": "A submission from reddit",
  "type":"object",
  "properties": {
    "author": {
      "description": "The author of the reddit submission.",
      "type": "string"
    },
    "created_at": {
      "description": "the unix timestamp this post was created at.",
      "type": "integer"
    },
    "downs": {
      "description": "The number of downvotes.",
      "type": "integer"
    },
    "submission_id": {
      "description": "The unique id for the reddit submission.",
      "type": "string"
    },
    "permalink": {
      "description": "permalink to the submission.",
      "type": "string"
    },
    "post_type": {
      "description": "What type of reddit post are we dealing with",
      "type": "string"
    },
    "score": {
      "description": "The visible reddit score between ups/downs",
      "type": "integer"
    },
    "self_text": {
      "description": "The submissions self text .",
      "type": "string"
    },
    "subreddit": {
      "description": "The name of the subreddit this post is from.",
      "type": "string"
    },
    "title": {
      "description": "The submissions title.",
      "type": "string"
    },
    "ups": {
      "description": "The number of upvotes.",
      "type": "integer"
    }
  },
  "required": [
    "author",
    "created_at",
    "title",
    "ups",
    "downs",
    "score",
    "post_type",
    "subreddit"
  ]
}"""


class Submission(object):
    def __init__(
        self,
        id,
        author,
        subreddit,
        created_at,
        score,
        ups,
        downs,
        permalink,
        post_type,
        title,
        self_text,
    ):
        self.id = id
        self.author = author
        self.subreddit = subreddit
        self.created_at = created_at
        self.score = score
        self.ups = ups
        self.downs = downs
        self.permalink = permalink
        self.post_type = post_type
        self.title = title
        self.self_text = str(self_text)


def process_submission(submission: praw.models.Submission):
    # create json dumps for posts
    body = {
        "author": str(submission.author.name),
        "created_at": int(submission.created_utc),
        "permalink": submission.permalink,
        "score": submission.score,
        "self_text": clean_post(submission.selftext) if submission.selftext else None,
        "title": clean_post(submission.title),
        "ups": submission.ups,
        "downs": submission.downs,
        "subreddit": submission.subreddit.display_name,
        "post_type": "submission",
        "id": submission.id,
    }

    return Submission(**body)


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


#! Broken: Switching not working properly
def generate_post(subreddit_stream, comment_stream):
    for submission in subreddit_stream:
        if not submission:
            continue
        else:
            yield submission

    for comment in comment_stream:
        if not comment:
            continue
        else:
            yield comment


def submission_to_dict(submission: Submission, ctx):
    return {
        "id": submission.id,
        "author": submission.author,
        "created_at": submission.created_at,
        "subreddit": submission.subreddit,
        "score": submission.score,
        "ups": submission.ups,
        "downs": submission.downs,
        "permalink": submission.permalink,
        "post_type": submission.post_type,
        "title": submission.title,
        "self_text": submission.self_text,
    }
