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

VIEW_STREAM_HTML = """<form action="/ViewPageHandler" method="post" enctype="multipart/form-data"></div><div><table class="tg">%s</table></></body></html>"""




def generateimagelinks(urllist,streamnamelist):
	BEGIN_ROW = '<tr>'
	BEGIN_LINK = '<th class="tg-031e"><img src="'
	LINK2 = '" alt="Image Unavailable"><br><input id="'
	LINK3 = '" name="'
	LINK4 = '" type="text" input style="font-size:10px" readonly="readonly" value="'
	END_LINK = '"></th>'
	END_ROW = '</tr>'
	htmlstringfinal = ""
	length = len(urllist)
	lengthstreams = length(streamnamelist)
    fullrow = length/3
    partrow = length%3
    iternum = 0
	for x in range(0,(fullrow + 1)):
		htmlstringfinal = htmlstringfinal + BEGIN_ROW
		if x <= fullrow:
			for y in range(0,3):
				htmlstringfinal = htmlstringfinal + BEGIN_LINK + urllist[iternum] + LINK2 + streamnamelist[iternum] + LINK3 + streamnamelist[iternum] + LINK4 + streamnamelist[iternum] + END_LINK
				iternum = iternum + 1
			htmlstringfinal = htmlstringfinal + END_ROW
		else:
			for y in range(0,partrow):
				htmlstringfinal = htmlstringfinal + BEGIN_LINK + urllist[iternum] + LINK2 + streamnamelist[iternum] + LINK3 + streamnamelist[iternum] + LINK4 + streamnamelist[iternum] + END_LINK
				iternum = iternum + 1
			htmlstringfinal = htmlstringfinal + END_ROW
	return htmlstringfinal


urllist = ['http://storage.googleapis.com/connexusssar.appspot.com/amy1/027c9d6b-4123-11e4-aa6a-154df3ce051e','http://storage.googleapis.com/connexusssar.appspot.com/amy1/027c9d6b-4123-11e4-aa6a-154df3ce051e','http://storage.googleapis.com/connexusssar.appspot.com/amy1/027c9d6b-4123-11e4-aa6a-154df3ce051e','http://storage.googleapis.com/connexusssar.appspot.com/amy1/027c9d6b-4123-11e4-aa6a-154df3ce051e','http://storage.googleapis.com/connexusssar.appspot.com/amy1/027c9d6b-4123-11e4-aa6a-154df3ce051e','http://storage.googleapis.com/connexusssar.appspot.com/amy1/027c9d6b-4123-11e4-aa6a-154df3ce051e']
html = generateimagelinks(urllist)
html = HEADER_HTML + VIEW_STREAM_HTML % ('Amy', html,'0', '2')
print html
jsonfile = open("viewstest.html",'w')
jsonfile.write(html)
jsonfile.close()


