<?php
/**
 * SAML 2.0 remote IdP metadata for SimpleSAMLphp.
 *
 * Remember to remove the IdPs you don't use from this file.
 *
 * See: https://simplesamlphp.org/docs/stable/simplesamlphp-reference-idp-remote
 */

/*
 * Guest IdP. allows users to sign up and register. Great for testing!
 */
$metadata['https://weko3.example.org/idp/shibboleth'] = array(
	'name' => array(
		'en' => 'Shibboleth IdP',
	),
	'description'          => 'Test Shibboleth IdP.',

	'SingleSignOnService'  => 'https://weko3.example.org/idp/profile/SAML2/Redirect/SSO',
	'SingleLogoutService'  => 'https://weko3.example.org/idp/profile/SAML2/Redirect/SLO',
	'certificate' => 'server.crt',
);

$metadata['https://weko3.example.org/idp/simplesamlphp'] = array(
	'name' => array(
		'en' => 'SimpleSAMLphp IdP',
	),
	'description'          => 'Test SimpleSAMLphp IdP.',

	'SingleSignOnService'  => 'https://weko3.example.org/simplesaml/saml2/idp/SSOService.php',
	'SingleLogoutService'  => 'https://weko3.example.org/simplesaml/saml2/idp/SingleLogoutService.php',
	'certificate' => 'server.crt',
);