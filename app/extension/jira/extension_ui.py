import random

from selenium.webdriver.common.by import By

from selenium_ui.base_page import BasePage
from selenium_ui.conftest import print_timing
from selenium_ui.jira.pages.pages import Login, Issue
from util.conf import JIRA_SETTINGS
from flask import Flask, jsonify
from threading import Thread
from uuid import uuid4
import sys

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def app_specific_action(webdriver, datasets):

    unleashed_issues = ["AANES-417", "AANES-348", "AANES-271"]

    page = BasePage(webdriver)
    eprint("Preloading the issue test")

    issue_page = Issue(webdriver, issue_key=random.choice(unleashed_issues))

    @print_timing("selenium_app_add_toggle")
    def measure():
        issue_page.go_to()
        page.wait_until_visible((By.CLASS_NAME, "toggle-status-container"))

    measure()

