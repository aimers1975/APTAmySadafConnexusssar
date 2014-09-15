import unittest
from google.appengine.api import memcache
from google.appengine.ext import testbed
import webapp2
import webtest
import connexus
import logging

class CreateStreamTest(unittest.TestCase):
  def setUp(self):
    app = webapp2.WSGIApplication([(r'/GetStreamData', connexus.GetStreamData)])
    self.testapp = webtest.TestApp(app)
    self.testbed = testbed.Testbed()
    self.testbed.activate()

  def tearDown(self):
    self.testbed.deactivate()

  def testCreateStream(self):
    streamname = 'Test Stream 1'
    subscribers = 'test.user@utexas.edu'
    tags = 'testStream'
    
    self.testbed.init_memcache_stub()
    params = {'streamname' : streamname, 'subscribers' : subscribers, 'tags' : tags}
    response = self.testapp.post('/GetStreamData', params)
    logging.info("Test response status : " + response.status)
    #logging.info("Test response content : " + str(response))
    logging.info("Test response content : " + str(response.normal_body))
