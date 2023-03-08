from argparse import ArgumentParser, FileType
from configparser import ConfigParser
from confluent_kafka import Consumer, OFFSET_BEGINNING, Producer
import openai
from pprint import pprint
import os
import json
import random
import callbacks
import json

nouns = """
trade
icicle
feeling
sort
maid
food
desire
wood
shake
ground
frog
comparison
smash
way
side
increase
daughter
basketball
eggnog
shop
recess
library
judge
trees
teaching
office
scarf
class
blade
rhythm
design
bit
week
lunchroom
rock
belief
song
children
wave
corn
behavior
airport
building
nut
friend
plate
cherries
story
rabbits
jeans
test
pest
wind
army
basket
porter
pollution
truck
button
visitor
mother
dolls
geese
wash
stocking
gold
afternoon
health
machine
knowledge
reaction
stamp
show
rule
thumb
town
tooth
baseball
coal
title
rub
event
month
can
committee
sky
shame
lumber
cracker
exchange
chalk
string
love
waste
knee
reward
attraction
plastic
oatmeal
size
brake
foot
brass
mine
cherry
part
grain
coast
team
grandmother
knife
texture
whistle
guide
wool
hill
government
position
quartz
stove
shirt
crate
bells
mass
engine
connection
number
selection
north
fall
aunt
bottle
trouble
camera
value
meat
liquid
afterthought
sand
moon
trucks
sugar
crow
appliance
soda
market
nest
income
pear
blow
hour
toys
drop
tree
spark
seat
tramp
cause
calculator
honey
watch
trousers
bubble
car
stew
insect
regret
carriage
leg
plane
secretary
underwear
sign
pizzas
van
scarecrow
rat
burst
ice
skirt
dime
water
weight
key
laugh
kitty
letters
ink
birth
insurance
deer
powder
juice
sock
airplane
approval
need
earthquake
talk
road
head
crowd
rake
quicksand
frogs
writer
idea
bed
bikes
mom
zipper
jail
drawer
flower
throat
furniture
clover
ticket
spy
woman
loaf
partner
cloth
pickle
fire
train
farm
wheel
wish
giraffe
shade
gate
agreement
pencil
work
board
door
curve
reading
mind
seashore
smell
order
observation
shock
rail
person
cactus
nation
straw
ghost
beds
rose
ray
fork
produce
camp
house
match
edge
notebook
quill
driving
humor
jump
grape
church
pail
collar
needle
horses
hobbies
page
invention
trick
war
expansion
rifle
argument
achiever
tiger
thought
snake
care
word
thing
swim
jam
snakes
time
uncle
pig
day
cast
stone
back
aftermath
stream
authority
"""
nouns = nouns.split()


def request_davinci(paraphrase, utterance, entity, n=1):
    if paraphrase:
        if entity:
            prompt = f"create {n} sentences similar to:\n '{utterance}' and keep {entity} in the new sentences."
        else:
            prompt = f"create {n} sentences similar to:\n '{utterance}'"
    else:
        prompt = f"Create {n} examples of the following: \n '{entity}'"

    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt,
        temperature=0.20,
        max_tokens=500,
    )
    # print(response["choices"][0]["text"])
    return response["choices"][0]["text"]


if __name__ == "__main__":
    openai.api_key = os.getenv("OPENAI_API_KEY")

    # Parse the command line.
    parser = ArgumentParser()
    parser.add_argument("config_file", type=FileType("r"))
    parser.add_argument("--topic", default="thoughts")
    parser.add_argument("--etopic", default="entities")
    parser.add_argument("--ptopic", default="paraphrases")
    parser.add_argument("--reset", action="store_true")

    args = parser.parse_args()

    # * Parse config file for setting up Consumer
    # * See https://github.com/edenhill/librdkafka/blob/master/CONFIGURATION.md
    config_parser = ConfigParser()
    config_parser.read_file(args.config_file)
    config = dict(config_parser["default"])
    config.update(config_parser["consumer"])

    # Set up a callback to reset and simulate flow from begggining
    def reset_offset(consumer, partitions):
        if args.reset:
            for p in partitions:
                p.offset = OFFSET_BEGINNING
            consumer.assign(partitions)

    # Create Consumer/Producer instance
    consumer = Consumer(config)
    producer = Producer(config)

    # Subscribe to topic
    consumer.subscribe([args.topic], on_assign=reset_offset)

    # begin polling
    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                # Initial message consumption may take up to
                # `session.timeout.ms` for the consumer group to
                # rebalance and start consuming
                print("Waiting...")
            elif msg.error():
                print("ERROR: %s".format(msg.error()))
            else:
                key = msg.key().decode("utf-8")
                value = json.loads(msg.value().decode("utf-8"))
                print("********************************")
                print(value)
                # extract values
                utterance, subreddit = value["title"], value["subreddit"]
                print(utterance, subreddit)
                print(
                    f"Consumed event from topic {msg.topic()} \nkey = {key} \nphrase = {utterance} \nsubreddit = {subreddit}"
                )

                # get shower thought
                print("Requesting Davicni for paraphrase...")
                davinci_output_1 = json.dumps(
                    request_davinci(
                        paraphrase=True,
                        utterance=utterance,
                        entity=None,
                        n=random.randint(2, 6),
                    )
                ).encode("utf-8")

                # produce paraphrase
                producer.produce(
                    topic=args.ptopic,
                    key=f"{subreddit}:\t\t {utterance}",
                    value=davinci_output_1,
                    callback=callbacks.delivery_callback,
                )

                # * Simulate entity generation
                # get random entity
                print("Requesting Davicni for entities examples...")
                entity = random.choice(nouns)
                davinci_output_2 = json.dumps(
                    request_davinci(
                        paraphrase=False,
                        utterance=None,
                        entity=entity,
                        n=random.randint(3, 10),
                    )
                ).encode("utf-8")

                producer.produce(
                    topic=args.etopic,
                    key=entity,
                    value=davinci_output_2,
                    callback=callbacks.delivery_callback,
                )
                producer.poll(10)
                producer.flush()

    except KeyboardInterrupt:
        print("Closing producer ...")
        producer.poll(1)
        producer.flush()

    finally:
        print("Closing consumer ...")
        consumer.close()
