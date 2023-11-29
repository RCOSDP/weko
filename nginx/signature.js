let crypto = require("crypto");
let querystring =  require('querystring');
let d = new Date();

function gettz(r){
    if(r.headersIn["tz"]){
        return r.headersIn["tz"];
    }
    return d.toISOString().replaceAll("-", "").replaceAll(":", "").slice(0,15) + "Z";
}

function getAuth(r){
    const accessKey = process.env["S3ACCESSKEY"];
    const secretKey = process.env["S3SECRETKEY"];
    const regionName = process.env["S3REGIONNAME"];

    const tz = gettz(r);
    const authorization = "AWS4-HMAC-SHA256 Credential=" + accessKey + "/" + 
                        tz.slice(0,8) + 
                        `/${regionName}/s3/aws4_request, SignedHeaders=host;x-amz-content-sha256;x-amz-date, Signature=`;

    const payloadHash = getPayloadHash(r);

    let uri = "/" + getPath(r);

    const query = querystring.stringify(r.args);

    const canonicalRequest =  r.method + "\n" +
                            encodeURI(uri) + "\n" +
                            query + "\n" +
                            "host:" + getHost(r) + "\n" +
                            "x-amz-content-sha256:" + payloadHash + "\n" +
                            "x-amz-date:" + tz + "\n" +
                            "\n" +
                            "host;x-amz-content-sha256;x-amz-date\n" +
                            payloadHash

    const urlenc = crypto.createHash("sha256").update(canonicalRequest).digest("hex");

    const stringToSign =    "AWS4-HMAC-SHA256\n" +
                            tz + "\n" +
                            tz.slice(0,8) + `/${regionName}/s3/aws4_request\n` +
                            urlenc

    const dateKey = crypto.createHmac("sha256", "AWS4" + secretKey).update(tz.slice(0,8)).digest();
    const dateRegionKey = crypto.createHmac("sha256", dateKey).update(regionName).digest();
    const dateRegionServiceKey = crypto.createHmac("sha256", dateRegionKey).update("s3").digest();
    const signingKey = crypto.createHmac("sha256", dateRegionServiceKey).update("aws4_request").digest();

    const signature = crypto.createHmac("sha256", signingKey).update(stringToSign).digest("hex");

    return authorization + signature;
}

function getPath(r){
    const bucketName = process.env["S3BUCKETNAME"];
    const kikanmei = process.env["KIKANMEI"];

    const uri = r.uri;
    if(uri == "/"){
        return `${bucketName}`;
    }else{
        return `${bucketName}/${kikanmei}${uri}`;
    }
}

function getURL(r){
    const bucketName = process.env["S3BUCKETNAME"];
    const kikanmei = process.env["KIKANMEI"];
    const host = process.env["S3HOST"];
    const uri = r.uri;
    if(uri == "/"){
        return `${host}/${bucketName}`;
    }else{
        return `${host}/${bucketName}/${kikanmei}`;
    }
}

function getContentType(r){
    return r.headersIn["Content-Type"];
}

function getContentLength(r){
    return r.headersIn["Content-Length"];
}

function getPayloadHash(r){
    if(r.headersIn["bodyHash"]){
        return r.headersIn["bodyHash"];
    }
    const pay = r.requestText;
    if(!pay){
        return crypto.createHash("sha256").update("").digest("hex");
    }else{
        return crypto.createHash("sha256").update(pay).digest("hex");
    }
}

function getRange(r){
    return r.headersIn["range"];
}

function getHost(r){
    return process.env["S3HOST"];
}

export default {
    gettz,
    getContentType, 
    getContentLength, 
    getPayloadHash,
    getAuth,
    getPath,
    getURL,
    getRange,
    getHost
};