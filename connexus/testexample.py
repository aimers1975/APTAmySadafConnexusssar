+import json
 import httplib
 import urllib

-globals = {
+globals = {
            "server": "localhost",
+           "port"  : "8080",
            # prepare request header
            "headers": {"Content-type": "application/json", "Accept": "text/plain"},
-           "userId": "Adnan Aziz"
+           "userId": "TODO"
           }

-conn = httplib.HTTPConnection(globals["server"])
+conn = httplib.HTTPConnection(globals["server"],globals["port"])

 def send_request(conn, url, req):
+    print "json request:"
     print '%s' % json.dumps(req)
     conn.request("POST", url, json.dumps(req), globals["headers"])
     resp = conn.getresponse()
+    print "status reason"
+    print resp.status, resp.reason
     jsonresp = json.loads(resp.read())
     print '  %s' % jsonresp
     return jsonresp

@@ -26,3 +39,11 @@ def place_create_request(conn):
     return res

 # many more functions like the above
+
+if __name__ == '__main__':
+
+  service = 'jsonreturntest'
+  serviceUrl = '/' + service
+  import random;
+  tmpRequest = str(random.random()) # send any request for now
+  send_request(conn,serviceUrl,tmpRequest)