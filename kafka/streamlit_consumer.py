import streamlit as st
from confluent_kafka import Consumer, TopicPartition
from argparse import ArgumentParser, FileType
from configparser import ConfigParser
from datetime import datetime
import streamlit as st
import re

from pprint import pprint

st.set_page_config(page_title="Paraphrase Thoughts", layout="wide")


seperator = """
                <div style="background-color:{};
                padding:2px">

                </div>
            """


def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


local_css("./style.css")

pattern = re.compile(r"(\d+)\.(.*)")

if __name__ == "__main__":
    # Parse the command line.
    parser = ArgumentParser()
    parser.add_argument("config_file", type=FileType("r"))
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--etopic", default="entities")
    parser.add_argument("--ptopic", default="paraphrases")

    args = parser.parse_args()

    # * Parse config file for setting up Consumer
    # * See https://github.com/edenhill/librdkafka/blob/master/CONFIGURATION.md
    config_parser = ConfigParser()
    config_parser.read_file(args.config_file)
    config = dict(config_parser["default"])
    config.update(config_parser["consumer"])

    # Create Consumer instance
    consumer = Consumer(config)

    # Whenever a group rebalance is triggered, we can reset to offset 0 if args.reset
    # group rebalances triggered by consumers joing or leaving the group.
    def reset_offset(consumer, partitions):
        if args.reset:
            for p in partitions:
                p.offset = 0
            consumer.assign(partitions)

    # Subscribe to topic
    consumer.subscribe([args.ptopic, args.etopic], on_assign=reset_offset)
    count = 0
    limit = 50
    # Poll for new messages from Kafka and print them.
    try:
        while True:
            # print(
            #     f"Consumer offset: {consumer.position([TopicPartition(args.topic, 0)])}"
            # )
            msg = consumer.poll(1.0)
            if msg is None:
                count += 1
                if count > limit and args.reset:
                    raise ValueError
                # Initial message consumption may take up to `session.timeout.ms` for
                # rebalance and start consuming
                print(f"Waiting, count untill reset {count}/{limit}")
            elif msg.error():
                print("ERROR: %s".format(msg.error()))
            else:
                key, value = msg.key().decode("unicode_escape"), msg.value().decode(
                    "unicode_escape"
                )

                # print(
                #     f"Consumed event from: \n {msg.topic()} \n key: \n {key} \n value:\n {value}"
                # )
                if msg.topic() == "entities":
                    entity_type = "Examples of"
                else:
                    entity_type = "Paraphrase(s)"

                # * Streamlit rendering
                st.markdown(seperator.format("#DF8877"), unsafe_allow_html=True)
                st.caption(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                st.text(f"{entity_type}: {key}")
                st.markdown(seperator.format("#E1B87F"), unsafe_allow_html=True)
                # remove empty first line bug
                value = value[2:]
                st.text(
                    f"Generated Samples: \n {value}",
                )

    except ValueError:
        print("Closing Consumer ...")

    finally:
        consumer.close()

    # finally:
    # Leave group and commit final offsets
