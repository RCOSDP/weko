var myUV;
window.addEventListener('uvLoaded', function (e) {
    myUV = createUV('#uv', {
        iiifResourceUri: '{{ file.uri }}',
    }, new UV.URLDataProvider());

    myUV.on("created", function(obj) {
        console.log('parsed metadata', myUV.extension.helper.manifest.getMetadata());
        console.log('raw jsonld', myUV.extension.helper.manifest.__jsonld);
    });
}, false);
