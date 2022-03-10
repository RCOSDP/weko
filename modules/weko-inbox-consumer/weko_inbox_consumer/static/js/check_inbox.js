
$("#check_push").on("click", function(){
    reload_notify_publish();
});

function reload_notify_publish(){
    $.ajax({
        type:"GET",
        url:"/check_inbox/publish",
        success: function(result){
            result.forEach(function(push_data){
                check_permission_and_create(push_data)
            })
        },
        error: function(result){
        }
    });
};
function check_permission_and_create(push_data){
    if (!('Notification' in window)){
        console.log("It is a browser that does not support push notifications");
    }
    else if (Notification.permission === "granted") {
        create_notification(push_data);
    }
    else if (Notification.permission !== "denied") {
        Notification.requestPermission().then(function (permission){
            if (permission === "granted"){
                create_notification(push_data);
            };
        });
    }
};

function create_notification(push_data){
    var notify = new Notification(push_data.title,{
        body:push_data.body,
        data:push_data.data
    });
    notify.onclick=function(event){
        send_data_to_flask(notify)
        window.open(push_data.url)
    };
}

function send_data_to_flask(n){
    $.ajax({
        url:"/check_inbox/push_data",
        method: "POST",
        contentType:"application/json",
        dataType:"json",
        data: JSON.stringify(n.data)
    });
};
