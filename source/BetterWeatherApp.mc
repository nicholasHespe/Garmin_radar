import Toybox.Application;
import Toybox.Lang;
import Toybox.WatchUi;
import Toybox.Time;

const IMG_NUM = 7;
var img_request_response = 200;
var imgs_remaining = IMG_NUM-1;

var URL_FORMAT = "http://betterweather.nickhespe.com/images/$1$.png";

var imgs_template = new Array<Null or WatchUi.BitmapResource>[IMG_NUM];

class BetterWeatherApp extends Application.AppBase {

    var refreshImgTimer = new Timer.Timer();

    function onImageReceived(responseCode as $.Toybox.Lang.Number , data as Null or $.Toybox.Graphics.BitmapReference or $.Toybox.WatchUi.BitmapResource) as Void {
        img_request_response = responseCode;
        if (responseCode != 200) {
            MakeRequest( Lang.format(URL_FORMAT , [imgs_remaining] ) );
        }else{
            // Store img in Storage
            var imgs = Storage.getValue("radar_imgaes");
            imgs[imgs_remaining] = data;
            Storage.setValue("radar_imgaes",imgs);
            
            // Check if any images remaining
            if( imgs_remaining != 0 ){
                // Decrement image counter
                imgs_remaining--;
                MakeRequest( Lang.format(URL_FORMAT , [imgs_remaining] ) );
            }else{
                refreshImgTimer.start(method(:GetImages), 5*60000, false);
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
        MakeRequest( Lang.format(URL_FORMAT , [imgs_remaining] ) );
    }

    function initialize() {
        AppBase.initialize();
        if(Storage.getValue("radar_imgaes") == null){
            Storage.deleteValue("radar_imgaes");
            Storage.setValue("radar_imgaes", imgs_template);
            System.println("Reset imgaes");
        }
        GetImages();       
    }

    // onStart() is called on application start up
    function onStart(state as Dictionary?) as Void {
    }

    function onUpdate() as Void {
        System.println("hey");
        if (imgs_remaining == IMG_NUM-1){
            MakeRequest( Lang.format(URL_FORMAT , [imgs_remaining] ) );
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




