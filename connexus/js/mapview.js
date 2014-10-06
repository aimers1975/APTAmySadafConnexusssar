($(function() { 

    var imageurls = new Array();
    var imagecreationdates = new Array();
    var imagelatitudes = new Array();
    var imagelongitudes = new Array();
    var markers = [];
    var markerhash = [];


$(function() {
	$.ajax({url: "/GetAllImages",success:function(data) {
		console.log(data)
		var json = JSON.parse(data);
        imagecreationdates = json.creationdatelist;
        imagelatitudes = json.imagelatitudelist;
        imagelongitudes = json.imagelongitudelist;
        imageurls = json.imageurllist; 
        console.log("in ajax call");
   	    console.log("imageurls: " + imageurls);
	    console.log("latitude: " + imagelatitudes);
	    console.log("longitude: " + imagelongitudes);
	    console.log("length is: " + imageurls.length);
	    var yourStartLatLng = new google.maps.LatLng(31, -98);
        $('#map_canvas').gmap({'center': yourStartLatLng});
        console.log("imageurl length: " + imageurls.length);

        $('#map_canvas').gmap({'zoom': 2, 'disableDefaultUI':true}).bind('init', function(evt, map) {
	        var markerCluster = new MarkerClusterer(map, markers);
	        if (imageurls.length > 0) {    
	            for ( var i = 0; i < imageurls.length; i++ ) {
	        	    var contentstring = '<div id="content"><IMG SRC="' + imageurls[i] + '" ALT="some text" WIDTH=100 HEIGHT=100></div>';
	        	    console.log('Image ' + i + ": " + contentstring);
	        	    imagelat = imagelatitudes[i] + (i*.0002);
	        	    var infowindow = new google.maps.InfoWindow({ content: contentstring });
				    var myLatLng = new google.maps.LatLng(imagelat,imagelongitudes[i]);
				    var imagemarker = new google.maps.Marker({
				        position: myLatLng,
				        map: map,
				    });
				    imagemarker['infowindow'] = new google.maps.InfoWindow({ content: contentstring});
					console.log('Created marker');
					markerCluster.addMarker(imagemarker)
					google.maps.event.addListener(imagemarker, 'mouseover', function() { this['infowindow'].open(map, this); });
                }
            } 
        });
    }});
});
} (jQuery)));
