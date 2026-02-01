import Toybox.Application;
import Toybox.Lang;
import Toybox.WatchUi;
import Toybox.Time;
import Toybox.Application.Storage;
import Toybox.Communications;
import Toybox.Timer;
import Toybox.Position;
using Toybox.System;

const IMG_NUM = 7;
var img_request_response = 200;
var imgs_remaining = IMG_NUM-1;

// GPS and radar state
var current_radar_id = "IDR063";  // Default to Sydney
var gps_acquired = false;
var radar_id_received = false;

var URL_FORMAT = "http://betterweather.nickhespe.com/images/$1$-$2$.png";  // radar_id-index

var imgs_template = new Array<Null or WatchUi.BitmapResource>[IMG_NUM];

class BetterWeatherApp extends Application.AppBase {

    var refreshImgTimer = new Timer.Timer();

    function onImageReceived(responseCode as $.Toybox.Lang.Number , data as Null or $.Toybox.Graphics.BitmapReference or $.Toybox.WatchUi.BitmapResource) as Void {
        img_request_response = responseCode;
        System.println(Lang.format("Image response: $1$ for index: $2$", [responseCode, imgs_remaining]));

        if (responseCode == 200) {
            // Store img in Storage
            var imgs = Storage.getValue("radar_imgaes");
            if(imgs != null) {
                imgs[imgs_remaining] = data;
                Storage.setValue("radar_imgaes", imgs);
                System.println(Lang.format("Stored image $1$", [imgs_remaining]));
            }

            // Check if any images remaining
            if( imgs_remaining != 0 ){
                // Decrement image counter
                imgs_remaining--;
                MakeRequest( Lang.format(URL_FORMAT, [current_radar_id, imgs_remaining]) );
            }else{
                System.println("All images downloaded, starting refresh timer");
                refreshImgTimer.start(method(:GetImages), 5*60000, false);
            }
        } else {
            // On error, continue to next image instead of retrying same one
            System.println(Lang.format("Failed to download image $1$: $2$", [imgs_remaining, responseCode]));
            if( imgs_remaining != 0 ){
                imgs_remaining--;
                MakeRequest( Lang.format(URL_FORMAT, [current_radar_id, imgs_remaining]) );
            } else {
                // All downloads attempted, retry all after delay
                refreshImgTimer.start(method(:GetImages), 30000, false);
            }
        }
    }
    
    function MakeRequest(url as String) {
        var parameters = null;                                  // set the parameters
        var options = {                                         // set the options
            :dithering => Communications.IMAGE_DITHERING_NONE,
            :packingFormat => Communications.PACKING_FORMAT_YUV
        };

        // Make the image request
        System.println(Lang.format("Requesting Image: $1$",[url]));
        Communications.makeImageRequest(url, parameters, options, method(:onImageReceived));
    }

    function GetImages() as Void{
        imgs_remaining = IMG_NUM-1;
        MakeRequest( Lang.format(URL_FORMAT, [current_radar_id, imgs_remaining]) );
    }

    function onLocationUpdate(info as Position.Info) as Void {
        if (info has :position && info.position != null) {
            var pos = info.position.toDegrees();
            var lat = pos[0];
            var lon = pos[1];
            System.println(Lang.format("GPS Location: $1$, $2$", [lat, lon]));
            gps_acquired = true;
            SendLocationToServer(lat, lon);
        } else {
            System.println("GPS position unavailable, using default Sydney radar");
            gps_acquired = true;
            radar_id_received = true;
            WatchUi.requestUpdate();
        }
    }

    function SendLocationToServer(lat as Double, lon as Double) as Void {
        var url = Lang.format("http://betterweather.nickhespe.com/api/location?lat=$1$&lon=$2$", [lat, lon]);
        var params = {};
        var options = {
            :method => Communications.HTTP_REQUEST_METHOD_GET,
            :responseType => Communications.HTTP_RESPONSE_CONTENT_TYPE_JSON
        };

        System.println(Lang.format("Sending GPS to server: $1$", [url]));
        Communications.makeWebRequest(url, params, options, method(:onLocationSent));
    }

    function onLocationSent(responseCode as Number, data as Dictionary or String or Null) as Void {
        System.println(Lang.format("Location sent response: $1$", [responseCode]));
        if (responseCode == 200 && data != null && data instanceof Dictionary) {
            System.println(Lang.format("Server response: $1$", [data]));

            // Extract radar_id from response
            var new_radar_id = data.get("radar_id");
            if (new_radar_id != null && new_radar_id instanceof String) {
                System.println(Lang.format("Received radar ID: $1$", [new_radar_id]));

                var radar_changed = !new_radar_id.equals(current_radar_id);
                var first_time = !radar_id_received;

                // Update radar if changed or first time
                if (radar_changed || first_time) {
                    if (radar_changed) {
                        System.println(Lang.format("Radar changed from $1$ to $2$, re-downloading images", [current_radar_id, new_radar_id]));
                    } else {
                        System.println(Lang.format("First radar ID received: $1$, starting download", [new_radar_id]));
                    }

                    current_radar_id = new_radar_id;
                    Storage.setValue("radar_id", current_radar_id);

                    // Clear existing images and re-download
                    var imgs = new Array<Null or WatchUi.BitmapResource>[IMG_NUM];
                    for(var i = 0; i < IMG_NUM; i++) {
                        imgs[i] = null;
                    }
                    Storage.setValue("radar_imgaes", imgs);
                    GetImages();
                }

                radar_id_received = true;
                WatchUi.requestUpdate();
            }
        }
    }

    function initialize() {
        AppBase.initialize();

        // Load saved radar_id if available
        var saved_radar_id = Storage.getValue("radar_id");
        if (saved_radar_id != null && saved_radar_id instanceof String) {
            current_radar_id = saved_radar_id;
            radar_id_received = true;  // We have a cached radar ID
            System.println(Lang.format("Loaded saved radar ID: $1$", [current_radar_id]));
        }

        // Initialize storage array if it doesn't exist
        var imgs = Storage.getValue("radar_imgaes");
        if(imgs == null){
            imgs = new Array<Null or WatchUi.BitmapResource>[IMG_NUM];
            for(var i = 0; i < IMG_NUM; i++) {
                imgs[i] = null;
            }
            Storage.setValue("radar_imgaes", imgs);
            System.println("Initialized radar images array");
        }

        // Only start downloading if we have a cached radar_id
        // Otherwise, wait for GPS to provide one
        if (radar_id_received) {
            System.println("Using cached radar, starting download");
            GetImages();
        } else {
            System.println("No cached radar, waiting for GPS");
        }
    }

    // onStart() is called on application start up
    function onStart(state as Dictionary?) as Void {
        // Request GPS position
        System.println("Requesting GPS position...");
        Position.enableLocationEvents(Position.LOCATION_ONE_SHOT, method(:onLocationUpdate));
    }

    function onUpdate() as Void {
        System.println("hey");
        if (imgs_remaining == IMG_NUM-1){
            MakeRequest( Lang.format(URL_FORMAT, [current_radar_id, imgs_remaining]) );
        }
    }

    // onStop() is called when your application is exiting
    function onStop(state as Dictionary?) as Void {
    }   

    // Return the initial view of your application here
    function getInitialView() as Array<Views or InputDelegates>? {
        return [ new BetterWeatherView(), new RadarDelegate(method(:GetImages)) ] as Array<Views or InputDelegates>;
    }
}

function getApp() as BetterWeatherApp {
    return Application.getApp() as BetterWeatherApp;
}




