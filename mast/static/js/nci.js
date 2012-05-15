(function() {
    /**
        Adds the lat and long, if available, to a form
    **/
    var geopos = 0;
    
    var useCurrentPosition = function(success,error) {
        // if we have geopos just use that
        if (geopos) {
            success(geopos);
            return;
        }
        // otherwise try to get it
        var func = function(pos) {
            // store the returned pos so we don't have to check every call
            geopos = pos;
            // call the given function
            success(pos);
        };
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(success,error);
        } else {
            error();
        }
    };
    
    var addGeo = function(frm) {
        var lat = frm.find('input:hidden[name="lat"]');
        var lon = frm.find('input:hidden[name="lon"]');
        var setCoords = function(pos) {
            lat.val(pos.coords.latitude);
            lon.val(pos.coords.longitude);
        };
        useCurrentPosition(setCoords);
    };
    
    var nci = {
        'addGeo': addGeo
    };
    window.nci = nci;
})();