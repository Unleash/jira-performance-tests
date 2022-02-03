import random

from selenium.webdriver.common.by import By

from selenium_ui.base_page import BasePage
from selenium_ui.conftest import print_timing
from selenium_ui.jira.pages.pages import Login, Issue
from util.conf import JIRA_SETTINGS
import requests
from flask import Flask, jsonify
from threading import Thread
from uuid import uuid4

feature_response = """{
    "environments": [
        {
            "name": "development",
            "enabled": false,
            "type": "development",
            "sortOrder": 100,
            "strategies": [
                {
                    "name": "flexibleRollout",
                    "constraints": [],
                    "parameters": {},
                    "sortOrder": 9999,
                    "id": "e0aac0c3-ff75-4c1d-aadb-9829c957db2c"
                }
            ]
        },
        {
            "name": "production",
            "enabled": false,
            "type": "production",
            "sortOrder": 200,
            "strategies": [
                {
                    "name": "flexibleRollout",
                    "constraints": [],
                    "parameters": {},
                    "sortOrder": 9999,
                    "id": "b91efbe7-9f93-438e-898c-64aab1ab0f24"
                }
            ]
        }
    ],
    "name": "Test",
    "description": "Test",
    "project": "CoolProject",
    "stale": false,
    "variants": [],
    "createdAt": "2022-01-28T09:32:23.809Z",
    "lastSeenAt": null,
    "type": "release",
    "archived": false
}"""

create_env_response = """{
    "id": "90ea74ac-7920-40d7-af0e-d195a1a8e599",
    "name": "flexibleRollout",
    "constraints": [],
    "parameters": {}
}"""

class FauxUnleashServer(Thread):
    def __init__(self, port=5000):
        super().__init__()
        self.port = port
        self.app = Flask(__name__)
        self.url = "http://localhost:%s" % self.port

        self.app.add_url_rule("/shutdown", view_func=self._shutdown_server)

    def _shutdown_server(self):
        from flask import request
        if not 'werkzeug.server.shutdown' in request.environ:
            raise RuntimeError('Not running the development server')
        request.environ['werkzeug.server.shutdown']()
        return 'Server shutting down...'

    def shutdown_server(self):
        requests.get("http://localhost:%s/shutdown" % self.port)
        self.join()

    def add_callback_response(self, url, callback, methods=('GET',)):
        callback.__name__ = str(uuid4())  # change name of method to mitigate flask exception
        self.app.add_url_rule(url, view_func=callback, methods=methods)

    def add_str_response(self, url, string, methods=('GET',)):
        def callback():
            return string

        self.add_callback_response(url, callback, methods=methods)

    def add_json_response(self, url, serializable, methods=('GET',)):
        def callback():
            return jsonify(serializable)

        self.add_callback_response(url, callback, methods=methods)

    def run(self):
        self.app.run(port=self.port)

def app_specific_action(webdriver, datasets):

    unleashed_issues = ["SCRUM-1", "SCRUM-1"]
    project_name = "TestProject"
    feature_name = "Toggle-" + str(uuid4())
    port = 4242

    unleash_server = FauxUnleashServer(port=port)
    unleash_server.start()
    unleash_server.add_str_response(f"/api/admin/projects/{project_name}/features{feature_name}", feature_response)
    unleash_server.add_str_response(f"/api/admin/projects/{project_name}/features/{feature_name}/environments/development/strategies", create_env_response)
    unleash_server.add_str_response(f"/api/admin/projects/{project_name}/features/{feature_name}/environments/production/strategies", create_env_response)

    page = BasePage(webdriver)

    issue_page = Issue(webdriver, issue_key=random.choice(unleashed_issues))

    @print_timing("selenium_app_add_toggle")
    def measure():
        issue_page.go_to()
        page.wait_until_visible((By.CLASS_NAME, "toggle-status-container"))

    measure()
    unleash_server.shutdown_server()

