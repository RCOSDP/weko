<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output method="xml" indent="yes"/>

    <xsl:template match="/">
        <junii2 xmlns="http://irdb.nii.ac.jp/oai"
                xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                xsi:schemaLocation="http://irdb.nii.ac.jp/oai http://irdb.nii.ac.jp/oai/junii2-3-1.xsd"
                version="3.1">
            <xsl:for-each select="root/*">
                <xsl:variable name="j2" select="junii2_mapping"></xsl:variable>
                <xsl:if test="string-length($j2) > 0">
                    <xsl:for-each select="attribute_value">
                        <xsl:element name="{$j2}">
                            <xsl:value-of select="."></xsl:value-of>
                        </xsl:element>
                    </xsl:for-each>
                    <xsl:for-each select="attribute_value_mlt">
                        <xsl:choose>
                            <xsl:when
                                    test="contains($j2,'jtitle') or contains($j2,'volume') or contains($j2,'issue') or contains($j2,'spage') or contains($j2,'epage') or contains($j2,'dateofissued')">
                                <xsl:if test="contains($j2,'jtitle')">
                                    <xsl:element name="jtitle">
                                        <xsl:value-of select="biblio_name"></xsl:value-of>
                                    </xsl:element>
                                </xsl:if>
                                <xsl:if test="contains($j2,'volume')">
                                    <xsl:element name="volume">
                                        <xsl:value-of select="volume"></xsl:value-of>
                                    </xsl:element>
                                </xsl:if>
                                <xsl:if test="contains($j2,'issue')">
                                    <xsl:element name="issue">
                                        <xsl:value-of select="issue"></xsl:value-of>
                                    </xsl:element>
                                </xsl:if>
                                <xsl:if test="contains($j2,'spage')">
                                    <xsl:element name="spage">
                                        <xsl:value-of select="start_page"></xsl:value-of>
                                    </xsl:element>
                                </xsl:if>
                                <xsl:if test="contains($j2,'epage')">
                                    <xsl:element name="epage">
                                        <xsl:value-of select="end_page"></xsl:value-of>
                                    </xsl:element>
                                </xsl:if>
                                <xsl:if test="contains($j2,'dateofissued')">
                                    <xsl:element name="dateofissued">
                                        <xsl:value-of select="date_of_issued"></xsl:value-of>
                                    </xsl:element>
                                </xsl:if>
                            </xsl:when>
                            <xsl:when test="$j2='fullTextURL'">
                                <xsl:variable name="fn" select="file_name"></xsl:variable>
                                <xsl:if test="string-length($fn) > 0">
                                    <xsl:element name="{$j2}">
                                        <xsl:value-of select="file_name"></xsl:value-of>
                                    </xsl:element>
                                </xsl:if>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:element name="{$j2}">
                                    <xsl:value-of select="concat(family,',',name)"></xsl:value-of>
                                </xsl:element>
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:for-each>
                </xsl:if>
            </xsl:for-each>
        </junii2>
    </xsl:template>
</xsl:stylesheet>
