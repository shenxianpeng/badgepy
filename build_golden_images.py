#!/usr/bin/env python3

# Copyright 2018 The pybadge Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import json
import os
import os.path
import importlib.resources

import badgepy
from tests import image_server
from tests import test_badgepy


def generate_images(source_json_path, target_directory):
    srv = image_server.ImageServer(test_badgepy.PNG_IMAGE)
    srv.start_server()
    try:
        os.makedirs(target_directory, exist_ok=True)
        with open(source_json_path) as f:
            examples = json.load(f)

        for example in examples:
            srv.fix_embedded_url_reference(example)
            filename = os.path.join(target_directory, example.pop('file_name'))
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(badgepy.badge(**example))
    finally:
        srv.stop_server()


def main():
    parser = argparse.ArgumentParser(
        description='generate a github-style badge given some text and colors')

    with importlib.resources.as_file(
            importlib.resources.files('tests') /
            'test-badges.json') as test_badges_path:
        parser.add_argument(
            '--source-path',
            default=str(test_badges_path),
            help='the text to show on the left-hand-side of the badge')

    with importlib.resources.as_file(
            importlib.resources.files('tests') /
            'golden-images') as golden_images_path:
        parser.add_argument(
            '--destination-dir',
            default=str(golden_images_path),
            help='the text to show on the left-hand-side of the badge')

    args = parser.parse_args()
    generate_images(args.source_path, args.destination_dir)


if __name__ == '__main__':
    main()
