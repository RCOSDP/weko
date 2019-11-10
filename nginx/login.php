<?php

  // ERROR
  if(!$_SERVER['mail']){
    header("HTTP/1.1 403 Forbidden");
    exit;
  }

  $base =  $_SERVER['REQUEST_SCHEME']."://".$_SERVER['SERVER_NAME'];
  $url = $base."/weko/shib/login?next=%2F";

  $curl = curl_init($url);

  $post_args=[];
  $post_args["SHIB_ATTR_EPPN"]=$_SERVER['eppn'];  
  $post_args["SHIB_ATTR_MAIL"]=$_SERVER['mail'];
  $post_args["SHIB_ATTR_SESSION_ID"]=$_SERVER['Shib-Session-ID'];

  $options = array(
  //Method
  CURLOPT_POST => true,//POST
  //body
  CURLOPT_POSTFIELDS => http_build_query($post_args), 
);

$cookie=tempnam(sys_get_temp_dir(),'cookie_');

//set options
curl_setopt($curl, CURLOPT_RETURNTRANSFER, true);
curl_setopt($curl,CURLOPT_SSL_VERIFYPEER, false);
curl_setopt($curl, CURLOPT_SSL_VERIFYHOST, 0);
curl_setopt($curl, CURLOPT_COOKIESESSION, true);
curl_setopt_array($curl, $options);
curl_setopt($curl,CURLOPT_COOKIEJAR,$cookie);
curl_setopt($curl,CURLOPT_COOKIEFILE,$cookie);

// request
$result = curl_exec($curl);

curl_close($curl);

header("HTTP/1.1 302 Found");
header("Location: ".$base.$result);
  //var_dump($app_cookies[0]['value']);
?>
