import unittest
from google.appengine.api import memcache
from google.appengine.ext import testbed
import webapp2
import webtest
import connexus
import logging
import json

TEST_LOGGER = "GetMostViewedStreamsTest"

class SearchStreamsTest(unittest.TestCase):
  def setUp(self):
    app = webapp2.WSGIApplication([
       (r'/SearchStreams', connexus.SearchStreams),
       (r'/CreateStream', connexus.CreateStream)
    ])
    self.testapp = webtest.TestApp(app)
    self.testbed = testbed.Testbed()
    self.testbed.activate()

  def tearDown(self):
    self.testbed.deactivate()

  def testSearchStreamsByStreamName(self):
    logging.info("Creating streams")
    self.testbed.init_memcache_stub()
   
    # searchStream1 - streamname contains subset connexus
    streamname = 'connexusStream1'
    coverurl = 'www.test1.com'
    currentuser = 'ss1@gmail.com'
    subscribers = ['bo1@done.com','jo1@dawn.com']
    tags = ['sstr1']
    params = json.dumps({"streamname":streamname,"coverurl":coverurl,"currentuser":currentuser, "subscribers":subscribers, "tags":tags})
    response = self.testapp.post('/CreateStream', params)
    expected_result = json.dumps({"errorcode": 0})    
    self.assertEqual(response.normal_body, expected_result)
    
    # searchStream2 - tag contains subset of connexus
    streamname = 'stream2'
    coverurl = 'www.test2.com'
    currentuser = 'ss2@gmail.com'
    subscribers = ['bo2@done.com','jo2@dawn.com']
    tags = ['connexusTag2', 'sstr2']
    params = json.dumps({"streamname":streamname,"coverurl":coverurl,"currentuser":currentuser, "subscribers":subscribers, "tags":tags})
    response = self.testapp.post('/CreateStream', params)
    expected_result = json.dumps({"errorcode": 0})    
    self.assertEqual(response.normal_body, expected_result)
    
    # searchStream3 - stream name is exact match of connexus
    streamname = 'connexus'
    coverurl = 'www.test3.com'
    currentuser = 'ss3@gmail.com'
    subscribers = ['bo3@done.com','jo3@dawn.com']
    tags = ['astr3']
    params = json.dumps({"streamname":streamname,"coverurl":coverurl,"currentuser":currentuser, "subscribers":subscribers, "tags":tags})
    response = self.testapp.post('/CreateStream', params)
    expected_result = json.dumps({"errorcode": 0})    
    self.assertEqual(response.normal_body, expected_result)

    # searchStream4 - tags name is exact match of connexus
    streamname = 'stream4'
    coverurl = 'www.test4.com'
    currentuser = 'ss4@gmail.com'
    subscribers = ['bo4@done.com','jo4@dawn.com']
    tags = ['astr4','connexus']
    params = json.dumps({"streamname":streamname,"coverurl":coverurl,"currentuser":currentuser, "subscribers":subscribers, "tags":tags})
    response = self.testapp.post('/CreateStream', params)
    expected_result = json.dumps({"errorcode": 0})    
    self.assertEqual(response.normal_body, expected_result)
   
    expected_result = [u'connexusStream1', u'connexus', u'stream2', u'stream4']   
    logging.info("Expected Result: " + str(expected_result))

    searchStreamJSON = json.dumps({"streamname": ["connexus"]})
    response = self.testapp.post('/SearchStreams', searchStreamJSON)
    #logging.info("Response Body : " + str(response.normal_body))
    responseData = json.loads(response.normal_body)
    logging.info("Response Body : " + str(responseData))
   
    resultStreamNames = list()
    for item in responseData:
      resultStreamNames.append(item['streamname'])
    logging.info("Streams found: " + str(resultStreamNames))

    #logging.info("Stream Name list : " + result) 
    #self.assertEqual('connexus', result[0])
    self.assertEqual(resultStreamNames, expected_result)
