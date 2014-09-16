import unittest
from google.appengine.api import memcache
from google.appengine.ext import testbed
import webapp2
import webtest
import connexus
import logging
import json

class DeleteStreamTest(unittest.TestCase):
  def setUp(self):
    app = webapp2.WSGIApplication([(r'/DeleteStreams', connexus.DeleteStreams)])
    self.testapp = webtest.TestApp(app)
    self.testbed = testbed.Testbed()
    self.testbed.activate()

  def tearDown(self):
    self.testbed.deactivate()

  def testDeleteStream(self):
    logging.info("in test delete stream")
    self.testbed.init_memcache_stub()
    params = json.dumps({"streamnamestodelete": ["amy1"]})
    logging.info("paramaters are: " + str(params))
    response = self.testapp.post('/DeleteStreams', params)
    logging.info("Test response status : " + response.status)
    logging.info("Test response content : " + str(response.normal_body))
    expected_result = json.dumps({"errorcode": 0})    
    logging.info("Expected result: " + str(type(expected_result)) + " Expected result: " + str(expected_result))
    logging.info("Response: " + str(type(response.normal_body)) + " Response: " + str(response.normal_body))
    assert response.normal_body == expected_result