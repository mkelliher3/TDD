import time
import unittest

from django.test import LiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import WebDriverException

MAX_WAIT = 10

class NewVisitorTest(LiveServerTestCase):
    def setUp(self):
        self.browser = webdriver.Firefox()

    def tearDown(self):
        self.browser.quit()

    def wait_for_row_in_list_table(self, row_text):
        start_time = time.time()
        # here is the loop that will go forever, unless we get to one of two possible exit routes
        while True:
            try:
                table = self.browser.find_element_by_id('id_list_table')
                rows = table.find_elements_by_tag_name('tr')
                self.assertIn(row_text, [row.text for row in rows])
                return # if the assertions passes, we return from the function and escape the loop
            # if we catch an exception, we wait a short amount of time and loop around to retry.
            # WebDriverException - when the page is not loaded or table element is not there.
            # AssertionError - when the table is there, so it doesn't have rows in yet.
            except (AssertionError, WebDriverException) as e:
                if time.time() - start_time > MAX_WAIT: # This is the second escape route.
                    raise e
                time.sleep(0.5)

    # def test_can_start_a_list_and_retrieve_it_later(self):
    def test_can_start_a_list_for_one_user(self):
        # self.browser.get('http://localhost:8000')
        self.browser.get(self.live_server_url)

        # assert title and header
        self.assertIn('To-Do', self.browser.title)
        header_text = self.browser.find_element_by_tag_name('h1').text
        self.assertIn('To-Do', header_text)

        # first test on inputbox
        inputbox = self.browser.find_element_by_id('id_new_item')
        self.assertEqual(
            inputbox.get_attribute('placeholder'),
            'Enter a to-do item'
        )
        inputbox.send_keys('Buy peacock feathers')
        inputbox.send_keys(Keys.ENTER)

        self.wait_for_row_in_list_table('1: Buy peacock feathers')

        # second test on inputbox.
        inputbox = self.browser.find_element_by_id('id_new_item')
        inputbox.send_keys('Use peacock feathers to make a fly')
        inputbox.send_keys(Keys.ENTER)

        self.wait_for_row_in_list_table('1: Buy peacock feathers')
        self.wait_for_row_in_list_table('2: Use peacock feathers to make a fly')

        self.fail('Finish the test!')

    # def test_can_start_a_list_for_one_user(self):
    #     self.wait_for_row_in_list_table('1: Buy peacock feathers')
    #     self.wait_for_row_in_list_table('2: Use peacock feathers to make a fly')

    def test_multiple_users_can_start_lists_at_different_urls(self):
        # Edith starts a new todo list
        self.browser.get(self.live_server_url)

        inputbox = self.browser.find_element_by_id('id_new_item')
        inputbox.send_keys('Buy peacock feathers')
        inputbox.send_keys(Keys.ENTER)

        self.wait_for_row_in_list_table('1: Buy peacock feathers')

        # she notices that her list has a unique URL
        edith_list_url = self.browser.current_url
        self.assertRegex(edith_list_url, '/lists/.+')
        # assertRegex is a helper function from unittest that checks whether
        # a string matches a regular experession. We use it to check that
        # our new REST-ish design has been implemented.

        # a new user, Francis, comes along to the site

        ## we use a new browser session to make sure that no information
        ## of Edith's is coming through from cookies, etc.
        self.browser.quit()
        self.browser = webdriver.Firefox()

        # Francis visits the homepage
        self.browser.get(self.live_server_url)
        page_text = self.browser.find_element_by_tag_name('body').text
        self.assertNotIn('Buy peacock feathers', page_text)
        self.assertNotIn('make a fly', page_text)

        # Francis starts a new list
        inputbox = self.browser.find_element_by_id('id_new_item')
        inputbox.send_keys('Buy milk')
        inputbox.send_keys(Keys.ENTER)
        self.wait_for_row_in_list_table('1: Buy milk')

        # Francis gets his own URL
        francis_list_url = self.browser.current_url
        self.assertRegex(francis_list_url, '/lists/.+')
        self.assertNotEqual(francis_list_url, edith_list_url)

        # There is no trace of Edith's list
        page_text = self.browser.find_element_by_tag_name('body').text
        self.assertNotIn('Buy peacock feathers', page_text)
        self.assertIn('Buy milk', page_text)

