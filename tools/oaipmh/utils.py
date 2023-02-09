import glob
import sys
import time
import random
import xml.dom.minidom

from lxml import etree
from lxml.etree import ElementTree
from sickle import Sickle
from sickle.iterator import OAIItemIterator, OAIResponseIterator


class XSDValidator:
    def __init__(self, xsd_path: str):
        xmlschema_doc = etree.parse(xsd_path)
        self.xmlschema = etree.XMLSchema(xmlschema_doc)

    def validateFile(self, xml_path: str) -> bool:
        xml_doc = etree.parse(xml_path)
        result = self.xmlschema.validate(xml_doc)
        return result

    def validate(self, xml_doc: ElementTree) -> bool:
        result = self.xmlschema.validate(xml_doc)
        return result

    def assertValid(self, xml_doc: ElementTree) -> bool:
        result = self.xmlschema.assertValid(xml_doc)
        return result


def countListRecords(baseURL='https://localhost/oai',
                     meta='oai_dc', setspec=None):
    startTime = time.time()
    sickle = Sickle(endpoint=baseURL,
                    max_retries=4, timeout=900, verify=False, iterator=OAIItemIterator)
    ids = 0
    deletedIds = 0
    records = sickle.ListRecords(metadataPrefix=meta, set=setspec)
    for r in records:
        if r.header.deleted == False:
            ids=ids+1
        else:
            deletedIds=deletedIds+1
    elapsedTime = time.time() - startTime
    print("# of items: {0}".format(ids))
    print("# of deleted items: {0}".format(deletedIds))
    print("elapsed time: {0}".format(elapsedTime))


def dumpListRecords(baseURL='https://localhost/oai', meta='oai_dc', setspec=None,max_retries=4,timeout=300,interval=30,max_interval=120):
    startTime = time.time()
    sickle = Sickle(endpoint=baseURL,
                    max_retries=max_retries, timeout=timeout, verify=False, iterator=OAIResponseIterator)
    n = 0
    responses = sickle.ListRecords(metadataPrefix=meta)
    try:
        for r in responses:
            with open("responses{0:04}.xml".format(n), 'w', encoding='UTF-8') as f:
                f.write(xml.dom.minidom.parseString(r.raw).toprettyxml())
                sec = random.uniform(interval,max_interval)
                time.sleep(sec)
                print("sleep: {} ".format(sec))
                elapsedTime = time.time() - startTime
                print("elapsed time: {0}".format(elapsedTime))
                n = n+1
    except Exception as e:
        print("{}".format(e))
    elapsedTime = time.time() - startTime
    print("elapsed time: {0}".format(elapsedTime))


def OAIResponseFileValidator(filepath: str, validator: XSDValidator, debug: bool = False):
    """[summary]

    Usage:

    from oaiListRecord import OAIResponseFilesValidator,XSDValidator
    validator = XSDValidator('schema/jpcoar/1.0/jpcoar_scm.xsd')
    OAIResponseFilesValidator('jpcoar/*',validator)

    Args:
        filepath (str): [description]
        validator (XSDValidator): [description]
    """
    doc = etree.parse(filepath)
    root = doc.getroot()
    records = root.xpath(
        '//x:record', namespaces={'x': 'http://www.openarchives.org/OAI/2.0/'})
    numTotal = 0
    numDelete = 0
    numSuccess = 0
    numError = 0
    print("validated file: {0}".format(filepath))
    for r in records:
        numTotal = numTotal + 1
        header = r.find(
            './x:header', namespaces={'x': 'http://www.openarchives.org/OAI/2.0/'})
        metadata = r.find(
            './x:metadata', namespaces={'x': 'http://www.openarchives.org/OAI/2.0/'})
        if header:
            identifier = header.find(
                './x:identifier', namespaces={'x': 'http://www.openarchives.org/OAI/2.0/'})
        if metadata:
            meta = metadata.getchildren()
            for m in meta:
                if validator.validate(m):
                    numSuccess = numSuccess + 1
                else:
                    if debug:
                        # print(etree.dump(m))
                        try:
                            validator.assertValid(m)
                        except etree.DocumentInvalid as e:
                            print(identifier.text)
                            print(e)
                    numError = numError + 1
        else:
            numDelete = numDelete + 1
    print("total: {0}".format(numTotal))
    print("delete records: {0}".format(numDelete))
    print("validate success: {0}".format(numSuccess))
    print("validate error: {0}".format(numError))


def OAIResponseFilesValidator(fileset: str, validator: XSDValidator):
    """[summary]

    Usage:

    from oaiListRecord import OAIResponseFilesValidator,XSDValidator
    validator = XSDValidator('schema/jpcoar/1.0/jpcoar_scm.xsd')
    OAIResponseFilesValidator('jpcoar/*',validator)

    Args:
        fileset (str): OAI-PMH response file set path. (examples: 'files/*','files/*.xml' )
        validator (XSDValidator): XSDValidator instance for OAI-PMH metadata
    """
    files = glob.glob(fileset)
    for f in files:
        OAIResponseFileValidator(f, validator)


def countTagInOAIResponses(fileset: str, namespace: str = 'https://github.com/JPCOAR/schema/blob/master/1.0/', tag: str = 'identifierRegistration', debug: bool = False):
    """Count number of tag in OAI response files.

    Args:
        fileset (str): A set of OAI response files path
        namespace (str, optional): namespace of tag. Defaults to 'https://github.com/JPCOAR/schema/blob/master/1.0/'.
        tag (str, optional): tag name. Defaults to 'identifierRegistration'.
        debug (bool, optional): Output detail information. Defaults to False.
    """
    files = glob.glob(fileset)
    for f in files:
        countTagInOAIResponse(f, namespace, tag, debug)


def countTagInOAIResponse(filepath: str, namespace: str = 'https://github.com/JPCOAR/schema/blob/master/1.0/', tag: str = 'identifierRegistration', debug: bool = False):
    """Count number of tag in OAI response file.

    Args:
        filepath (str): An OAI response file path
        namespace (str): namespace tag
        tag (str): tag name
        debug (bool, optional): Output detail information. Defaults to False.
    """
    doc = etree.parse(filepath)
    root = doc.getroot()
    records = root.xpath(
        '//x:record', namespaces={'x': 'http://www.openarchives.org/OAI/2.0/'})
    numTotal = 0
    count = 0
    print("check file: {0}".format(filepath))
    for r in records:
        numTotal = numTotal + 1
        header = r.find(
            './x:header', namespaces={'x': 'http://www.openarchives.org/OAI/2.0/'})
        metadata = r.find(
            './x:metadata', namespaces={'x': 'http://www.openarchives.org/OAI/2.0/'})
        if header:
            identifier = header.find(
                './x:identifier', namespaces={'x': 'http://www.openarchives.org/OAI/2.0/'})
        if metadata:
            meta = metadata.getchildren()
            for m in meta:
                e = m.find("./x:{0}".format(tag),
                           namespaces={'x': namespace})
                if e is not None:
                    count = count + 1
                    if debug:
                        print(identifier.text)
                        print(e.text)

    print("total: {0}".format(numTotal))
    print("{0}: {1}".format(tag, count))
