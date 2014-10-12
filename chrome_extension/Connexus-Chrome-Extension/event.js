//Chrome Extension sample code reference: http://markashleybell.com/building-a-simple-google-chrome-extension.html
//called onload in the popup code
function getPageDetails(callback) { 
    // Inject the content script into the popup page 
    chrome.tabs.executeScript(null, { file: 'content.js' }); 
    chrome.runtime.onMessage.addListener(function(message)  { 
        callback(message); 
    }); 
}; 

chrome.runtime.onInstalled.addListener(function() {
  var context = "image";
  var title = "Upload to Connexus Stream";
  var id = chrome.contextMenus.create({
    "title": title, 
    "contexts":[context],
    "id": "context" + context
  });  
});

// add click event
chrome.contextMenus.onClicked.addListener(onClickHandler);

function onClickHandler(info, tab) {
  var details = {}

  // get the image url
  details.imgurl = info.srcUrl;

  chrome.windows.create({ url: 'popup.html', type: 'popup', width: 700, height: 500 }, function() {
  	chrome.runtime.sendMessage({ details: details }, function(response) {});
  });
}