#!/usr/bin/env python3

import json
import re
from collections import namedtuple
from datetime import datetime
from functools import reduce
from tabulate import tabulate

import csv

import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt

def ilen(iterable):
    return reduce(lambda sum, element: sum + 1, iterable, 0)


message = namedtuple("message", ["timestamp", "sender", "content"])
nickname_change = namedtuple("nickname_change", ["timestamp", "changer", "changee", "to"])
gc_name_change = namedtuple("gc_name_change", ["timestamp", "changer", "to"])


def read_hangouts():
    CONVERSATION_IDS = ["UgxYeiT2UQ4vUkeU5fF4AaABAQ", "UgzICWRigHQSFdsdWkV4AaABAQ"]
    GAIA_IDS = {
        "117831168959985416582": "Feroze Mohideen",
        "110016282469576169727": "Max Callaway",
        "114081268830068285022": "Sebastian Rojas",
        "106040547883252384969": "Sebastian Rojas",
        "100965530828306607935": "Alex Jacobs",
        "100260670144640857390": "Chris Fischer",
        "115286605722106641712": "Karthik Rao",
        "116728432097345341294": "Ryan Klarnet",
        "107814281058182658144": "Tommy Praeger",
        "111558170382520512555": "Matthew Neuendorf",
        "112968795311581921290": "Matthew Neuendorf", # "Jonathan Vilma",
    }

    with open('hangouts/Hangouts.json') as f:
        data = json.load(f)

    messages = []
    nickname_changes = []
    gc_name_changes = []

    for conversation in data["conversations"]:
        if conversation["conversation"]["conversation_id"]["id"] not in CONVERSATION_IDS:
            continue

        for event in conversation["events"]:
            timestamp = datetime.fromtimestamp(int(event["timestamp"]) / (1000 * 1000))
            sender_name = GAIA_IDS[event["sender_id"]["gaia_id"]]

            if "conversation_rename" in event:
                gc_name_changes.append(
                    gc_name_change(
                        timestamp,
                        sender_name,
                        event["conversation_rename"]["new_name"],
                    )
                )

            elif "chat_message" in event:
                # skip photos
                if "segment" not in event["chat_message"]["message_content"]:
                    continue
                
                content = ""
                for segment in event["chat_message"]["message_content"]["segment"]:
                    if segment["type"] == "LINE_BREAK":
                        content += " "
                    else:
                        content += segment["text"]
                messages.append(
                    message(
                        timestamp,
                        sender_name, 
                        content,
                    )
                )

    return messages, nickname_changes, gc_name_changes


def read_messenger():
    MY_NAME = "Chris"
    nickname_regex = r"([\w\s]+) set the nickname for ([\w\s]+) to (.*)."
    my_nickname_regex = r"([\w\s]+) set your nickname to (.*)."
    their_nickname_regex = r"([\w\s]+) set \w+ own nickname to (.*)."
    group_rename_regex = r"([\w\s]+) named the group (.*)."

    group_theme_regex = r"([\w\s]+) changed the chat theme."
    joined_video_chat = r"([\w\s]+) joined the video chat."
    started_video_chat = r"([\w\s]+) started a video chat."
    ended_video_chat = r"The video chat ended."
    to_skip = [
        group_theme_regex,
        joined_video_chat,
        started_video_chat,
        ended_video_chat,
    ]

    messages = []
    nickname_changes = []
    gc_name_changes = []

    for i in range(1, 7):
        with open(f'messenger/inbox/therealtfti_pwjklllfbw/message_{i}.json') as f:
            data = json.load(f)

        for message_json in data["messages"]:
            if message_json["is_unsent"]:
                continue
            # photos
            if "content" not in message_json:
                continue

            raw_content = message_json["content"]
            timestamp = datetime.fromtimestamp(message_json["timestamp_ms"] / 1000)
            sender_name = message_json["sender_name"]

            if any(re.match(reg, raw_content) for reg in to_skip):
                continue

            if m := re.match(nickname_regex, raw_content):
                nickname_changes.append(
                    nickname_change(
                        timestamp,
                        sender_name,
                        m.group(2),
                        m.group(3),
                    )
                )
            elif m := re.match(my_nickname_regex, raw_content):
                nickname_changes.append(
                    nickname_change(
                        timestamp,
                        sender_name,
                        MY_NAME,
                        m.group(2),
                    )
                )
            elif m := re.match(their_nickname_regex, raw_content):
                nickname_changes.append(
                    nickname_change(
                        timestamp,
                        sender_name,
                        sender_name,
                        m.group(2),
                    )
                )
            elif m := re.match(group_rename_regex, raw_content):
                gc_name_changes.append(
                    gc_name_change(
                        timestamp,
                        sender_name,
                        m.group(2),
                    )
                )
            else:
                messages.append(
                    message(
                        timestamp,
                        sender_name, 
                        raw_content,
                    )
                )

    return messages, nickname_changes, gc_name_changes


if __name__ == "__main__":
    m1, n1, g1 = read_hangouts()
    m2, n2, g2 = read_messenger()

    ms = sorted(m1 + m2, key=lambda m: m.timestamp)

    with open('messages.csv', 'w', newline='') as csvfile:
        fieldnames = ['time', 'sender', 'text']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        for m in ms:
            time_str = m.timestamp.strftime("%m/%d/%Y %H:%M:%S")
            writer.writerow({'time': time_str, 'sender': m.sender, 'text': m.content})

    # print(tabulate(
    #     [g.timestamp, g.changer, g.to] 
    #     for g in sorted(g1 + g2, key=lambda g: g.timestamp)
    # ))
    # print(tabulate(
    #     [n.timestamp, n.changer, n.changee, n.to]
    #     for n in sorted(sorted(n1 + n2, key=lambda n: n.timestamp), key=lambda n: n.changee)
    # ))

    # senders = set(m.sender for m in ms)
    # print(len(ms))
    # print(sum(len(m.content.split()) for m in ms))
    # print(tabulate(
    #     sorted(
    #         (
    #             [sender, ilen(filter(lambda m: m.sender == sender, ms))]
    #             for sender in senders
    #         ),
    #         key=lambda row: row[1]
    #     )
    # ))

    # words = ["tfti"]
    
    # print(tabulate(
    #     [word, ilen(filter(lambda m: word in m.content.lower().split(), ms))]
    #     for word in words
    # ))
    # print(tabulate(
    #     [word, sum(m.content.lower().split().count(word) for m in ms)]
    #     for word in words
    # ))

    # for buckets in range(20, 42, 2):
    # plt.hist([m.timestamp for m in ms], 40)
    # plt.savefig(f'buckets_40.png')
    