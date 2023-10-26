import Toybox.Lang;
import Toybox.WatchUi;

class RadarDelegate extends WatchUi.BehaviorDelegate {

    var mRadarCallback as Lang.Method;

    public function initialize( reloadImagesCallback ) {
        BehaviorDelegate.initialize();
        mRadarCallback = reloadImagesCallback;
    }

    function onPreviousPage() as Boolean {
        mRadarCallback.invoke();
        return true;
    }
}