# conftest.py
import pytest

# language code list
language_val3 = [
    None,
    "jpn",
    "eng",
    "aar",
    "abk",
    "afr",
    "aka",
    "amh",
    "ara",
    "arg",
    "asm",
    "ava",
    "ave",
    "aym",
    "aze",
    "bak",
    "bam",
    "bel",
    "ben",
    "bis",
    "bod",
    "bos",
    "bre",
    "bul",
    "cat",
    "ces",
    "cha",
    "che",
    "chu",
    "chv",
    "cor",
    "cos",
    "cre",
    "cym",
    "dan",
    "deu",
    "div",
    "dzo",
    "ell",
    "epo",
    "est",
    "eus",
    "ewe",
    "fao",
    "fas",
    "fij",
    "fin",
    "fra",
    "fry",
    "ful",
    "gla",
    "gle",
    "glg",
    "glv",
    "grn",
    "guj",
    "hat",
    "hau",
    "heb",
    "her",
    "hin",
    "hmo",
    "hrv",
    "hun",
    "hye",
    "ibo",
    "ido",
    "iii",
    "iku",
    "ile",
    "ina",
    "ind",
    "ipk",
    "isl",
    "ita",
    "jav",
    "kal",
    "kan",
    "kas",
    "kat",
    "kau",
    "kaz",
    "khm",
    "kik",
    "kin",
    "kir",
    "kom",
    "kon",
    "kor",
    "kua",
    "kur",
    "lao",
    "lat",
    "lav",
    "lim",
    "lin",
    "lit",
    "ltz",
    "lub",
    "lug",
    "mah",
    "mal",
    "mar",
    "mkd",
    "mlg",
    "mlt",
    "mon",
    "mri",
    "msa",
    "mya",
    "nau",
    "nav",
    "nbl",
    "nde",
    "ndo",
    "nep",
    "nld",
    "nno",
    "nob",
    "nor",
    "nya",
    "oci",
    "oji",
    "ori",
    "orm",
    "oss",
    "pan",
    "pli",
    "pol",
    "por",
    "pus",
    "que",
    "roh",
    "ron",
    "run",
    "rus",
    "sag",
    "san",
    "sin",
    "slk",
    "slv",
    "sme",
    "smo",
    "sna",
    "snd",
    "som",
    "sot",
    "spa",
    "sqi",
    "srd",
    "srp",
    "ssw",
    "sun",
    "swa",
    "swe",
    "tah",
    "tam",
    "tat",
    "tel",
    "tgk",
    "tgl",
    "tha",
    "tir",
    "ton",
    "tsn",
    "tso",
    "tuk",
    "tur",
    "twi",
    "uig",
    "ukr",
    "urd",
    "uzb",
    "ven",
    "vie",
    "vol",
    "wln",
    "wol",
    "xho",
    "yid",
    "yor",
    "zha",
    "zho",
    "zul",
]

# title map
title_map = [
    {"name": "jpn", "value": "jpn"},
    {"name": "eng", "value": "eng"},
    {"name": "aar", "value": "aar"},
    {"name": "abk", "value": "abk"},
    {"name": "afr", "value": "afr"},
    {"name": "aka", "value": "aka"},
    {"name": "amh", "value": "amh"},
    {"name": "ara", "value": "ara"},
    {"name": "arg", "value": "arg"},
    {"name": "asm", "value": "asm"},
    {"name": "ava", "value": "ava"},
    {"name": "ave", "value": "ave"},
    {"name": "aym", "value": "aym"},
    {"name": "aze", "value": "aze"},
    {"name": "bak", "value": "bak"},
    {"name": "bam", "value": "bam"},
    {"name": "bel", "value": "bel"},
    {"name": "ben", "value": "ben"},
    {"name": "bis", "value": "bis"},
    {"name": "bod", "value": "bod"},
    {"name": "bos", "value": "bos"},
    {"name": "bre", "value": "bre"},
    {"name": "bul", "value": "bul"},
    {"name": "cat", "value": "cat"},
    {"name": "ces", "value": "ces"},
    {"name": "cha", "value": "cha"},
    {"name": "che", "value": "che"},
    {"name": "chu", "value": "chu"},
    {"name": "chv", "value": "chv"},
    {"name": "cor", "value": "cor"},
    {"name": "cos", "value": "cos"},
    {"name": "cre", "value": "cre"},
    {"name": "cym", "value": "cym"},
    {"name": "dan", "value": "dan"},
    {"name": "deu", "value": "deu"},
    {"name": "div", "value": "div"},
    {"name": "dzo", "value": "dzo"},
    {"name": "ell", "value": "ell"},
    {"name": "epo", "value": "epo"},
    {"name": "est", "value": "est"},
    {"name": "eus", "value": "eus"},
    {"name": "ewe", "value": "ewe"},
    {"name": "fao", "value": "fao"},
    {"name": "fas", "value": "fas"},
    {"name": "fij", "value": "fij"},
    {"name": "fin", "value": "fin"},
    {"name": "fra", "value": "fra"},
    {"name": "fry", "value": "fry"},
    {"name": "ful", "value": "ful"},
    {"name": "gla", "value": "gla"},
    {"name": "gle", "value": "gle"},
    {"name": "glg", "value": "glg"},
    {"name": "glv", "value": "glv"},
    {"name": "grn", "value": "grn"},
    {"name": "guj", "value": "guj"},
    {"name": "hat", "value": "hat"},
    {"name": "hau", "value": "hau"},
    {"name": "heb", "value": "heb"},
    {"name": "her", "value": "her"},
    {"name": "hin", "value": "hin"},
    {"name": "hmo", "value": "hmo"},
    {"name": "hrv", "value": "hrv"},
    {"name": "hun", "value": "hun"},
    {"name": "hye", "value": "hye"},
    {"name": "ibo", "value": "ibo"},
    {"name": "ido", "value": "ido"},
    {"name": "iii", "value": "iii"},
    {"name": "iku", "value": "iku"},
    {"name": "ile", "value": "ile"},
    {"name": "ina", "value": "ina"},
    {"name": "ind", "value": "ind"},
    {"name": "ipk", "value": "ipk"},
    {"name": "isl", "value": "isl"},
    {"name": "ita", "value": "ita"},
    {"name": "jav", "value": "jav"},
    {"name": "kal", "value": "kal"},
    {"name": "kan", "value": "kan"},
    {"name": "kas", "value": "kas"},
    {"name": "kat", "value": "kat"},
    {"name": "kau", "value": "kau"},
    {"name": "kaz", "value": "kaz"},
    {"name": "khm", "value": "khm"},
    {"name": "kik", "value": "kik"},
    {"name": "kin", "value": "kin"},
    {"name": "kir", "value": "kir"},
    {"name": "kom", "value": "kom"},
    {"name": "kon", "value": "kon"},
    {"name": "kor", "value": "kor"},
    {"name": "kua", "value": "kua"},
    {"name": "kur", "value": "kur"},
    {"name": "lao", "value": "lao"},
    {"name": "lat", "value": "lat"},
    {"name": "lav", "value": "lav"},
    {"name": "lim", "value": "lim"},
    {"name": "lin", "value": "lin"},
    {"name": "lit", "value": "lit"},
    {"name": "ltz", "value": "ltz"},
    {"name": "lub", "value": "lub"},
    {"name": "lug", "value": "lug"},
    {"name": "mah", "value": "mah"},
    {"name": "mal", "value": "mal"},
    {"name": "mar", "value": "mar"},
    {"name": "mkd", "value": "mkd"},
    {"name": "mlg", "value": "mlg"},
    {"name": "mlt", "value": "mlt"},
    {"name": "mon", "value": "mon"},
    {"name": "mri", "value": "mri"},
    {"name": "msa", "value": "msa"},
    {"name": "mya", "value": "mya"},
    {"name": "nau", "value": "nau"},
    {"name": "nav", "value": "nav"},
    {"name": "nbl", "value": "nbl"},
    {"name": "nde", "value": "nde"},
    {"name": "ndo", "value": "ndo"},
    {"name": "nep", "value": "nep"},
    {"name": "nld", "value": "nld"},
    {"name": "nno", "value": "nno"},
    {"name": "nob", "value": "nob"},
    {"name": "nor", "value": "nor"},
    {"name": "nya", "value": "nya"},
    {"name": "oci", "value": "oci"},
    {"name": "oji", "value": "oji"},
    {"name": "ori", "value": "ori"},
    {"name": "orm", "value": "orm"},
    {"name": "oss", "value": "oss"},
    {"name": "pan", "value": "pan"},
    {"name": "pli", "value": "pli"},
    {"name": "pol", "value": "pol"},
    {"name": "por", "value": "por"},
    {"name": "pus", "value": "pus"},
    {"name": "que", "value": "que"},
    {"name": "roh", "value": "roh"},
    {"name": "ron", "value": "ron"},
    {"name": "run", "value": "run"},
    {"name": "rus", "value": "rus"},
    {"name": "sag", "value": "sag"},
    {"name": "san", "value": "san"},
    {"name": "sin", "value": "sin"},
    {"name": "slk", "value": "slk"},
    {"name": "slv", "value": "slv"},
    {"name": "sme", "value": "sme"},
    {"name": "smo", "value": "smo"},
    {"name": "sna", "value": "sna"},
    {"name": "snd", "value": "snd"},
    {"name": "som", "value": "som"},
    {"name": "sot", "value": "sot"},
    {"name": "spa", "value": "spa"},
    {"name": "sqi", "value": "sqi"},
    {"name": "srd", "value": "srd"},
    {"name": "srp", "value": "srp"},
    {"name": "ssw", "value": "ssw"},
    {"name": "sun", "value": "sun"},
    {"name": "swa", "value": "swa"},
    {"name": "swe", "value": "swe"},
    {"name": "tah", "value": "tah"},
    {"name": "tam", "value": "tam"},
    {"name": "tat", "value": "tat"},
    {"name": "tel", "value": "tel"},
    {"name": "tgk", "value": "tgk"},
    {"name": "tgl", "value": "tgl"},
    {"name": "tha", "value": "tha"},
    {"name": "tir", "value": "tir"},
    {"name": "ton", "value": "ton"},
    {"name": "tsn", "value": "tsn"},
    {"name": "tso", "value": "tso"},
    {"name": "tuk", "value": "tuk"},
    {"name": "tur", "value": "tur"},
    {"name": "twi", "value": "twi"},
    {"name": "uig", "value": "uig"},
    {"name": "ukr", "value": "ukr"},
    {"name": "urd", "value": "urd"},
    {"name": "uzb", "value": "uzb"},
    {"name": "ven", "value": "ven"},
    {"name": "vie", "value": "vie"},
    {"name": "vol", "value": "vol"},
    {"name": "wln", "value": "wln"},
    {"name": "wol", "value": "wol"},
    {"name": "xho", "value": "xho"},
    {"name": "yid", "value": "yid"},
    {"name": "yor", "value": "yor"},
    {"name": "zha", "value": "zha"},
    {"name": "zho", "value": "zho"},
    {"name": "zul", "value": "zul"}
]


default_schema = {
    "type": "object",
    "format": "object",
    "title": "original_language",
    "properties": {
        "original_language": {
            "type": ["null", "string"],
            "format": "select",
            "title": "Original Language",
            "enum": language_val3
        },
    },
}

default_post_data = {
    "table_row_map": {
        "form": [
            {
                "items": [
                    {
                        "key": "item_original_lang[].original_language",
                        "type": "select",
                        "titleMap": title_map,
                        "title": "原文の言語",
                        "title_i18n": {"ja": "原文の言語", "en": "Original Language"}
                    }
                ],
                "key": "item_original_lang",
                "add": "New",
                "style": {"add": "btn-success"},
                "title": "原文の言語",
                "title_i18n": {"ja": "原文の言語", "en": "Original Language"}
            }
        ],
        "schema": {
            "properties": {
                "item_original_lang": {
                    "type": "array",
                    "title": "原文の言語",
                    "minItems": "1",
                    "maxItems": "9999",
                    "items": default_schema
                }
            },
            "required": []
        },
        "mapping": {
            "item_original_lang": {
                "display_lang_type": "",
                "jpcoar_v1_mapping": "",
                "jpcoar_mapping": {
                    "originalLanguage": {
                        "@value": "original_language",
                        "@attributes": {"xml:lang": "original_language_language"},
                    }
                },
                "junii2_mapping": "",
                "lido_mapping": "",
                "lom_mapping": "",
                "oai_dc_mapping": "",
                "spase_mapping": "",
            }
        }
    },
    "table_row": ["item_original_lang"],
    "meta_system": {},
    "meta_list": {
        "item_original_lang": {
            "title": "原文の言語",
            "title_i18n": {"ja": "原文の言語", "en": "Original Language"},
            "input_type": "cus_1052",
            "input_value": "",
            "option": {
                "required": False,
                "multiple": True,
                "hidden": False,
                "showlist": False,
                "crtf": False,
                "oneline": False,
            },
            "input_minItems": "1",
            "input_maxItems": "9999"
        }
    },
    "schemaeditor": {
        "schema": {
            "item_original_lang": default_schema
        }
    },
    "edit_notes": {
        "item_original_lang": ""
    }
}

default_post_data_funding = {
	"table_row_map": {
		"form": [
			{
				"add": "New",
				"style": {"add": "btn-success"},
				"title": "助成情報",
				"title_i18n": {"ja": "助成情報", "en": "Funder"},
				"items": [
					{
						"items": [
							{
								"key": "item_funding_reference[].subitem_funder_identifiers.subitem_funder_identifier_type",
								"title": "助成機関識別子タイプ",
								"title_i18n": {
									"en": "Funder Identifier Type",
									"ja": "助成機関識別子タイプ",
								},
								"titleMap": [
									{"name": "Crossref Funder", "value": "Crossref Funder"},
									{"name": "e-Rad_funder", "value": "e-Rad_funder"},
									{"name": "GRID【非推奨】", "value": "GRID"},
									{"name": "ISNI", "value": "ISNI"},
									{"name": "ROR", "value": "ROR"},
									{"name": "Other", "value": "Other"}
								],
								"type": "select",
							},
							{
								"key": "item_funding_reference[].subitem_funder_identifiers.subitem_funder_identifier_type_uri",
								"title": "助成機関識別子URI",
								"title_i18n": {
									"en": "Funder Identifier Type URI",
									"ja": "助成機関識別子タイプURI",
								},
								"type": "text",
							},
							{
								"key": "item_funding_reference[].subitem_funder_identifiers.subitem_funder_identifier",
								"title": "助成機関識別子",
								"title_i18n": {"en": "Funder Identifier", "ja": "助成機関識別子"},
								"type": "text",
							},
						],
						"key": "item_funding_reference[].subitem_funder_identifiers",
						"type": "fieldset",
						"title": "助成機関識別子",
						"title_i18n": {"en": "Funder Identifier", "ja": "助成機関識別子"},
					},
					{
						"add": "New",
						"items": [
							{
								"key": "item_funding_reference[].subitem_funder_names[].subitem_funder_name",
								"title": "助成機関名",
								"title_i18n": {"en": "Funder Name", "ja": "助成機関名"},
								"type": "text",
							},
							{
								"key": "item_funding_reference[].subitem_funder_names[].subitem_funder_name_language",
								"title": "言語",
								"title_i18n": {"en": "Language", "ja": "言語"},
								"titleMap": [
									{"name": "ja", "value": "ja"},
									{"name": "ja-Kana", "value": "ja-Kana"},
									{"name": "ja-Latn", "value": "ja-Latn"},
									{"name": "en", "value": "en"},
									{"name": "fr", "value": "fr"},
									{"name": "it", "value": "it"},
									{"name": "de", "value": "de"},
									{"name": "es", "value": "es"},
									{"name": "zh-cn", "value": "zh-cn"},
									{"name": "zh-tw", "value": "zh-tw"},
									{"name": "ru", "value": "ru"},
									{"name": "la", "value": "la"},
									{"name": "ms", "value": "ms"},
									{"name": "eo", "value": "eo"},
									{"name": "ar", "value": "ar"},
									{"name": "el", "value": "el"},
									{"name": "ko", "value": "ko"}
								],
								"type": "select",
							},
						],
						"key": "item_funding_reference[].subitem_funder_names",
						"style": {"add": "btn-success"},
						"title": "助成機関名",
						"title_i18n": {"en": "Funder Name", "ja": "助成機関名"},
					},
					{
						"items": [
							{
								"key": "item_funding_reference[].subitem_funding_stream_identifiers.subitem_funding_stream_identifier_type",
								"title": "プログラム情報識別子タイプ",
								"title_i18n": {
									"en": "Funding Stream Identifier Type",
									"ja": "プログラム情報識別子タイプ",
								},
								"titleMap": [
									{"name": "Crossref Funder", "value": "Crossref Funder"},
									{"name": "JGN_fundingStream", "value": "JGN_fundingStream"}
								],
								"type": "select",
							},
							{
								"key": "item_funding_reference[].subitem_funding_stream_identifiers.subitem_funding_stream_identifier_type_uri",
								"title": "プログラム情報識別子タイプURI",
								"title_i18n": {
									"en": "Funding Stream Identifier Type URI",
									"ja": "プログラム情報識別子タイプURI",
								},
								"type": "text",
							},
							{
								"key": "item_funding_reference[].subitem_funding_stream_identifiers.subitem_funding_stream_identifier",
								"title": "プログラム情報識別子",
								"title_i18n": {
									"en": "Funding Stream Identifier",
									"ja": "プログラム情報識別子",
								},
								"type": "text",
							},
						],
						"key": "item_funding_reference[].subitem_funding_stream_identifiers",
						"title": "プログラム情報識別子",
						"title_i18n": {
							"en": "Funding Stream Identifiers",
							"ja": "プログラム情報識別子",
						},
					},
					{
						"add": "New",
						"items": [
							{
								"key": "item_funding_reference[].subitem_funding_streams[].subitem_funding_stream_language",
								"title": "言語",
								"title_i18n": {"en": "Language", "ja": "言語"},
								"titleMap": [
									{"name": "ja", "value": "ja"},
									{"name": "ja-Kana", "value": "ja-Kana"},
									{"name": "ja-Latn", "value": "ja-Latn"},
									{"name": "en", "value": "en"},
									{"name": "fr", "value": "fr"},
									{"name": "it", "value": "it"},
									{"name": "de", "value": "de"},
									{"name": "es", "value": "es"},
									{"name": "zh-cn", "value": "zh-cn"},
									{"name": "zh-tw", "value": "zh-tw"},
									{"name": "ru", "value": "ru"},
									{"name": "la", "value": "la"},
									{"name": "ms", "value": "ms"},
									{"name": "eo", "value": "eo"},
									{"name": "ar", "value": "ar"},
									{"name": "el", "value": "el"},
									{"name": "ko", "value": "ko"}
								],
								"type": "select",
							},
							{
								"key": "item_funding_reference[].subitem_funding_streams[].subitem_funding_stream",
								"title": "プログラム情報",
								"title_i18n": {
									"en": "Funding Stream",
									"ja": "プログラム情報",
								},
								"type": "text",
							},
						],
						"key": "item_funding_reference[].subitem_funding_streams",
						"style": {"add": "btn-success"},
						"title": "プログラム情報",
						"title_i18n": {"en": "Funding Streams", "ja": "プログラム情報"},
					},
					{
						"items": [
							{
								"key": "item_funding_reference[].subitem_award_numbers.subitem_award_uri",
								"title": "研究課題番号URI",
								"title_i18n": {"en": "Award Number URI", "ja": "研究課題番号URI"},
								"type": "text",
							},
							{
								"key": "item_funding_reference[].subitem_award_numbers.subitem_award_number",
								"title": "研究課題番号",
								"title_i18n": {"en": "Award Number", "ja": "研究課題番号"},
								"type": "text",
							},
							{
								"key": "item_funding_reference[].subitem_award_numbers.subitem_award_number_type",
								"title": "研究課題番号タイプ",
								"title_i18n": {
									"en": "Award Number Type",
									"ja": "研究課題番号タイプ",
								},
								"titleMap": [
									{"name": "JGN", "value": "JGN"}
								],
								"type": "select",
							},
						],
						"key": "item_funding_reference[].subitem_award_numbers",
						"title": "研究課題番号",
						"title_i18n": {"en": "Award Number", "ja": "研究課題番号"},
					},
					{
						"add": "New",
						"items": [
							{
								"key": "item_funding_reference[].subitem_award_titles[].subitem_award_title",
								"title": "研究課題名",
								"title_i18n": {"en": "Award Title", "ja": "研究課題名"},
								"type": "text",
							},
							{
								"key": "item_funding_reference[].subitem_award_titles[].subitem_award_title_language",
								"title": "言語",
								"title_i18n": {"en": "Language", "ja": "言語"},
								"titleMap": [
									{"name": "ja", "value": "ja"},
									{"name": "ja-Kana", "value": "ja-Kana"},
									{"name": "ja-Latn", "value": "ja-Latn"},
									{"name": "en", "value": "en"},
									{"name": "fr", "value": "fr"},
									{"name": "it", "value": "it"},
									{"name": "de", "value": "de"},
									{"name": "es", "value": "es"},
									{"name": "zh-cn", "value": "zh-cn"},
									{"name": "zh-tw", "value": "zh-tw"},
									{"name": "ru", "value": "ru"},
									{"name": "la", "value": "la"},
									{"name": "ms", "value": "ms"},
									{"name": "eo", "value": "eo"},
									{"name": "ar", "value": "ar"},
									{"name": "el", "value": "el"},
									{"name": "ko", "value": "ko"}
								],
								"type": "select",
							},
						],
						"key": "item_funding_reference[].subitem_award_titles",
						"style": {"add": "btn-success"},
						"title": "研究課題名",
						"title_i18n": {"en": "Award Title", "ja": "研究課題名"},
					},
				],
				"key": "item_funding_reference",
			}
		],
		"schema": {
			"properties": {
				"item_funding_reference": {
					"type": "array",
					"title": "助成情報",
					"minItems": "1",
					"maxItems": "9999",
					"items": {
						"type": "object",
						"properties": {
							"subitem_funder_identifiers": {
								"type": "object",
								"format": "object",
								"properties": {
									"subitem_funder_identifier_type": {
										"type": ["null", "string"],
										"format": "select",
										"enum": [
											None,
											"Crossref Funder",
											"e-Rad_funder",
											"GRID",
											"ISNI",
											"ROR",
											"Other",
										],
										"title": "助成機関識別子タイプ",
									},
									"subitem_funder_identifier": {
										"format": "text",
										"title": "助成機関識別子",
										"type": "string",
									},
								},
								"title": "助成機関識別子",
							},
							"subitem_funder_names": {
								"type": "array",
								"format": "array",
								"items": {
									"type": "object",
									"format": "object",
									"properties": {
										"subitem_funder_name_language": {
											"type": ["null", "string"],
											"format": "select",
											"enum": [
												None,
												"ja",
												"ja-Kana",
												"ja-Latn",
												"en",
												"fr",
												"it",
												"de",
												"es",
												"zh-cn",
												"zh-tw",
												"ru",
												"la",
												"ms",
												"eo",
												"ar",
												"el",
												"ko",
											],
											"title": "言語",
										},
										"subitem_funder_name": {
											"format": "text",
											"title": "助成機関名",
											"type": "string",
										},
									},
								},
								"title": "助成機関名",
							},
							"subitem_funding_stream_identifiers": {
								"type": "object",
								"format": "object",
								"properties": {
									"subitem_funding_stream_identifier_type": {
										"type": ["null", "string"],
										"format": "select",
										"enum": ["Crossref Funder", "JGN_fundingStream"],
										"title": "プログラム情報識別子タイプ",
									},
									"subitem_funding_stream_identifier_type_uri": {
										"format": "text",
										"title": "プログラム情報識別子タイプURI",
										"type": "string",
									},
									"subitem_funding_stream_identifier": {
										"format": "text",
										"title": "プログラム情報識別子",
										"type": "string",
									},
								},
								"title": "プログラム情報識別子",
							},
							"subitem_funding_streams": {
								"type": "array",
								"format": "array",
								"items": {
									"type": "object",
									"format": "object",
									"properties": {
										"subitem_funding_stream_language": {
											"type": ["null", "string"],
											"format": "select",
											"enum": [
												None,
												"ja",
												"ja-Kana",
												"ja-Latn",
												"en",
												"fr",
												"it",
												"de",
												"es",
												"zh-cn",
												"zh-tw",
												"ru",
												"la",
												"ms",
												"eo",
												"ar",
												"el",
												"ko",
											],
											"title": "言語",
										},
										"subitem_funding_stream": {
											"format": "text",
											"title": "プログラム情報",
											"type": "string",
										},
									},
								},
								"title": "プログラム情報",
							},
							"subitem_award_numbers": {
								"type": "object",
								"format": "object",
								"properties": {
									"subitem_award_uri": {
										"format": "text",
										"type": "string",
										"title": "研究課題番号URI",
									},
									"subitem_award_number": {
										"format": "text",
										"title": "研究課題番号",
										"type": "string",
									},
									"subitem_award_number_type": {
										"type": ["null", "string"],
										"format": "select",
										"enum": [None, "JGN"],
										"title": "研究課題番号タイプ",
									},
								},
								"title": "研究課題番号",
							},
							"subitem_award_titles": {
								"type": "array",
								"format": "array",
								"items": {
									"type": "object",
									"format": "object",
									"properties": {
										"subitem_award_title_language": {
											"type": ["null", "string"],
											"format": "select",
											"enum": [
												None,
												"ja",
												"ja-Kana",
												"ja-Latn",
												"en",
												"fr",
												"it",
												"de",
												"es",
												"zh-cn",
												"zh-tw",
												"ru",
												"la",
												"ms",
												"eo",
												"ar",
												"el",
												"ko",
											],
											"title": "言語",
										},
										"subitem_award_title": {
											"format": "text",
											"title": "研究課題名",
											"type": "string",
										},
									},
								},
								"title": "研究課題名",
							},
						},
					}
				}
			},
			"required": []
		},
		"mapping": {
			"item_funding_reference": {
				"display_lang_type": "",
				"jpcoar_v1_mapping": {
					"fundingReference": {
						"funderIdentifier": {
							"@attributes": {
								"funderIdentifierType": "subitem_funder_identifiers.subitem_funder_identifier_type"
							},
							"@value": "subitem_funder_identifiers.subitem_funder_identifier",
						},
						"funderName": {
							"@attributes": {
								"xml:lang": "subitem_funder_names.subitem_funder_name_language"
							},
							"@value": "subitem_funder_names.subitem_funder_name",
						},
						"awardNumber": {
							"@attributes": {
								"awardURI": "subitem_award_numbers.subitem_award_uri",
							},
							"@value": "subitem_award_numbers.subitem_award_number",
						},
						"awardTitle": {
							"@attributes": {
								"xml:lang": "subitem_award_titles.subitem_award_title_language"
							},
							"@value": "subitem_award_titles.subitem_award_title",
						},
					}
				},
				"jpcoar_mapping": {
					"fundingReference": {
						"funderIdentifier": {
							"@attributes": {
								"funderIdentifierType": "subitem_funder_identifiers.subitem_funder_identifier_type",
								"funderIdentifierTypeURI": "subitem_funder_identifiers.subitem_funder_identifier_type_uri",
							},
							"@value": "subitem_funder_identifiers.subitem_funder_identifier",
						},
						"funderName": {
							"@attributes": {
								"xml:lang": "subitem_funder_names.subitem_funder_name_language"
							},
							"@value": "subitem_funder_names.subitem_funder_name",
						},
						"fundingStreamIdentifier": {
							"@attributes": {
								"fundingStreamIdentifierType": "subitem_funding_stream_identifiers.subitem_funding_stream_identifier_type",
								"fundingStreamIdentifierTypeURI": "subitem_funding_stream_identifiers.subitem_funding_stream_identifier_type_uri",
							},
							"@value": "subitem_funding_stream_identifiers.subitem_funding_stream_identifier",
						},
						"fundingStream": {
							"@attributes": {
								"xml:lang": "subitem_funding_streams.subitem_funding_stream_language"
							},
							"@value": "subitem_funding_streams.subitem_funding_stream",
						},
						"awardNumber": {
							"@attributes": {
								"awardURI": "subitem_award_numbers.subitem_award_uri",
								"awardNumberType": "subitem_award_numbers.subitem_award_number_type",
							},
							"@value": "subitem_award_numbers.subitem_award_number",
						},
						"awardTitle": {
							"@attributes": {
								"xml:lang": "subitem_award_titles.subitem_award_title_language"
							},
							"@value": "subitem_award_titles.subitem_award_title",
						},
					}
				},
				"junii2_mapping": "",
				"lido_mapping": "",
				"lom_mapping": "",
				"oai_dc_mapping": "",
				"spase_mapping": "",
			}
		}
	},
	"table_row": ["item_funding_reference"],
	"meta_system": {},
	"meta_list": {
		"item_funding_reference": {
			"title": "助成情報",
			"title_i18n": {"ja": "助成情報", "en": "Funder"},
			"input_type": "cus_1022",
			"input_value": "",
			"input_minItems": "1",
			"input_maxItems": "9999",
			"option": {
				"required": False,
				"multiple": True,
				"hidden": False,
				"showlist": False,
				"crtf": False,
				"oneline": False,
			},
		}
	},
	"schemaeditor": {
		"schema": {
			"item_funding_reference": {
				"format": "object",
				"type": "object",
				"properties": {
					"subitem_funder_identifiers": {
						"type": "object",
						"format": "object",
						"properties": {
							"subitem_funder_identifier_type": {
								"type": ["null", "string"],
								"format": "select",
								"enum": [
									None,
									"Crossref Funder",
									"e-Rad_funder",
									"GRID",
									"ISNI",
									"ROR",
									"Other",
								],
								"title": "助成機関識別子タイプ",
							},
							"subitem_funder_identifier": {
								"format": "text",
								"title": "助成機関識別子",
								"type": "string",
							},
						},
						"title": "助成機関識別子",
					},
					"subitem_funder_names": {
						"type": "array",
						"format": "array",
						"items": {
							"type": "object",
							"format": "object",
							"properties": {
								"subitem_funder_name_language": {
									"type": ["null", "string"],
									"format": "select",
									"enum": [
										None,
										"ja",
										"ja-Kana",
										"ja-Latn",
										"en",
										"fr",
										"it",
										"de",
										"es",
										"zh-cn",
										"zh-tw",
										"ru",
										"la",
										"ms",
										"eo",
										"ar",
										"el",
										"ko",
									],
									"title": "言語",
								},
								"subitem_funder_name": {
									"format": "text",
									"title": "助成機関名",
									"type": "string",
								},
							},
						},
						"title": "助成機関名",
					},
					"subitem_funding_stream_identifiers": {
						"type": "object",
						"format": "object",
						"properties": {
							"subitem_funding_stream_identifier_type": {
								"type": ["null", "string"],
								"format": "select",
								"enum": ["Crossref Funder", "JGN_fundingStream"],
								"title": "プログラム情報識別子タイプ",
							},
							"subitem_funding_stream_identifier_type_uri": {
								"format": "text",
								"title": "プログラム情報識別子タイプURI",
								"type": "string",
							},
							"subitem_funding_stream_identifier": {
								"format": "text",
								"title": "プログラム情報識別子",
								"type": "string",
							},
						},
						"title": "プログラム情報識別子",
					},
					"subitem_funding_streams": {
						"type": "array",
						"format": "array",
						"items": {
							"type": "object",
							"format": "object",
							"properties": {
								"subitem_funding_stream_language": {
									"type": ["null", "string"],
									"format": "select",
									"enum": [
										None,
										"ja",
										"ja-Kana",
										"ja-Latn",
										"en",
										"fr",
										"it",
										"de",
										"es",
										"zh-cn",
										"zh-tw",
										"ru",
										"la",
										"ms",
										"eo",
										"ar",
										"el",
										"ko",
									],
									"title": "言語",
								},
								"subitem_funding_stream": {
									"format": "text",
									"title": "プログラム情報",
									"type": "string",
								},
							},
						},
						"title": "プログラム情報",
					},
					"subitem_award_numbers": {
						"type": "object",
						"format": "object",
						"properties": {
							"subitem_award_uri": {
								"format": "text",
								"type": "string",
								"title": "研究課題番号URI",
							},
							"subitem_award_number": {
								"format": "text",
								"title": "研究課題番号",
								"type": "string",
							},
							"subitem_award_number_type": {
								"type": ["null", "string"],
								"format": "select",
								"enum": [None, "JGN"],
								"title": "研究課題番号タイプ",
							},
						},
						"title": "研究課題番号",
					},
					"subitem_award_titles": {
						"type": "array",
						"format": "array",
						"items": {
							"type": "object",
							"format": "object",
							"properties": {
								"subitem_award_title_language": {
									"type": ["null", "string"],
									"format": "select",
									"enum": [
										None,
										"ja",
										"ja-Kana",
										"ja-Latn",
										"en",
										"fr",
										"it",
										"de",
										"es",
										"zh-cn",
										"zh-tw",
										"ru",
										"la",
										"ms",
										"eo",
										"ar",
										"el",
										"ko",
									],
									"title": "言語",
								},
								"subitem_award_title": {
									"format": "text",
									"title": "研究課題名",
									"type": "string",
								},
							},
						},
						"title": "研究課題名",
					},
				},
			}
		}
	},
	"edit_notes": {
		"item_funding_reference": ""
	}
}

default_schema_funding = {
	"type": "object",
	"properties": {
		"subitem_funder_identifiers": {
			"type": "object",
			"format": "object",
			"properties": {
				"subitem_funder_identifier_type": {
					"type": ["null", "string"],
					"format": "select",
					"enum": [
						None,
						"Crossref Funder",
						"e-Rad_funder",
						"GRID",
						"ISNI",
						"ROR",
						"Other",
					],
					"title": "助成機関識別子タイプ",
				},
				"subitem_funder_identifier": {
					"format": "text",
					"title": "助成機関識別子",
					"type": "string",
				},
			},
			"title": "助成機関識別子",
		},
		"subitem_funder_names": {
			"type": "array",
			"format": "array",
			"items": {
				"type": "object",
				"format": "object",
				"properties": {
					"subitem_funder_name_language": {
						"type": ["null", "string"],
						"format": "select",
						"enum": [
							None,
							"ja",
							"ja-Kana",
							"ja-Latn",
							"en",
							"fr",
							"it",
							"de",
							"es",
							"zh-cn",
							"zh-tw",
							"ru",
							"la",
							"ms",
							"eo",
							"ar",
							"el",
							"ko",
						],
						"title": "言語",
					},
					"subitem_funder_name": {
						"format": "text",
						"title": "助成機関名",
						"type": "string",
					},
				},
			},
			"title": "助成機関名",
		},
		"subitem_funding_stream_identifiers": {
			"type": "object",
			"format": "object",
			"properties": {
				"subitem_funding_stream_identifier_type": {
					"type": ["null", "string"],
					"format": "select",
					"enum": ["Crossref Funder", "JGN_fundingStream"],
					"title": "プログラム情報識別子タイプ",
				},
				"subitem_funding_stream_identifier_type_uri": {
					"format": "text",
					"title": "プログラム情報識別子タイプURI",
					"type": "string",
				},
				"subitem_funding_stream_identifier": {
					"format": "text",
					"title": "プログラム情報識別子",
					"type": "string",
				},
			},
			"title": "プログラム情報識別子",
		},
		"subitem_funding_streams": {
			"type": "array",
			"format": "array",
			"items": {
				"type": "object",
				"format": "object",
				"properties": {
					"subitem_funding_stream_language": {
						"type": ["null", "string"],
						"format": "select",
						"enum": [
							None,
							"ja",
							"ja-Kana",
							"ja-Latn",
							"en",
							"fr",
							"it",
							"de",
							"es",
							"zh-cn",
							"zh-tw",
							"ru",
							"la",
							"ms",
							"eo",
							"ar",
							"el",
							"ko",
						],
						"title": "言語",
					},
					"subitem_funding_stream": {
						"format": "text",
						"title": "プログラム情報",
						"type": "string",
					},
				},
			},
			"title": "プログラム情報",
		},
		"subitem_award_numbers": {
			"type": "object",
			"format": "object",
			"properties": {
				"subitem_award_uri": {
					"format": "text",
					"type": "string",
					"title": "研究課題番号URI",
				},
				"subitem_award_number": {
					"format": "text",
					"title": "研究課題番号",
					"type": "string",
				},
				"subitem_award_number_type": {
					"type": ["null", "string"],
					"format": "select",
					"enum": [None, "JGN"],
					"title": "研究課題番号タイプ",
				},
			},
			"title": "研究課題番号",
		},
		"subitem_award_titles": {
			"type": "array",
			"format": "array",
			"items": {
				"type": "object",
				"format": "object",
				"properties": {
					"subitem_award_title_language": {
						"type": ["null", "string"],
						"format": "select",
						"enum": [
							None,
							"ja",
							"ja-Kana",
							"ja-Latn",
							"en",
							"fr",
							"it",
							"de",
							"es",
							"zh-cn",
							"zh-tw",
							"ru",
							"la",
							"ms",
							"eo",
							"ar",
							"el",
							"ko",
						],
						"title": "言語",
					},
					"subitem_award_title": {
						"format": "text",
						"title": "研究課題名",
						"type": "string",
					},
				},
			},
			"title": "研究課題名",
		},
	},
}
# conftest.py
from __future__ import absolute_import, print_function

import pytest
import shutil
import json
import tempfile
import uuid
from flask import Flask

from invenio_db import InvenioDB
from invenio_records import InvenioRecords
from invenio_search import InvenioSearch
from weko_records import WekoRecords
from weko_workflow import WekoWorkflow
from weko_deposit import WekoDeposit

from invenio_db import db as db_
from sqlalchemy_utils.functions import create_database, database_exists
from weko_records.models import ItemMetadata
from invenio_records.models import RecordMetadata
from weko_workflow.models import (
    Activity,
    ActionStatus,
    Action,
    ActivityAction,
    WorkFlow,
    FlowDefine,
    FlowAction,
    ActionFeedbackMail,
    ActionIdentifier,
    FlowActionRole,
    ActivityHistory,
    GuestActivity, 
    WorkflowRole
)

@pytest.yield_fixture()
def instance_path():
    path = tempfile.mkdtemp()
    yield path
    shutil.rmtree(path)

@pytest.fixture()
def base_app(instance_path):
    """Flask application fixture."""

    app_ = Flask("testapp", instance_path=instance_path)

    app_.config.update(
        INDEXER_DEFAULT_DOCTYPE="item-v1.0.0",
        INDEXER_FILE_DOC_TYPE="content",
        SEARCH_UI_SEARCH_INDEX="test-search-weko"
    #     CELERY_ALWAYS_EAGER=True,
    #     CELERY_CACHE_BACKEND="memory",
    #     CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
    #     CELERY_RESULT_BACKEND="cache",
    #     CACHE_REDIS_URL=os.environ.get(
    #         "CACHE_REDIS_URL", "redis://redis:6379/0"
    #     ),
    #     CACHE_REDIS_DB=0,
    #     CACHE_REDIS_HOST="redis",
    #     REDIS_PORT="6379",
    #     JSONSCHEMAS_URL_SCHEME="http",
    #     SECRET_KEY="CHANGE_ME",
    #     SECURITY_PASSWORD_SALT="CHANGE_ME_ALSO",
    #     SQLALCHEMY_DATABASE_URI=os.environ.get(
    #         'SQLALCHEMY_DATABASE_URI',
    #         'postgresql+psycopg2://invenio:dbpass123@postgresql:5432/wekotest'),
    #     # SQLALCHEMY_DATABASE_URI=os.environ.get(
    #     #     "SQLALCHEMY_DATABASE_URI", "sqlite:///test.db"
    #     # ),
    #     SQLALCHEMY_TRACK_MODIFICATIONS=True,
    #     SQLALCHEMY_ECHO=False,
    #     TESTING=True,
    #     WTF_CSRF_ENABLED=False,
    #     DEPOSIT_SEARCH_API="/api/search",
    #     SECURITY_PASSWORD_HASH="plaintext",
    #     SECURITY_PASSWORD_SCHEMES=["plaintext"],
    #     SECURITY_DEPRECATED_PASSWORD_SCHEMES=[],
    #     OAUTHLIB_INSECURE_TRANSPORT=True,
    #     OAUTH2_CACHE_TYPE="simple",
    #     ACCOUNTS_JWT_ENABLE=False,
    #     INDEXER_DEFAULT_INDEX="{}-weko-item-v1.0.0".format("test"),
    #     SEARCH_UI_SEARCH_INDEX="{}-weko".format("test"),
    #     
    #     INDEXER_DEFAULT_DOC_TYPE="item-v1.0.0",
    #     
    #     WEKO_BUCKET_QUOTA_SIZE=WEKO_BUCKET_QUOTA_SIZE,
    #     WEKO_MAX_FILE_SIZE=WEKO_BUCKET_QUOTA_SIZE,
    #     INDEX_IMG="indextree/36466818-image.jpg",
    #     WEKO_SEARCH_MAX_RESULT=WEKO_SEARCH_MAX_RESULT,
    #     DEPOSIT_REST_ENDPOINTS=DEPOSIT_REST_ENDPOINTS,
    #     WEKO_DEPOSIT_REST_ENDPOINTS=WEKO_DEPOSIT_REST_ENDPOINTS,
    #     WEKO_INDEX_TREE_STYLE_OPTIONS={
    #         "id": "weko",
    #         "widths": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11"],
    #     },
    #     WEKO_INDEX_TREE_UPATED=True,
    #     WEKO_INDEX_TREE_REST_ENDPOINTS=WEKO_INDEX_TREE_REST_ENDPOINTS,
    #     I18N_LANGUAGES=[("ja", "Japanese"), ("en", "English"),("da", "Danish")],
    #     SERVER_NAME="TEST_SERVER",
    #     SEARCH_ELASTIC_HOSTS=os.environ.get("SEARCH_ELASTIC_HOSTS", "elasticsearch"),
    #     SEARCH_INDEX_PREFIX="test-",
    #     WEKO_SCHEMA_JPCOAR_V1_SCHEMA_NAME=WEKO_SCHEMA_JPCOAR_V1_SCHEMA_NAME,
    #     WEKO_SCHEMA_DDI_SCHEMA_NAME=WEKO_SCHEMA_DDI_SCHEMA_NAME,
    #     WEKO_PERMISSION_SUPER_ROLE_USER=[
    #         "System Administrator",
    #         "Repository Administrator",
    #     ],
    #     WEKO_PERMISSION_ROLE_COMMUNITY=["Community Administrator"],
    )

    InvenioDB(app_)
    InvenioRecords(app_)
    InvenioSearch(app_)
    WekoRecords(app_)
    WekoDeposit(app_)
    WekoWorkflow(app_)

    return app_


@pytest.yield_fixture()
def app(base_app):
    with base_app.app_context():
        yield base_app


@pytest.fixture()
def db(app):
    if not database_exists(str(db_.engine.url)):
        create_database(str(db_.engine.url))
    db_.create_all()
    yield db_
    db_.session.remove()
    db_.drop_all()


@pytest.fixture()
def item_data(db):
    obj_uuid1 = uuid.uuid4()
    obj_uuid2 = uuid.uuid4()
    item_meta1 = ItemMetadata(id=obj_uuid1, item_type_id=1, json={"item_0001": {"resourcetype": "periodical"}})
    item_meta2 = ItemMetadata(id=obj_uuid2, item_type_id=1, json={"item_0001": {"resourcetype": "periodical", "resourceuri": ""}})
    rec_meta1 = RecordMetadata(id=obj_uuid1, json={"item_0001": {"attribute_name": "item_resource_type", "attribute_value_mlt": [{"resourcetype": "periodical"}]}})
    rec_meta2 = RecordMetadata(id=obj_uuid2, json={"item_0001": {"attribute_name": "item_resource_type", "attribute_value_mlt": [{"resourcetype": "periodical", "resourceuri": ""}]}})
    db.session.add_all([item_meta1, item_meta2, rec_meta1, rec_meta2])
    db.session.commit()

    return [obj_uuid1, obj_uuid2]

@pytest.fixture()
def action_data(db):
    action_datas=dict()
    with open('tests/data/actions.json', 'r') as f:
        action_datas = json.load(f)
    actions_db = list()
    with db.session.begin_nested():
        for data in action_datas:
            actions_db.append(Action(**data))
        db.session.add_all(actions_db)
    db.session.commit()

    actionstatus_datas = dict()
    with open('tests/data/action_status.json') as f:
        actionstatus_datas = json.load(f)
    actionstatus_db = list()
    with db.session.begin_nested():
        for data in actionstatus_datas:
            actionstatus_db.append(ActionStatus(**data))
        db.session.add_all(actionstatus_db)
    db.session.commit()
    return actions_db, actionstatus_db

