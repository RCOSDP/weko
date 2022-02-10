window.addEventListener("DOMContentLoaded", function(){
    setInterval(() => {
        //reload_notiry_publish()
        console.log("interval test")
    },5000)
})

function reload_notify_publish(){
    console.log("check inbox test")
    //$.ajax({
    //    type:"GET",
    //    url:"/check_inbox",
    //    success: function(result){
    //        result.forEach(function(data){
    //            create_push_notification(data)
    //        })
    //    }
    //})
}

function create_push_notification(data){
    var notify = new Notification(data.title,{
        body:data.body,
        data:data.data
    })
    notify.onclick=function(event){
        //send_data_to_flask(notify)
        console.log(notify.data)
    }
}

function send_data_to_flask(n){
    $.ajax({
        url:"/push_data",
        method: "POST",
        contentType:"application/json",
        dataType:"json",
        data: JSON.stringify(notify.data)
    })
}