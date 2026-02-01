import Toybox.Application;
import Toybox.Lang;
import Toybox.WatchUi;
import Toybox.Time;
import Toybox.Application.Storage;
import Toybox.Communications;
import Toybox.Timer;
using Toybox.System;

const IMG_NUM = 7;
var img_request_response = 200;
var imgs_remaining = IMG_NUM-1;

var current_radar_id = "IDR063";  // Sydney radar
var URL_FORMAT = "http://betterweather.nickhespe.com/images/$1$-$2$.png";

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
        var parameters = null;
        var options = {
            :dithering => Communications.IMAGE_DITHERING_NONE,
            :packingFormat => Communications.PACKING_FORMAT_YUV
        };

        System.println(Lang.format("Requesting Image: $1$",[url]));
        Communications.makeImageRequest(url, parameters, options, method(:onImageReceived));
    }

    function GetImages() as Void{
        imgs_remaining = IMG_NUM-1;
        MakeRequest( Lang.format(URL_FORMAT, [current_radar_id, imgs_remaining]) );
    }

    function initialize() {
        AppBase.initialize();

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

        // Start downloading immediately
        System.println("Starting image download for Sydney (IDR063)");
        GetImages();
    }

    // onStart() is called on application start up
    function onStart(state as Dictionary?) as Void {
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
