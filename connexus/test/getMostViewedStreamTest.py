import unittest
from google.appengine.api import memcache
from google.appengine.ext import testbed
import webapp2
import webtest
import connexus
import logging
import json

TEST_LOGGER = "GetMostViewedStreamsTest"

class GetMostViewedStreamsTest(unittest.TestCase):
  def setUp(self):
    app = webapp2.WSGIApplication([
       (r'/GetMostViewedStreams', connexus.GetMostViewedStreams),
       (r'/CreateStream', connexus.CreateStream),
       (r'/ViewStream', connexus.ViewStream)
    ])
    self.testapp = webtest.TestApp(app)
    self.testbed = testbed.Testbed()
    self.testbed.activate()

  def tearDown(self):
    self.testbed.deactivate()

  def testGetMostViewedStreams(self):
    logging.info("Creating four test streams")
    self.testbed.init_memcache_stub()
    
    streamname = 'ssstream1'
    coverurl = 'www.test.com'
    currentuser = 'ss@gmail.com'
    subscribers = ['bo@done.com','jo@dawn.com']
    tags = ['ss1']
    params = json.dumps({"streamname":streamname,"coverurl":coverurl,"currentuser":currentuser, "subscribers":subscribers, "tags":tags})
    logging.info("paramaters are: " + str(params))
    response = self.testapp.post('/CreateStream', params)
    logging.info(")Test response status : " + response.status)
    logging.info("Test response content : " + str(response.normal_body))
    expected_result = json.dumps({"errorcode": 0})    
    logging.info("Expected result: " + str(type(expected_result)) + " Expected result: " + str(expected_result))
    logging.info("Response: " + str(type(response.normal_body)) + " Response: " + str(response.normal_body))
    self.assertEqual(response.normal_body, expected_result)
    
    streamname = 'ssstream2'
    coverurl = 'www.test.com'
    currentuser = 'ss@gmail.com'
    subscribers = ['bo2@done.com','jo2@dawn.com']
    tags = ['ss2']
    params = json.dumps({"streamname":streamname,"coverurl":coverurl,"currentuser":currentuser, "subscribers":subscribers, "tags":tags})
    logging.info("paramaters are: " + str(params))
    response = self.testapp.post('/CreateStream', params)
    logging.info("Test response status : " + response.status)
    logging.info("Test response content : " + str(response.normal_body))
    expected_result = json.dumps({"errorcode": 0})    
    logging.info("Expected result: " + str(type(expected_result)) + " Expected result: " + str(expected_result))
    logging.info("Response: " + str(type(response.normal_body)) + " Response: " + str(response.normal_body))
    self.assertEqual(response.normal_body, expected_result)
    
    streamname = 'ssstream3'
    coverurl = 'www.test.com'
    currentuser = 'ss@gmail.com'
    subscribers = ['bo3@done.com','jo3@dawn.com']
    tags = ['ss3']
    params = json.dumps({"streamname":streamname,"coverurl":coverurl,"currentuser":currentuser, "subscribers":subscribers, "tags":tags})
    logging.info("paramaters are: " + str(params))
    response = self.testapp.post('/CreateStream', params)
    logging.info("Test response status : " + response.status)
    logging.info("Test response content : " + str(response.normal_body))
    expected_result = json.dumps({"errorcode": 0})    
    logging.info("Expected result: " + str(type(expected_result)) + " Expected result: " + str(expected_result))
    logging.info("iiiiiiResponse: " + str(type(response.normal_body)) + " Response: " + str(response.normal_body))
    self.assertEqual(response.normal_body, expected_result)
    
    streamname = 'ssstream4'
    coverurl = 'www.test.com'
    currentuser = 'ss@gmail.com'
    subscribers = ['bo4@done.com','jo4@dawn.com']
    tags = ['ss4']
    params = json.dumps({"streamname":streamname,"coverurl":coverurl,"currentuser":currentuser, "subscribers":subscribers, "tags":tags})
    logging.info("paramaters are: " + str(params))
    response = self.testapp.post('/CreateStream', params)
    logging.info("Test response status : " + response.status)
    logging.info("Test response content : " + str(response.normal_body))
    expected_result = json.dumps({"errorcode": 0})    
    logging.info("Expected result: " + str(type(expected_result)) + " Expected result: " + str(expected_result))
    logging.info("Response: " + str(type(response.normal_body)) + " Response: " + str(response.normal_body))
    self.assertEqual(response.normal_body, expected_result)
    
    logging.info("View test streams")
    logging.info("--Viewing stream 1--")
    viewStreamJSON = json.dumps({"pagerange": [0, 0], "streamname": "sstream1"})
    response = self.testapp.post('/ViewStream', viewStreamJSON)
    response = self.testapp.post('/ViewStream', viewStreamJSON)
    logging.info("response json is : " + response.normal_body)
    expectedResponse = json.dumps({"pagerange":[], "picurls":""})
    logging.info("expected response is : " + expectedResponse)
    self.assertEqual(response.normal_body, expectedResponse)
	
    logging.info("--Viewing stream 2--")
    viewStreamJSON = json.dumps({"pagerange": [0, 0], "streamname": "sstream2"})
    response = self.testapp.post('/ViewStream', viewStreamJSON)
    logging.info("response json is : " + response.normal_body)
    
    logging.info("--Viewing stream 3--")
    viewStreamJSON = json.dumps({"pagerange": [0, 0], "streamname": "sstream3"})
    response = self.testapp.post('/ViewStream', viewStreamJSON)
    response = self.testapp.post('/ViewStream', viewStreamJSON)
    response = self.testapp.post('/ViewStream', viewStreamJSON)
    
    viewStreamJSON = json.dumps({"pagerange": [0, 0], "streamname": "sstream4"})
    response = self.testapp.post('/ViewStream', viewStreamJSON)
    response = self.testapp.post('/ViewStream', viewStreamJSON)
    response = self.testapp.post('/ViewStream', viewStreamJSON)
    response = self.testapp.post('/ViewStream', viewStreamJSON)
    
    # ss4,ss3,ss1
    logging.info("Find top three streams")
    response = self.testapp.post('/GetMostViewedStreams', '{}')
    logging.info("Most Viewed stream" + response.normal_body)
