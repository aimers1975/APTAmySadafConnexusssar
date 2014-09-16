import unittest
from google.appengine.api import memcache
from google.appengine.ext import testbed
import webapp2
import webtest
import connexus
import logging
import json

class CreateStreamTest(unittest.TestCase):
  def setUp(self):
    app = webapp2.WSGIApplication([(r'/CreateStream', connexus.CreateStream)])
    self.testapp = webtest.TestApp(app)
    self.testbed = testbed.Testbed()
    self.testbed.activate()

  def tearDown(self):
    self.testbed.deactivate()

  def testCreateStream(self):
    logging.info("in testcreatestream")
    self.testbed.init_memcache_stub()
    streamname = 'amy1'
    coverurl = 'www.test.com'
    currentuser = 'amy_hindman@yahoo.com'
    subscribers = ['bo@done.com','jo@dawn.com']
    tags = ['tags']
    params = json.dumps({"streamname":streamname,"coverurl":coverurl,"currentuser":currentuser, "subscribers":subscribers, "tags":tags})
    logging.info("paramaters are: " + str(params))
    response = self.testapp.post('/CreateStream', params)
    logging.info("Test response status : " + response.status)
    logging.info("Test response content : " + str(response.normal_body))
    expected_result = json.dumps({"errorcode": 0})    
    logging.info("Expected result: " + str(type(expected_result)) + " Expected result: " + str(expected_result))
    logging.info("Response: " + str(type(response.normal_body)) + " Response: " + str(response.normal_body))
    assert response.normal_body == expected_result


