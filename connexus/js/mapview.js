($(function() { 

    var imageurls = new Array();
    var imagecreationdates = new Array();
    var imagelatitudes = new Array();
    var imagelongitudes = new Array();
    var markers = [];
    var markerhash = [];
    var markerCluster = {};
    var seconddate = new Date();
    var firstdate = new Date();


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
            markerCluster = new MarkerClusterer(map, markers);
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
					markers.push(imagemarker);
					markerCluster.addMarker(imagemarker);
					google.maps.event.addListener(imagemarker, 'mouseover', function() { this['infowindow'].open(map, this); });
                }
            } 
        });
    }});
});

$(document).ready(function () {
        // Initialize jquery slider
        $("#slider").slider({  
        	 range: true,
             min: 0,
             max: 365,
             step: 1,
             values: [1,365],
             change: function( event, ui ) {}
            	 
     });
    var slider1 = $('.ui-slider-handle:first');
    var slider2 = $('.ui-slider-handle:last');
    var position1 = slider1.offset();
    var position2 = slider2.offset();
    console.log("position is: " + position1.left + ' ' + position1.top);
    console.log("position is: " + position2.left + ' ' + position2.top);
    seconddate.setDate(firstdate.getDate() - 365);
    var firstday = firstdate.getDate();
    var firstmonth = firstdate.getMonth() + 1;
    var firstyear = firstdate.getFullYear();
    var secondday = seconddate.getDate();
    var secondmonth = seconddate.getMonth() + 1;
    var secondyear = seconddate.getFullYear();
    console.log("First date: " + firstmonth + "/" + firstday + "/" + firstyear);
    console.log("second date: " + secondmonth + "/" + secondday + "/" + secondyear);
    $("#handle1").html(firstmonth + "/" + firstday + "/" + firstyear);
    $("#handle1").css("position","absolute");
    $("#handle1").css("top",position1.top+30);
    $("#handle1").css("left",position1.left);
    $("#handle2").html(secondmonth + "/" + secondday + "/" + secondyear);
    $("#handle2").css("position","absolute");
    $("#handle2").css("top",position2.top+30);
    $("#handle2").css("left",position2.left-40);

     $( "#slider" ).on( "slidechange", function( event, ui ) {

        	var myvalues = $( "#slider" ).slider( "option", "values" );
        	console.log("Lenght is: " + myvalues.length);
        	console.log("My values: " + myvalues);
        	console.log("My val1: " + myvalues[0]);
        	console.log("My val2: " + myvalues[1]);
        	console.log("Imageurls length: " + imageurls.length);
        	console.log("Markers length: " + markers.length);
        	//get date
        	//iterate through markers
            var slider1 = $('.ui-slider-handle:first');
            var slider2 = $('.ui-slider-handle:last');
            var position1 = slider1.offset();
            var position2 = slider2.offset();
            console.log("position is: " + position1.left + ' ' + position1.top);
            console.log("position is: " + position2.left + ' ' + position2.top);
            firstdate = new Date();
            firstdate.setDate(firstdate.getDate() - (365-myvalues[0]));
            console.log("First date: " + firstdate)
            var firstday = firstdate.getDate();
            var firstmonth = firstdate.getMonth() + 1;
            var firstyear = firstdate.getFullYear();
            seconddate = new Date();
            seconddate.setDate(seconddate.getDate() - (365-myvalues[1]));
            console.log("Second date: " + seconddate)
            var secondday = seconddate.getDate();
            var secondmonth = seconddate.getMonth() + 1;
            var secondyear = seconddate.getFullYear();
            console.log("First date: " + firstmonth + "/" + firstday + "/" + firstyear);
            console.log("second date: " + secondmonth + "/" + secondday + "/" + secondyear);            
            seconddate = seconddate.getDate();
            $("#handle1").html(firstmonth + "/" + firstday + "/" + firstyear);
            $("#handle1").css("position","absolute");
            $("#handle1").css("top",position1.top+30);
            $("#handle1").css("left",position1.left);
            $("#handle2").html(secondmonth + "/" + secondday + "/" + secondyear);
            $("#handle2").css("position","absolute");
            $("#handle2").css("top",position2.top+30);
            $("#handle2").css("left",position2.left-40);

            markerCluster.clearMarkers();
            console.log("clear markers");
            if (markers.length > 0) {    
                console.log("markers length is greater than 0")
                for ( var i = 0; i < markers.length; i++ ) {
                    console.log("this image date is: " + (365-imagecreationdates[i]));
                    if((365-imagecreationdates[i]) >= myvalues[0] && (365-imagecreationdates[i]) <= myvalues[1]) {
                        console.log('Adding marker: ' + i);
                        markerCluster.addMarker(markers[i]);
                    }
                    else {
                        markerCluster.removeMarker(markers[i]);
                        console.log('removing marker: ' + i);          
                    }
                }
            } 
        });
    });

} (jQuery)));
