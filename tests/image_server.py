# Copyright 2022 The pybadge Authors
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
"""An HTTP image server that can be used to set logo embedding.

The server will respond to any request with the image data provided in the
constructor, using the given Content-Type (or none if it is None).
"""

from http import server
import threading


class ImageServer:
    def __init__(self, image_data, content_type="image/png"):
        self._image_data = image_data
        self._content_type = content_type

    def start_server(self):
        srv = self

        class Handler(server.BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                if srv._content_type is not None:
                    self.send_header("Content-Type", srv._content_type)
                self.end_headers()
                self.wfile.write(srv._image_data)

        self._httpd = server.HTTPServer(("localhost", 0), Handler)
        self.logo_url = "http://localhost:{0}".format(self._httpd.server_port)

        self._thread = threading.Thread(target=self._httpd.serve_forever)
        self._thread.start()

    def fix_embedded_url_reference(self, example):
        if example.get("logo") == "<embedded>":
            example["logo"] = self.logo_url

    def stop_server(self):
        self._httpd.shutdown()
        self._httpd.server_close()
        self._thread.join()
