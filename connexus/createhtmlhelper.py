MGMT_PAGE_HTML = """<h3>Streams I own</h3>
<style type="text/css">
.tg  {border-collapse:collapse;border-spacing:0;}
.tg tr {border:none;}
.tg td{font-family:Arial, sans-serif;font-size:14px;padding:10px 5px; border-right: solid 1px; border-left: solid 1px; border-top:none; border-bottom:none; border-width:0px;overflow:hidden;word-break:normal;}
.tg th{font-family:Arial, sans-serif;font-size:14px;font-weight:normal;padding:10px 5px;border-style:none;border-width:0px;overflow:hidden;word-break:normal;}</style>
<table class="tg">
  <tr>
    <th class="tg-031e">Name</th>
    <th class="tg-031e">Last Picture</th>
    <th class="tg-031e">Number of Pictures</th>
    <th class="tg-031e">Delete</th>
  </tr>
<!--will need to dynamically generate each ITEM based on streamlist-->
%s
</table>

<class="buttons"><input type="hidden" name="form_id" value="903438" /><br>
<input id="delete_checked" class="button_text" type="submit" name="delete_checked" value="Delete Checked Streams" /></></body></html>
<h3>Streams I subscribe to</h3>

<style type="text/css">
.tg  {border-collapse:collapse;border-spacing:0;}
.tg tr {border:none;}
.tg td{font-family:Arial, sans-serif;font-size:14px;padding:10px 5px;border-style:solid;border-right: solid 1px; border-left: solid 1px; border-top: none; border-bottom: none; border-width:1px;overflow:hidden;word-break:normal;}
.tg th{font-family:Arial, sans-serif;font-size:14px;font-weight:normal;padding:10px 5px;border-style:solid;border-width:0px;overflow:hidden;word-break:normal;}
</style>
<table class="tg">
  <tr>
    <th class="tg-031e">Name</th>
    <th class="tg-031e">Last Picture</th>
    <th class="tg-031e">Number of Pictures</th>
    <th class="tg-031e">Views</th>
    <th class="tg-031e">Unsubscribe</th>
  </tr>
<style>
.submitLink {
background-color: transparent;
text-decoration: underline;
border: none;
color: blue;
cursor: pointer;
}
</style>
%s
</table>

<class="buttons"><input type="hidden" name="form_id" value="903438" /><br>
<input id="unsubscribe_checked" class="button_text" type="submit" name="unsubscribe_checked" value="Unsubscribe Checked Streams" /></></body></html>"""

def generatestreamsiownlist(updatelist):
  BEGIN = '<tr>'
  START_ITEM_HTML = '<td class="tg-031e">'
  NAME_LINK = '<class="buttons"><input type="hidden" name="form_id" value="903438" /><br><input id="view" class="submitLink" type="submit" name="view" value="'
  NAME_LINK2 = '" />'
  END_ITEM_HTML = '</td>'
  START_CHECKBOX = '<td class="tg-031e"><input id="own-'
  MIDDLE_CHECKBOX = '" name="own-'
  MIDDLE_CHECKBOX_2 = '" class="element checkbox" type="checkbox" value="'
  END_CHECKBOX = '" /></td></tr>'
  htmlstringfinal = ""
  length = len(updatelist['streamnames'])
  for x in range(0,length):
    htmlstringfinal = htmlstringfinal + BEGIN + START_ITEM_HTML + NAME_LINK + updatelist['streamnames'][x] + NAME_LINK2 + END_ITEM_HTML + START_ITEM_HTML+ updatelist['dates'][x] + END_ITEM_HTML + START_ITEM_HTML + str(updatelist['imagenums'][x]) + END_ITEM_HTML
    htmlstringfinal = htmlstringfinal + START_CHECKBOX + str(x) + MIDDLE_CHECKBOX + str(x) + MIDDLE_CHECKBOX_2 + updatelist['streamnames'][x] + END_CHECKBOX
  return htmlstringfinal

def generatestreamssubscribed(updatelist):
  BEGIN = '<tr>'
  START_ITEM_HTML = '<td class="tg-031e">'
  END_ITEM_HTML = '</td>'
  START_CHECKBOX = '<td class="tg-031e"><input id="sub-'
  MIDDLE_CHECKBOX = '" name="sub-'
  MIDDLE_CHECKBOX_2 = '" class="element checkbox" type="checkbox" value="'
  END_CHECKBOX = '" /></td></tr>'
  htmlstringfinal = ""
  length = len(updatelist['streamnames'])
  for x in range(0,length):
    htmlstringfinal = htmlstringfinal + BEGIN + START_ITEM_HTML + updatelist['streamnames'][x] + END_ITEM_HTML + START_ITEM_HTML+ updatelist['dates'][x] + END_ITEM_HTML + START_ITEM_HTML + str(updatelist['imagenums'][x]) + END_ITEM_HTML + START_ITEM_HTML + str(updatelist['views'][x]) + END_ITEM_HTML
    htmlstringfinal = htmlstringfinal + START_CHECKBOX + str(x) + MIDDLE_CHECKBOX + str(x) + MIDDLE_CHECKBOX_2 + updatelist['streamnames'][x] + END_CHECKBOX
  return htmlstringfinal 

myupdatelist = {'streamnames':['amy1','amy2','amy3'],'dates':['10-30-2014','12-20-2014','3-5-2014'],'imagenums':[34,700,2]}
html = generatestreamsiownlist(myupdatelist)
myupdatelist2 = {'streamnames':['amy1','amy2','amy3'],'dates':['10-30-2014','12-20-2014','3-5-2014'],'views':[10000,400,12],'imagenums':[34,700,2]}
html2 = generatestreamssubscribed(myupdatelist2)
html = MGMT_PAGE_HTML % (html,html2)
print html
jsonfile = open("listtest.html",'w')
jsonfile.write(html)
jsonfile.close()


