<!--

   Copyright 2013 National Institute of Informatics

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

-->

<html>
  <head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    <title>属性受信の確認ページ</title>
    <style type="text/css">
    body {
        background-color: #FFFFFF;
        font-family: Arial, Helvetica, sans-serif;
        font-size: 12px;
        text-align:center;
        line-height: 24px;
    }

    h2 {
        color: #FFFFFF;
        font-size: 18px;
    }

    table {
        margin: auto auto;
        border-collapse: collapse;
    }

    body#maintop {
        background-image: url('https://www.gakunin.jp/docs/files/bg2.jpg');
        background-repeat: repeat-x;
        background-position: 0px 110px;
    }

    #logoA {
        position: absolute;
        left: 20px;
    }

    div#maincenter{
        position: relative;
        top: 85px;
        margin: 0 auto;
        text-align: center;
    }

    div#logincenter{
        text-align: center;
    }

    strong#logintitle {
        font-size: 11px;
        color: #FFFFFF;
    }

    strong#loginname {
        font-size: 12px;
        color: #FFFFFF;
    }

    #main {
        margin: 90px auto;
        color: #333333;
    }

    td,th.chart {
        padding: 8px 15px;
        font-size: 12px;
        border-style: solid;
        border-width: 3px;
        border-collapse: collapse;
        border-color: #006633;
    }

    th.chart {
        background-color: #333333;
        color: #FFFFFF;
    }

    td.chart-key_odd {
        background-color: #CED5AE;
        white-space: nowrap;
    }

    td.chart-value_odd {
        background-color: #EDF5C8;
    }

    td.chart-key_even {
        background-color: #FFFFFF;
        white-space: nowrap;
    }

    td.chart-value_even {
        background-color: #FFFFFF;
    }

    td.chart-key_notreceived {
        background-color: #c0c0c0;
        white-space: nowrap;
    }

    td.chart-value_notreceived {
        background-color: #c0c0c0;
        white-space: nowrap;
    }

    p.message_notice {
        color: #FF8C00;
        font-weight: bold;
    }
    
    p.message_warning {
        color: #FF0000;
        font-weight: bold;
    }
    </style>
  </head>
  <body id="maintop">

    <img id="logoA" src="https://www.gakunin.jp/docs/files/GakuNin_logo_yoko-small.png">
    <br>

    <div id="maincenter">
      <strong id="logintitle">属性受信の確認ページ</strong><br>
<?php
//error_reporting(E_ERROR | E_WARNING | E_PARSE);
error_reporting(E_ALL ^ E_NOTICE);
print "      <strong id='loginname'>あなたのIdPは、&lt;" . htmlspecialchars($_SERVER['Shib-Identity-Provider']) . "&gt;です。</strong>";
?>
      <br>
    </div>

    <table id="main" cellspacing="0">
      <colgroup>
        <col width="280">
        <col width="420" valign="top">
      </colgroup>
      <thead>
      <tr>
        <th scope="col" class="chart">属性</th>
        <th scope="col" class="chart">属性値</th>
      </tr>
      </thead>
      <tbody>
<?php
    // checkScopedAttribute
    //
    // If true, compare the attribute value obtained by an environment variable
    // and exportAssersion. The feature is disabled by default.
    //
    // exportAssersion settings:
    //   1. Add 'exportLocation' to a Sessions element of shibboleth2.xml.
    //      (see also: https://wiki.shibboleth.net/confluence/display/SHIB2/NativeSPSessions)
    //      
    //      Example:
    //        <Sessions ... 
    //          exportLocation="https://localhost/Shibboleth.sso/Assertion" <- add
    // 
    //   2. Add 'ShibRequestSetting exportAssertion 1' to <Location /secure> 
    //      of shib.conf.
    // 
    //   3. shibd and httpd restart
    // 
    $checkScopedAttribute = false;
    //$checkScopedAttribute = true;

    function get_exportAssertion(){
        $eadata = "";
        $xml = simplexml_load_string(file_get_contents($_SERVER['Shib-Assertion-01']));
        foreach ( $xml->children("urn:oasis:names:tc:SAML:2.0:assertion")->AttributeStatement->Attribute as $attr) {
            // eduPersonPrincipalName (ePPN)
            if ((string)$attr->attributes()->Name == 'urn:oid:1.3.6.1.4.1.5923.1.1.1.6') {
               $eadata["eppn"] = $attr->AttributeValue;
            }
        
            // eduPersonScopedAffiliation (ePSA)
            if ((string)$attr->attributes()->Name == 'urn:oid:1.3.6.1.4.1.5923.1.1.1.9') {
               $affiliation_array = array();
               foreach ($attr->AttributeValue as $val) {
                   // Add a backslash to match the behavior of SP.
                   // example: "member;staff" --> "member\;staff"
                   $val = str_replace(';', '\\;', $val);
                   array_push($affiliation_array, $val);
               }
               $eadata["affiliation"] = (string)join(";", $affiliation_array);
            }

            // eduPersonAffiliation (ePA)
            if ((string)$attr->attributes()->Name == 'urn:oid:1.3.6.1.4.1.5923.1.1.1.1') {
               $affiliation_array = array();
               foreach ($attr->AttributeValue as $val) {
                   // Add a backslash to match the behavior of SP.
                   // example: "member;staff@example.ac.jp" --> "member\;staff@example.ac.jp"
                   $val = str_replace(';', '\\;', $val);
                   array_push($affiliation_array, $val);
               }
               $eadata["unscoped-affiliation"] = (string)join(";", $affiliation_array);
            }

            // gakuninScopedPersonalUniqueCode
            if ((string)$attr->attributes()->Name == 'urn:oid:1.3.6.1.4.1.32264.1.1.6') {
               $affiliation_array = array();
               foreach ($attr->AttributeValue as $val) {
                   // Add a backslash to match the behavior of SP.
                   // example: "faculty;staff:12345@example.ac.jp" --> "faculty\;staff:12345@example.ac.jp"
                   $val = str_replace(';', '\\;', $val);
                   array_push($affiliation_array, $val);
               }
               $eadata["gakuninScopedPersonalUniqueCode"] = (string)join(";", $affiliation_array);
            }

            // eduPersonUniqueId
            if ((string)$attr->attributes()->Name == 'urn:oid:1.3.6.1.4.1.5923.1.1.1.13') {
               $eadata["eduPersonUniqueId"] = $attr->AttributeValue;
            }
        }
        return $eadata;
    }

    function normal_value($attr_value = ''){
    }

    function notice_value($attr_value = ''){
        if (strpos($attr_value, '\;') !== FALSE)
            print '<p class="message_notice">注意：属性値にセミコロンが含まれているためSPによっては正しく動作しない可能性があります</p>';
    }

    function warning_value($attr_value = ''){
        if (strpos($attr_value, '\;') !== FALSE)
            print '<p class="message_warning">警告：属性値にセミコロンが含まれているため正しくありません</p>';
    }

    function check_exportAssertion($attr, $attr_value = '', $ea_attr_value = ''){
	// scoped attributes (e.g. ePPN, ePSA)
	$scoped_attrs = array(
		"eppn",
		"affiliation",
		"gakuninScopedPersonalUniqueCode",
        "eduPersonUniqueId",
        "eduPersonScopedAffiliation",
	);

	// affiliation attributes (i.e. ePA, ePSA)
	$affiliation_attrs = array(
		"unscoped-affiliation",
        "affiliation",
        "eduPersonAffiliation",
        "eduPersonScopedAffiliation",
	);

        // eduPersonAffiliation permissible values
        //    (eduPerson Object Class Specification (200806))
        $epaary = array(
            "faculty", "student", "staff", "alum", "member",
            "affiliate", "employee", "library-walk-in",
        );

        // Check of scope for scoped attributes (e.g. ePPN, ePSA)
        if (in_array($attr, $scoped_attrs, true)) {
            if (strcmp($attr_value, $ea_attr_value)) {
                print '<p class="message_warning">警告：メタデータで定義されているスコープと送出された属性のスコープが一致していないか、利用できる属性値ではありません。<br>';
                print '（送出された属性値は' . $ea_attr_value . 'でした。）</p>';
            }
        }

        // Check of vocabulary for affiliation attributes
        if (in_array($attr, $affiliation_attrs, true)) {
            $ea_attr_value_ary = preg_split("/(?<!\\\);/", $ea_attr_value);

            foreach ($ea_attr_value_ary as $val) {
                $match = FALSE;
                foreach ($epaary as $epaval) {
                    if(preg_match("/^$epaval(@|$)/", $val) === 1){
                        $match = TRUE;
                        break;
                    }
                }
                if ($match === FALSE) {
                    print '<p class="message_warning">警告：' . $val . "は利用できる属性値ではありません。</p>";
                }
            }

        }
    }

    $envary = array(
        "eppn"                 => array("<a href='https://meatwiki.nii.ac.jp/confluence/display/GakuNinShibInstall/eduPersonPrincipalName'>ePPN(eduPersonPrincipalName)</a>"                     , "normal_value"),
        "persistent-id"        => array("<a href='https://meatwiki.nii.ac.jp/confluence/display/GakuNinShibInstall/eduPersonTargetedID'>eduPersonTargetedID</a>"                                 , "notice_value"),
        "o"                    => array("<a href='https://meatwiki.nii.ac.jp/confluence/display/GakuNinShibInstall/o'>o(organizationName)</a>"                                                   , "normal_value"),
        "jao"                  => array("<a href='https://meatwiki.nii.ac.jp/confluence/display/GakuNinShibInstall/jao'>jao(jaOrganizationName)[日本語]</a>"                                     , "normal_value"),
        "ou"                   => array("<a href='https://meatwiki.nii.ac.jp/confluence/display/GakuNinShibInstall/ou'>ou(organizationalUnitName)</a>"                                           , "normal_value"),
        "jaou"                 => array("<a href='https://meatwiki.nii.ac.jp/confluence/display/GakuNinShibInstall/jaou'>jaou(jaOrganizationalUnitName)[日本語]</a>"                             , "normal_value"),
        "unscoped-affiliation" => array("<a href='https://meatwiki.nii.ac.jp/confluence/display/GakuNinShibInstall/eduPersonAffiliation'>職位(eduPersonAffiliation)</a>"                         , "warning_value"),
        "affiliation"          => array("<a href='https://meatwiki.nii.ac.jp/confluence/display/GakuNinShibInstall/eduPersonScopedAffiliation'>スコープ付き職位(eduPersonScopedAffiliation)</a>" , "warning_value"),
        "entitlement"          => array("<a href='https://meatwiki.nii.ac.jp/confluence/display/GakuNinShibInstall/eduPersonEntitlement'>権限(eduPersonEntitlement)</a>"                         , "notice_value"),
        "mail"                 => array("<a href='https://meatwiki.nii.ac.jp/confluence/display/GakuNinShibInstall/mail'>メールアドレス(mail)</a>"                                               , "normal_value"),
        "givenName"            => array("<a href='https://meatwiki.nii.ac.jp/confluence/display/GakuNinShibInstall/givenName'>名(givenName)</a>"                                                 , "normal_value"),
        "jaGivenName"          => array("<a href='https://meatwiki.nii.ac.jp/confluence/display/GakuNinShibInstall/jaGivenName'>名(jaGivenName)[日本語]</a>"                                     , "normal_value"),
        "sn"                   => array("<a href='https://meatwiki.nii.ac.jp/confluence/display/GakuNinShibInstall/sn'>姓(sn)</a>"                                                               , "normal_value"),
        "jasn"                 => array("<a href='https://meatwiki.nii.ac.jp/confluence/display/GakuNinShibInstall/jasn'>姓(jasn)[日本語]</a>"                                                   , "normal_value"),
        "displayName"          => array("<a href='https://meatwiki.nii.ac.jp/confluence/display/GakuNinShibInstall/displayName'>表示名(displayName)</a>"                                         , "normal_value"),
        "jaDisplayName"        => array("<a href='https://meatwiki.nii.ac.jp/confluence/display/GakuNinShibInstall/jaDisplayName'>表示名(jaDisplayName)[日本語]</a>"                             , "normal_value"),
        "gakuninScopedPersonalUniqueCode"
                               => array("<a href='https://meatwiki.nii.ac.jp/confluence/display/GakuNinShibInstall/gakuninScopedPersonalUniqueCode'>gakuninScopedPersonalUniqueCode</a>"         , "notice_value"),
        "isMemberOf"           => array("<a href='https://meatwiki.nii.ac.jp/confluence/display/GakuNinShibInstall/isMemberOf'>isMemberOf</a>"                                                   , "notice_value"),
        "assurance"            => array("<a href='https://meatwiki.nii.ac.jp/confluence/display/GakuNinShibInstall/eduPersonAssurance'>eduPersonAssurance</a>"                                   , "notice_value"),
        "eduPersonUniqueId"    => array("<a href='https://meatwiki.nii.ac.jp/confluence/display/GakuNinShibInstall/eduPersonUniqueId'>eduPersonUniqueId</a>"                                     , "normal_value"),
        "eduPersonOrcid"       => array("<a href='https://meatwiki.nii.ac.jp/confluence/display/GakuNinShibInstall/eduPersonOrcid'>eduPersonOrcid</a>"                                           , "notice_value"),
    );

    $chart_classes = array(
        array("key" => "chart-key_even", "val" => "chart-value_even"),
        array("key" => "chart-key_odd",  "val" => "chart-value_odd" ),
    );

    $chart_class_notreceived = array(
        "key" => "chart-key_notreceived",
        "val" => "chart-value_notreceived");

    if ($checkScopedAttribute === TRUE){
        $eadata=get_exportAssertion();
    }

    $i = 0;
    foreach ($envary as $attr => $key) {
        list($attr_description, $print_message) = $key;

        if ($i != 0) {
          print "\n";
        }

        $chart_class = $chart_classes[$i % 2];

        if (isset($_SERVER[$attr]) === FALSE) {
            $chart_class = $chart_class_notreceived;
            $val = "NOT RECEIVED";
        } else {
            $val = htmlspecialchars($_SERVER[$attr], ENT_QUOTES, "UTF-8");
        }

        print '        <tr>';
        print '<td class="' . $chart_class["key"] . '" scope="col" nowrap>' . $attr_description . '</td>';
        print '<td class="' . $chart_class["val"] . '">' . $val;
        print $print_message($_SERVER[$attr]);

        if ($checkScopedAttribute === TRUE && empty($eadata[$attr]) === FALSE){
            check_exportAssertion($attr, $_SERVER[$attr], $eadata[$attr]);
        }
        print '</td></tr>';

        $i = $i + 1;
    }
?>       
      </tbody>
    </table>
    <p>現在のセッション情報の詳細はこちらへ。&rArr;<a href="/Shibboleth.sso/Session">セッション情報</a></p>
    <p>このSPに対してログアウトする場合はこちらへ。&rArr;<a href="/Shibboleth.sso/Logout?return=https://<?php print urlencode($_SERVER['HTTP_HOST']) ?>/">ログアウト</a><br>
    (IdPに対してはログインした状態のままになりますのでご注意ください。<br>
    IdPからもログアウトするためにはブラウザを閉じてください)</p>

<?php
    $debug = 0;

    if ($debug > 0) {
        print "    <table>\n";
        while (list($key, $value) = each($_SERVER)) {
            print "      <tr><td>$key</td><td>" . htmlspecialchars($value, ENT_QUOTES, "UTF-8") . "</td>\n";
        }
        print "    </table>\n";
    }
?>

  </body>
</html>
