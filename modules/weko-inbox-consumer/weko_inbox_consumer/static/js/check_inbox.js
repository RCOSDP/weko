
$("#check_push").on("click", function(){
    console.log("push botton")
    reload_notify_publish();
});

function reload_notify_publish(){
    console.log("check inbox test");
    $.ajax({
        type:"GET",
        url:"/check_inbox/publish",
        success: function(result){
            console.log(result)
            result.forEach(function(push_data){
                console.log(push_data)
                check_permission_and_create(push_data)
            })
        },
        error: function(result){
            console.log("notiry_check_error")
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
    console.log("make push notification")
    notify.onclick=function(event){
        send_data_to_flask(notify)
        console.log(notify.data)
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
