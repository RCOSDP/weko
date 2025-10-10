DATABASE = {
  'host': 'localhost',
  'port': 25401,
  'dbname': 'invenio',
  'user': 'invenio',
  'password': 'dbpass123'
}

USERS = {
  'sysadmin': {
    'email': 'wekosoftware@nii.ac.jp',
    'password': 'uspass123'
  },
  'repoadmin': {
    'email': 'repoadmin@example.org',
    'password': 'uspass123'
  },
  'comadmin': {
    'email': 'comadmin@example.org',
    'password': 'uspass123'
  },
  'contributor': {
    'email': 'contributor@example.org',
    'password': 'uspass123'
  },
  'user': {
    'email': 'user@example.org',
    'password': 'uspass123'
  }
}

REPLACEMENT_DECISION_STRING = {
    'BEGIN': '<<',
    'END': '>>'
}

INVENIO_WEB_HOST_NAME='weko3.example.org'

VERSION_TYPE_URI = {
    "AO": "http://purl.org/coar/version/c_b1a7d7d4d402bcce",
    "SMUR": "http://purl.org/coar/version/c_71e4c1898caa6e32",
    "AM": "http://purl.org/coar/version/c_ab4af688f83e57aa",
    "P": "http://purl.org/coar/version/c_fa2ee174bc00049f",
    "VoR": "http://purl.org/coar/version/c_970fb48d4fbd8a85",
    "CVoR": "http://purl.org/coar/version/c_e19f295774971610",
    "EVoR": "http://purl.org/coar/version/c_dc82b40f9837b551",
    "NA": "http://purl.org/coar/version/c_be7fb7dd8ff6fe43",
}

ACCESS_RIGHT_TYPE_URI = {
    "embargoed access": "http://purl.org/coar/access_right/c_f1cf",
    "metadata only access": "http://purl.org/coar/access_right/c_14cb",
    "open access": "http://purl.org/coar/access_right/c_abf2",
    "restricted access": "http://purl.org/coar/access_right/c_16ec",
}

RESOURCE_TYPE_URI = {
    "conference paper": "http://purl.org/coar/resource_type/c_5794",
    "data paper": "http://purl.org/coar/resource_type/c_beb9",
    "departmental bulletin paper": "http://purl.org/coar/resource_type/c_6501",
    "editorial": "http://purl.org/coar/resource_type/c_b239",
    "journal": "http://purl.org/coar/resource_type/c_0640",
    "journal article": "http://purl.org/coar/resource_type/c_6501",
    "newspaper": "http://purl.org/coar/resource_type/c_2fe3",
    "review article": "http://purl.org/coar/resource_type/c_dcae04bc",
    "other periodical":"http://purl.org/coar/resource_type/QX5C-AR31",
    "software paper": "http://purl.org/coar/resource_type/c_7bab",
    "article": "http://purl.org/coar/resource_type/c_6501",
    "book": "http://purl.org/coar/resource_type/c_2f33",
    "book part": "http://purl.org/coar/resource_type/c_3248",
    "cartographic material": "http://purl.org/coar/resource_type/c_12cc",
    "map": "http://purl.org/coar/resource_type/c_12cd",
    "conference output":"http://purl.org/coar/resource_type/c_c94f",
    "conference presentation":"http://purl.org/coar/resource_type/c_c94f",
    "conference proceedings": "http://purl.org/coar/resource_type/c_f744",
    "conference poster": "http://purl.org/coar/resource_type/c_6670",
    "aggregated data": "http://purl.org/coar/resource_type/ACF7-8YT9",
    "clinical trial data": "http://purl.org/coar/resource_type/c_cb28",
    "compiled data": "http://purl.org/coar/resource_type/FXF3-D3G7",
    "dataset": "http://purl.org/coar/resource_type/c_ddb1",
    "encoded data": "http://purl.org/coar/resource_type/AM6W-6QAW",
    "experimental data": "http://purl.org/coar/resource_type/63NG-B465",
    "genomic data": "http://purl.org/coar/resource_type/A8F1-NPV9",
    "geospatial data": "http://purl.org/coar/resource_type/2H0M-X761",
    "laboratory notebook": "http://purl.org/coar/resource_type/H41Y-FW7B",
    "measurement and test data": "http://purl.org/coar/resource_type/DD58-GFSX",
    "observational data": "http://purl.org/coar/resource_type/FF4C-28RK",
    "recorded data": "http://purl.org/coar/resource_type/CQMR-7K63",
    "simulation data": "http://purl.org/coar/resource_type/W2XT-7017",
    "survey data": "http://purl.org/coar/resource_type/NHD0-W6SY",
    "image": "http://purl.org/coar/resource_type/c_c513",
    "still image": "http://purl.org/coar/resource_type/c_ecc8",
    "moving image": "http://purl.org/coar/resource_type/c_8a7e",
    "video": "http://purl.org/coar/resource_type/c_12ce",
    "lecture": "http://purl.org/coar/resource_type/c_8544",
    "design patent":"http://purl.org/coar/resource_type/C53B-JCY5/",
    "patent": "http://purl.org/coar/resource_type/c_15cd",
    "PCT application":"http://purl.org/coar/resource_type/SB3Y-W4EH/",
    "plant patent":"http://purl.org/coar/resource_type/Z907-YMBB/",
    "plant variety protection":"http://purl.org/coar/resource_type/GPQ7-G5VE/",
    "software patent":"http://purl.org/coar/resource_type/MW8G-3CR8/",
    "trademark":"http://purl.org/coar/resource_type/H6QP-SC1X/",
    "utility model":"http://purl.org/coar/resource_type/9DKX-KSAF/",
    "report": "http://purl.org/coar/resource_type/c_93fc",
    "research report": "http://purl.org/coar/resource_type/c_18ws",
    "technical report": "http://purl.org/coar/resource_type/c_18gh",
    "policy report": "http://purl.org/coar/resource_type/c_186u",
    "working paper": "http://purl.org/coar/resource_type/c_8042",
    "data management plan": "http://purl.org/coar/resource_type/c_ab20",
    "sound": "http://purl.org/coar/resource_type/c_18cc",
    "thesis": "http://purl.org/coar/resource_type/c_46ec",
    "bachelor thesis": "http://purl.org/coar/resource_type/c_7a1f",
    "master thesis": "http://purl.org/coar/resource_type/c_bdcc",
    "doctoral thesis": "http://purl.org/coar/resource_type/c_db06",
    "commentary":"http://purl.org/coar/resource_type/D97F-VB57/",
    'design': 'http://purl.org/coar/resource_type/542X-3S04/',
    'industrial design': 'http://purl.org/coar/resource_type/JBNF-DYAD/',
    "interactive resource": "http://purl.org/coar/resource_type/c_e9a0",
    'layout design': 'http://purl.org/coar/resource_type/BW7T-YM2G/',
    "learning object": "http://purl.org/coar/resource_type/c_e059",
    "manuscript": "http://purl.org/coar/resource_type/c_0040",
    "musical notation": "http://purl.org/coar/resource_type/c_18cw",
    'peer review': 'http://purl.org/coar/resource_type/H9BQ-739P/',
    "research proposal": "http://purl.org/coar/resource_type/c_baaf",
    'research protocol': 'http://purl.org/coar/resource_type/YZ1N-ZFT9/',
    "software": "http://purl.org/coar/resource_type/c_5ce6",
    'source code':'http://purl.org/coar/resource_type/QH80-2R4E/',
    "technical documentation": "http://purl.org/coar/resource_type/c_71bd",
    'transcription': 'http://purl.org/coar/resource_type/6NC7-GK9S/',
    "workflow": "http://purl.org/coar/resource_type/c_393c",
    "other": "http://purl.org/coar/resource_type/c_1843"
}

WEKO_RECORDS_UI_LICENSE_DICT = [
    {
        'name': 'write your own license',
        'value': 'license_free',
    },
    # version 0
    {
        'name': 'Creative Commons CC0 1.0 Universal Public Domain Designation',
        'code' : 'CC0',
        'href_ja': 'https://creativecommons.org/publicdomain/zero/1.0/deed.ja',
        'href_default': 'https://creativecommons.org/publicdomain/zero/1.0/',
        'value': 'license_12',
        'src': '88x31(0).png',
        'src_pdf': 'cc-0.png',
        'href_pdf': 'https://creativecommons.org/publicdomain/zero/1.0/'
                    'deed.ja',
        'txt': 'This work is licensed under a Public Domain Dedication '
               'International License.'
    },
    # version 3.0
    {
        'name': 'Creative Commons Attribution 3.0 Unported (CC BY 3.0)',
        'code' : 'CC BY 3.0',
        'href_ja': 'https://creativecommons.org/licenses/by/3.0/deed.ja',
        'href_default': 'https://creativecommons.org/licenses/by/3.0/',
        'value': 'license_6',
        'src': '88x31(1).png',
        'src_pdf': 'by.png',
        'href_pdf': 'http://creativecommons.org/licenses/by/3.0/',
        'txt': 'This work is licensed under a Creative Commons Attribution'
               ' 3.0 International License.'
    },
    {
        'name': 'Creative Commons Attribution-ShareAlike 3.0 Unported (CC BY-SA 3.0)',
        'code' : 'CC BY-SA 3.0',
        'href_ja': 'https://creativecommons.org/licenses/by-sa/3.0/deed.ja',
        'href_default': 'https://creativecommons.org/licenses/by-sa/3.0/',
        'value': 'license_7',
        'src': '88x31(2).png',
        'src_pdf': 'by-sa.png',
        'href_pdf': 'http://creativecommons.org/licenses/by-sa/3.0/',
        'txt': 'This work is licensed under a Creative Commons Attribution'
               '-ShareAlike 3.0 International License.'
    },
    {
        'name': 'Creative Commons Attribution-NoDerivs 3.0 Unported (CC BY-ND 3.0)',
        'code' : 'CC BY-ND 3.0',
        'href_ja': 'https://creativecommons.org/licenses/by-nd/3.0/deed.ja',
        'href_default': 'https://creativecommons.org/licenses/by-nd/3.0/',
        'value': 'license_8',
        'src': '88x31(3).png',
        'src_pdf': 'by-nd.png',
        'href_pdf': 'http://creativecommons.org/licenses/by-nd/3.0/',
        'txt': 'This work is licensed under a Creative Commons Attribution'
               '-NoDerivatives 3.0 International License.'

    },
    {
        'name': 'Creative Commons Attribution-NonCommercial 3.0 Unported (CC BY-NC 3.0)',
        'code' : 'CC BY-NC 3.0',
        'href_ja': 'https://creativecommons.org/licenses/by-nc/3.0/deed.ja',
        'href_default': 'https://creativecommons.org/licenses/by-nc/3.0/',
        'value': 'license_9',
        'src': '88x31(4).png',
        'src_pdf': 'by-nc.png',
        'href_pdf': 'http://creativecommons.org/licenses/by-nc/3.0/',
        'txt': 'This work is licensed under a Creative Commons Attribution'
               '-NonCommercial 3.0 International License.'
    },
    {
        'name': 'Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported (CC BY-NC-SA 3.0)',
        'code' : 'CC BY-NC-SA 3.0',
        'href_ja': 'https://creativecommons.org/licenses/by-nc-sa/3.0/deed.ja',
        'href_default': 'https://creativecommons.org/licenses/by-nc-sa/3.0/',
        'value': 'license_10',
        'src': '88x31(5).png',
        'src_pdf': 'by-nc-sa.png',
        'href_pdf': 'http://creativecommons.org/licenses/by-nc-sa/3.0/',
        'txt': 'This work is licensed under a Creative Commons Attribution'
               '-NonCommercial-ShareAlike 3.0 International License.'
    },
    {
        'name': 'Creative Commons Attribution-NonCommercial-NoDerivs 3.0 Unported (CC BY-NC-ND 3.0)',
        'code' : 'CC BY-NC-ND 3.0',
        'href_ja': 'https://creativecommons.org/licenses/by-nc-nd/3.0/deed.ja',
        'href_default': 'https://creativecommons.org/licenses/by-nc-nd/3.0/',
        'value': 'license_11',
        'src': '88x31(6).png',
        'src_pdf': 'by-nc-nd.png',
        'href_pdf': 'http://creativecommons.org/licenses/by-nc-nd/3.0/',
        'txt': 'This work is licensed under a Creative Commons Attribution'
               '-NonCommercial-ShareAlike 3.0 International License.'
    },
    # version 4.0
    {
        'name': 'Creative Commons Attribution 4.0 International (CC BY 4.0)',
        'code' : 'CC BY 4.0',
        'href_ja': 'https://creativecommons.org/licenses/by/4.0/deed.ja',
        'href_default': 'https://creativecommons.org/licenses/by/4.0/',
        'value': 'license_0',
        'src': '88x31(1).png',
        'src_pdf': 'by.png',
        'href_pdf': 'http://creativecommons.org/licenses/by/4.0/',
        'txt': 'This work is licensed under a Creative Commons Attribution'
               ' 4.0 International License.'
    },
    {
        'name': 'Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)',
        'code' : 'CC BY-SA 4.0',
        'href_ja': 'https://creativecommons.org/licenses/by-sa/4.0/deed.ja',
        'href_default': 'https://creativecommons.org/licenses/by-sa/4.0/',
        'value': 'license_1',
        'src': '88x31(2).png',
        'src_pdf': 'by-sa.png',
        'href_pdf': 'http://creativecommons.org/licenses/by-sa/4.0/',
        'txt': 'This work is licensed under a Creative Commons Attribution'
               '-ShareAlike 4.0 International License.'
    },
    {
        'name': 'Creative Commons Attribution-NoDerivatives 4.0 International (CC BY-ND 4.0)',
        'code' : 'CC BY-ND 4.0',
        'href_ja': 'https://creativecommons.org/licenses/by-nd/4.0/deed.ja',
        'href_default': 'https://creativecommons.org/licenses/by-nd/4.0/',
        'value': 'license_2',
        'src': '88x31(3).png',
        'src_pdf': 'by-nd.png',
        'href_pdf': 'http://creativecommons.org/licenses/by-nd/4.0/',
        'txt': 'This work is licensed under a Creative Commons Attribution'
               '-NoDerivatives 4.0 International License.'
    },
    {
        'name': 'Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)',
        'code' : 'CC BY-NC 4.0',
        'href_ja': 'https://creativecommons.org/licenses/by-nc/4.0/deed.ja',
        'href_default': 'https://creativecommons.org/licenses/by-nc/4.0/',
        'value': 'license_3',
        'src': '88x31(4).png',
        'src_pdf': 'by-nc.png',
        'href_pdf': 'http://creativecommons.org/licenses/by-nc/4.0/',
        'txt': 'This work is licensed under a Creative Commons Attribution'
               '-NonCommercial 4.0 International License.'
    },
    {
        'name': 'Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)',
        'code' : 'CC BY-NC-SA 4.0',
        'href_ja': 'https://creativecommons.org/licenses/by-nc-sa/4.0/deed.ja',
        'href_default': 'https://creativecommons.org/licenses/by-nc-sa/4.0/',
        'value': 'license_4',
        'src': '88x31(5).png',
        'src_pdf': 'by-nc-sa.png',
        'href_pdf': 'http://creativecommons.org/licenses/by-nc-sa/4.0/',
        'txt': 'This work is licensed under a Creative Commons Attribution'
               '-NonCommercial-ShareAlike 4.0 International License.'
    },
    {
        'name': 'Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International (CC BY-NC-ND 4.0)',
        'code' : 'CC BY-NC-ND 4.0',
        'href_ja': 'https://creativecommons.org/licenses/by-nc-nd/4.0/deed.ja',
        'href_default': 'https://creativecommons.org/licenses/by-nc-nd/4.0/',
        'value': 'license_5',
        'src': '88x31(6).png',
        'src_pdf': 'by-nc-nd.png',
        'href_pdf': 'http://creativecommons.org/licenses/by-nc-nd/4.0/',
        'txt': 'This work is licensed under a Creative Commons Attribution'
               '-NonCommercial-ShareAlike 4.0 International License.'
    },
]
