//Chrome Extension sample code reference: http://markashleybell.com/building-a-simple-google-chrome-extension.html
// Send a message with the imagr url to the popup
chrome.runtime.sendMessage({
    'title': document.title,
    'url': window.location.href,
    'comments': window.getSelection().toString(),
    'img1': window.location.src
});