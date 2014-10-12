function onPageDetailsReceived(pageDetails)  { 
    document.getElementById('title').value = pageDetails.title; 
    document.getElementById('url').value = pageDetails.url; 
    document.getElementById('comments').innerText = pageDetails.comments; 
} 

var statusDisplay = null;

// POST the data to the connexus server using XMLHttpRequest
function uploadImage() {
    event.preventDefault();

    // Connexus POST URL
    var postUrl = 'http://connexusssar.com/UploadUrlImage';

    //asynchronous AJAX POST request
    var xhr = new XMLHttpRequest();
    xhr.open('POST', postUrl, true);
    
    // get the data from the popup
    var title = document.getElementById('title').value;
    var imageurl = document.getElementById('imgurl').value;
    var comments = encodeURIComponent(document.getElementById('comments').value);

    //var tmpdirectory = chrome.extension.getURL("tmp/image.jpeg");
    //console.log(tmpdirectory);

    //chrome.downloads.download({
    //    url: imageurl,
    //    filename: tmpdirectory
    //});
    
    var data = {};
    data['imageurl'] = imageurl;
    data['streamname'] = title;
    data['contenttype'] = 'image/jpeg';
    data['comments'] = comments;

    // Handle request state change events
    xhr.onreadystatechange = function() { 
        // If the request completed
        if (xhr.readyState == 4) {
            statusDisplay.innerHTML = '';
            if (xhr.status == 200) {
                // close the popup when successful
                statusDisplay.innerHTML = 'Image Uploaded to Connexus';
                window.setTimeout(window.close, 1000);
            } else {
                statusDisplay.innerHTML = 'Error while uploading to Connexus:' + xhr.statusText;
            }
        }
    };

    // Send the request to connexus instance
    xhr.send(JSON.stringify(data));
    statusDisplay.innerHTML = 'Saving now... ';
}

// after loading the popup html
window.addEventListener('load', function(evt) {
    statusDisplay = document.getElementById('status-display');
    // Handle the upload form submit event with uploadImage function
    document.getElementById('uploadimage').addEventListener('submit', uploadImage);

    chrome.runtime.getBackgroundPage(function(eventPage) {
        eventPage.getPageDetails(onPageDetailsReceived);
    });
});