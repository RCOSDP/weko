<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="2.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:f="http://mydomain.org/myfunctions">
    <xsl:output method="xml" indent="yes"/>

    <xsl:function name="f:change_name">
        <xsl:param name="strN"/>
        <xsl:choose>
            <xsl:when test="$strN='description'">
                <xsl:value-of select="concat('datacite',':',$strN)"/>
            </xsl:when>
            <xsl:when test="$strN='date'">
                <xsl:value-of select="concat('datacite',':',$strN)"/>
            </xsl:when>
            <xsl:when test="$strN='version'">
                <xsl:value-of select="concat('datacite',':',$strN)"/>
            </xsl:when>
            <xsl:when test="$strN='geoLocation'">
                <xsl:value-of select="concat('datacite',':',$strN)"/>
            </xsl:when>

            <xsl:when test="$strN='title'">
                <xsl:value-of select="concat('dc',':',$strN)"/>
            </xsl:when>
            <xsl:when test="$strN='rights'">
                <xsl:value-of select="concat('dc',':',$strN)"/>
            </xsl:when>
            <xsl:when test="$strN='publisher'">
                <xsl:value-of select="concat('dc',':',$strN)"/>
            </xsl:when>
            <xsl:when test="$strN='language'">
                <xsl:value-of select="concat('dc',':',$strN)"/>
            </xsl:when>
            <xsl:when test="$strN='type'">
                <xsl:value-of select="concat('dc',':',$strN)"/>
            </xsl:when>

            <xsl:when test="$strN='dissertationNumber'">
                <xsl:value-of select="concat('dcndl',':',$strN)"/>
            </xsl:when>
            <xsl:when test="$strN='degreeName'">
                <xsl:value-of select="concat('dcndl',':',$strN)"/>
            </xsl:when>
            <xsl:when test="$strN='dateGranted'">
                <xsl:value-of select="concat('dcndl',':',$strN)"/>
            </xsl:when>

            <xsl:when test="$strN='alternative'">
                <xsl:value-of select="concat('dcterms',':',$strN)"/>
            </xsl:when>
            <xsl:when test="$strN='accessRights'">
                <xsl:value-of select="concat('dcterms',':',$strN)"/>
            </xsl:when>
            <xsl:when test="$strN='temporal'">
                <xsl:value-of select="concat('dcterms',':',$strN)"/>
            </xsl:when>

            <xsl:when test="$strN='versionType'">
                <xsl:value-of select="concat('openaire',':',$strN)"/>
            </xsl:when>

            <xsl:otherwise>
                <xsl:value-of select="concat('jpcoar',':',$strN)"/>
            </xsl:otherwise>

        </xsl:choose>
    </xsl:function>

    <xsl:template match="/">
        <jpcoar:jpcoar xmlns:jpcoar="https://irdb.nii.ac.jp/schema/jpcoar/1.0/"
                       xmlns:dc="http://purl.org/dc/elements/1.1/"
                       xmlns:dcterms="http://purl.org/dc/terms/"
                       xmlns:rioxxterms="http://www.rioxx.net/schema/v2.0/rioxxterms/"
                       xmlns:datacite="http://datacite.org/schema/kernel-4"
                       xmlns:openaire="http://openaire.eu/schema/v4"
                       xmlns:dcndl="http://ndl.go.jp/dcndl/terms/"
                       xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
                       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                       xsi:schemaLocation="https://irdb.nii.ac.jp/schema/jpcoar/1.0/jpcoar_scm.xsd">
            <xsl:for-each select="root/*">
                <xsl:variable name="jc" select="jpcoar_mapping"></xsl:variable>
                <xsl:variable name="atr" select="attribute_value_mlt"></xsl:variable>
                <xsl:if test="string-length($jc) > 0">
                    <xsl:choose>
                        <xsl:when test="contains($jc,',')">
                            <xsl:variable name="array" select="f:tokenize(string($jc),',')"></xsl:variable>
                            <xsl:for-each select="$array">
                                <xsl:variable name="vc" select="."></xsl:variable>
                                <xsl:choose>
                                    <xsl:when test="contains($vc,'.')">
                                        <xsl:for-each select="$atr">
                                            <xsl:variable name="fn" select="file_name"></xsl:variable>
                                            <xsl:variable name="sf" select="family"></xsl:variable>
                                            <xsl:variable name="sn" select="name"></xsl:variable>
                                            <xsl:variable name="kc" select="substring-after($vc,'.')"></xsl:variable>
                                            <xsl:variable name="sc" select="f:tokenize($kc,'_')"></xsl:variable>
                                            <xsl:element name="{f:change_name(substring-before($vc,'.'))}">
                                                <xsl:for-each select="$sc">
                                                    <xsl:variable name="ac" select="."></xsl:variable>
                                                    <xsl:choose>
                                                        <xsl:when test="$ac='url'">
                                                            <xsl:if test="string-length($fn) > 0">
                                                                <xsl:element name="{f:change_name(string($ac))}">
                                                                    <xsl:value-of select="$fn"></xsl:value-of>
                                                                </xsl:element>
                                                            </xsl:if>
                                                        </xsl:when>
                                                        <xsl:when test="contains($ac,'familyName')">
                                                            <xsl:element name="{f:change_name('familyName')}">
                                                                <xsl:value-of select="$sf"></xsl:value-of>
                                                            </xsl:element>
                                                        </xsl:when>
                                                        <xsl:when test="contains($ac,'givenName')">
                                                            <xsl:element name="{f:change_name('givenName')}">
                                                                <xsl:value-of select="$sn"></xsl:value-of>
                                                            </xsl:element>
                                                        </xsl:when>
                                                    </xsl:choose>
                                                </xsl:for-each>
                                            </xsl:element>
                                        </xsl:for-each>

                                    </xsl:when>
                                    <xsl:otherwise>
                                        <xsl:for-each select="$atr">
                                            <xsl:choose>
                                                <xsl:when
                                                        test="contains($vc,'sourceTitle') or contains($vc,'volume') or contains($vc,'numPages')
                                                        or contains($vc,'pageStart') or contains($vc,'pageEnd') or contains($vc,'date')">
                                                    <xsl:if test="contains($vc,'sourceTitle')">
                                                        <xsl:element name="{f:change_name('sourceTitle')}">
                                                            <xsl:value-of select="biblio_name"></xsl:value-of>
                                                        </xsl:element>
                                                    </xsl:if>
                                                    <xsl:if test="contains($vc,'volume')">
                                                        <xsl:element name="{f:change_name('volume')}">
                                                            <xsl:value-of select="volume"></xsl:value-of>
                                                        </xsl:element>
                                                    </xsl:if>
                                                    <xsl:if test="contains($vc,'numPages')">
                                                        <xsl:element name="{f:change_name('numPages')}">
                                                            <xsl:value-of select="issue"></xsl:value-of>
                                                        </xsl:element>
                                                    </xsl:if>
                                                    <xsl:if test="contains($vc,'pageStart')">
                                                        <xsl:element name="{f:change_name('pageStart')}">
                                                            <xsl:value-of select="start_page"></xsl:value-of>
                                                        </xsl:element>
                                                    </xsl:if>
                                                    <xsl:if test="contains($vc,'pageEnd')">
                                                        <xsl:element name="{f:change_name('pageEnd')}">
                                                            <xsl:value-of select="end_page"></xsl:value-of>
                                                        </xsl:element>
                                                    </xsl:if>
                                                    <xsl:if test="contains($vc,'date')">
                                                        <xsl:element name="{f:change_name('date')}">
                                                            <xsl:value-of select="date_of_issued"></xsl:value-of>
                                                        </xsl:element>
                                                    </xsl:if>
                                                </xsl:when>
                                            </xsl:choose>
                                        </xsl:for-each>
                                    </xsl:otherwise>
                                </xsl:choose>
                            </xsl:for-each>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:for-each select="attribute_value">
                                <xsl:choose>
                                    <xsl:when test="contains($jc,'.')">
                                        <xsl:element name="{f:change_name(substring-before($jc,'.'))}">
                                            <xsl:element name="{f:change_name(substring-after($jc,'.'))}">
                                                <xsl:value-of select="."></xsl:value-of>
                                            </xsl:element>
                                        </xsl:element>
                                    </xsl:when>
                                    <xsl:otherwise>
                                        <xsl:element name="{f:change_name(string($jc))}">
                                            <xsl:value-of select="."></xsl:value-of>
                                        </xsl:element>
                                    </xsl:otherwise>
                                </xsl:choose>
                            </xsl:for-each>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:if>
            </xsl:for-each>
        </jpcoar:jpcoar>
    </xsl:template>
</xsl:stylesheet>
