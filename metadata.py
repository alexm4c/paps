#!/usr/bin/env python

"""
metadata.py

This module is a library of classes and functions and collecting
metadata. Specifically it contains functions that help with finding
and opening audio files, reading and writing metadata to csv.

#---------------------------------------------------------------------#

Classes and functions defined in this module include:

    VLCPlayer
    write_metadata_csv
    read_metadata_csv
    print_metadata
    list_audio_files
    find
    timestamp_seconds
    is_valid_segment
    Style
    print_info
    print_error
    print_title
    clear_and_title
    prompt
    multi_prompt
"""

import csv
import os
import re
import subprocess

from ui import *

# The list of extensions of file types that this module will process
VALID_AUDIO = ('.mp3',)


class VLCPlayer:
    # Provide a clean way to open an audio file with VLC, silence
    # it's stdout messages, and then terminate the subprocess.
    def __init__(self, path):
        self.path = path

    def __enter__(self):
        self.devnull = open(os.devnull, 'w')
        self.vlc = subprocess.Popen(
            ['vlc', self.path],
            stdout=self.devnull,
            stderr=self.devnull,
        )
        return self

    def __exit__(self, type, value, traceback):
        self.vlc.terminate()
        self.devnull.close()


class MetadataList(list):
    # Dictionary list of audio metadata in a specific format
    KEYS = ['filepath', 'event_name', 'title', 'speakers', 'segments']

    def add_item(self, data={}):
        metadata = self.Metadata(data)
        self.append(metadata)
        return metadata

    def get_item(self, key, value):
        # Search through metadata and returns the
        # first item with matching key value pair.
        for item in self:
            if item and item[key] == value:
                return item

    def write_to_csv(self, output_csv):
        # Write the dictionary list of audio metadata into a csv file.
        print_info('Writing metadata to {}'.format(output_csv))

        rows = []
        for metadata in self:
            if metadata:
                row = {}
                row['filepath'] = metadata['filepath']
                row['event_name'] = metadata['event_name']
                row['title'] = metadata['title']
                if metadata['speakers']:
                    row['speakers'] = ';'.join(metadata['speakers'])
                if metadata['segments']:
                    row['segments'] = ';'.join(metadata['segments'])
                rows.append(row)

        with open(output_csv, "w", newline='') as file:
            writer = csv.DictWriter(
                file,
                self.KEYS,
                quoting=csv.QUOTE_ALL,
            )
            writer.writeheader()
            writer.writerows(rows)

    def read_from_csv(self, input_csv):
        # Reads a csv file of audio metadata into a dictionary list
        print_info('Reading metadata from {}'.format(input_csv))

        with open(input_csv, "r") as file:
            reader = csv.DictReader(
                file,
                quoting=csv.QUOTE_ALL,
            )
            for row in reader:
                row['speakers'] = row['speakers'].split(';')
                row['segments'] = row['segments'].split(';')
                self.add_item(row)

    class Metadata(dict):
        def toId3(self):
            id3 = {}
            id3['title'] = self['title']
            id3['artist'] = ', '.join(self['speakers'])
            id3['album'] = self['event_name']
            return id3

        def print_pretty(self):
            # Print in a human readable format
            print()
            print('{0}Filepath:{1}\t{2}'.format(
                Style.BOLD,
                Style.END,
                self['filepath'],
            ))
            print('{0}Event:{1}\t\t{2}'.format(
                Style.BOLD,
                Style.END,
                self['event_name'],
            ))
            print('{0}Title:{1}\t\t{2}'.format(
                Style.BOLD,
                Style.END,
                self['title'],
            ))
            print('{0}Speakers:{1}\t{2}'.format(
                Style.BOLD,
                Style.END,
                ', '.join(self['speakers']),
            ))
            print('{0}Segments:{1}\t{2}'.format(
                Style.BOLD,
                Style.END,
                ', '.join(self['segments'])),
            )


def timestamp_seconds(seconds=None, minutes=None, hours=None):
    # Convert and audio timestamp in hours, minutes, seconds
    # into the total number of seconds. This function will generally
    # be used with unknown user input, hence why we use heavy handed
    # validation here.
    hours = hours * 3600 if hours else 0
    minutes = minutes * 60 if minutes else 0
    seconds = seconds if seconds else 0
    return hours + minutes + seconds


def segment_seconds(string):
    # Interpret audio segment made up of a start timestamp and end
    # timestamp delimited by '-' ([hh:]mm:ss-[hh:]mm:ss). Segments with
    # end cuts that precede start cuts are invalid. Returns start time
    # and end time as a tuple.
    pattern = re.compile(
        # Start timestamp
        r'^(\d{2})?:?([0-5]\d):?([0-5]\d)'
        # Separator
        r'\s*[-|+;]\s*'
        # End timestamp
        r'(\d{2})?:?([0-5]\d):?([0-5]\d)$'
    )
    regex = re.search(pattern, string)

    if not regex:
        raise ValueError(
            'Audio timestamp segment format is invalid: {}'.format(string)
        )

    groups = [int(x) if x else 0 for x in regex.groups()]

    start_hr, start_min, start_sec, end_hr, end_min, end_sec = groups

    start = timestamp_seconds(start_sec, start_min, start_hr)
    end = timestamp_seconds(end_sec, end_min, end_hr)

    if end < start:
        raise ValueError('Start timestamp must precede end timestamp')

    return start, end


def is_valid_segment(string):
    # Simple function for validating audio segments. A falsey 'string'
    # value will return True because this function is intended to be
    # used in conjunction with the multi_prompt() function in the ui
    # package where an empty string is the signal to exit and continue.
    # This is a little weird and may need revision.
    if not string:
        # Defer None validation
        return True
    try:
        segment_seconds(string)
    except (ValueError, TypeError):
        return False
    else:
        return True


def list_audio_files(path):
    # Search the given input directory for all audio that matches
    # valid file extensions and returns a list of their paths.
    audio_files = []

    for root, _, files in os.walk(path):
        for file in files:
            audio_files.append(os.path.join(root, file))

    audio_files = filter(
        lambda x: True if x.lower().endswith(VALID_AUDIO) else False,
        audio_files,
    )

    return list(audio_files)


if __name__ == "__main__":
    print(__doc__)
