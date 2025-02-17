$(document).ready(function() {
    var interval = $("#interval_config").val()
    if (!(typeof interval === "undefined")){
        setInterval(() => {
            reload_notify_publish()
        },interval)
    }
})