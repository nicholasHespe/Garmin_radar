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
        
        // var radar_imgaes = Storage.getValue("radar_imgaes");
        var wp = Storage.getValue("weatherPage");
        var img = null;
        if(Storage.getValue("radar_imgaes")){
            img = Storage.getValue("radar_imgaes")[wp];
        }

        dc.setColor(Graphics.COLOR_BLACK ,Graphics.COLOR_TRANSPARENT );
        dc.setPenWidth(4);

        if($.imgs_remaining != 0){
            dc.setColor(Graphics.COLOR_DK_RED ,Graphics.COLOR_TRANSPARENT );
        }        
        

        if( img instanceof WatchUi.BitmapResource){
            dc.drawBitmap(0,0,img);
            //dc.drawText(120, 100, Graphics.FONT_MEDIUM, Storage.getValue("radar_imgaes").toString(), Graphics.TEXT_JUSTIFY_CENTER);
        }
        dc.drawArc(120,120,120*0.95,Graphics.ARC_CLOCKWISE,90, (wp*30+89-($.IMG_NUM-1)*30) % 360 );

        if($.img_request_response != 200){
            dc.drawText(120, 120, Graphics.FONT_MEDIUM, Lang.format("Failed request : $1$", [$.img_request_response]), Graphics.TEXT_JUSTIFY_CENTER);    
        }
    }
    
    // function onUpdate(dc) as Void {
    //     dc.drawArc(120,120,120*0.9,Graphics.ARC_CLOCKWISE,90,Storage.getValue("weatherPage"));
    // }
}
