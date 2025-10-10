function handleOnclickCid(e){
    console.log('weko_admin_cris_linkage_js')
    $('#researchmap_cidkey').click();
    $('#researchmap_cidkey').on("change", (event) =>{
        const file = event.target.files[0];
        const reader = new FileReader();
        reader.onload = () =>{
            console.log(reader.result);
            $('#researchmap_cidkey_contents').val(reader.result);
        }
        reader.readAsText(file);

        $('#file_name_researchmap_cidkey').text(file.name)
    });
}
function handleOnclickp(e){
    $('#researchmap_pkey').click();
    $('#researchmap_pkey').on("change", (event) =>{
        const file = event.target.files[0];
        const reader = new FileReader();
        reader.onload = () =>{
            console.log(reader.result);
            $('#researchmap_pkey_contents').val(reader.result);
        }
        reader.readAsText(file);

        $('#file_name_researchmap_pkey').text(file.name)
    });
}