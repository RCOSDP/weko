<?php
  require_once "HTTP/Request2.php";

  if(!$_SERVER['HTTP_MAIL']){
    header("HTTP/1.1 403 Forbidden");
    exit;
  }

  $request = new HTTP_Request2();
  $request->setUrl('https://172.27.0.9/weko/shib/login');
  $request->setConfig(array( 'ssl_verify_peer' => false,
                          'ssl_verify_host' => false));
  $request->setMethod(HTTP_REQUEST2::METHOD_POST);
  $request->addPostParameter("SHIB_ATTR_EPPN", $_SERVER['HTTP_DISPLAYNAME']);
  $request->addPostParameter("SHIB_ATTR_MAIL", $_SERVER['HTTP_MAIL']);
  $request->addPostParameter("SHIB_ATTR_SESSION_ID", $_SERVER['HTTP_SHIB_SESSION_ID']);

  $response = $request->send();
  $response_body = $response->getBody();

  header("HTTP/1.1 302 Found");
  header("Location: https://www.we50hitdev.com/".$response_body);
?>
