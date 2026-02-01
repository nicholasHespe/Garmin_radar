import Toybox.Graphics;
import Toybox.WatchUi;
import Toybox.Application.Storage;
import Toybox.Timer;
using Toybox.System;
using Toybox.Communications;
import Toybox.Lang;



class BetterWeatherView extends WatchUi.View {

    var myTimer = new Timer.Timer();
    var updateTime = 500;

    function timerCallback() {
        var wp = Storage.getValue("weatherPage");
        updateTime = 500;
        wp++;
        if(wp >= $.IMG_NUM){
            wp = 0;
        }
        if( wp >= $.IMG_NUM - 1 ){
            updateTime = 2000;
        }
        Storage.setValue("weatherPage",wp);
        WatchUi.requestUpdate();
        myTimer.start(method(:timerCallback), updateTime, false);
    }

    function initialize() {
        View.initialize();
        Storage.setValue("weatherPage",0);
        myTimer.start(method(:timerCallback), updateTime, false);
    }

    // Load your resources here
    function onLayout(dc as Dc) as Void {
        setLayout(Rez.Layouts.MainLayout(dc));
    }

    // Called when this View is brought to the foreground. Restore
    // the state of this View and prepare it to be shown. This includes
    // loading resources into memory.
    function onShow() as Void {
    }

    // Update the view
    function onUpdate(dc as Dc) as Void {
        // Call the parent onUpdate function to redraw the layout
        View.onUpdate(dc);
    }

    // Called when this View is removed from the screen. Save the
    // state of this View here. This includes freeing resources from
    // memory.
    function onHide() as Void {
    }

}

class CustomTimeRing extends WatchUi.Drawable {


    //private var fn = [230404,230409,230414,230419,230424,230434,23039,230444,230449,230454,230459,230504];

    public function initialize(params as Dictionary) {
        // You should always call the parent's initializer and
        // in this case you should pass the params along as size
        // and location values may be defined.
        Drawable.initialize(params);
    }
    
    function draw(dc as Dc) as Void {
        // Clear screen
        dc.setColor(Graphics.COLOR_BLACK, Graphics.COLOR_BLACK);
        dc.clear();

        var wp = Storage.getValue("weatherPage");
        var img = null;
        if(Storage.getValue("radar_imgaes")){
            img = Storage.getValue("radar_imgaes")[wp];
        }

        // Check if we have images loaded
        var hasImages = (img instanceof WatchUi.BitmapResource);

        if (!hasImages) {
            // Show loading screen
            dc.setColor(Graphics.COLOR_WHITE, Graphics.COLOR_TRANSPARENT);
            dc.drawText(120, 80, Graphics.FONT_MEDIUM, "BetterWeather", Graphics.TEXT_JUSTIFY_CENTER);
            dc.drawText(120, 120, Graphics.FONT_SMALL, "Loading radar...", Graphics.TEXT_JUSTIFY_CENTER);

            // Show download progress
            if($.imgs_remaining >= 0 && $.imgs_remaining < $.IMG_NUM){
                var progress = (($.IMG_NUM - 1 - $.imgs_remaining) * 100) / $.IMG_NUM;
                dc.drawText(120, 160, Graphics.FONT_TINY, Lang.format("$1$%", [progress.toNumber()]), Graphics.TEXT_JUSTIFY_CENTER);
            }
        } else {
            // Draw the radar image (now includes background from server)
            dc.drawBitmap(0, 0, img);

            // Draw progress arc
            dc.setColor(Graphics.COLOR_WHITE, Graphics.COLOR_TRANSPARENT);
            dc.setPenWidth(4);

            // Red arc while downloading
            if($.imgs_remaining != 0){
                dc.setColor(Graphics.COLOR_DK_RED, Graphics.COLOR_TRANSPARENT);
            }

            dc.drawArc(120, 120, 120*0.95, Graphics.ARC_CLOCKWISE, 90, (wp*30+89-($.IMG_NUM-1)*30) % 360);
        }

        // Show error message if request failed
        if($.img_request_response != 200 && $.img_request_response != 0){
            dc.setColor(Graphics.COLOR_WHITE, Graphics.COLOR_DK_RED);
            dc.fillRectangle(20, 100, 200, 40);
            dc.setColor(Graphics.COLOR_BLACK, Graphics.COLOR_TRANSPARENT);
            dc.drawText(120, 120, Graphics.FONT_SMALL, Lang.format("Error: $1$", [$.img_request_response]), Graphics.TEXT_JUSTIFY_CENTER);
        }
    }
    
    // function onUpdate(dc) as Void {
    //     dc.drawArc(120,120,120*0.9,Graphics.ARC_CLOCKWISE,90,Storage.getValue("weatherPage"));
    // }
}
