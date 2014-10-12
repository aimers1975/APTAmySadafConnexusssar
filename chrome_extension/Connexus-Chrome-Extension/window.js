//Chrome Extension sample code reference: http://markashleybell.com/building-a-simple-google-chrome-extension.html
chrome.runtime.onMessage.addListener(
  function(req, sender, sendResponse) {
  if (req.details) {
    var details = req.details;
    $('input[name="imgurl"]').val(details.imgurl);
    $('input[name="img1"]').val(details.imgurl);
  }
});