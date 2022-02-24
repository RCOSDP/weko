$(document).ready(function() {
    var interval = $("#interval_config").val()
    if (!(typeof interval === "undefined")){
        console.log(interval)
        setInterval(() => {
            console.log("interval method:"+interval)
            reload_notify_publish()
        },interval)
    }
})