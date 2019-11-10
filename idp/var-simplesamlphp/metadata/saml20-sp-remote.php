<?php
/**
 * SAML 2.0 remote SP metadata for SimpleSAMLphp.
 *
 * See: https://simplesamlphp.org/docs/stable/simplesamlphp-reference-sp-remote
 */

/*
 * Example SimpleSAMLphp SAML 2.0 SP
 */

$metadata['http://weko3.example.org/sp/simplesamlphp'] = array(
	'AssertionConsumerService' => 'https://weko3.example.org/simplesaml/module.php/saml/sp/saml2-acs.php/default-sp',
	'SingleLogoutService' => 'https://weko3.example.org/simplesaml/module.php/saml/sp/saml2-logout.php/default-sp',
);

/*
 * This example shows an example config that works with Google Apps for education.
 * What is important is that you have an attribute in your IdP that maps to the local part of the email address
 * at Google Apps. In example, if your google account is foo.com, and you have a user that has an email john@foo.com, then you
 * must set the simplesaml.nameidattribute to be the name of an attribute that for this user has the value of 'john'.
 
$metadata['google.com'] = array(
	'AssertionConsumerService' => 'https://www.google.com/a/g.feide.no/acs',
	'NameIDFormat' => 'urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress',
	'simplesaml.nameidattribute' => 'uid',
	'simplesaml.attributes' => FALSE,
);
*/
$metadata['https://weko3.example.org/shibboleth-sp'] = array (
	'entityid' => 'https://weko3.example.org/shibboleth-sp',
	'contacts' => 
	array (
	),
	'metadata-set' => 'saml20-sp-remote',
	'AssertionConsumerService' => 
	array (
	  0 => 
	  array (
		'Binding' => 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST',
		'Location' => 'https://weko3.example.org/Shibboleth.sso/SAML2/POST',
		'index' => 1,
	  ),
	  1 => 
	  array (
		'Binding' => 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST-SimpleSign',
		'Location' => 'https://weko3.example.org/Shibboleth.sso/SAML2/POST-SimpleSign',
		'index' => 2,
	  ),
	  2 => 
	  array (
		'Binding' => 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Artifact',
		'Location' => 'https://weko3.example.org/Shibboleth.sso/SAML2/Artifact',
		'index' => 3,
	  ),
	  3 => 
	  array (
		'Binding' => 'urn:oasis:names:tc:SAML:2.0:bindings:PAOS',
		'Location' => 'https://weko3.example.org/Shibboleth.sso/SAML2/ECP',
		'index' => 4,
	  ),
	),
	'SingleLogoutService' => 
	array (
	  0 => 
	  array (
		'Binding' => 'urn:oasis:names:tc:SAML:2.0:bindings:SOAP',
		'Location' => 'https://weko3.example.org/Shibboleth.sso/SLO/SOAP',
	  ),
	  1 => 
	  array (
		'Binding' => 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect',
		'Location' => 'https://weko3.example.org/Shibboleth.sso/SLO/Redirect',
	  ),
	  2 => 
	  array (
		'Binding' => 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST',
		'Location' => 'https://weko3.example.org/Shibboleth.sso/SLO/POST',
	  ),
	  3 => 
	  array (
		'Binding' => 'urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Artifact',
		'Location' => 'https://weko3.example.org/Shibboleth.sso/SLO/Artifact',
	  ),
	),
	'keys' => 
	array (
	  0 => 
	  array (
		'encryption' => false,
		'signing' => true,
		'type' => 'X509Certificate',
		'X509Certificate' => 'MIID2jCCAsKgAwIBAgIJAKPV0ct70y2rMA0GCSqGSIb3DQEBBQUAMFExCzAJBgNV
  BAYTAkFVMRMwEQYDVQQIEwpTb21lLVN0YXRlMSEwHwYDVQQKExhJbnRlcm5ldCBX
  aWRnaXRzIFB0eSBMdGQxCjAIBgNVBAMUASowHhcNMTYwMTIyMDk1NjU1WhcNMTcw
  MTIxMDk1NjU1WjBRMQswCQYDVQQGEwJBVTETMBEGA1UECBMKU29tZS1TdGF0ZTEh
  MB8GA1UEChMYSW50ZXJuZXQgV2lkZ2l0cyBQdHkgTHRkMQowCAYDVQQDFAEqMIIB
  IjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAoWebMBDnOXrgh9Oo4ZO6RLra
  awmaASgN47YTUlZLZIPsSG+7BnNR+c0tjxdZTkfb2+7s92SsTGvR6xRd22I0J9SE
  /mxMjqTW84s9+5SJPEAG0P+vCaRxOc0d+r3278X+jjpBXD7YecdsP6DqNoGkdjdK
  8Vod/CDlZyKgj2f1VVEOOrTJoKSFgc8CX7DkAdKgnM1EhX/5eHnungWWX6qCWmnR
  KVFqry8HkXi5dq24kVTJkuAHk5vMzUjvSd2W7VduNGwiutk1R1pI8/uwTRSXY7tj
  xZE8bJ9QfY83Mluo3RwfDJoWH1ksNvhUdxfEXBBFvwFge2oDZ3R0AjB6/2EUHQID
  AQABo4G0MIGxMB0GA1UdDgQWBBTxXhfJqG1fYdNB960kC7u4QvbhZjCBgQYDVR0j
  BHoweIAU8V4XyahtX2HTQfetJAu7uEL24WahVaRTMFExCzAJBgNVBAYTAkFVMRMw
  EQYDVQQIEwpTb21lLVN0YXRlMSEwHwYDVQQKExhJbnRlcm5ldCBXaWRnaXRzIFB0
  eSBMdGQxCjAIBgNVBAMUASqCCQCj1dHLe9MtqzAMBgNVHRMEBTADAQH/MA0GCSqG
  SIb3DQEBBQUAA4IBAQB4i4B+fXEprXfFc/yLSVDEdZc8uvBMLu6a+AnL9JqjOJIA
  K4hbGi22EG0lI3s8gbfe5JycheyqVGNZziRphF3JlT7QbA36rFrCrad5V4O1739G
  oP+j++4xqqSUhKjwD+nbTuihEOfBDxw3vaZ8kc8yIKaHU+A3+Ir4LNG8ttb/6smn
  +TcVnUESmoTyAKN7j8qdGDj26kec+M94Fl+DjzeKLoiYDeVN64ep9Xf5x3PIMjV1
  QZ4vy5m0s4tC6OrSwrH41shh9kklyf+008T+XpXzCiXtAyp8UTD6q+705hWCT34n
  AF5vPFVGIYa8nNIeSZ+MGAazoni712j1kIHrkOou
  ',
	  ),
	  1 => 
	  array (
		'encryption' => true,
		'signing' => false,
		'type' => 'X509Certificate',
		'X509Certificate' => 'MIID2jCCAsKgAwIBAgIJAKPV0ct70y2rMA0GCSqGSIb3DQEBBQUAMFExCzAJBgNV
  BAYTAkFVMRMwEQYDVQQIEwpTb21lLVN0YXRlMSEwHwYDVQQKExhJbnRlcm5ldCBX
  aWRnaXRzIFB0eSBMdGQxCjAIBgNVBAMUASowHhcNMTYwMTIyMDk1NjU1WhcNMTcw
  MTIxMDk1NjU1WjBRMQswCQYDVQQGEwJBVTETMBEGA1UECBMKU29tZS1TdGF0ZTEh
  MB8GA1UEChMYSW50ZXJuZXQgV2lkZ2l0cyBQdHkgTHRkMQowCAYDVQQDFAEqMIIB
  IjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAoWebMBDnOXrgh9Oo4ZO6RLra
  awmaASgN47YTUlZLZIPsSG+7BnNR+c0tjxdZTkfb2+7s92SsTGvR6xRd22I0J9SE
  /mxMjqTW84s9+5SJPEAG0P+vCaRxOc0d+r3278X+jjpBXD7YecdsP6DqNoGkdjdK
  8Vod/CDlZyKgj2f1VVEOOrTJoKSFgc8CX7DkAdKgnM1EhX/5eHnungWWX6qCWmnR
  KVFqry8HkXi5dq24kVTJkuAHk5vMzUjvSd2W7VduNGwiutk1R1pI8/uwTRSXY7tj
  xZE8bJ9QfY83Mluo3RwfDJoWH1ksNvhUdxfEXBBFvwFge2oDZ3R0AjB6/2EUHQID
  AQABo4G0MIGxMB0GA1UdDgQWBBTxXhfJqG1fYdNB960kC7u4QvbhZjCBgQYDVR0j
  BHoweIAU8V4XyahtX2HTQfetJAu7uEL24WahVaRTMFExCzAJBgNVBAYTAkFVMRMw
  EQYDVQQIEwpTb21lLVN0YXRlMSEwHwYDVQQKExhJbnRlcm5ldCBXaWRnaXRzIFB0
  eSBMdGQxCjAIBgNVBAMUASqCCQCj1dHLe9MtqzAMBgNVHRMEBTADAQH/MA0GCSqG
  SIb3DQEBBQUAA4IBAQB4i4B+fXEprXfFc/yLSVDEdZc8uvBMLu6a+AnL9JqjOJIA
  K4hbGi22EG0lI3s8gbfe5JycheyqVGNZziRphF3JlT7QbA36rFrCrad5V4O1739G
  oP+j++4xqqSUhKjwD+nbTuihEOfBDxw3vaZ8kc8yIKaHU+A3+Ir4LNG8ttb/6smn
  +TcVnUESmoTyAKN7j8qdGDj26kec+M94Fl+DjzeKLoiYDeVN64ep9Xf5x3PIMjV1
  QZ4vy5m0s4tC6OrSwrH41shh9kklyf+008T+XpXzCiXtAyp8UTD6q+705hWCT34n
  AF5vPFVGIYa8nNIeSZ+MGAazoni712j1kIHrkOou
  ',
	  ),
	),
	'NameIDFormat' => 'urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress',
	'simplesaml.nameidattribute' => 'uid',
	'simplesaml.attributes' => true,
  );