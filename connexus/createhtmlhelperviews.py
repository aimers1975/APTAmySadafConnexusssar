HEADER_HTML = """<!DOCTYPE html><html><head><title>Connex.us!</title></head>           
<body><head><h1>Connex.us</h1></head>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=ISO-8859-1">
<title>Style Test</title>
<style type="text/css">
#list 
.horizontal { display: inline; border-left: 2px solid; padding-left: 0.8em; padding-right: 0.8em; }
.first { border-left: none; padding-left: 0; }
</style>
</head>

<div>
<body>
<!--Need to add links for pages once done-->
<ul id="list">
<li class="horizontal first"><a href="http://%s/MgmtPage">Manage</a></li>  
<li class="horizontal"><a href="http://%s/CreatePage">Create</a></li>
<li class="horizontal"><a href="http://%s/ViewPage">View</a></li>
<li class="horizontal first"><a href="http://%s/SearchPage">Search</a></li>
<li class="horizontal"><a href="http://%s/TrendingPage">Trending</a></li>
<li class="horizontal"><a href="http://%s/SocialPage">Social</a></li>
</ul>"""

VIEW_STREAM_HTML = """<form action="/ViewPageHandler" method="post" enctype="multipart/form-data"></div>
<input id="Streamname" name="Streamname" type="text" input style="font-size:25px" readonly="readonly" value="%s's Stream"><br>
<div><table class="tg"><tr>
%s
    <th class="tg-031e"><class="buttons"><input id="More_Pictures" class="button_text" type="submit" name="More_Pictures" value="More Pictures" /></th>
  </tr>
</table></div>
<input id="Pagerange" name="Pagerange" type="text" input style="font-size:10px" readonly="readonly" value="Showing images: [%s-%s]"><br>
<div><br><br><table class="tg"><label class="description" for="Comments">Comments</label><br><tr><textarea id="Comments" name="Comments" class="element textarea 

medium"></textarea></tr><tr><th class="tg-031e"><input id="Filename" name="Filename" class="element file" type="file"/></th></tr>
<tr><td class="tg-031e"><class="buttons"><input id="Upload" class="button_text" type="submit" name="Upload" value="Upload" /></td></tr></table><br><br></div>
<class="buttons"><input type="hidden" name="form_id" value="903438" /><input id="Subscribe" class="button_text" type="submit" name="Subscribe" value="Subscribe" />
</></body></html>"""


def generateimagelinks(urllist):
  BEGIN = '<th class="tg-031e"><img src="'
  END = '" alt="Image Unavailable"></th>'
  htmlstringfinal = ""
  length = len(urllist)
  for x in range(0,length):
    htmlstringfinal = htmlstringfinal + BEGIN + urllist[x] + END
  return htmlstringfinal


urllist = ['http://storage.googleapis.com/connexusssar.appspot.com/amy1/027c9d6b-4123-11e4-aa6a-154df3ce051e','http://storage.googleapis.com/connexusssar.appspot.com/amy1/027c9d6b-4123-11e4-aa6a-154df3ce051e','http://storage.googleapis.com/connexusssar.appspot.com/amy1/027c9d6b-4123-11e4-aa6a-154df3ce051e']
html = generateimagelinks(urllist)
html = HEADER_HTML + VIEW_STREAM_HTML % ('Amy', html,'0', '2')
print html
jsonfile = open("viewstest.html",'w')
jsonfile.write(html)
jsonfile.close()


