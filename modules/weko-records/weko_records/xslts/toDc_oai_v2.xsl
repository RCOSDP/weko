<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet version="1.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output method="xml" indent="yes"/>

    <xsl:template match="/">
        <oai_dc:dc xmlns:dc="http://purl.org/dc/elements/1.1/"
                   xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/oai_dc/ http://www.openarchives.org/OAI/2.0/oai_dc.xsd">
            <xsl:for-each select="root/*">
                <xsl:variable name="j2" select="dublin_core_mapping"></xsl:variable>
                <xsl:if test="string-length($j2) > 0">
                    <xsl:for-each select="attribute_value">
                        <xsl:element name="dc:{$j2}">
                            <xsl:value-of select="."></xsl:value-of>
                        </xsl:element>
                    </xsl:for-each>
                    <xsl:for-each select="attribute_value_mlt">
                        <xsl:choose>
                            <xsl:when
                                    test="contains($j2,'jtitle') or contains($j2,'volume') or contains($j2,'issue') or contains($j2,'spage') or contains($j2,'epage') or contains($j2,'dateofissued')">
                                <xsl:element name="dc:identifier">
                                    <xsl:value-of select="$j2"></xsl:value-of>
                                </xsl:element>
                            </xsl:when>
                            <xsl:when test="$j2='fullTextURL'">
                                <xsl:variable name="fn" select="file_name"></xsl:variable>
                                <xsl:if test="string-length($fn) > 0">
                                    <xsl:element name="dc:identifier">
                                        <xsl:value-of select="file_name"></xsl:value-of>
                                    </xsl:element>
                                </xsl:if>
                            </xsl:when>
                            <xsl:when test="$j2='creator'">
                                <xsl:element name="dc:creator">
                                    <xsl:value-of select="concat(family,',',name)"></xsl:value-of>
                                </xsl:element>
                            </xsl:when>
                        </xsl:choose>
                    </xsl:for-each>
                </xsl:if>
            </xsl:for-each>
        </oai_dc:dc>
    </xsl:template>
</xsl:stylesheet>
